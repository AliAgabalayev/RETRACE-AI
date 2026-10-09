"""Local persistence: run directories, atomic writes, export, reference versions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gameqa.config import resolve_dir
from gameqa.contracts import AnalysisResult
from gameqa.imageio import load_image, save_png

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
RUN_SUBDIRS = ("images", "crops", "diagnostics")


class StorageError(ValueError):
    pass


def validate_id(value: str, kind: str = "id") -> str:
    if not isinstance(value, str) or not _ID_RE.match(value) or ".." in value:
        raise StorageError(f"invalid {kind}: {value!r}")
    return value


def safe_join(root: Path, *parts: str) -> Path:
    """Join under ``root`` and refuse anything that resolves outside it."""
    root = Path(root).resolve()
    target = root.joinpath(*parts).resolve()
    if target != root and root not in target.parents:
        raise StorageError(f"path escapes root: {'/'.join(parts)}")
    return target


def write_json_atomic(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{uuid.uuid4().hex[:6]}.tmp")
    try:
        tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, p)
    finally:
        tmp.unlink(missing_ok=True)


def write_text_atomic(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{uuid.uuid4().hex[:6]}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, p)
    finally:
        tmp.unlink(missing_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_run_dir(cfg: dict) -> tuple[str, Path]:
    root = resolve_dir(cfg, "artifacts_dir")
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{uuid.uuid4().hex[:6]}"
    run_dir = safe_join(root, run_id)
    run_dir.mkdir(parents=True, exist_ok=False)
    for sub in RUN_SUBDIRS:
        (run_dir / sub).mkdir()
    return run_id, run_dir


def run_dir_for(run_id: str, cfg: dict) -> Path:
    validate_id(run_id, "run id")
    return safe_join(resolve_dir(cfg, "artifacts_dir"), run_id)


def load_run(run_id: str, cfg: dict) -> AnalysisResult:
    path = run_dir_for(run_id, cfg) / "analysis.json"
    if not path.is_file():
        raise StorageError(f"run not found: {run_id}")
    return AnalysisResult.model_validate_json(path.read_text(encoding="utf-8"))


def list_runs(cfg: dict) -> list[dict]:
    """Saved runs, newest first. Unreadable runs are skipped."""
    root = resolve_dir(cfg, "artifacts_dir")
    if not root.is_dir():
        return []
    rows = []
    for d in root.iterdir():
        f = d / "analysis.json"
        if not (d.is_dir() and f.is_file()):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            rows.append(
                {
                    "run_id": data["run_id"],
                    "created_at": data.get("created_at", ""),
                    "final_decision": data.get("final_decision", "?"),
                    "sample_id": data.get("sample_id"),
                    "engine_mode": data.get("engine_mode", "?"),
                }
            )
        except (OSError, ValueError, KeyError):
            continue
    return sorted(rows, key=lambda r: (r["created_at"], r["run_id"]), reverse=True)


def zip_path_for(run_dir: Path) -> Path:
    return run_dir.parent / f"{run_dir.name}.zip"


def export_report(result: AnalysisResult, run_dir: str | Path) -> Path:
    """Write report.md in ``run_dir`` and a ZIP of the run directory. Returns report.md."""
    from gameqa.report import render_report, write_evidence

    run_dir = Path(run_dir)
    report = run_dir / "report.md"
    write_evidence(result, run_dir)
    write_text_atomic(report, render_report(result, run_dir))
    zpath = zip_path_for(run_dir)
    tmp = zpath.with_name(zpath.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(run_dir.rglob("*")):
            if f.is_file() and not f.name.endswith(".tmp"):
                zf.write(f, Path(run_dir.name) / f.relative_to(run_dir))
    os.replace(tmp, zpath)
    return report


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _link_new(src: Path, dst: Path) -> None:
    """Place ``src`` at ``dst`` without ever overwriting an existing file."""
    try:
        os.link(src, dst)
    except FileExistsError as exc:
        raise StorageError(f"version already exists: {dst.name}") from exc
    finally:
        src.unlink(missing_ok=True)


def _next_version(versions_dir: Path) -> int:
    nums = [int(m.group(1)) for p in versions_dir.glob("v*.png") if (m := re.fullmatch(r"v(\d+)\.png", p.name))]
    return max(nums, default=0) + 1


def approve_reference(
    reference_id: str,
    candidate_path: str | Path,
    run_id: str,
    cfg: dict,
    *,
    previous_reference_path: str | Path | None = None,
) -> dict:
    """Store ``candidate_path`` as the next version of ``reference_id``.

    Older versions are never overwritten. If the reference has no versions yet and
    ``previous_reference_path`` is given, it is stored as v1 first so the replaced
    image is preserved. Benchmark source assets are never touched.
    """
    validate_id(reference_id, "reference id")
    run_dir = run_dir_for(run_id, cfg)
    if not run_dir.is_dir():
        raise StorageError(f"run not found: {run_id}")
    ref_dir = safe_join(resolve_dir(cfg, "references_dir"), reference_id)
    versions_dir = ref_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    history_path = ref_dir / "history.json"
    history = (
        json.loads(history_path.read_text(encoding="utf-8"))
        if history_path.is_file()
        else {"reference_id": reference_id, "events": []}
    )

    def _store(image_path: str | Path) -> tuple[str, str]:
        img = load_image(image_path, cfg)
        n = _next_version(versions_dir)
        tmp = versions_dir / f".new-{uuid.uuid4().hex[:6]}.tmp"
        save_png(tmp, img.array)
        _link_new(tmp, versions_dir / f"v{n}.png")
        return f"v{n}", _sha256_file(versions_dir / f"v{n}.png")

    previous = f"v{_next_version(versions_dir) - 1}" if _next_version(versions_dir) > 1 else None
    if previous is None and previous_reference_path is not None:
        previous, prev_sha = _store(previous_reference_path)
        history["events"].append(
            {"timestamp": utc_now_iso(), "run_id": run_id, "previous_version": None,
             "new_version": previous, "sha256": prev_sha, "note": "baseline: original reference"}
        )
    new_version, sha = _store(candidate_path)
    history["events"].append(
        {"timestamp": utc_now_iso(), "run_id": run_id, "previous_version": previous,
         "new_version": new_version, "sha256": sha, "note": "candidate approved as new reference"}
    )
    write_json_atomic(history_path, history)
    return {
        "reference_id": reference_id,
        "previous_version": previous,
        "new_version": new_version,
        "path": str((versions_dir / f"{new_version}.png")),
        "sha256": sha,
        "run_id": run_id,
    }
