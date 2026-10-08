"""Prepare VideoGameQA-Bench visual-regression pairs (idempotent, selective download)."""
from __future__ import annotations

import argparse
import json

from gameqa.data import prepare as P


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="only the first N records (label-balanced seeded order)")
    ap.add_argument("--revision", default=None, help="HF dataset commit sha (default: current main, pinned in output)")
    ap.add_argument("--max-gb", type=float, default=3.0, help="abort if selected images exceed this size")
    args = ap.parse_args()

    revision = P.resolve_revision(args.revision)
    print("revision:", revision)
    df = P.download_metadata(revision)
    vr = P.select_visual_regression(df)
    print(f"total records {len(df)}, visual regression {len(vr)}")
    selected = P.ordered_records(vr)
    if args.limit:
        selected = selected[: args.limit]
    sizes = P.remote_sizes([r["custom_id"] for r in selected], revision)
    total_gb = sum(sizes.values()) / 1e9
    print(f"selected {len(selected)} pairs, remote size {total_gb:.2f} GB")
    if total_gb > args.max_gb:
        raise SystemExit(f"selected size {total_gb:.2f} GB exceeds --max-gb {args.max_gb}")
    prepared = []
    for i, rec in enumerate(selected, 1):
        p = P.prepare_pair(rec, revision)
        prepared.append(p)
        print(f"[{i}/{len(selected)}] {p['sample_id']} {p['validation_status']}", flush=True)
    summary = P.build_manifests(selected, prepared, revision)
    summary["remote_gb"] = round(total_gb, 3)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
