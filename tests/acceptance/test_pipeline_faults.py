"""Pipeline fault-injection acceptance tests.

MOCK-BASED: every judge here is a labelled mock/stub (is_mock=True) or an explicitly named
StubRealJudge that stands in for a *validated real* VLM answer so policy plumbing can be probed.
None of these results is evidence about real model quality.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from tests.acceptance.helpers import MockJudge, ZeroExtractor

pipeline = pytest.importorskip("gameqa.pipeline")
from gameqa.config import load_config  # noqa: E402
from gameqa.contracts import (  # noqa: E402
    ExecutionStatus,
    FinalDecision,
    PairInput,
    Rule,
    RegionJudgment,
    SceneAudit,
    Verdict,
)
from gameqa.storage import approve_reference, load_run  # noqa: E402

PASS, FAIL, REVIEW = FinalDecision.PASS, FinalDecision.FAIL, FinalDecision.NEEDS_REVIEW
REPO = Path(__file__).resolve().parents[2]


class StubRealJudge(MockJudge):
    """TEST STUB posing as a real, validated VLM (is_mock=False) with a fixed verdict.

    Only used to check pipeline/policy plumbing (e.g. extractor failure must not become PASS).
    """

    model_id = "stub:validated-real"
    is_mock = False

    def __init__(self, behaviour="allowed", **kw):
        super().__init__(behaviour, **kw)

    def _j(self, region_id):
        j = super()._j(region_id)
        return j.model_copy(update={"is_mock": False, "model": self.model_id})


@pytest.fixture
def cfg(tmp_path):
    return load_config(overrides={"run": {"artifacts_dir": str(tmp_path / "artifacts"),
                                          "references_dir": str(tmp_path / "references"),
                                          "cache_dir": str(tmp_path / "cache")}})


def pair_of(c, rules=None):
    rules = c["rules"] if rules is None else rules
    return PairInput(reference_path=c["reference"], candidate_path=c["candidate"],
                     rules=[Rule(**r) for r in rules], sample_id=c["dir"].name)


def run(cfg, c, judge, extractor=None, rules=None):
    return pipeline.analyze(pair_of(c, rules), cfg, judge=judge, extractor=extractor or ZeroExtractor())


# ---------------------------------------------------------------- mock judges never FAIL/PASS
@pytest.mark.parametrize("behaviour", ["allowed", "forbidden", "uncertain", "timeout", "invalid_json", "unknown_rule"])
def test_qa_mock_judge_never_pass_or_fail(case, cfg, behaviour):
    res = run(cfg, case("object_removed"), MockJudge(behaviour))
    assert res.final_decision == REVIEW
    assert res.engine_mode == "mock"
    assert res.execution_status != ExecutionStatus.COMPLETE


@pytest.mark.parametrize("behaviour", ["allowed", "forbidden", "uncertain", "timeout", "invalid_json", "unknown_rule"])
def test_dl_mock_provider_never_pass_or_fail(case, cfg, behaviour):
    from gameqa.vision.judge import Judge

    cfg = {**cfg, "vlm": {**cfg["vlm"], "provider": "mock", "mock_behavior": behaviour}}
    res = run(cfg, case("object_removed"), Judge(cfg))
    assert res.final_decision == REVIEW, res.decision_reason
    assert res.engine_mode == "mock"
    assert all(j.is_mock for j in res.judgments)


def test_judge_raising_is_review_not_crash(case, cfg):
    class Boom(StubRealJudge):
        def judge_region(self, *a, **k):
            raise RuntimeError("provider exploded")

    res = run(cfg, case("object_removed"), Boom("allowed"))
    assert res.final_decision == REVIEW


def test_audit_raising_is_review(case, cfg):
    class Boom(StubRealJudge):
        def audit_scene(self, *a, **k):
            raise RuntimeError("audit exploded")

    res = run(cfg, case("object_removed"), Boom("allowed"))
    assert res.final_decision == REVIEW and not res.coverage.scene_audit_ran


def test_audit_extra_changes_reported_is_review(case, cfg):
    res = run(cfg, case("object_removed"), StubRealJudge("allowed", audit_extra=True))
    assert res.final_decision == REVIEW


# ---------------------------------------------------------------- degraded components
def test_extractor_load_failure_is_degraded_not_pass(case, cfg, monkeypatch):
    from gameqa.vision.features import ModelLoadError

    def boom(_cfg):
        raise ModelLoadError("weights unavailable (injected)")

    monkeypatch.setattr(pipeline, "build_extractor", boom)
    c = case("object_removed")
    res = pipeline.analyze(pair_of(c), cfg, judge=StubRealJudge("allowed"), extractor=None)
    assert res.final_decision == REVIEW, res.decision_reason
    assert res.execution_status == ExecutionStatus.DEGRADED
    assert res.engine_mode == "degraded"
    assert any("feature" in e for e in res.errors)


def test_reliable_forbidden_survives_extractor_failure(case, cfg, monkeypatch):
    monkeypatch.setattr(pipeline, "build_extractor", lambda _c: (_ for _ in ()).throw(RuntimeError("x")))
    res = pipeline.analyze(pair_of(case("object_removed")), cfg, judge=StubRealJudge("forbidden"), extractor=None)
    assert res.final_decision == FAIL
    assert res.execution_status == ExecutionStatus.DEGRADED  # still reported as degraded


def test_control_stub_allowed_with_working_extractor_can_pass(case, cfg):
    """Control: proves the REVIEW outcomes above come from the injected fault, not from the stub."""
    res = run(cfg, case("lighting_change"), StubRealJudge("allowed"))
    assert res.final_decision == PASS, res.decision_reason


def test_truncation_blocks_pass(tmp_path, cfg):
    spec = importlib.util.spec_from_file_location("make_fixtures", REPO / "scripts" / "make_fixtures.py")
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    ref, cand = mf.render(1), mf.render(1, remove=("tree", "barrel", "character"))
    mf.save_png(tmp_path / "r.png", ref)
    mf.save_png(tmp_path / "c.png", cand)
    c = {"reference": str(tmp_path / "r.png"), "candidate": str(tmp_path / "c.png"), "rules": mf.RULES_STD,
         "dir": tmp_path}
    cfg1 = load_config(overrides={"proposals": {"max_regions": 1}, "run": cfg["run"]})
    res = run(cfg1, c, StubRealJudge("allowed"))
    assert res.coverage.truncated and res.coverage.proposals_total > 1
    assert res.final_decision == REVIEW
    # control: with the default cap the same pair is not truncated
    res2 = run(cfg, c, StubRealJudge("allowed"))
    assert not res2.coverage.truncated


def test_deadline_blocks_pass(case, cfg):
    cfg0 = load_config(overrides={"run": {**cfg["run"], "deadline_s": 0}})
    res = run(cfg0, case("object_removed"), StubRealJudge("allowed"))
    assert res.final_decision == REVIEW
    assert res.coverage.deadline_exceeded


# ---------------------------------------------------------------- inputs
def test_identical_images_pass_without_models(case, cfg):
    res = pipeline.analyze(pair_of(case("identical")), cfg, judge=None, extractor=None)
    assert res.final_decision == PASS and res.alignment.status.value == "identity"


def test_corrupt_upload_needs_review_no_crash(case, cfg):
    res = run(cfg, case("corrupt_upload"), StubRealJudge("allowed"))
    assert res.final_decision == REVIEW
    assert res.execution_status == ExecutionStatus.ERROR
    assert any("candidate" in e for e in res.errors)


def test_missing_file_needs_review(cfg, tmp_path):
    p = PairInput(reference_path=str(tmp_path / "nope.png"), candidate_path=str(tmp_path / "nope2.png"),
                  rules=[Rule(id="A1", effect="allow", description="x")])
    res = pipeline.analyze(p, cfg, judge=StubRealJudge("allowed"), extractor=ZeroExtractor())
    assert res.final_decision == REVIEW


def test_empty_rules_never_pass(case, cfg):
    res = run(cfg, case("empty_rules"), StubRealJudge("allowed"))
    assert res.final_decision == REVIEW


def test_conflicting_rules_never_pass(case, cfg):
    res = run(cfg, case("conflicting_rules"), StubRealJudge("allowed"))
    assert res.final_decision != PASS


def test_large_misalignment_never_pass(case, cfg):
    res = run(cfg, case("large_misalignment"), StubRealJudge("allowed"))
    assert res.final_decision == REVIEW and res.alignment.status.value == "unreliable"


def test_translation_with_removed_object_not_pass(case, cfg):
    res = run(cfg, case("translation_object_removed"), StubRealJudge("forbidden"))
    assert res.final_decision == FAIL


# ---------------------------------------------------------------- artifacts / storage
def test_artifacts_written(case, cfg):
    res = run(cfg, case("object_removed"), StubRealJudge("forbidden"))
    root = Path(cfg["run"]["artifacts_dir"]) / res.run_id
    assert (root / "analysis.json").is_file() and (root / "report.md").is_file()
    crops = sorted(p.name for p in (root / "crops").glob("*.png"))
    assert crops and any(n.endswith("_ref.png") for n in crops) and any(n.endswith("_cand.png") for n in crops)
    for rel in res.paths.values():
        assert (root / rel).is_file(), rel
    data = json.loads((root / "analysis.json").read_text())
    assert data["final_decision"] == "FAIL" and data["versions"]["config_hash"]
    assert load_run(res.run_id, cfg).final_decision == FAIL
    assert "FAIL" in (root / "report.md").read_text()


def test_mock_report_is_labelled(case, cfg):
    res = run(cfg, case("object_removed"), MockJudge("forbidden"))
    report = (Path(cfg["run"]["artifacts_dir"]) / res.run_id / "report.md").read_text().lower()
    assert "mock" in report


def test_repeated_analysis_distinct_run_ids(case, cfg):
    c = case("object_removed")
    ids = {run(cfg, c, StubRealJudge("allowed")).run_id for _ in range(3)}
    assert len(ids) == 3


def test_approve_reference_preserves_history(case, cfg):
    c = case("object_removed")
    res = run(cfg, c, StubRealJudge("forbidden"))
    r1 = approve_reference("scene1", c["candidate"], res.run_id, cfg, previous_reference_path=c["reference"])
    res2 = run(cfg, case("lighting_change"), StubRealJudge("allowed"))
    r2 = approve_reference("scene1", case("lighting_change")["candidate"], res2.run_id, cfg)
    refdir = Path(cfg["run"]["references_dir"]) / "scene1"
    versions = sorted(p.name for p in (refdir / "versions").glob("v*.png"))
    assert versions == ["v1.png", "v2.png", "v3.png"], versions  # baseline + 2 approvals
    hist = json.loads((refdir / "history.json").read_text())["events"]
    assert len(hist) == 3 and hist[-1]["new_version"] == "v3" and hist[-1]["previous_version"] == "v2"
    assert r1["new_version"] == "v2" and r2["new_version"] == "v3"
    import hashlib
    assert hashlib.sha256((refdir / "versions/v2.png").read_bytes()).hexdigest() == hist[1]["sha256"]
    # benchmark source file untouched
    assert Path(c["candidate"]).is_file() and Path(c["reference"]).is_file()


def test_approve_rejects_path_traversal(case, cfg):
    c = case("object_removed")
    res = run(cfg, c, StubRealJudge("forbidden"))
    with pytest.raises(Exception):
        approve_reference("../evil", c["candidate"], res.run_id, cfg)
    with pytest.raises(Exception):
        approve_reference("ok", c["candidate"], "../../etc", cfg)
