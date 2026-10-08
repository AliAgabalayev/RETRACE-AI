"""Deterministic final decision policy (docs/PROJECT_BRIEF.md section 5.D).

This is the ONLY place that maps pipeline outputs to PASS / FAIL / NEEDS_REVIEW.
Order matters:
1. A reliable forbidden judgment -> FAIL, even if other components failed.
2. Identical decoded images with valid inputs -> PASS (documented shortcut).
3. Any incompleteness, error, mock, or uncertainty -> NEEDS_REVIEW.
4. Otherwise (everything ran, every change allowed, audit clean) -> PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gameqa.contracts import (
    AlignmentResult,
    AlignmentStatus,
    Coverage,
    FinalDecision,
    RegionJudgment,
    Rule,
    RuleEffect,
    SceneAudit,
    Verdict,
)


@dataclass
class DecisionInput:
    rules: list[Rule]
    judgments: list[RegionJudgment]
    scene_audit: SceneAudit | None
    coverage: Coverage
    alignment: AlignmentResult | None
    identical_images: bool = False
    inputs_valid: bool = True
    pipeline_errors: list[str] = field(default_factory=list)


def _conflicted_rule_ids(rules: list[Rule]) -> set[str]:
    """IDs of rules involved in a conflict found by ``find_rule_conflicts``."""
    by_text: dict[str, list[Rule]] = {}
    for r in rules:
        by_text.setdefault(" ".join(r.description.lower().split()), []).append(r)
    ids = {r.id for group in by_text.values() if len({r.effect for r in group}) > 1 for r in group}
    seen: set[str] = set()
    for r in rules:
        if r.id in seen:
            ids.add(r.id)
        seen.add(r.id)
    return ids


def is_reliable_forbidden(j: RegionJudgment, rules: list[Rule]) -> bool:
    """Forbidden verdict from a real, validated response with evidence, citing only known rule
    IDs, at least one of which is a deny rule that is not involved in a rule conflict."""
    known = {r.id for r in rules}
    deny_ids = {r.id for r in rules if r.effect == RuleEffect.DENY} - _conflicted_rule_ids(rules)
    return (
        j.verdict == Verdict.FORBIDDEN
        and j.validated
        and not j.is_mock
        and not j.errors
        and bool(j.evidence.strip())
        and all(rid in known for rid in j.rule_ids)
        and any(rid in deny_ids for rid in j.rule_ids)
    )


def find_rule_conflicts(rules: list[Rule]) -> list[str]:
    """Detect rule sets we cannot decide under: duplicate IDs, or the same description
    (case/whitespace-insensitive) declared both allow and deny. Semantic conflicts beyond
    this are left to the VLM, which must answer ``uncertain`` for them."""
    conflicts: list[str] = []
    seen: set[str] = set()
    for r in rules:
        if r.id in seen:
            conflicts.append(f"duplicate rule id {r.id}")
        seen.add(r.id)
    by_text: dict[str, set[RuleEffect]] = {}
    for r in rules:
        by_text.setdefault(" ".join(r.description.lower().split()), set()).add(r.effect)
    for text, effects in by_text.items():
        if len(effects) > 1:
            conflicts.append(f"same rule text is both allow and deny: {text[:60]!r}")
    return conflicts


def is_acceptable_allowed(j: RegionJudgment, rules: list[Rule]) -> bool:
    """Allowed verdict we can rely on for PASS: validated, evidence given, only known rule IDs,
    no deny rule cited."""
    known = {r.id for r in rules}
    deny_ids = {r.id for r in rules if r.effect == RuleEffect.DENY}
    return (
        j.verdict == Verdict.ALLOWED
        and j.validated
        and not j.is_mock
        and not j.errors
        and bool(j.evidence.strip())
        and all(rid in known for rid in j.rule_ids)
        and not any(rid in deny_ids for rid in j.rule_ids)
    )


def decide(inp: DecisionInput) -> tuple[FinalDecision, str]:
    """Return (decision, human-readable reason)."""
    all_judgments = list(inp.judgments)
    if inp.scene_audit is not None:
        all_judgments.append(inp.scene_audit.judgment)

    # Region crops compare the same reference box in both images, so they are only
    # trustworthy when alignment is trustworthy. Under unreliable/failed/missing alignment a
    # "missing object" may be a misregistration artefact: only the whole-scene audit, which
    # sees both full images, can establish FAIL (DECISIONS D9).
    alignment_ok = inp.alignment is not None and inp.alignment.status not in (
        AlignmentStatus.UNRELIABLE,
        AlignmentStatus.FAILED,
    )
    fail_sources = all_judgments if alignment_ok else [
        j for j in all_judgments if j.region_id == "SCENE"
    ]
    forbidden = [j for j in fail_sources if is_reliable_forbidden(j, inp.rules)]
    if forbidden:
        ids = ", ".join(f"{j.region_id} ({'/'.join(j.rule_ids)})" for j in forbidden)
        return FinalDecision.FAIL, f"Forbidden change with visual evidence: {ids}."

    if not inp.inputs_valid:
        return FinalDecision.NEEDS_REVIEW, "Invalid input images; comparison not performed."

    if inp.identical_images:
        return FinalDecision.PASS, "Decoded images are pixel-identical (deterministic shortcut)."

    reasons: list[str] = []
    if not inp.rules:
        reasons.append("no rules provided")
    for conflict in find_rule_conflicts(inp.rules):
        reasons.append(f"rule conflict: {conflict}")
    if inp.alignment is None or inp.alignment.status in (
        AlignmentStatus.UNRELIABLE,
        AlignmentStatus.FAILED,
    ):
        reasons.append("alignment unreliable or missing")
    if inp.coverage.truncated:
        reasons.append(
            f"proposals truncated ({inp.coverage.proposals_judged}/{inp.coverage.proposals_total} judged)"
        )
    if inp.coverage.deadline_exceeded:
        reasons.append("deadline exceeded")
    if inp.coverage.proposals_judged < inp.coverage.proposals_total and not inp.coverage.truncated:
        reasons.append("not all proposals were judged")
    if inp.scene_audit is None or not inp.coverage.scene_audit_ran:
        reasons.append("whole-scene audit did not run")
    elif inp.scene_audit.extra_changes_reported:
        reasons.append("scene audit reported changes outside proposals")
    if inp.pipeline_errors:
        reasons.append(f"{len(inp.pipeline_errors)} pipeline error(s)")

    for j in all_judgments:
        if j.is_mock:
            reasons.append(f"{j.region_id}: mock judgment (not real inference)")
        elif j.errors or not j.validated:
            reasons.append(f"{j.region_id}: invalid or failed model response")
        elif j.verdict != Verdict.ALLOWED:
            reasons.append(f"{j.region_id}: {j.verdict.value}")
        elif not is_acceptable_allowed(j, inp.rules):
            reasons.append(f"{j.region_id}: allowed verdict without evidence or citing a deny rule")

    if reasons:
        return FinalDecision.NEEDS_REVIEW, "Needs review: " + "; ".join(reasons) + "."

    n = len(inp.judgments)
    return (
        FinalDecision.PASS,
        f"All {n} proposed region(s) judged allowed and the scene audit found no forbidden change. "
        "PASS is a heuristic result, not proof that no bug exists.",
    )
