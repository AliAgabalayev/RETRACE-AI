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


def is_reliable_forbidden(j: RegionJudgment, rules: list[Rule]) -> bool:
    """Forbidden verdict from a real, validated response citing a deny rule with evidence."""
    deny_ids = {r.id for r in rules if r.effect == RuleEffect.DENY}
    return (
        j.verdict == Verdict.FORBIDDEN
        and j.validated
        and not j.is_mock
        and not j.errors
        and bool(j.evidence.strip())
        and any(rid in deny_ids for rid in j.rule_ids)
    )


def decide(inp: DecisionInput) -> tuple[FinalDecision, str]:
    """Return (decision, human-readable reason)."""
    all_judgments = list(inp.judgments)
    if inp.scene_audit is not None:
        all_judgments.append(inp.scene_audit.judgment)

    forbidden = [j for j in all_judgments if is_reliable_forbidden(j, inp.rules)]
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

    if reasons:
        return FinalDecision.NEEDS_REVIEW, "Needs review: " + "; ".join(reasons) + "."

    n = len(inp.judgments)
    return (
        FinalDecision.PASS,
        f"All {n} proposed region(s) judged allowed and the scene audit found no forbidden change. "
        "PASS is a heuristic result, not proof that no bug exists.",
    )
