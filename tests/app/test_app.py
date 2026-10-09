"""Headless Streamlit checks (AppTest). Engines are fakes; mock mode is exercised for banners."""

from pathlib import Path
import hashlib
import json
import zipfile

import pytest
from streamlit.testing.v1 import AppTest

from gameqa import pipeline
from gameqa.contracts import Verdict

from .conftest import FakeExtractor, FakeJudge


@pytest.fixture
def app(cfg, patch_vision, monkeypatch, tmp_path):
    import gameqa.config as gc

    calls = {"n": 0}
    real_load = gc.load_config

    def load(path=None, overrides=None):
        return real_load(path, {"run": {"artifacts_dir": str(tmp_path / "artifacts"),
                                        "references_dir": str(tmp_path / "references")},
                                **(overrides or {})})

    monkeypatch.setattr(gc, "load_config", load)
    judge = FakeJudge(Verdict.FORBIDDEN, ["D1"])

    def engines(c):
        calls["n"] += 1
        return FakeExtractor(), judge

    monkeypatch.setattr(pipeline, "build_engines", engines)
    at = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"), default_timeout=30)
    at.calls = calls
    return at


def test_demo_analyze_does_not_rerun_inference(app, tmp_path):
    app.run()
    assert not app.exception
    [r for r in app.radio if r.label == "Pair source"][0].set_value("Demo pair").run()
    if "synthetic fixture | object_removed" not in app.selectbox[-1].options:
        pytest.skip("fixture not available")
    app.selectbox[-1].set_value("synthetic fixture | object_removed").run()
    app.button[0].click().run()
    assert not app.exception, app.exception
    banners = [e.value for e in list(app.error) + list(app.warning) + list(app.success)]
    assert any(b.startswith("**FAIL") for b in banners), banners
    judge_calls = app.calls["n"]
    app.run()  # plain rerun
    assert app.calls["n"] == judge_calls
    app.button[0].click().run()  # same inputs again -> cached run
    assert app.calls["n"] == judge_calls
    assert len(list((tmp_path / "artifacts").glob("*/analysis.json"))) == 1


def _analyze_fixture(app):
    app.run()
    next(r for r in app.radio if r.label == "Pair source").set_value("Demo pair").run()
    demo = next(s for s in app.selectbox if s.label == "Demo pair")
    if "synthetic fixture | object_removed" not in demo.options:
        pytest.skip("fixture not available")
    demo.set_value("synthetic fixture | object_removed").run()
    next(b for b in app.button if b.label == "Analyze").click().run()
    assert not app.exception


def test_saved_replay_shows_stored_rules_and_preserves_export(app, tmp_path):
    _analyze_fixture(app)
    analysis_path = next((tmp_path / "artifacts").glob("*/analysis.json"))
    saved = json.loads(analysis_path.read_text())
    archive = analysis_path.parent.with_suffix(".zip")
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr(f"{saved['run_id']}/provider-capture/original.txt", "original evidence")
    before = hashlib.sha256(archive.read_bytes()).hexdigest()
    calls = app.calls["n"]
    app.run()  # refresh Saved runs list
    next(b for b in app.sidebar.button if b.label == "Load saved run").click().run()
    assert not app.exception
    assert any(e.value == "Saved run replay — no new inference" for e in app.info)
    assert app.dataframe[0].value.to_dict("records") == saved["rules"]
    assert not any(b.label == "Analyze" for b in app.button)
    assert any(e.value.startswith("**FAIL") for e in app.error)
    assert app.calls["n"] == calls
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == before
    with zipfile.ZipFile(archive) as z:
        assert json.loads(z.read(f"{saved['run_id']}/analysis.json"))["run_id"] == saved["run_id"]
        assert json.loads(z.read(f"{saved['run_id']}/evidence.json"))["decision"]["final"] == "FAIL"
    next(b for b in app.button if b.label == "Compare new screenshots").click().run()
    assert not app.exception
    assert any(b.label == "Analyze" for b in app.button)
    assert app.calls["n"] == calls


def test_approval_stays_open_and_requires_both_confirmations(app):
    _analyze_fixture(app)
    approve = lambda: next(b for b in app.button if b.label == "Approve as new reference")
    assert approve().disabled
    next(t for t in app.text_input if t.label == "Reference ID").set_value("c4_isolated_test").run()
    assert not app.exception
    assert next(e for e in app.expander if e.label == "Approve as new reference").proto.expanded
    next(c for c in app.checkbox if c.label == "I confirm this candidate becomes the new reference").check().run()
    assert approve().disabled
    next(c for c in app.checkbox if c.label == "I reviewed the regions and override the verdict").check().run()
    assert not approve().disabled
    next(c for c in app.checkbox if c.label == "I confirm this candidate becomes the new reference").uncheck().run()
    assert approve().disabled


def test_frozen_demo_uses_inventory_rules_and_blocks_changed_inputs(app, monkeypatch, tmp_path):
    import gameqa.config as gc
    from PIL import Image
    root = tmp_path / "demo_repo"
    bundle = root / "artifacts/c1-demo-20261009/bundle/vr_4b921c5d"
    bundle.mkdir(parents=True)
    hashes = {}
    for side in ("reference", "candidate"):
        path = bundle / f"{side}.png"
        Image.new("RGB", (20, 20), "white").save(path)
        hashes[side] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    rules = [{"id": "D1", "effect": "deny", "description": "Exact frozen test rule"}]
    (bundle.parents[1] / "inventory.json").write_text(json.dumps({"samples": [
        {"sample_id": "vr_4b921c5d", "rules": rules, "images": hashes}]}))
    monkeypatch.setattr(gc, "REPO_ROOT", root)
    manifest = root / "data/manifests/inference_manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps([{"split": "demo", "sample_id": "unavailable_example",
        "reference_path": "missing_reference.png", "candidate_path": "missing_candidate.png"}]))
    app.run()
    next(r for r in app.radio if r.label == "Pair source").set_value("Demo pair").run()
    assert not app.exception
    assert next(s for s in app.selectbox if s.label == "Demo pair").value == "Frozen dev demo | vr_4b921c5d"
    assert next(s for s in app.selectbox if s.label == "Demo pair").options == ["Frozen dev demo | vr_4b921c5d"]
    assert app.dataframe[0].value.to_dict("records") == rules
    assert not next(b for b in app.button if b.label == "Analyze").disabled
    Image.new("RGB", (20, 20), "black").save(bundle / "candidate.png")
    app.run()
    assert any("hash does not match" in e.value for e in app.error)
    assert next(b for b in app.button if b.label == "Analyze").disabled
    assert app.calls["n"] == 0
