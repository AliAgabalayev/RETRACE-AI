"""Prompt templates and JSON schemas. Bump PROMPT_VERSION on any change (it is part of the cache key)."""
PROMPT_VERSION = "v1"

REGION_SCHEMA = {
    "type": "object",
    "properties": {
        "observed_change": {"type": "string"},
        "verdict": {"type": "string", "enum": ["allowed", "forbidden", "uncertain"]},
        "rule_ids": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "string"},
    },
    "required": ["observed_change", "verdict", "rule_ids", "evidence"],
}

AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "observed_change": {"type": "string"},
        "verdict": {"type": "string", "enum": ["allowed", "forbidden", "uncertain"]},
        "rule_ids": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "string"},
        "other_changes_outside_boxes": {"type": "boolean"},
    },
    "required": ["observed_change", "verdict", "rule_ids", "evidence", "other_changes_outside_boxes"],
}

_COMMON_RULES = """RULES (use the rule IDs exactly as written):
{rules}

Answer with JSON only, with keys: observed_change (one short sentence of what differs), verdict, rule_ids, evidence (one short sentence naming what you can see).
verdict = "forbidden" if the change breaks a DENY rule, "allowed" if it is covered by an ALLOW rule or there is no visible change, "uncertain" if you cannot tell.
rule_ids = IDs of the rules that apply (a forbidden verdict must cite a DENY rule, an allowed verdict an ALLOW rule). Use [] only if there is no visible change.
Do not guess: if the images do not clearly show it, answer "uncertain"."""

REGION_PROMPT = """You compare two game screenshots. Image 1 is the REFERENCE (before). Image 2 is the CANDIDATE (after). Both show the same region [{x1},{y1},{x2},{y2}] (pixel box in the reference frame). Image 3 is context: full REFERENCE on the left, full CANDIDATE on the right, the region outlined in red.

Question: what changed inside the region between Image 1 and Image 2, and is that change allowed by the rules?

""" + _COMMON_RULES

AUDIT_PROMPT = """You compare two full game screenshots. Image 1 is the REFERENCE (before). Image 2 is the CANDIDATE (after). Regions already checked are outlined in yellow: {boxes}.

Question: look at the WHOLE picture. Is there any change anywhere that breaks a DENY rule, especially outside the yellow boxes? Set other_changes_outside_boxes to true if you see any visible difference outside the yellow boxes, otherwise false.

""" + _COMMON_RULES
