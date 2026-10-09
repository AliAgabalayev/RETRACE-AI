import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "ali_select_dev12.py"
OUT = REPO / "configs" / "ali_dev12.json"


def _load():
    spec = importlib.util.spec_from_file_location("ali_select_dev12", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(tmp_path) -> bytes:
    mod = _load()
    # Exercise the actual entrypoint with committed inputs and isolated output.
    # Tests must not regenerate the frozen selection file.
    mod.REPO = tmp_path
    mod.OUT = tmp_path / "ali_dev12.json"
    assert mod.main() == 0
    return mod.OUT.read_bytes()


def test_output_is_byte_identical_across_runs(tmp_path):
    assert _run(tmp_path) == _run(tmp_path)


def test_counts_and_membership(tmp_path):
    data = json.loads(_run(tmp_path))
    manifest = {e["sample_id"]: e for e in json.loads((REPO / "data/manifests/inference_manifest.json").read_text())}
    labels = json.loads((REPO / "data/manifests/eval_labels.json").read_text())
    ids = [r["sample_id"] for r in data["dev12"]]
    assert len(ids) == len(set(ids)) == 12
    assert all(manifest[i]["split"] == "dev" for i in ids)
    assert sum(labels[i]["label"] == "no_bug" for i in ids) == 6
    assert sum(labels[i]["label"] == "bug" and manifest[i]["media_source"] == "UnityCapturesDataset" for i in ids) == 3
    assert sum(labels[i]["label"] == "bug" and manifest[i]["media_source"] == "Youtube-Cutscene" for i in ids) == 3
    six = [r["sample_id"] for r in data["balanced_six"]]
    assert len(six) == 6 and set(six) <= set(ids)
    assert sum(labels[i]["label"] == "no_bug" for i in six) == 3
    assert sum(manifest[i]["media_source"] == "UnityCapturesDataset" for i in six) == 2


def test_json_has_no_label_values(tmp_path):
    text = _run(tmp_path).decode().lower()
    for token in ("no_bug", "test_pass", '"label"', "ground_truth", '"eval"'):
        assert token not in text
    assert "bug" not in text.replace("no label", "")


def test_selection_function_differs_by_seed():
    mod = _load()
    manifest = json.loads((REPO / "data/manifests/inference_manifest.json").read_text())
    labels = json.loads((REPO / "data/manifests/eval_labels.json").read_text())
    a = mod.select(manifest, labels, 1)
    b = mod.select(manifest, labels, 2)
    assert [r["sample_id"] for r in a["dev12"]] != [r["sample_id"] for r in b["dev12"]]
