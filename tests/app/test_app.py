"""Headless UI checks: fake test engines and recorded replay never perform paid inference."""

from pathlib import Path
import hashlib
import json
import re
import shutil
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


def test_missing_live_key_blocks_analyze_but_allows_saved_replay(app, monkeypatch):
    _analyze_fixture(app)
    calls = app.calls["n"]
    monkeypatch.setenv("GAMEQA_CONFIG", str(Path(__file__).resolve().parents[2] / "configs/openrouter_gemini_pilot.yaml"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    app.run()
    assert not app.exception
    assert next(b for b in app.button if b.label == "Analyze").disabled
    assert any("Live analysis requires OPENROUTER_API_KEY" in w.value for w in app.warning)
    next(b for b in app.sidebar.button if b.label == "Load saved run").click().run()
    assert not app.exception
    assert any(e.value == "Saved run replay — no new inference" for e in app.info)
    assert app.calls["n"] == calls


@pytest.fixture
def public_replay(app, monkeypatch, tmp_path):
    """Use original bundled replay bytes, without inference or regenerated evidence."""
    import gameqa.config as gc
    import gameqa.storage as storage

    root = Path(__file__).resolve().parents[2]
    source = root / "deploy/replay/barrel"
    stored = json.loads((source / "analysis.json").read_text())
    run = tmp_path / "deploy/replay/barrel"
    shutil.copytree(source, run)
    shutil.copytree(root / "configs", tmp_path / "configs")
    monkeypatch.setattr(gc, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("GAMEQA_PUBLIC_REPLAY", "1")
    monkeypatch.setenv("GAMEQA_CONFIG", str(root / "configs/openrouter_gemini_pilot.yaml"))
    # Deliberately nonsecret test value: presence must never enable public inference.
    monkeypatch.setenv("OPENROUTER_API_KEY", "qa-only-not-a-credential")
    calls = []

    def forbidden(operation):
        def fail(*args, **kwargs):
            calls.append(operation)
            raise AssertionError(f"Public replay invoked forbidden operation: {operation}")
        return fail

    monkeypatch.setattr(gc, "load_env_file", forbidden("local dotenv loading"))
    monkeypatch.setattr(pipeline, "build_engines", forbidden("engine construction"))
    monkeypatch.setattr(pipeline, "analyze", forbidden("new inference"))
    monkeypatch.setattr(storage, "approve_reference", forbidden("reference approval"))
    monkeypatch.setattr(storage, "export_report", forbidden("evidence regeneration"))
    return app, run, stored, calls


def _file_hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob("*") if p.is_file()}


def test_public_replay_defaults_to_recorded_barrel_and_shows_original_results(public_replay):
    app, run, stored, calls = public_replay
    app.run()
    assert not app.exception, app.exception
    assert any(e.value == "Recorded model run — replay, no new inference." for e in app.info)
    assert any(e.value.startswith("**FAIL") for e in app.error)
    assert stored["run_id"] == "20261009T123704Z-8e4e19"
    assert any(stored["run_id"] in e.value for e in app.caption)
    assert app.dataframe[0].value.to_dict("records") == stored["rules"]
    displayed = "\n".join(e.value for e in app.markdown)
    for judgment in stored["judgments"]:
        assert judgment["observed_change"] in displayed
        assert judgment["evidence"] in displayed
    assert stored["scene_audit"]["judgment"]["observed_change"] in displayed
    image_count = len(app.get("image")) + len(app.get("imgs"))
    assert image_count >= 2 + 2 * len(stored["proposals"])
    assert not calls


def test_public_replay_has_no_mutation_controls_even_when_host_key_exists(public_replay):
    app, run, stored, calls = public_replay
    app.run()
    assert not app.exception, app.exception
    button_labels = {b.label for b in app.button}
    assert not button_labels.intersection({"Analyze", "Approve as new reference",
                                           "Compare new screenshots", "Reload models"})
    assert not any(r.label in {"Pair source", "VLM engine"} for r in app.radio)
    assert not any(s.label == "Mock behavior" for s in app.selectbox)
    assert not app.get("file_uploader")
    assert not app.get("data_editor")
    assert not app.checkbox
    assert not calls


@pytest.mark.parametrize("static", [False, True])
def test_public_missing_original_archive_is_explicit_and_never_regenerated(public_replay, monkeypatch, static):
    app, run, stored, calls = public_replay
    monkeypatch.setenv("GAMEQA_PUBLIC_STATIC", "1" if static else "0")
    before = _file_hashes(run)
    app.run()
    app.run()
    assert not app.exception, app.exception
    messages = [e.value for e in list(app.error) + list(app.warning) + list(app.info)]
    assert any("original" in m.lower() and "zip" in m.lower() for m in messages), messages
    assert not app.get("download_button")
    assert not any('download="' in element.proto.body for element in app.get("html"))
    assert not run.with_suffix(".zip").exists()
    assert _file_hashes(run) == before
    assert not calls


@pytest.mark.parametrize("static", [False, True])
def test_public_rerun_preserves_existing_archive_bytes(public_replay, monkeypatch, static):
    """Fault-injection ZIP is QA-only; it is never represented as original evidence."""
    app, run, stored, calls = public_replay
    monkeypatch.setenv("GAMEQA_PUBLIC_STATIC", "1" if static else "0")
    archive = run.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w") as zipped:
        prefix = stored["run_id"] + "/"
        zipped.writestr(prefix + "analysis.json", (run / "analysis.json").read_bytes())
        zipped.writestr(prefix + "evidence.json", json.dumps({
            "decision": {"final": "FAIL"}, "test_fixture": "QA archive byte-preservation simulation"}))
        zipped.writestr(prefix + "report.md", "QA simulation; this is not original run evidence.")
        zipped.writestr(prefix + "provider-capture/qa.txt", "QA preservation sentinel")
    # This anchor is changed only in the disposable QA fixture; the repository's
    # historical source_zip_sha256 is never edited or represented by this ZIP.
    manifest_path = run / "package.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["source_zip_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    before = archive.read_bytes()
    hashes = _file_hashes(run)
    app.run()
    app.run()
    assert not app.exception, app.exception
    if static:
        assert not app.get("download_button")
        html = "\n".join(element.proto.body for element in app.get("html"))
        assert 'href="/app/static/replay/barrel.zip"' in html
        assert f'download="{stored["run_id"]}.zip"' in html
        assert not any("Portable replay export" in element.value for element in app.caption)
    else:
        assert any(e.label == "Download evidence ZIP" for e in app.get("download_button"))
    assert archive.read_bytes() == before
    assert _file_hashes(run) == hashes
    assert not calls


@pytest.mark.parametrize("static", [False, True])
def test_public_rejects_untrusted_archive_without_replacing_it(public_replay, monkeypatch, static):
    app, run, stored, calls = public_replay
    monkeypatch.setenv("GAMEQA_PUBLIC_STATIC", "1" if static else "0")
    archive = run.with_suffix(".zip")
    archive.write_bytes(b"QA-only corrupted archive; not original evidence")
    before = archive.read_bytes()
    app.run()
    assert not app.exception, app.exception
    assert not app.get("download_button")
    assert not any('download="' in element.proto.body for element in app.get("html"))
    assert any("checksum" in e.value.lower() or "hash" in e.value.lower()
               for e in list(app.error) + list(app.warning))
    assert archive.read_bytes() == before
    assert not calls


def _qa_reconstructed_export(public_replay, *, omitted_asset=None, changed_asset=None):
    """QA-only fallback: preserve original bundled bytes, label rebuilt metadata."""
    app, run, stored, calls = public_replay
    manifest = json.loads((run / "package.json").read_text())
    archive = run.parent / "barrel-replay.zip"
    provenance = {"kind": "reconstructed_replay_export", "run_id": stored["run_id"],
                  "original_source_zip_sha256": manifest["source_zip_sha256"],
                  "note": "QA replay fixture; report and evidence index reconstructed, original ZIP unavailable."}
    with zipfile.ZipFile(archive, "w") as zipped:
        prefix = stored["run_id"] + "/"
        for relative in manifest["files"]:
            if relative != omitted_asset:
                data = (run / relative).read_bytes()
                if relative == changed_asset:
                    data = b"QA-only changed original asset: must be rejected"
                zipped.writestr(prefix + relative, data)
        zipped.writestr(prefix + "package.json", (run / "package.json").read_bytes())
        zipped.writestr(prefix + "report.md", "QA reconstructed replay report; not the original report.")
        zipped.writestr(prefix + "evidence.json", json.dumps({
            "run_id": stored["run_id"], "decision": {"final": "FAIL"}, "provenance": provenance}))
        zipped.writestr(prefix + "export-provenance.json", json.dumps(provenance))
    descriptor = {**provenance, "archive_name": archive.name,
                  "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    (run.parent / "barrel-replay-export.json").write_text(json.dumps(descriptor))
    return archive


def test_public_reconstructed_replay_download_is_labelled_and_immutable(public_replay):
    app, run, stored, calls = public_replay
    archive = _qa_reconstructed_export(public_replay)
    before = _file_hashes(run.parent)
    app.run()
    app.run()
    assert not app.exception, app.exception
    assert any(e.label == "Download evidence ZIP" for e in app.get("download_button"))
    messages = "\n".join(e.value for e in list(app.caption) + list(app.warning) + list(app.info))
    assert "original run files preserved" in messages.lower()
    assert "report and evidence index reconstructed" in messages.lower()
    assert "original zip unavailable" in messages.lower()
    assert any(e.value.startswith("**FAIL") for e in app.error)
    assert _file_hashes(run.parent) == before
    assert not calls
    with zipfile.ZipFile(archive) as zipped:
        manifest = json.loads((run / "package.json").read_text())
        for relative, expected in manifest["files"].items():
            assert hashlib.sha256(zipped.read(stored["run_id"] + "/" + relative)).hexdigest() == expected


def test_public_reconstructed_replay_rejects_archive_hash_mismatch(public_replay):
    app, run, stored, calls = public_replay
    archive = _qa_reconstructed_export(public_replay)
    archive.write_bytes(archive.read_bytes() + b"QA-only archive corruption")
    before = _file_hashes(run.parent)
    app.run()
    assert not app.exception, app.exception
    assert not app.get("download_button")
    assert any("checksum" in e.value.lower() or "hash" in e.value.lower() for e in app.error)
    assert _file_hashes(run.parent) == before
    assert not calls


@pytest.mark.parametrize("omitted_asset,changed_asset", [
    ("images/candidate.png", None), (None, "rules.yaml"),
])
def test_public_reconstructed_replay_rejects_missing_or_changed_original_asset(
        public_replay, omitted_asset, changed_asset):
    app, run, stored, calls = public_replay
    _qa_reconstructed_export(public_replay, omitted_asset=omitted_asset, changed_asset=changed_asset)
    before = _file_hashes(run.parent)
    app.run()
    assert not app.exception, app.exception
    assert not app.get("download_button")
    assert any("asset" in e.value.lower() or "checksum" in e.value.lower()
               or (omitted_asset is not None and omitted_asset in e.value)
               for e in app.error)
    assert _file_hashes(run.parent) == before
    assert not calls


def _image_urls(app):
    return [image.url for element in app.get("image") for image in element.proto.imgs]


def test_public_static_replay_uses_original_file_urls_and_validated_download(public_replay, monkeypatch):
    app, run, stored, calls = public_replay
    _qa_reconstructed_export(public_replay)
    monkeypatch.setenv("GAMEQA_PUBLIC_STATIC", "1")
    before = _file_hashes(run.parent)
    app.run()
    app.run()
    assert not app.exception, app.exception
    html = "\n".join(element.proto.body for element in app.get("html"))
    urls = re.findall(r'<img[^>]* src="([^"]+)"', html)
    expected = ["images/reference.png", "images/candidate.png", "diagnostics/heatmap.png",
                "diagnostics/overlap_mask.png"]
    expected += [f"crops/{p['id']}_{side}.png" for p in stored["proposals"] for side in ("ref", "cand")]
    assert set(urls) == {"/app/static/replay/barrel/" + relative for relative in expected}
    assert not app.get("image")
    assert 'alt="Reference · original screenshot"' in html
    assert 'alt="Candidate · original screenshot"' in html
    assert not app.get("download_button")
    assert 'href="/app/static/replay/barrel-replay.zip"' in html
    assert f'download="{stored["run_id"]}-replay.zip"' in html
    assert "Download evidence ZIP" in html
    assert any("Original ZIP unavailable" in element.value for element in app.caption)
    assert any(element.value.startswith("**FAIL") for element in app.error)
    assert _file_hashes(run.parent) == before
    assert not calls


def test_public_static_replay_rejects_corrupt_download(public_replay, monkeypatch):
    app, run, stored, calls = public_replay
    archive = _qa_reconstructed_export(public_replay)
    archive.write_bytes(archive.read_bytes() + b"QA-only corruption")
    monkeypatch.setenv("GAMEQA_PUBLIC_STATIC", "1")
    before = _file_hashes(run.parent)
    app.run()
    assert not app.exception, app.exception
    html = "\n".join(element.proto.body for element in app.get("html"))
    assert 'download="' not in html
    assert any("checksum" in element.value.lower() for element in app.error)
    assert _file_hashes(run.parent) == before
    assert not calls


def test_static_flag_keeps_local_reference_approval_and_native_download(app, monkeypatch):
    monkeypatch.setenv("GAMEQA_PUBLIC_STATIC", "1")
    _analyze_fixture(app)
    assert not app.exception, app.exception
    assert any(button.label == "Approve as new reference" for button in app.button)
    assert any(element.label == "Download evidence ZIP" for element in app.get("download_button"))
    assert all(not url.startswith("/app/static/") for url in _image_urls(app))
