import json

import pytest

from gameqa import cli, pipeline

from .conftest import FakeExtractor, FakeJudge


@pytest.fixture
def fake_engines(monkeypatch):
    monkeypatch.setattr(pipeline, "build_engines", lambda cfg: (FakeExtractor(), FakeJudge()))


def _cfg_file(tmp_path):
    f = tmp_path / "c.yaml"
    f.write_text(f"run:\n  artifacts_dir: {tmp_path / 'art'}\n  references_dir: {tmp_path / 'refs'}\n")
    return str(f)


def test_cli_analyze_json_and_approve(pair, patch_vision, fake_engines, tmp_path, capsys):
    rules = tmp_path / "r.yaml"
    rules.write_text('rules:\n - {id: A1, effect: allow, description: "ok"}\n - {id: D1, effect: deny, description: "no"}\n')
    cfgf = _cfg_file(tmp_path)
    rc = cli.main(["analyze", "--reference", pair.reference_path, "--candidate", pair.candidate_path,
                   "--rules", str(rules), "--config", cfgf, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["final_decision"] == "PASS" and (tmp_path / "art" / out["run_id"]).is_dir()
    rc = cli.main(["approve", "--reference-id", "g1", "--run-id", out["run_id"], "--config", cfgf])
    assert rc == 0 and (tmp_path / "refs" / "g1" / "versions" / "v2.png").is_file()


def test_cli_approve_of_non_pass_run_requires_force(pair, patch_vision, fake_engines, tmp_path, capsys):
    rules = tmp_path / "r.yaml"
    rules.write_text('rules:\n - {id: A1, effect: allow, description: "ok"}\n - {id: D1, effect: deny, description: "no"}\n')
    cfgf = _cfg_file(tmp_path)
    cli.main(["analyze", "--reference", pair.reference_path, "--candidate", pair.candidate_path,
              "--rules", str(rules), "--config", cfgf, "--json"])
    out = json.loads(capsys.readouterr().out)
    analysis = tmp_path / "art" / out["run_id"] / "analysis.json"
    saved = json.loads(analysis.read_text())
    saved["final_decision"] = "FAIL"  # simulate a run whose verdict the human overrides
    analysis.write_text(json.dumps(saved))
    rc = cli.main(["approve", "--reference-id", "g2", "--run-id", out["run_id"], "--config", cfgf])
    assert rc == 3 and not (tmp_path / "refs" / "g2").exists()
    rc = cli.main(["approve", "--reference-id", "g2", "--run-id", out["run_id"], "--config", cfgf, "--force"])
    assert rc == 0 and (tmp_path / "refs" / "g2" / "history.json").is_file()


def test_cli_batch_reads_only_inference_fields(pair, patch_vision, fake_engines, tmp_path, capsys):
    manifest = [{"sample_id": "m1", "split": "demo", "reference_path": pair.reference_path,
                 "candidate_path": pair.candidate_path,
                 "rules": [{"id": "Q1", "effect": "deny", "description": "d"}]},
                {"sample_id": "m2", "split": "dev", "reference_path": "x", "candidate_path": "y", "rules": []}]
    mf, out = tmp_path / "m.json", tmp_path / "o.jsonl"
    mf.write_text(json.dumps(manifest))
    rc = cli.main(["batch", "--manifest", str(mf), "--split", "demo", "--out", str(out),
                   "--config", _cfg_file(tmp_path)])
    lines = [json.loads(l) for l in out.read_text().splitlines()]
    assert rc == 0 and [l["sample_id"] for l in lines] == ["m1"]
    assert "ground_truth" not in out.read_text()


def test_batch_row_fields_and_ids_file(pair, patch_vision, fake_engines, tmp_path):
    mk = lambda i: {"sample_id": i, "split": "dev", "reference_path": pair.reference_path,
                    "candidate_path": pair.candidate_path,
                    "rules": [{"id": "Q1", "effect": "deny", "description": "d"}]}
    mf, out, ids = tmp_path / "m.json", tmp_path / "o.jsonl", tmp_path / "ids.json"
    mf.write_text(json.dumps([mk("a"), mk("b")]))
    ids.write_text(json.dumps({"sample_ids": ["b"]}))
    cli.main(["batch", "--manifest", str(mf), "--split", "dev", "--ids-file", str(ids), "--out", str(out),
              "--config", _cfg_file(tmp_path)])
    rows = [json.loads(l) for l in out.read_text().splitlines()]
    assert [r["sample_id"] for r in rows] == ["b"]
    need = {"sample_id", "decision", "execution_status", "engine_mode", "n_regions", "proposals_judged",
            "seconds_total", "prompt_version", "feature_model", "vlm_model", "run_dir"}
    assert need <= set(rows[0]) and rows[0]["vlm_model"] == "fake:test"
