"""Portable real historical replay must seed and export without any model/provider."""
import importlib.util
from pathlib import Path
import shutil
import zipfile

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
