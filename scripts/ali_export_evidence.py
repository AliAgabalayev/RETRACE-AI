"""Export an existing run as an evidence report ZIP (report.md + evidence.json + images/crops).

Bridge until Celal's storage/pipeline call ``report.write_evidence`` themselves (see
docs/ali/evidence_shape.md): this script only reads a finished run and writes inside its run dir,
so it does not touch storage.py / pipeline.py.

Usage: .venv/bin/python scripts/ali_export_evidence.py <run_id> [--config configs/ali_x.yaml]
"""

from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

from gameqa.config import load_config
from gameqa.report import render_report, write_evidence
from gameqa.storage import StorageError, load_run, run_dir_for, write_text_atomic, zip_path_for


def export_with_evidence(run_id: str, cfg: dict) -> Path:
    """Write evidence.json and a hash-carrying report.md into the run dir, then zip the run dir."""
    result = load_run(run_id, cfg)
    run_dir = run_dir_for(run_id, cfg)
    write_evidence(result, run_dir, cfg)
    write_text_atomic(run_dir / "report.md", render_report(result, run_dir, cfg))
    zpath = zip_path_for(run_dir)
    tmp = zpath.with_name(zpath.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(run_dir.rglob("*")):
            if f.is_file() and not f.name.endswith(".tmp"):
                zf.write(f, Path(run_dir.name) / f.relative_to(run_dir))
    os.replace(tmp, zpath)
    return zpath


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_id")
    ap.add_argument("--config", default=None, help="config used for the run (for identity/cache status)")
    args = ap.parse_args(argv)
    try:
        zpath = export_with_evidence(args.run_id, load_config(args.config))
    except StorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(zpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
