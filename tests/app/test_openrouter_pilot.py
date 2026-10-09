"""Offline mock run verifies the pilot observer accepts Ali's stage-aware Judge API."""
import hashlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from gameqa.config import load_config


def test_stage_aware_observer_records_mock_without_network(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / "scripts/openrouter_pilot.py"
    spec = importlib.util.spec_from_file_location("pilot_under_test", path)
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    pilot.REPO = tmp_path
    pilot.OUT = tmp_path / "outputs"
    pilot.OUT.mkdir()
    pilot.CUTOFF = datetime.now(timezone.utc) + timedelta(minutes=1)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-placeholder")
    monkeypatch.setattr("sys.argv", [str(path), "--mode", "B"])
    cfg = load_config(overrides={"vlm": {"provider": "mock", "mock_behavior": "allowed"}})
    monkeypatch.setattr("gameqa.config.load_config", lambda *a, **k: cfg)
    def refuse_network(*args, **kwargs):
        pytest.fail("offline observer check must never contact a provider")
    monkeypatch.setattr("httpx.post", refuse_network)
    monkeypatch.setattr("httpx.get", refuse_network)
    sample_id = "synthetic_observer"
    monkeypatch.setattr(pilot.subprocess, "check_output", lambda *a, **k:
                        json.dumps({"dev12": [{"sample_id": sample_id}]}).encode())
    bundle = tmp_path / "artifacts/c1-demo-20261009/bundle" / sample_id
    bundle.mkdir(parents=True)
    image = b"synthetic test input; helper uses its own mock array"
    for side in ("reference", "candidate"):
        (bundle / (side + ".png")).write_bytes(image)
    inventory = {"samples": [{"sample_id": sample_id, "source": "synthetic",
        "rules": [], "images": {side: {"sha256": hashlib.sha256(image).hexdigest()}
                                 for side in ("reference", "candidate")}}]}
    (bundle.parents[1] / "inventory.json").write_text(json.dumps(inventory))
    (pilot.OUT / "model-metadata.json").write_text(json.dumps({
        "pricing": {"prompt": "0", "completion": "0"},
        "top_provider": {"context_length": 1, "max_completion_tokens": 1}}))
    (pilot.OUT / "Ali_a1_run.py").write_text('''import numpy as np
def git_commit(): return 'offline-test'
def run_B(rec, ctx):
    judge = ctx['build_judge'](ctx['cfg'])
    raw, errors, latency = judge._two_stage([np.zeros((8, 8, 3), np.uint8)],
                                           'offline observation', True, [], 'test')
    assert raw is not None and errors == []
    return {'decision': 'PASS', 'is_mock': True}
''')
    pilot.main()
    row = json.loads((pilot.OUT / "B/predictions.jsonl").read_text())
    stage = json.loads((pilot.OUT / "stages.jsonl").read_text())
    assert row["is_mock"] and row["attempts"] == 0
    assert stage["attempts"] == 0 and stage["stage"] == "observation"
    assert not (pilot.OUT / "calls.jsonl").exists()
