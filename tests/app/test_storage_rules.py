import json
import zipfile

import numpy as np
import pytest
from PIL import Image

from gameqa.contracts import FinalDecision, RuleEffect
from gameqa.imageio import ImageError, decode_image, load_image
from gameqa.pipeline import analyze
from gameqa.config import config_hash, deep_merge, load_config
from gameqa.rules import RulesError, dump_rules, load_rules, parse_rules
from gameqa.storage import (StorageError, approve_reference, export_report, list_runs, load_run,
                            new_run_dir, safe_join, write_json_atomic, zip_path_for)

from .conftest import FakeExtractor, FakeJudge


def test_rules_example_roundtrip():
    rules = load_rules("configs/rules_example.yaml")
    assert [r.id for r in rules] == ["A1", "A2", "D1", "D2"]
    assert rules[2].effect == RuleEffect.DENY
    assert parse_rules(dump_rules(rules)) == rules


def test_rules_verbatim_multiline_unicode():
    from gameqa.contracts import Rule
    desc = "  Line one: with colon # and hash\nsecond line – ə  "
    out = parse_rules(dump_rules([Rule(id="A1", effect="allow", description=desc)]))
    assert out[0].description == desc


def test_rules_duplicate_and_invalid():
    with pytest.raises(RulesError):
        parse_rules("rules:\n - {id: A, effect: allow, description: x}\n - {id: A, effect: deny, description: y}")
    with pytest.raises(RulesError):
        parse_rules("rules:\n - {id: A, effect: maybe, description: x}")
    assert parse_rules("") == []


def test_config_merge_and_hash():
    c = load_config(overrides={"run": {"deadline_s": 5}})
    assert c["run"]["deadline_s"] == 5 and c["run"]["artifacts_dir"] == "artifacts"
    assert config_hash(c) != config_hash(load_config())
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    assert deep_merge({"a": {"x": 1}}, {"a": {"y": 2}}) == {"a": {"x": 1, "y": 2}}


def test_imageio_limits(tmp_path, cfg):
    p = tmp_path / "a.png"
    Image.fromarray(np.zeros((10, 10, 4), np.uint8)).save(p)
    img = load_image(p, cfg)
    assert img.array.shape == (10, 10, 3) and img.array.dtype == np.uint8 and len(img.sha256) == 64
    cfg["input"]["max_pixels"] = 50
    with pytest.raises(ImageError):
        load_image(p, cfg)
    with pytest.raises(ImageError):
        decode_image(b"garbage", load_config())
    with pytest.raises(ImageError):
        decode_image(b"", load_config())


def test_imageio_format_limit(tmp_path, cfg):
    p = tmp_path / "a.gif"
    Image.fromarray(np.zeros((4, 4, 3), np.uint8)).save(p, format="GIF")
    with pytest.raises(ImageError):
        load_image(p, cfg)


def test_atomic_write_leaves_no_tmp(tmp_path):
    p = tmp_path / "d" / "x.json"
    write_json_atomic(p, {"a": 1})
    write_json_atomic(p, {"a": 2})
    assert json.loads(p.read_text()) == {"a": 2}
    assert [f.name for f in p.parent.iterdir()] == ["x.json"]


def test_path_validation(tmp_path, cfg):
    with pytest.raises(StorageError):
        safe_join(tmp_path, "..", "etc")
    with pytest.raises(StorageError):
        safe_join(tmp_path, "/etc/passwd")
    with pytest.raises(StorageError):
        load_run("../../etc", cfg)
    with pytest.raises(StorageError):
        approve_reference("../evil", "x.png", "run", cfg)


def test_new_run_dirs_unique(cfg):
    a, da = new_run_dir(cfg)
    b, db = new_run_dir(cfg)
    assert a != b and (da / "images").is_dir() and (db / "crops").is_dir()


def _analyzed(pair, cfg, patch_vision):
    return analyze(pair, cfg, judge=FakeJudge(), extractor=FakeExtractor())


def test_export_creates_report_and_zip(pair, cfg, patch_vision, tmp_path):
    r = _analyzed(pair, cfg, patch_vision)
    run_dir = tmp_path / "artifacts" / r.run_id
    report = export_report(r, run_dir)
    text = report.read_text()
    assert report.name == "report.md" and r.run_id in text and "D1" in text and "R1" in text
    assert "Build ID" not in text and "build id" not in text.lower().replace("no engine/build", "")
    names = zipfile.ZipFile(zip_path_for(run_dir)).namelist()
    assert f"{r.run_id}/analysis.json" in names and f"{r.run_id}/report.md" in names
    assert f"{r.run_id}/crops/R1_ref.png" in names


def test_list_and_load_runs(pair, cfg, patch_vision):
    r = _analyzed(pair, cfg, patch_vision)
    rows = list_runs(cfg)
    assert rows[0]["run_id"] == r.run_id and rows[0]["final_decision"] == "PASS"
    assert load_run(r.run_id, cfg).final_decision == FinalDecision.PASS


def test_approve_keeps_history(pair, cfg, patch_vision, tmp_path):
    r = _analyzed(pair, cfg, patch_vision)
    cand = tmp_path / "artifacts" / r.run_id / "images" / "candidate.png"
    ref = tmp_path / "artifacts" / r.run_id / "images" / "reference.png"
    first = approve_reference("game1", cand, r.run_id, cfg, previous_reference_path=ref)
    assert first["previous_version"] == "v1" and first["new_version"] == "v2"
    second = approve_reference("game1", ref, r.run_id, cfg)
    assert second["previous_version"] == "v2" and second["new_version"] == "v3"
    vdir = tmp_path / "references" / "game1" / "versions"
    assert sorted(p.name for p in vdir.iterdir()) == ["v1.png", "v2.png", "v3.png"]
    hist = json.loads((tmp_path / "references" / "game1" / "history.json").read_text())
    assert [e["new_version"] for e in hist["events"]] == ["v1", "v2", "v3"]
    assert all(e["run_id"] == r.run_id and len(e["sha256"]) == 64 and e["timestamp"] for e in hist["events"])
    assert np.array_equal(np.asarray(Image.open(vdir / "v1.png")), np.asarray(Image.open(ref)))


def test_approve_unknown_run(cfg, tmp_path):
    with pytest.raises(StorageError):
        approve_reference("g", tmp_path / "x.png", "nope", cfg)


def test_rules_unquoted_yaml_bool_rejected_not_mangled():
    with pytest.raises(RulesError, match="quotes"):
        parse_rules("rules:\n - {id: A1, effect: allow, description: no}")
    out = parse_rules(dump_rules(parse_rules("rules:\n - {id: A1, effect: allow, description: 'no'}")))
    assert out[0].description == "no"
