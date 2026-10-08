"""Prompt templates and JSON schemas. Bump PROMPT_VERSION on any change (it is part of the cache key).

Two-stage design (measured with qwen2.5vl:3b via Ollama, see docs/MODEL_NOTES.md):
- Stage 1 (image): ONE composite image (BEFORE | AFTER, captions burned in) and NO rules in the prompt. The model
  only describes what it sees and classifies the change. With rules in the same prompt the 3B model echoed rule
  text, called deletions 'replaced' and cited every allow rule; with several separate images it described both
  crops identically.
- Stage 2 (text only, no image): rules + the stage-1 observation -> verdict, rule IDs, evidence. Fast (~seconds).
- No concrete example sentences in prompts: the 3B model copies them.
"""
PROMPT_VERSION = "v9"

CHANGE_TYPES = ["none", "disappeared", "appeared", "color_or_lighting", "moved", "distorted_or_corrupted", "other"]

STAGE1_SCHEMA = {
    "type": "object",
    "properties": {
        "before_shows": {"type": "string"},
        "after_shows": {"type": "string"},
        "observed_change": {"type": "string"},
        "change_type": {"type": "string", "enum": CHANGE_TYPES},
        "any_difference": {"type": "boolean"},
    },
    "required": ["before_shows", "after_shows", "observed_change", "change_type", "any_difference"],
}
STAGE1_AUDIT_SCHEMA = {
    "type": "object",
    "properties": {**STAGE1_SCHEMA["properties"], "other_changes_outside_boxes": {"type": "boolean"}},
    "required": STAGE1_SCHEMA["required"] + ["other_changes_outside_boxes"],
}
STAGE2_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["allowed", "forbidden", "uncertain"]},
        "rule_ids": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "string"},
    },
    "required": ["verdict", "rule_ids", "evidence"],
}

_KEYS = """Reply with JSON only, keys in this order:
- before_shows: describe plainly what the BEFORE half shows (objects, colours, positions).
- after_shows: the same for the AFTER half.
- observed_change: one short sentence: what is different between BEFORE and AFTER.
- change_type: none, disappeared (something in BEFORE is gone in AFTER), appeared, color_or_lighting, moved, distorted_or_corrupted, or other.
- any_difference: true if BEFORE and AFTER differ in any visible way, false if they look the same."""

REGION_PROMPT = """The image shows one region of a game screenshot: BEFORE (left half, reference build) and AFTER (right half, new build). Region box in the reference frame: [{x1},{y1},{x2},{y2}].

Compare the two halves carefully. Is anything in BEFORE missing in AFTER?

""" + _KEYS

AUDIT_PROMPT = """The image shows a whole game screenshot: BEFORE (left half, reference build) and AFTER (right half, new build). Regions already checked are outlined in yellow with their IDs: {boxes}.

Compare the two halves carefully over the WHOLE picture. Is anything in BEFORE missing in AFTER?

""" + _KEYS + """
- other_changes_outside_boxes (last key): true if you see a visible difference outside the yellow boxes, otherwise false."""

DECIDE_PROMPT = """A game QA tool compared a BEFORE and an AFTER screenshot{where} and recorded:
- BEFORE shows: {before_shows}
- AFTER shows: {after_shows}
- Change: {observed_change}
- Change type: {change_type}; any difference: {any_difference}

RULES:
{rules}

ALLOW rule IDs: {allow_ids}
DENY rule IDs: {deny_ids}

Decide using ONLY the recorded observation and the rules. Reply with JSON only, keys in this order:
- verdict: "forbidden" if the change breaks a DENY rule (rule_ids must contain that DENY rule ID); "allowed" if an ALLOW rule covers the WHOLE change (rule_ids must contain that ALLOW rule ID; if there is no difference use []); "uncertain" if unclear or no rule clearly applies (rule_ids []).
- rule_ids: only the IDs of the rules that actually apply, from the lists above.
- evidence: one short sentence quoting what BEFORE and AFTER show that supports the verdict.
Something that disappeared, or geometry/texture that became corrupted, is never covered by an ALLOW rule unless that rule says so explicitly. If unsure, answer "uncertain"."""
