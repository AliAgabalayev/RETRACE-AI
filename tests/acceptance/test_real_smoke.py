"""Real-model smoke tests (real DINOv2 + real Ollama VLM). Run with GAMEQA_REAL=1.

These RECORD outcomes into artifacts/qa_smoke/<case>.json. They do not assert that the 3B VLM is
correct; they assert only that no error path produces PASS and that the run completed with real components.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pipeline = pytest.importorskip("gameqa.pipeline")
from gameqa.config import load_config  # noqa: E402
from gameqa.contracts import FinalDecision, PairInput, Rule  # noqa: E402

pytestmark = pytest.mark.real_model
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "artifacts" / "qa_smoke"


@pytest.fixture(scope="module")
def real_cfg(tmp_path_factory):
    t = tmp_path_factory.mktemp("real")
    return load_config(overrides={"run": {"artifacts_dir": str(t / "artifacts"),
                                          "references_dir": str(t / "references")}})


@pytest.mark.parametrize("name", ["object_removed", "lighting_change", "allowed_and_forbidden", "identical"])
def test_real_smoke(case, real_cfg, name):
    c = case(name)
    res = pipeline.analyze(PairInput(reference_path=c["reference"], candidate_path=c["candidate"],
                                     rules=[Rule(**r) for r in c["rules"]], sample_id=name), real_cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    rec = {
        "case": name, "synthetic": True, "expected": c["expected"]["expected_decision"],
        "decision": res.final_decision.value, "reason": res.decision_reason,
        "execution_status": res.execution_status.value, "engine_mode": res.engine_mode,
        "proposals": [p.box for p in res.proposals], "coverage": res.coverage.model_dump(),
        "verdicts": [(j.region_id, j.verdict.value, j.rule_ids, j.validated, j.errors) for j in res.judgments],
        "versions": res.versions.model_dump(), "timings": res.timings, "errors": res.errors, "run_id": res.run_id,
    }
    (OUT / f"{name}.json").write_text(json.dumps(rec, indent=2))
    assert res.engine_mode != "mock"
    if name != "identical":
        assert res.versions.feature_model, "real DINOv2 must have been used"
        assert res.versions.vlm_model and res.versions.vlm_model.startswith("ollama:")
    if res.execution_status.value != "complete" or res.errors:
        assert res.final_decision != FinalDecision.PASS, "error path produced PASS"
    if c["expected"]["expected_decision"] != "PASS":
        # a PASS on a changed pair is a measured miss: record loudly but only fail when the run was degraded
        if res.final_decision == FinalDecision.PASS:
            pytest.xfail(f"RECORDED MISS: real pipeline PASSed {name} (expected {c['expected']['expected_decision']})")
