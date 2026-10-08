"""Manifest loaders and benchmark-question -> rules mapping."""
from __future__ import annotations

import json
import re
from pathlib import Path

from gameqa.contracts import Rule, RuleEffect

REPO_ROOT = Path(__file__).resolve().parents[3]
INFERENCE_MANIFEST = REPO_ROOT / "data" / "manifests" / "inference_manifest.json"
EVAL_LABELS = REPO_ROOT / "data" / "manifests" / "eval_labels.json"

# Keys that must never appear in inference records
FORBIDDEN_INFERENCE_KEYS = frozenset({"label", "ground_truth", "ground_truth_raw", "test_pass"})

_ACCEPTABLE_BLOCK = re.compile(
    r"^(?P<block>[^\n]*ACCEPTABLE[^\n]*:\n(?:[ \t]*-[^\n]*\n?)+)", re.MULTILINE
)


def rules_from_question(question: str) -> list[Rule]:
    """Map a benchmark question to rules.

    Q1 (DENY): the original question text, verbatim, prefixed with "Report a regression: ".
    A1 (ALLOW): only when the question has an explicit ACCEPTABLE header with bullet lines;
    that header block is copied verbatim. No label information is ever used.
    """
    rules = [Rule(id="Q1", effect=RuleEffect.DENY, description=f"Report a regression: {question}")]
    for m in _ACCEPTABLE_BLOCK.finditer(question):
        block = m.group("block").strip()
        if block.upper().lstrip().startswith(("CONSIDER", "ACCEPTABLE")) and "UNACCEPTABLE" not in block.split(":")[0].upper():
            rules.append(Rule(id="A1", effect=RuleEffect.ALLOW, description=block))
            break
    return rules


def _resolve(path: Path | str | None, default: Path) -> Path:
    return Path(path) if path is not None else default


def load_inference_manifest(path: Path | str | None = None) -> list[dict]:
    """Load inference records (no labels). Paths inside are relative to the repo root."""
    records = json.loads(_resolve(path, INFERENCE_MANIFEST).read_text(encoding="utf-8"))
    for rec in records:
        leaked = FORBIDDEN_INFERENCE_KEYS & set(rec)
        if leaked:
            raise ValueError(f"label keys in inference manifest: {sorted(leaked)}")
    return records


def load_eval_labels(path: Path | str | None = None) -> dict:
    """Load evaluation-only labels: {sample_id: {ground_truth_raw, label, split}}."""
    return json.loads(_resolve(path, EVAL_LABELS).read_text(encoding="utf-8"))
