"""Markdown bug-report rendering and box drawing helpers."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

import cv2
import numpy as np

from gameqa.contracts import AnalysisResult, RegionProposal

EVIDENCE_SCHEMA_VERSION = 1
EVIDENCE_FILE = "evidence.json"
CACHE_UNKNOWN = "unknown (replay possible)"

_COLOR = (255, 64, 64)


def draw_boxes(
    image: np.ndarray,
    proposals: list[RegionProposal],
    candidate_to_reference: list[list[float]] | None = None,
) -> np.ndarray:
    """Draw numbered boxes. Boxes are in reference coordinates; if a candidate->reference
    transform is given they are mapped back into the original candidate frame."""
    out = np.ascontiguousarray(image.copy())
    inv = None
    if candidate_to_reference is not None:
        try:
            inv = np.linalg.inv(np.asarray(candidate_to_reference, dtype=np.float64))
        except np.linalg.LinAlgError:
            inv = None
    thick = max(2, round(max(out.shape[:2]) / 400))
    for p in proposals:
        x1, y1, x2, y2 = p.box
        corners = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float64)
        if inv is not None:
            h = np.hstack([corners, np.ones((4, 1))]) @ inv.T
            corners = h[:, :2] / h[:, 2:3]
        pts = np.round(corners).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(out, [pts], True, _COLOR, thick)
        tx, ty = int(pts[0, 0, 0]), int(pts[0, 0, 1])
        scale = max(0.5, max(out.shape[:2]) / 1200)
        cv2.putText(out, p.id, (tx + 2, max(ty - 4, 12)), cv2.FONT_HERSHEY_SIMPLEX, scale, _COLOR, thick)
    return out


def _rules_block(result: AnalysisResult) -> list[str]:
    if not result.rules:
        return ["_No rules were provided._"]
    return [f"- **{r.id}** ({r.effect.value}): {r.description}" for r in result.rules]


def render_report(result: AnalysisResult, run_dir: str | Path | None = None, cfg: dict | None = None) -> str:
    sample = result.sample_id or "n/a"
    lines = [
        f"# Visual regression report: {result.final_decision.value}",
        "",
        f"- Run ID: `{result.run_id}`",
        f"- Sample ID: `{sample}`",
        f"- Created (UTC): {result.created_at}",
        f"- Engine mode: **{result.engine_mode}**"
        + (" (MOCK: not real model inference)" if result.engine_mode == "mock" else ""),
        f"- Execution status: {result.execution_status.value}",
        "",
        "This is an automated screenshot comparison report. It carries no engine/build "
        "metadata and no gameplay reproduction steps; those need human follow-up.",
        "",
        "## Decision",
        "",
        f"**{result.final_decision.value}**: {result.decision_reason}",
        "",
        "## Expected behavior (rules)",
        "",
        *_rules_block(result),
        "",
        "## Observed behavior",
        "",
        "Reference: `images/reference.png`; candidate: `images/candidate.png`; "
        "aligned candidate: `images/aligned_candidate.png`; overlay: `images/overlay.png`.",
        "",
    ]
    if result.judgments:
        for j in result.judgments:
            prop = next((p for p in result.proposals if p.id == j.region_id), None)
            box = f" box={list(prop.box)}" if prop else ""
            lines += [
                f"### {j.region_id} ({j.verdict.value}){box}",
                "",
                f"- Observed change: {j.observed_change or 'n/a'}",
                f"- Applicable rules: {', '.join(j.rule_ids) or 'none cited'}",
                f"- Evidence: {j.evidence or 'n/a'}",
                f"- Model: {j.model}{' (MOCK)' if j.is_mock else ''}; validated: {j.validated}",
            ]
            if j.errors:
                lines.append(f"- Errors: {'; '.join(j.errors)}")
            lines += [
                "",
                f"![{j.region_id} reference](crops/{j.region_id}_ref.png) "
                f"![{j.region_id} candidate](crops/{j.region_id}_cand.png)",
                "",
            ]
    else:
        lines += ["_No regions were judged._", ""]
    if result.scene_audit:
        a = result.scene_audit
        lines += [
            "## Whole-scene audit",
            "",
            f"- Verdict: {a.judgment.verdict.value}",
            f"- Observed: {a.judgment.observed_change or 'n/a'}",
            f"- Rules: {', '.join(a.judgment.rule_ids) or 'none'}",
            f"- Evidence: {a.judgment.evidence or 'n/a'}",
            f"- Extra changes reported outside proposals: {a.extra_changes_reported}",
            f"- Model: {a.judgment.model}{' (MOCK)' if a.judgment.is_mock else ''}",
            "",
        ]
    c = result.coverage
    v = result.versions
    lines += [
        "## Coverage",
        "",
        f"- Proposals judged: {c.proposals_judged}/{c.proposals_total}; truncated: {c.truncated}; "
        f"scene audit ran: {c.scene_audit_ran}; deadline exceeded: {c.deadline_exceeded}",
        f"- Alignment: {result.alignment.status.value if result.alignment else 'n/a'}",
        "",
        "## Versions",
        "",
        f"- Feature model: {v.feature_model}",
        f"- VLM: {v.vlm_model} (prompt {v.prompt_version})",
        f"- Config hash: {v.config_hash}",
        f"- Device/dtype: {v.device}/{v.dtype}",
        "",
        "## Timings (s)",
        "",
        *[f"- {k}: {t:.2f}" for k, t in result.timings.items()],
        "",
    ]
    if result.errors:
        lines += ["## Pipeline errors", "", *[f"- {e}" for e in result.errors], ""]
    lines += _evidence_lines(build_evidence(result, run_dir, cfg))
    return "\n".join(lines)


def _file_facts(run_dir: Path | None, rel: str | None) -> dict:
    """Existence, sha256 and pixel size of one stored artifact; None values when not checkable."""
    facts: dict = {"path": rel, "sha256": None, "width": None, "height": None}
    if run_dir is None or not rel:
        return facts
    f = Path(run_dir) / rel
    if not f.is_file():
        facts["missing"] = True
        return facts
    facts["sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
    try:
        from PIL import Image

        with Image.open(f) as im:
            facts["width"], facts["height"] = im.size
    except Exception:  # noqa: BLE001 - non-image files (rules.yaml) have no size
        pass
    return facts


def _cache_status(result: AnalysisResult, cfg: dict | None) -> dict:
    if result.engine_mode == "mock":
        return {"status": "not applicable (mock engine, no provider call)", "per_stage_recorded": False}
    if cfg is not None and not bool(cfg.get("vlm", {}).get("cache", True)):
        return {"status": "live (vlm.cache disabled in config)", "per_stage_recorded": False}
    return {
        "status": CACHE_UNKNOWN,
        "per_stage_recorded": False,
        "note": "analysis.json does not record per-call cache hits; do not read this run as live.",
    }


def build_evidence(result: AnalysisResult, run_dir: str | Path | None = None, cfg: dict | None = None) -> dict:
    """Evidence sidecar content. Only facts present in the result or on disk; nothing inferred."""
    rd = Path(run_dir) if run_dir is not None else None
    rules = {r.id: r for r in result.rules}
    judged_ids = {j.region_id for j in result.judgments}
    regions = []
    for j in result.judgments:
        prop = next((p for p in result.proposals if p.id == j.region_id), None)
        regions.append({
            "region_id": j.region_id,
            "box": list(prop.box) if prop else None,
            "proposal_source": prop.source if prop else None,
            "proposal_score": prop.score if prop else None,
            "verdict": j.verdict.value,
            "expected_rules": [
                {"id": rid, "effect": rules[rid].effect.value, "description": rules[rid].description}
                if rid in rules else {"id": rid, "effect": None, "description": "unknown rule id"}
                for rid in j.rule_ids
            ],
            "observed_change_vlm_reported": j.observed_change,
            "evidence_text_vlm_reported": j.evidence,
            "reference_crop": _file_facts(rd, result.paths.get(f"{j.region_id}_ref")),
            "candidate_crop": _file_facts(rd, result.paths.get(f"{j.region_id}_cand")),
            "model": j.model,
            "is_mock": j.is_mock,
            "validated": j.validated,
            "errors": list(j.errors),
        })
    scene = None
    if result.scene_audit:
        a = result.scene_audit.judgment
        scene = {
            "verdict": a.verdict.value,
            "observed_change_vlm_reported": a.observed_change,
            "rule_ids": list(a.rule_ids),
            "evidence_text_vlm_reported": a.evidence,
            "extra_changes_reported": result.scene_audit.extra_changes_reported,
            "model": a.model,
            "is_mock": a.is_mock,
            "validated": a.validated,
            "errors": list(a.errors),
        }

    c, al = result.coverage, result.alignment
    assessed, not_assessed = [], []
    assessed.append(f"{c.proposals_judged} of {c.proposals_total} proposed regions judged")
    if c.scene_audit_ran:
        assessed.append("whole-scene audit ran")
    unjudged = [p.id for p in result.proposals if p.id not in judged_ids]
    # Global-change collapse (D10): one full-frame region with truncated=True means the whole frame
    # differed, so no localized region check happened. Distinguish it from the max-region cap.
    global_collapse = (
        c.truncated
        and len(result.proposals) == 1
        and result.proposals[0].area_fraction >= 0.99
        and c.proposals_total == len(result.proposals)
    )
    if global_collapse:
        not_assessed.append(
            "global change: the whole frame differed beyond the collapse threshold, so it was collapsed "
            "into one full-frame region; no localized region-level check was possible"
        )
    elif c.truncated or c.proposals_total > len(result.proposals):
        not_assessed.append(
            f"proposals dropped by the region cap: {c.proposals_total - len(result.proposals)}"
        )
    if unjudged:
        not_assessed.append(f"proposed but not judged: {', '.join(unjudged)}")
    if c.deadline_exceeded:
        not_assessed.append("deadline exceeded; later stages skipped")
    if not c.scene_audit_ran:
        not_assessed.append("whole-scene audit did not run")
    if al is None:
        not_assessed.append("alignment did not run")
    else:
        if al.status.value in ("unreliable", "failed"):
            not_assessed.append(f"alignment {al.status.value}; region comparison is not trustworthy")
        if al.overlap_fraction < 1.0:
            not_assessed.append(
                f"uncompared border: {1.0 - al.overlap_fraction:.1%} of reference pixels have no candidate overlap"
            )
    if result.scene_audit and result.scene_audit.extra_changes_reported:
        not_assessed.append("audit reported extra changes outside proposed regions; they are not localized")
    if not result.proposals and not result.judgments:
        not_assessed.append("no regions were produced or judged")

    v = result.versions
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "run_id": result.run_id,
        "sample_id": result.sample_id,
        "created_at": result.created_at,
        "engine_mode": result.engine_mode,
        "execution_status": result.execution_status.value,
        "inputs": {
            "note": "sha256 and size are of the stored copies inside the run directory, not of the original uploads.",
            "reference": _file_facts(rd, result.paths.get("reference")),
            "candidate": _file_facts(rd, result.paths.get("candidate")),
            "aligned_candidate": _file_facts(rd, result.paths.get("aligned_candidate")),
            "rules_yaml": _file_facts(rd, "rules.yaml"),
        },
        "expected": [
            {"id": r.id, "effect": r.effect.value, "description": r.description} for r in result.rules
        ],
        "regions": regions,
        "scene_audit": scene,
        "alignment": {
            "status": al.status.value if al else None,
            "overlap_fraction": al.overlap_fraction if al else None,
        },
        "scope": {
            "proposals_total": c.proposals_total,
            "proposals_judged": c.proposals_judged,
            "truncated": c.truncated,
            "scene_audit_ran": c.scene_audit_ran,
            "deadline_exceeded": c.deadline_exceeded,
            "assessed": assessed,
            "not_assessed": not_assessed,
        },
        "decision": {
            "final": result.final_decision.value,
            "reason": result.decision_reason,
            "pipeline_errors": list(result.errors),
        },
        "identity": {
            "vlm_model": v.vlm_model,
            "prompt_version": v.prompt_version,
            "config_hash": v.config_hash,
            "feature_model": v.feature_model,
            "device": v.device,
            "dtype": v.dtype,
            "reasoning_effort": (cfg or {}).get("vlm", {}).get("reasoning_effort") if cfg else None,
            "reasoning_effort_note": None if cfg else "not recorded in analysis.json",
        },
        "cache": _cache_status(result, cfg),
        "limitations": (
            "Observed facts are VLM-reported per region and are not independently verified. "
            "No root cause, engine/build metadata or gameplay reproduction steps are known to this report."
        ),
    }


def write_evidence(
    result: AnalysisResult, run_dir: str | Path, cfg: dict | None = None
) -> Path:
    """Write evidence.json atomically into the run directory."""
    run_dir = Path(run_dir)
    path = run_dir / EVIDENCE_FILE
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:6]}.tmp")
    try:
        tmp.write_text(
            json.dumps(build_evidence(result, run_dir, cfg), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def _evidence_lines(ev: dict) -> list[str]:
    inp, sc, ident = ev["inputs"], ev["scope"], ev["identity"]
    lines = ["## Input IDs", "", f"- Run ID: `{ev['run_id']}`; sample ID: `{ev['sample_id'] or 'n/a'}`"]
    for key in ("reference", "candidate", "aligned_candidate", "rules_yaml"):
        f = inp[key]
        size = f"{f['width']}x{f['height']}" if f["width"] else "n/a"
        lines.append(f"- {key}: `{f['path'] or 'n/a'}`; size {size}; sha256 `{f['sha256'] or 'not computed'}`")
    lines += ["- " + inp["note"], "", "## Scope", ""]
    lines += [f"- Assessed: {a}" for a in sc["assessed"]]
    lines += [f"- NOT assessed: {n}" for n in sc["not_assessed"]] or ["- NOT assessed: nothing recorded"]
    effort = ident["reasoning_effort"] or ident["reasoning_effort_note"] or "not set"
    lines += [
        "",
        "## Model identity and cache",
        "",
        f"- VLM: {ident['vlm_model']}; prompt version: {ident['prompt_version']}; "
        f"config hash: {ident['config_hash']}; reasoning effort: {effort}",
        f"- VLM cache status: **{ev['cache']['status']}**",
        "",
        "## Limitations",
        "",
        ev["limitations"],
        "",
        f"Machine-readable evidence: `{EVIDENCE_FILE}`.",
        "",
    ]
    return lines
