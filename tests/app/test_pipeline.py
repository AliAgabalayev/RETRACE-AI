import numpy as np
from PIL import Image

from gameqa.contracts import (Coverage, ExecutionStatus, FinalDecision, PairInput, RegionProposal,
                              Verdict)
from gameqa.pipeline import analyze
from gameqa.storage import load_run

from .conftest import RULES, FakeExtractor, FakeJudge


def run(pair, cfg, judge, extractor=None):
    return analyze(pair, cfg, judge=judge, extractor=extractor or FakeExtractor())


def test_forbidden_fails(pair, cfg, patch_vision):
    r = run(pair, cfg, FakeJudge(Verdict.FORBIDDEN, ["D1"]))
    assert r.final_decision == FinalDecision.FAIL
    assert r.engine_mode == "real" and r.execution_status == ExecutionStatus.COMPLETE


def test_all_allowed_passes_and_artifacts_written(pair, cfg, patch_vision, tmp_path):
    r = run(pair, cfg, FakeJudge())
    assert r.final_decision == FinalDecision.PASS
    d = tmp_path / "artifacts" / r.run_id
    for rel in ["analysis.json", "rules.yaml", "report.md", "images/reference.png", "images/candidate.png",
                "images/aligned_candidate.png", "images/overlay.png", "crops/R1_ref.png", "crops/R1_cand.png",
                "diagnostics/heatmap.png", "diagnostics/overlap_mask.png"]:
        assert (d / rel).is_file(), rel
    assert load_run(r.run_id, cfg).final_decision == FinalDecision.PASS
    assert r.versions.feature_model == "fake-dino" and r.versions.vlm_model == "fake:test"
    assert r.versions.config_hash and {"align", "features", "judge", "total"} <= set(r.timings)


def test_crop_uses_reference_box(pair, cfg, patch_vision, tmp_path):
    r = run(pair, cfg, FakeJudge())
    crop = np.asarray(Image.open(tmp_path / "artifacts" / r.run_id / "crops" / "R1_cand.png"))
    assert crop.shape == (40, 50, 3) and (crop == 200).all()


def test_judge_errors_need_review(pair, cfg, patch_vision):
    r = run(pair, cfg, FakeJudge(Verdict.UNCERTAIN, [], errors=["timeout"], validated=False))
    assert r.final_decision == FinalDecision.NEEDS_REVIEW
    assert r.engine_mode == "degraded"


def test_judge_raising_needs_review(pair, cfg, patch_vision):
    assert run(pair, cfg, FakeJudge(raises=True)).final_decision == FinalDecision.NEEDS_REVIEW


def test_extractor_raises_degraded_not_pass(pair, cfg, patch_vision):
    r = run(pair, cfg, FakeJudge(), FakeExtractor(raises=RuntimeError("no weights")))
    assert patch_vision["dino_map_seen"] is None
    assert r.execution_status == ExecutionStatus.DEGRADED and r.engine_mode == "degraded"
    assert r.final_decision == FinalDecision.NEEDS_REVIEW
    assert any("feature extraction failed" in e for e in r.errors)


def test_degraded_still_fails_on_forbidden(pair, cfg, patch_vision):
    r = run(pair, cfg, FakeJudge(Verdict.FORBIDDEN, ["D1"]), FakeExtractor(raises=RuntimeError("x")))
    assert r.final_decision == FinalDecision.FAIL and r.engine_mode == "degraded"


def test_truncation_not_pass(pair, cfg, patch_vision):
    patch_vision["coverage"] = Coverage(proposals_total=12, truncated=True)
    assert run(pair, cfg, FakeJudge()).final_decision == FinalDecision.NEEDS_REVIEW


def test_deadline_exceeded_not_pass(pair, cfg, patch_vision):
    cfg["run"]["deadline_s"] = 0.05
    patch_vision["proposals"] = [
        RegionProposal(id=f"R{i}", box=(10 * i, 10, 10 * i + 8, 30), score=0.5, source="classical",
                       area_fraction=0.01) for i in range(1, 5)
    ]
    patch_vision["coverage"] = Coverage(proposals_total=4)
    judge = FakeJudge(delay=0.1)
    r = run(pair, cfg, judge)
    assert r.coverage.deadline_exceeded and judge.calls < 4
    assert r.final_decision == FinalDecision.NEEDS_REVIEW
    assert not r.coverage.scene_audit_ran


def test_mock_judge_loud_and_not_pass(pair, cfg, patch_vision):
    r = run(pair, cfg, FakeJudge(is_mock=True))
    assert r.engine_mode == "mock" and r.final_decision == FinalDecision.NEEDS_REVIEW


def test_scene_audit_extra_changes_not_pass(pair, cfg, patch_vision):
    assert run(pair, cfg, FakeJudge(audit_extra=True)).final_decision == FinalDecision.NEEDS_REVIEW


def test_invalid_image_needs_review_and_artifacts(pair, cfg, tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    p = PairInput(reference_path=pair.reference_path, candidate_path=str(bad), rules=RULES)
    r = analyze(p, cfg, judge=FakeJudge(), extractor=FakeExtractor())
    assert r.final_decision == FinalDecision.NEEDS_REVIEW
    assert r.execution_status == ExecutionStatus.ERROR and r.errors
    d = tmp_path / "artifacts" / r.run_id
    assert (d / "analysis.json").is_file() and (d / "report.md").is_file()


def test_missing_file_needs_review(cfg, tmp_path):
    p = PairInput(reference_path=str(tmp_path / "x.png"), candidate_path=str(tmp_path / "y.png"), rules=RULES)
    assert analyze(p, cfg).final_decision == FinalDecision.NEEDS_REVIEW


def test_identical_shortcut_recorded(pair, cfg, tmp_path):
    p = PairInput(reference_path=pair.reference_path, candidate_path=pair.reference_path, rules=RULES)
    judge = FakeJudge()
    r = analyze(p, cfg, judge=judge)  # no vision patches needed: shortcut skips models
    assert r.final_decision == FinalDecision.PASS and judge.calls == 0
    assert "pixel-identical" in r.decision_reason
    assert (tmp_path / "artifacts" / r.run_id / "analysis.json").is_file()


def test_empty_rules_not_pass(pair, cfg, patch_vision):
    p = pair.model_copy(update={"rules": []})
    assert run(p, cfg, FakeJudge()).final_decision == FinalDecision.NEEDS_REVIEW


def test_alignment_failure_needs_review(pair, cfg, monkeypatch):
    from gameqa import pipeline

    def boom(*a):
        raise RuntimeError("align boom")

    monkeypatch.setattr(pipeline, "_align", boom)
    r = run(pair, cfg, FakeJudge())
    assert r.final_decision == FinalDecision.NEEDS_REVIEW and r.alignment.status.value == "failed"
