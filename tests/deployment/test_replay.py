"""Portable real historical replay must seed and export without any model/provider."""
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

import pytest

from gameqa import config
from gameqa.storage import load_run, zip_path_for


def test_keyless_seed_exports_and_preserves_existing_run(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("prepare_deployment", root / "scripts/prepare_deployment.py")
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    shutil.copytree(root / "deploy/replay/barrel", tmp_path / "deploy/replay/barrel")
    shutil.copytree(root / "configs", tmp_path / "configs")
    monkeypatch.setattr(seed, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    run = seed.prepare()
    cfg = config.load_config(tmp_path / "configs/openrouter_gemini_pilot.yaml")
    assert config.config_hash(cfg) == "eaa371255716"
    assert load_run(run.name, cfg).final_decision.value == "FAIL"
    zpath = zip_path_for(run)
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        assert run.name + "/evidence.json" in z.namelist()
        assert run.name + "/crops/R1_cand.png" in z.namelist()
    before = zpath.read_bytes()
    assert seed.prepare() == run
    assert zpath.read_bytes() == before


@pytest.fixture
def public_package(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("prepare_public_qa", root / "scripts/prepare_deployment.py")
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    source = tmp_path / "deploy/replay/barrel"
    shutil.copytree(root / "deploy/replay/barrel", source)
    shutil.copytree(root / "configs", tmp_path / "configs")
    monkeypatch.setattr(seed, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "qa-only-not-a-credential")
    def forbid(*args, **kwargs):
        raise AssertionError("Public startup regenerated historical evidence")
    monkeypatch.setattr(seed, "export_report", forbid)
    return seed, source


def test_public_startup_returns_verified_immutable_package_without_generating_evidence(public_package):
    seed, source = public_package
    before = {str(p.relative_to(source)): p.read_bytes() for p in source.rglob("*") if p.is_file()}
    assert seed.prepare(public_replay=True) == source
    assert seed.prepare(public_replay=True) == source
    assert {str(p.relative_to(source)): p.read_bytes() for p in source.rglob("*") if p.is_file()} == before
    manifest = json.loads((source / "package.json").read_text())
    for relative, expected in manifest["files"].items():
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == expected
    assert not source.with_suffix(".zip").exists()
    assert not (source.parents[2] / "artifacts").exists()


def test_public_startup_rejects_changed_original_asset_without_mutation(public_package):
    seed, source = public_package
    damaged = source / "images/candidate.png"
    damaged.write_bytes(b"QA-only corruption, never an original asset")
    before = damaged.read_bytes()
    with pytest.raises(RuntimeError, match="checksum"):
        seed.prepare(public_replay=True)
    assert damaged.read_bytes() == before
    assert not (source.parents[2] / "artifacts").exists()


@pytest.mark.parametrize("public_flag", ["1", " 1 "])
def test_public_entrypoint_preserves_public_mode_and_strips_provider_key(monkeypatch, public_flag):
    """Fault injection: capture launch arguments; do not start a server or inference."""
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    spec = importlib.util.spec_from_file_location("start_public_qa", root / "scripts/start_deployment.py")
    startup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(startup)
    monkeypatch.setenv("GAMEQA_PUBLIC_REPLAY", public_flag)
    monkeypatch.setenv("OPENROUTER_API_KEY", "qa-only-not-a-credential")
    monkeypatch.setenv("PORT", "8642")
    prepared = []
    launched = []
    monkeypatch.setattr(startup, "prepare", lambda **kwargs: prepared.append(kwargs))
    monkeypatch.setattr(startup.os, "chdir", lambda path: None)

    def capture_launch(command):
        launched.append(command)
        credential_present = "OPENROUTER_API_KEY" in startup.os.environ
        assert credential_present is False
        return 0

    monkeypatch.setattr(startup.subprocess, "call", capture_launch)
    with pytest.raises(SystemExit) as exit_info:
        startup.main()
    assert exit_info.value.code == 0
    assert prepared == [{"public_replay": True}]
    assert len(launched) == 1
    assert launched[0][1:5] == ["-m", "streamlit", "run", "app.py"]
    assert launched[0][launched[0].index("--server.port") + 1] == "8642"
