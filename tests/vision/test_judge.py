import json

import numpy as np
import pytest
import yaml

from gameqa.contracts import RegionProposal, Rule, Verdict
from gameqa.vision.judge import Judge, validate_response

RULES = [Rule(id="A1", effect="allow", description="lighting may change"),
         Rule(id="D1", effect="deny", description="objects must not disappear")]
BASE = {"observed_change": "x", "change_type": "color_or_lighting", "any_difference": True,
        "verdict": "allowed", "rule_ids": ["A1"], "evidence": "sky darker"}


def v(**kw):
    return validate_response(json.dumps({**BASE, **kw}), RULES)


def test_valid_allowed_and_forbidden():
    assert v()["validated"]
    r = v(verdict="forbidden", rule_ids=["D1"], change_type="disappeared")
    assert r["validated"] and r["verdict"] == Verdict.FORBIDDEN


@pytest.mark.parametrize("raw", ["not json", "[1]", "{\"verdict\": \"allowed\"", ""])
def test_malformed_json_is_uncertain(raw):
    r = validate_response(raw, RULES)
    assert not r["validated"] and r["verdict"] == Verdict.UNCERTAIN and r["errors"]


def test_unknown_rule_id():
    r = v(rule_ids=["Z9"])
    assert not r["validated"] and r["verdict"] == Verdict.UNCERTAIN and "unknown rule" in r["errors"][0]


def test_forbidden_citing_allow_rule_or_without_evidence():
    assert not v(verdict="forbidden", rule_ids=["A1"])["validated"]
    assert not v(verdict="forbidden", rule_ids=["D1"], evidence="")["validated"]
    assert not v(verdict="forbidden", rule_ids=["A1", "D1"])["validated"]


def test_allowed_rules():
    assert not v(rule_ids=["D1"])["validated"]
    assert not v(evidence="")["validated"]
    assert not v(rule_ids=[])["validated"]  # no allow rule and a difference exists
    assert v(rule_ids=[], any_difference=False, change_type="none")["validated"]  # explicit no change
    assert not v(change_type="disappeared")["validated"]  # allowed + disappeared never auto-validated
    assert not v(observed_change="the crate is missing")["validated"]


def test_invalid_verdict_value():
    assert not v(verdict="maybe")["validated"]


def _prop():
    return RegionProposal(id="R1", box=(5, 5, 40, 40), score=1.0, source="dinov2", area_fraction=0.1)


@pytest.mark.parametrize("beh,verdict,validated", [("allowed", Verdict.ALLOWED, True), ("forbidden", Verdict.FORBIDDEN, True),
                                                   ("uncertain", Verdict.UNCERTAIN, True), ("timeout", Verdict.UNCERTAIN, False),
                                                   ("invalid_json", Verdict.UNCERTAIN, False), ("unknown_rule", Verdict.UNCERTAIN, False)])
def test_mock_behaviors_labelled_and_never_raise(beh, verdict, validated):
    cfg = {"vlm": {"provider": "mock", "mock_behavior": beh, "max_attempts": 2}}
    j = Judge(cfg)
    assert j.is_mock and j.model_id == f"mock:{beh}"
    img = np.zeros((60, 60, 3), np.uint8)
    r = j.judge_region(_prop(), img[5:40, 5:40], img[5:40, 5:40], img, img, RULES)
    assert r.is_mock and r.model == f"mock:{beh}" and r.verdict == verdict and r.validated == validated
    if not validated:
        assert r.errors
    a = j.audit_scene(img, img, RULES, [_prop()])
    assert a.judgment.region_id == "SCENE" and a.judgment.is_mock


def test_ollama_unreachable_returns_uncertain_not_exception():
    cfg = {"vlm": {"provider": "ollama", "base_url": "http://127.0.0.1:9", "timeout_s": 1, "max_attempts": 1, "cache": False}}
    j = Judge(cfg)
    img = np.zeros((60, 60, 3), np.uint8)
    r = j.judge_region(_prop(), img[5:40, 5:40], img[5:40, 5:40], img, img, RULES)
    assert r.verdict == Verdict.UNCERTAIN and not r.validated and r.errors and not r.is_mock


def test_tiny_crop_is_upscaled_for_ollama():
    from gameqa.vision.judge import labelled_pair
    a = np.zeros((12, 20, 3), np.uint8)
    im = labelled_pair(a, a, 336)
    assert min(im.shape[:2]) >= 28


def test_recovered_retry_leaves_no_judgment_errors(monkeypatch):
    """QA-D10: attempt 1 fails, attempt 2 answers validly -> no errors carried into the judgment."""
    j = Judge({"vlm": {"provider": "ollama", "base_url": "http://127.0.0.1:9", "max_attempts": 2, "cache": False}})
    calls = {"n": 0}

    def flaky(images, prompt, schema):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("simulated timeout")
        return json.dumps({**BASE, "verdict": "forbidden", "rule_ids": ["D1"], "change_type": "disappeared"})

    monkeypatch.setattr(j, "_ollama_reply", flaky)
    monkeypatch.setattr("gameqa.vision.judge.time.sleep", lambda s: None)
    raw, errors, _ = j._ask([], "p", {}, RULES, False)
    assert raw is not None and errors == [] and calls["n"] == 2


def _dump_judge(tmp_path, with_key=True):
    vlm = {"provider": "mock", "mock_behavior": "allowed"}
    if with_key:
        vlm.update(dump_inputs_dir=str(tmp_path / "dump"), dump_tag="s1")
    return Judge({"vlm": vlm, "run": {"cache_dir": str(tmp_path / "cache")}})


def test_dump_inputs_writes_png_prompt_calls(tmp_path):
    j = _dump_judge(tmp_path)
    img = np.full((60, 60, 3), 90, np.uint8)
    j.judge_region(_prop(), img, img.copy(), img, img, RULES)
    d = tmp_path / "dump" / "s1"
    assert (d / "R1_stage1_1.png").stat().st_size > 0
    assert "5" in (d / "R1_stage1_1.txt").read_text()
    meta = json.loads((d / "R1_stage1_1.json").read_text())
    assert meta["is_mock"] and meta["cache_hit"] is False and meta["stage"] == "stage1" and meta["raw_reply"]
    rec = [json.loads(x) for x in (d / "calls.jsonl").read_text().splitlines()]
    assert rec[0]["is_mock"] is True and rec[0]["model"].startswith("mock:") and rec[0]["cache_hit"] is False


def test_dump_unset_writes_nothing(tmp_path):
    j = _dump_judge(tmp_path, with_key=False)
    img = np.full((60, 60, 3), 90, np.uint8)
    j.judge_region(_prop(), img, img.copy(), img, img, RULES)
    assert j.dump_dir is None and not (tmp_path / "dump").exists()
