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


def _criteria_block(question: str, unacceptable: bool) -> str | None:
    """Return the verbatim '... ACCEPTABLE:' or '... UNACCEPTABLE:' header + bullet block."""
    for m in _ACCEPTABLE_BLOCK.finditer(question):
        block = m.group("block").strip()
        header = block.split(":")[0].upper()
        if ("UNACCEPTABLE" in header) == unacceptable:
            return block
    return None


def rules_from_question(question: str) -> list[Rule]:
    """Map a benchmark question to rules (DECISIONS D8). No label information is used.

    A1 (ALLOW): the question's ACCEPTABLE header + bullets, verbatim.
    D1 (DENY):  the question's UNACCEPTABLE header + bullets, verbatim.
    If the question has no UNACCEPTABLE block, D1 falls back to the whole question
    verbatim, prefixed with "Report a regression: ". The benchmark's output-format
    instruction is deliberately not turned into a rule; the full original question is
    kept in the manifest's ``question`` field for provenance.
    """
    rules: list[Rule] = []
    allow = _criteria_block(question, unacceptable=False)
    if allow:
        rules.append(Rule(id="A1", effect=RuleEffect.ALLOW, description=allow))
    deny = _criteria_block(question, unacceptable=True)
    rules.append(
        Rule(
            id="D1",
            effect=RuleEffect.DENY,
            description=deny if deny else f"Report a regression: {question}",
        )
    )
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
