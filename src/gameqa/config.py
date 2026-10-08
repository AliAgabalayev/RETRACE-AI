"""YAML configuration loading with deep-merge overrides and a stable hash."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"


def deep_merge(base: dict, override: dict) -> dict:
    """Return a new dict: ``override`` values win, nested dicts are merged."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: str | Path | None = None, overrides: dict | None = None) -> dict[str, Any]:
    """Load the default config, optionally layer ``path`` and ``overrides`` on top."""
    with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    if path is not None and Path(path).resolve() != DEFAULT_CONFIG_PATH:
        with open(path, encoding="utf-8") as fh:
            cfg = deep_merge(cfg, yaml.safe_load(fh) or {})
    if overrides:
        cfg = deep_merge(cfg, overrides)
    return cfg


def config_hash(cfg: dict) -> str:
    """Short stable hash of the full config (key order independent)."""
    blob = json.dumps(cfg, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def resolve_dir(cfg: dict, key: str) -> Path:
    """Resolve ``cfg['run'][key]`` against the repo root when relative."""
    p = Path(cfg["run"][key])
    return p if p.is_absolute() else REPO_ROOT / p
