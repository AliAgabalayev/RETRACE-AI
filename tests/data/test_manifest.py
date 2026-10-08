import json

import pytest

from gameqa.contracts import RuleEffect
from gameqa.data import prepare as P
from gameqa.data.manifest import load_eval_labels, load_inference_manifest, rules_from_question

Q_UNITY = (
    "You are a tool.\n\nConsider these variations ACCEPTABLE:\n- Lighting\n- Weather\n\n"
    "Consider these variations UNACCEPTABLE:\n- Missing textures\n\nProvide JSON\n"
)
Q_PLAIN = "Is anything broken?"


def test_rules_split_acceptable_and_unacceptable_blocks_verbatim():
    rules = rules_from_question(Q_UNITY)
    assert [(r.id, r.effect) for r in rules] == [("A1", RuleEffect.ALLOW), ("D1", RuleEffect.DENY)]
    assert rules[0].description == "Consider these variations ACCEPTABLE:\n- Lighting\n- Weather"
    assert rules[1].description == "Consider these variations UNACCEPTABLE:\n- Missing textures"
    assert all("Provide JSON" not in r.description for r in rules)


def test_question_without_criteria_falls_back_to_verbatim_deny_rule():
    rules = rules_from_question(Q_PLAIN)
    assert [r.id for r in rules] == ["D1"]
    assert rules[0].description == "Report a regression: " + Q_PLAIN


def test_parse_label():
    assert P.parse_label('{"test_pass": false}') == "bug"
    assert P.parse_label('{"test_pass": true}') == "no_bug"
    assert P.parse_label("garbage") is None
    assert P.parse_label('{"x": 1}') is None


def test_splits_group_aware_and_deterministic():
    items = []
    for i in range(60):
        items.append({"sample_id": f"s{i}", "group_id": f"g{i // 2 if i < 10 else i}",
                      "label": "no_bug" if i % 4 == 0 else "bug",
                      "source": "Youtube-Cutscene" if i % 2 else "UnityCapturesDataset"})
    a = P.assign_splits(items)
    assert a == P.assign_splits(items)
    by_group = {}
    for it in items:
        by_group.setdefault(it["group_id"], set()).add(a[it["sample_id"]])
    assert all(len(v) == 1 for v in by_group.values())
    assert sum(v == "demo" for v in a.values()) == 5


def test_loaders_and_no_label_keys(tmp_path):
    inf = tmp_path / "i.json"
    inf.write_text(json.dumps([{"sample_id": "a", "reference_path": "r", "candidate_path": "c"}]))
    lab = tmp_path / "l.json"
    lab.write_text(json.dumps({"a": {"ground_truth_raw": "{}", "label": None, "split": "dev"}}))
    assert load_inference_manifest(inf)[0]["sample_id"] == "a"
    assert load_eval_labels(lab)["a"]["split"] == "dev"
    inf.write_text(json.dumps([{"sample_id": "a", "label": "bug"}]))
    with pytest.raises(ValueError):
        load_inference_manifest(inf)


def test_real_manifest_has_no_label_keys_if_present():
    from gameqa.data.manifest import INFERENCE_MANIFEST
    if not INFERENCE_MANIFEST.exists():
        pytest.skip("manifest not generated")
    for rec in load_inference_manifest():
        assert not ({"label", "ground_truth", "ground_truth_raw"} & set(rec))
