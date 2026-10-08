"""Rules YAML parsing and dumping. Descriptions are kept verbatim."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from gameqa.contracts import Rule


class RulesError(ValueError):
    pass


def validate_rules(rules: list[Rule]) -> list[Rule]:
    seen: set[str] = set()
    for r in rules:
        if r.id in seen:
            raise RulesError(f"duplicate rule id: {r.id}")
        seen.add(r.id)
    return rules


def rules_from_dicts(items: list[dict]) -> list[Rule]:
    for item in items:
        for key in ("id", "description"):
            if isinstance(item, dict) and key in item and not isinstance(item[key], str):
                raise RulesError(
                    f"rule {key} {item[key]!r} is not text (YAML turned it into "
                    f"{type(item[key]).__name__}); wrap it in quotes to keep it verbatim"
                )
    try:
        rules = [Rule(**item) for item in items]
    except (ValidationError, TypeError) as exc:
        raise RulesError(f"invalid rule: {exc}") from exc
    return validate_rules(rules)


def parse_rules(text: str) -> list[Rule]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RulesError(f"invalid YAML: {exc}") from exc
    if isinstance(data, dict):
        data = data.get("rules")
    if data is None:
        return []
    if not isinstance(data, list):
        raise RulesError("'rules' must be a list of id/effect/description entries")
    return rules_from_dicts(data)


def load_rules(path: str | Path) -> list[Rule]:
    return parse_rules(Path(path).read_text(encoding="utf-8"))


def dump_rules(rules: list[Rule]) -> str:
    items = [
        {"id": r.id, "effect": r.effect.value, "description": r.description} for r in rules
    ]
    return yaml.safe_dump(
        {"rules": items}, sort_keys=False, allow_unicode=True, default_flow_style=False, width=10_000
    )
