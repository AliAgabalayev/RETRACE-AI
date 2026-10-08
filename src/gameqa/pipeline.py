"""End-to-end analysis: validate -> align -> features -> propose -> crops -> judge -> decide.

All PASS/FAIL/NEEDS_REVIEW logic lives in ``gameqa.decision``; this module only
passes truthful coverage and errors to it and writes artifacts.
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from gameqa.config import config_hash
from gameqa.contracts import (
    AlignmentResult,
    AlignmentStatus,
    AnalysisResult,
    Coverage,
    ExecutionStatus,
    PairInput,
    RegionJudgment,
    SceneAudit,
    Verdict,
    Versions,
)
from gameqa.decision import DecisionInput, decide
from gameqa.imageio import ImageError, LoadedImage, load_image, save_png
from gameqa.report import draw_boxes, render_report
from gameqa.rules import dump_rules
from gameqa.storage import new_run_dir, utc_now_iso, write_json_atomic, write_text_atomic

SCENE_ID = "SCENE"


# Thin lazy wrappers so this module imports (and tests can patch them) without torch/vision.
def _align(reference, candidate, cfg):
    from gameqa.vision.alignment import align

    return align(reference, candidate, cfg)


def _propose(reference, aligned, mask, dino_map, cfg):
    from gameqa.vision.proposals import propose

    return propose(reference, aligned, mask, dino_map, cfg)


def build_extractor(cfg: dict):
    from gameqa.vision.features import FeatureExtractor

    return FeatureExtractor(cfg)


def build_judge(cfg: dict):
    from gameqa.vision.judge import Judge

    return Judge(cfg)


def _identity_alignment(status: AlignmentStatus, overlap: float) -> AlignmentResult:
    return AlignmentResult(
        status=status,
        candidate_to_reference=np.eye(3).tolist(),
        overlap_fraction=overlap,
    )


def _failed_judgment(region_id: str, judge, exc: Exception) -> RegionJudgment:
    return RegionJudgment(
        region_id=region_id,
        observed_change="",
        verdict=Verdict.UNCERTAIN,
        model=str(getattr(judge, "model_id", "unknown")),
        is_mock=bool(getattr(judge, "is_mock", False)),
        errors=[f"judge raised {exc.__class__.__name__}: {exc}"],
    )


def _clip_box(box, h: int, w: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return max(0, x1), max(0, y1), min(w, x2), min(h, y2)


def _heatmap_image(dino_map: np.ndarray) -> np.ndarray:
    m = np.nan_to_num(dino_map.astype(np.float32))
    lo, hi = float(m.min()), float(m.max())
    norm = ((m - lo) / (hi - lo) * 255).astype(np.uint8) if hi > lo else np.zeros_like(m, np.uint8)
    return cv2.cvtColor(cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO), cv2.COLOR_BGR2RGB)


class _Run:
    """Mutable bookkeeping for one analysis (timings, errors, paths)."""

    def __init__(self, pair: PairInput, cfg: dict, run_id: str, run_dir: Path):
        self.pair, self.cfg, self.run_id, self.run_dir = pair, cfg, run_id, run_dir
        self.t0 = time.perf_counter()
        self.timings: dict[str, float] = {}
        self.errors: list[str] = []
        self.paths: dict[str, str] = {}

    def elapsed(self) -> float:
        return time.perf_counter() - self.t0

    def stage(self, name: str, start: float) -> None:
        self.timings[name] = round(time.perf_counter() - start, 4)

    def save_image(self, rel: str, key: str, array: np.ndarray) -> None:
        save_png(self.run_dir / rel, array)
        self.paths[key] = rel


def analyze(
    pair: PairInput,
    cfg: dict,
    *,
    judge=None,
    extractor=None,
    run_dir: str | Path | None = None,
) -> AnalysisResult:
    if run_dir is None:
        run_id, rdir = new_run_dir(cfg)
    else:
        rdir = Path(run_dir)
        run_id = rdir.name
        for sub in ("images", "crops", "diagnostics"):
            (rdir / sub).mkdir(parents=True, exist_ok=True)
    run = _Run(pair, cfg, run_id, rdir)
    write_text_atomic(rdir / "rules.yaml", dump_rules(pair.rules))

    versions = Versions(config_hash=config_hash(cfg))
    is_mock = bool(getattr(judge, "is_mock", False))
    result = _analyze_inner(run, versions, judge, extractor, is_mock)
    result.timings["total"] = round(run.elapsed(), 4)
    write_text_atomic(rdir / "report.md", render_report(result))
    write_json_atomic(rdir / "analysis.json", result.model_dump(mode="json"))
    return result


def _finish(run: _Run, **kw) -> AnalysisResult:
    return AnalysisResult(
        run_id=run.run_id,
        sample_id=run.pair.sample_id,
        created_at=utc_now_iso(),
        rules=run.pair.rules,
        timings=run.timings,
        errors=run.errors,
        paths=run.paths,
        **kw,
    )


def _analyze_inner(run: _Run, versions: Versions, judge, extractor, is_mock: bool) -> AnalysisResult:
    cfg, pair = run.cfg, run.pair
    mode = "mock" if is_mock else "real"

    # 1. Input validation
    t = time.perf_counter()
    loaded: dict[str, LoadedImage] = {}
    for key, path in (("reference", pair.reference_path), ("candidate", pair.candidate_path)):
        try:
            loaded[key] = load_image(path, cfg)
            run.save_image(f"images/{key}.png", key, loaded[key].array)
        except ImageError as exc:
            run.errors.append(f"invalid {key} image: {exc}")
    run.stage("load", t)
    if len(loaded) < 2:
        decision, reason = decide(
            DecisionInput(pair.rules, [], None, Coverage(), None, inputs_valid=False,
                          pipeline_errors=list(run.errors))
        )
        return _finish(run, execution_status=ExecutionStatus.ERROR, final_decision=decision,
                       decision_reason=reason, versions=versions, engine_mode=mode)

    ref, cand = loaded["reference"].array, loaded["candidate"].array

    # 2. Identical shortcut (recorded, no models)
    if ref.shape == cand.shape and np.array_equal(ref, cand):
        alignment = _identity_alignment(AlignmentStatus.IDENTITY, 1.0)
        run.save_image("images/aligned_candidate.png", "aligned_candidate", cand)
        decision, reason = decide(
            DecisionInput(pair.rules, [], None, Coverage(), alignment, identical_images=True)
        )
        return _finish(run, execution_status=ExecutionStatus.COMPLETE, final_decision=decision,
                       decision_reason=reason, alignment=alignment, versions=versions, engine_mode=mode)

    # 3. Alignment
    t = time.perf_counter()
    try:
        alignment, aligned, mask = _align(ref, cand, cfg)
    except Exception as exc:  # noqa: BLE001 - must not crash the run
        run.errors.append(f"alignment failed: {exc.__class__.__name__}: {exc}")
        alignment = _identity_alignment(AlignmentStatus.FAILED, 0.0)
        alignment.diagnostics["error"] = str(exc)
        aligned = mask = None
    run.stage("align", t)
    if aligned is not None:
        run.save_image("images/aligned_candidate.png", "aligned_candidate", aligned)
        run.save_image("diagnostics/overlap_mask.png", "overlap_mask", mask)
        alignment = alignment.model_copy(update={"overlap_mask_path": "diagnostics/overlap_mask.png"})
    if aligned is None:
        decision, reason = decide(
            DecisionInput(pair.rules, [], None, Coverage(), alignment, pipeline_errors=list(run.errors))
        )
        return _finish(run, execution_status=ExecutionStatus.ERROR, final_decision=decision,
                       decision_reason=reason, alignment=alignment, versions=versions, engine_mode=mode)

    degraded = False

    # 4. Features (failure -> classical-only proposals)
    t = time.perf_counter()
    dino_map = None
    try:
        extractor = extractor if extractor is not None else build_extractor(cfg)
        versions.feature_model = getattr(extractor, "version", None)
        versions.device = getattr(extractor, "device", None)
        versions.dtype = getattr(extractor, "dtype", None)
        dino_map = extractor.distance_map(ref, aligned)
    except Exception as exc:  # noqa: BLE001
        degraded = True
        dino_map = None
        run.errors.append(f"feature extraction failed, classical-only proposals: {exc.__class__.__name__}: {exc}")
    run.stage("features", t)
    if dino_map is not None:
        run.save_image("diagnostics/heatmap.png", "heatmap", _heatmap_image(dino_map))

    # 5. Proposals
    t = time.perf_counter()
    try:
        proposals, coverage = _propose(ref, aligned, mask, dino_map, cfg)
        coverage = coverage.model_copy()
    except Exception as exc:  # noqa: BLE001
        proposals, coverage = [], Coverage()
        run.errors.append(f"proposal generation failed: {exc.__class__.__name__}: {exc}")
    run.stage("propose", t)

    # 6. Crops (same reference box on reference and aligned candidate)
    t = time.perf_counter()
    h, w = ref.shape[:2]
    crops: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for p in proposals:
        x1, y1, x2, y2 = _clip_box(p.box, h, w)
        if x2 <= x1 or y2 <= y1:
            run.errors.append(f"{p.id}: box {list(p.box)} outside image")
            continue
        rc, cc = ref[y1:y2, x1:x2], aligned[y1:y2, x1:x2]
        crops[p.id] = (rc, cc)
        run.save_image(f"crops/{p.id}_ref.png", f"{p.id}_ref", rc)
        run.save_image(f"crops/{p.id}_cand.png", f"{p.id}_cand", cc)
    run.save_image("images/overlay.png", "overlay", draw_boxes(ref, proposals))
    run.stage("crops", t)

    # 7. Judge regions, then scene audit, within the deadline
    deadline = float(cfg["run"]["deadline_s"])
    judgments: list[RegionJudgment] = []
    scene_audit: SceneAudit | None = None
    judge_failed = False
    try:
        judge = judge if judge is not None else build_judge(cfg)
        versions.vlm_model = getattr(judge, "model_id", None)
        versions.prompt_version = getattr(judge, "prompt_version", None)
        is_mock = bool(getattr(judge, "is_mock", False))
        mode = "mock" if is_mock else "real"
    except Exception as exc:  # noqa: BLE001
        judge_failed = True
        run.errors.append(f"judge unavailable: {exc.__class__.__name__}: {exc}")

    if not judge_failed:
        t = time.perf_counter()
        for p in proposals:
            if p.id not in crops:
                continue
            if run.elapsed() > deadline:
                coverage.deadline_exceeded = True
                run.errors.append(f"deadline of {deadline:g}s exceeded before judging {p.id}")
                break
            rc, cc = crops[p.id]
            try:
                judgments.append(judge.judge_region(p, rc, cc, ref, aligned, pair.rules))
            except Exception as exc:  # noqa: BLE001
                judgments.append(_failed_judgment(p.id, judge, exc))
        run.stage("judge", t)

        t = time.perf_counter()
        if run.elapsed() > deadline:
            coverage.deadline_exceeded = True
            run.errors.append(f"deadline of {deadline:g}s exceeded before scene audit")
        else:
            try:
                scene_audit = judge.audit_scene(ref, aligned, pair.rules, proposals)
                coverage.scene_audit_ran = True
            except Exception as exc:  # noqa: BLE001
                run.errors.append(f"scene audit failed: {exc.__class__.__name__}: {exc}")
        run.stage("audit", t)

    coverage.proposals_judged = len(judgments)
    # Only component failures (provider errors, timeouts, exceptions) degrade the engine. A real
    # model answer rejected by validation is still real inference; decide() turns it into review.
    all_j = judgments + ([scene_audit.judgment] if scene_audit else [])
    judge_errors = any(_is_component_failure(e) for j in all_j for e in j.errors)
    if degraded or judge_errors or judge_failed:
        mode = "mock" if is_mock else "degraded"

    if judge_failed:
        status = ExecutionStatus.ERROR
    elif degraded or judge_errors or is_mock or run.errors:
        status = ExecutionStatus.DEGRADED
    else:
        status = ExecutionStatus.COMPLETE

    decision, reason = decide(
        DecisionInput(pair.rules, judgments, scene_audit, coverage, alignment,
                      pipeline_errors=list(run.errors))
    )
    return _finish(
        run, execution_status=status, final_decision=decision, decision_reason=reason,
        alignment=alignment, proposals=proposals, judgments=judgments, scene_audit=scene_audit,
        coverage=coverage, versions=versions, engine_mode=mode,
    )


class UnavailableExtractor:
    """Stand-in used when the real extractor failed to load once; keeps the failure visible."""

    version = device = dtype = None

    def __init__(self, error: Exception):
        self.error = error

    def distance_map(self, reference, aligned):
        raise RuntimeError(f"feature extractor unavailable: {self.error.__class__.__name__}: {self.error}")


_COMPONENT_FAILURE_MARKERS = ("provider error", "failure:", "timeout", "timed out", "unavailable")


def _is_component_failure(error: str) -> bool:
    low = error.lower()
    return any(m in low for m in _COMPONENT_FAILURE_MARKERS)


def build_engines(cfg: dict):
    """Build (extractor, judge) once for reuse; load failures become visible degraded modes."""
    # dl-engineer: warm the VLM FIRST. Ollama refuses to load the CPU-resident qwen2.5vl:3b (~9.7 GiB) when
    # torch/CUDA has already consumed RAM, and a cold load takes ~70 s. warmup() never raises.
    judge = _try_judge(cfg)
    if judge is not None and hasattr(judge, "warmup"):
        judge.warmup()
    try:
        extractor = build_extractor(cfg)
    except Exception as exc:  # noqa: BLE001
        extractor = UnavailableExtractor(exc)
    return extractor, judge


def _try_judge(cfg: dict):
    try:
        return build_judge(cfg)
    except Exception:  # noqa: BLE001 - analyze() records "judge unavailable" itself
        return None
