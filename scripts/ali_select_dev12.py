"""Deterministic dev12 selection (seed 20261009). Selection precedes any model output."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEED = 20261009
OUT = REPO / "configs" / "ali_dev12.json"
MANIFESTS = REPO / "data" / "manifests"

# (stratum, label class, media_source, wanted count, fallback count)
STRATA = [
    ("S0", "no_bug", "Youtube-Cutscene", 6, 3),
    ("S1", "bug", "UnityCapturesDataset", 3, 2),
    ("S2", "bug", "Youtube-Cutscene", 3, 1),
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select(manifest: list[dict], labels: dict, seed: int = SEED) -> dict:
    """Stratify dev entries by (label class, source); labels are used only to form strata."""
    rng = random.Random(seed)
    entries = {e["sample_id"]: e for e in manifest if e["split"] == "dev"}
    selected, fallback, counts = [], [], {}
    for name, cls, source, want, fb in STRATA:
        pool = sorted(i for i, e in entries.items()
                      if labels[i]["label"] == cls and e["media_source"] == source)
        n = min(want, len(pool))
        counts[name] = {"source": source, "available": len(pool), "wanted": want, "selected": n}
        picked = rng.sample(pool, n)
        selected += picked
        fallback += picked[:min(fb, n)]

    def row(i: str) -> dict:
        e = entries[i]
        return {"sample_id": i, "source": e["media_source"],
                "reference_path": e["reference_path"], "candidate_path": e["candidate_path"]}

    return {
        "seed": seed,
        "selection_rule": (
            "dev split only; IDs sorted lexicographically per stratum, then random.Random(seed).sample "
            "without replacement, strata in order S0,S1,S2. Strata are formed from (label class, media_source); "
            "the label class is used only to form strata (allowed: dev is the development set) and is not stored. "
            "Selection made before any model output. Never filled from eval."
        ),
        "strata": counts,
        "balanced_six_rule": "first 3 of S0, first 2 of S1, first 1 of S2 in seeded order (predeclared)",
        "dev12": [row(i) for i in selected],
        "balanced_six": [row(i) for i in fallback],
    }


def main() -> int:
    manifest_path = MANIFESTS / "inference_manifest.json"
    labels_path = MANIFESTS / "eval_labels.json"
    result = select(json.loads(manifest_path.read_text()), json.loads(labels_path.read_text()))
    result["input_manifest_sha256_prefix"] = {
        "inference_manifest": _sha(manifest_path)[:16],
        "eval_labels": _sha(labels_path)[:16],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}: {len(result['dev12'])} ids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
