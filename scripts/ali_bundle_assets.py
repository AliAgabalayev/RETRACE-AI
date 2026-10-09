"""Copy the dev12 image pairs from data/work into artifacts/ali/bundle and write a hash inventory."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "artifacts" / "ali" / "bundle"
INVENTORY = REPO / "artifacts" / "ali" / "inventory.json"


def main() -> int:
    cfg = json.loads((REPO / "configs" / "ali_dev12.json").read_text())
    manifest = {e["sample_id"]: e for e in json.loads((REPO / "data/manifests/inference_manifest.json").read_text())}
    samples = []
    for row in cfg["dev12"]:
        sid = row["sample_id"]
        entry = manifest[sid]
        images = {}
        for role, key in (("reference", "reference_path"), ("candidate", "candidate_path")):
            src = REPO / row[key]
            dst = BUNDLE / sid / f"{role}.png"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            with Image.open(dst) as im:
                width, height = im.size
            images[role] = {
                "bundle_path": str(dst.relative_to(REPO)),
                "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                "width": width,
                "height": height,
                "source_path": row[key],
            }
        samples.append({
            "sample_id": sid,
            "source": entry["media_source"],
            "dataset_revision": entry["dataset_revision"],
            "rules": [{"id": r["id"], "effect": r["effect"], "description": r["description"]} for r in entry["rules"]],
            "images": images,
        })
    INVENTORY.write_text(json.dumps({"samples": samples}, indent=2, sort_keys=True) + "\n")
    print(f"bundled {len(samples)} pairs -> {INVENTORY.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
