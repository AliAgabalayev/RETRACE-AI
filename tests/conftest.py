"""Shared QA helpers. Owner: qa-engineer.

``real_model`` tests (real DINOv2 + real Ollama VLM) are skipped unless GAMEQA_REAL=1.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "data" / "fixtures"


def pytest_configure(config):
    config.addinivalue_line("markers", "real_model: needs real DINOv2 weights + running Ollama (set GAMEQA_REAL=1)")


def pytest_collection_modifyitems(config, items):
    if os.environ.get("GAMEQA_REAL") == "1":
        return
    skip = pytest.mark.skip(reason="real-model test; set GAMEQA_REAL=1 to run")
    for item in items:
        if "real_model" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


def load_case(name: str) -> dict:
    """Load a synthetic fixture case; skip if fixtures have not been generated."""
    import json

    import yaml

    d = FIXTURES / name
    if not (d / "expected.json").exists():
        pytest.skip(f"fixture {name} missing; run scripts/make_fixtures.py")
    rules = yaml.safe_load((d / "rules.yaml").read_text())["rules"] if (d / "rules.yaml").exists() else []
    return {
        "dir": d,
        "reference": str(d / "reference.png"),
        "candidate": str(d / "candidate.png"),
        "rules": rules,
        "expected": json.loads((d / "expected.json").read_text()),
    }


@pytest.fixture
def case():
    return load_case


def default_cfg() -> dict:
    import yaml

    return yaml.safe_load((REPO / "configs" / "default.yaml").read_text())
