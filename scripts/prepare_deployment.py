"""Seed portable historical barrel replay into frozen relative storage; never overwrite runs."""
import hashlib
import json
from pathlib import Path
import shutil

from gameqa.config import REPO_ROOT, load_config, resolve_dir, config_hash
from gameqa.contracts import AnalysisResult
from gameqa.imageio import load_image, save_png
from gameqa.report import draw_boxes
from gameqa.storage import export_report


def prepare():
    cfg = load_config(REPO_ROOT / "configs/openrouter_gemini_pilot.yaml")
    if config_hash(cfg) != "eaa371255716":
        raise RuntimeError("Frozen runtime config changed; explicit unblock required")
    source = REPO_ROOT / "deploy/replay/barrel"
    manifest = json.loads((source / "package.json").read_text())
    for name, expected in manifest["files"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Replay package checksum mismatch: {name}")
    result = AnalysisResult.model_validate_json((source / "analysis.json").read_text())
    root = resolve_dir(cfg, "artifacts_dir")
    destination = root / result.run_id
    root.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not (destination / "analysis.json").is_file():
            raise RuntimeError("Existing replay directory incomplete; preserve and inspect it")
        return destination  # Preserve existing original ZIP/evidence/history.
    shutil.copytree(source, destination)
    shutil.copyfile(destination / "images/candidate.png", destination / "images/aligned_candidate.png")
    save_png(destination / "images/overlay.png", draw_boxes(load_image(destination / "images/reference.png", cfg).array, result.proposals))
    export_report(result, destination)
    return destination


if __name__ == "__main__":
    print(f"Prepared saved replay: {prepare().name}; no new inference")
