"""Exhaustive tests of gameqa.decision.decide (QA-owned expectations, brief 5.D)."""

from __future__ import annotations

import pytest

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
from gameqa.decision import DecisionInput, decide

PASS, FAIL, REVIEW = FinalDecision.PASS, FinalDecision.FAIL, FinalDecision.NEEDS_REVIEW

RULES = [
    Rule(id="A1", effect=RuleEffect.ALLOW, description="lighting may change"),
    Rule(id="D1", effect=RuleEffect.DENY, description="objects must not disappear"),
]


def J(region="R1", verdict=Verdict.ALLOWED, rule_ids=None, evidence="clear evidence", mock=False,
      errors=None, validated=True):
    if rule_ids is None:
        rule_ids = ["D1"] if verdict == Verdict.FORBIDDEN else ["A1"]
    return RegionJudgment(region_id=region, observed_change="x", verdict=verdict, rule_ids=rule_ids,
                          evidence=evidence, model="mock:x" if mock else "ollama:qwen2.5vl:3b",
                          is_mock=mock, errors=errors or [], validated=validated)


def audit(j=None, extra=False):
    return SceneAudit(judgment=j or J("SCENE"), extra_changes_reported=extra)


def align(status=AlignmentStatus.IDENTITY):
    return AlignmentResult(status=status, candidate_to_reference=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                           overlap_fraction=1.0)


def cov(total=1, judged=1, truncated=False, audit_ran=True, deadline=False):
    return Coverage(proposals_total=total, proposals_judged=judged, truncated=truncated,
                    scene_audit_ran=audit_ran, deadline_exceeded=deadline)


def inp(**kw):
    base = dict(rules=RULES, judgments=[J()], scene_audit=audit(), coverage=cov(), alignment=align())
    base.update(kw)
    return DecisionInput(**base)


def d(**kw):
    return decide(inp(**kw))[0]


# ---- baseline ---------------------------------------------------------------

def test_clean_all_allowed_passes():
    assert d() == PASS


def test_zero_proposals_with_clean_audit_passes():
    assert d(judgments=[], coverage=cov(0, 0)) == PASS


def test_zero_proposals_without_audit_never_passes():
    assert d(judgments=[], coverage=cov(0, 0, audit_ran=False), scene_audit=None) == REVIEW


def test_identical_images_pass():
    assert d(identical_images=True, judgments=[], scene_audit=None, coverage=cov(0, 0, audit_ran=False)) == PASS


def test_identical_but_invalid_inputs_review():
    assert d(identical_images=True, inputs_valid=False) == REVIEW


# ---- FAIL precedence --------------------------------------------------------

@pytest.mark.parametrize("extra", [
    dict(pipeline_errors=["extractor failed"]),
    dict(coverage=cov(10, 8, truncated=True)),
    dict(coverage=cov(2, 1, deadline=True)),
    dict(alignment=align(AlignmentStatus.UNRELIABLE)),
    dict(alignment=align(AlignmentStatus.FAILED)),
    dict(alignment=None),
    dict(scene_audit=None, coverage=cov(audit_ran=False)),
    dict(rules=RULES),  # control
], ids=lambda e: next(iter(e)))
def test_reliable_forbidden_fails_despite_other_problems(extra):
    judgments = [J("R1", Verdict.FORBIDDEN), J("R2", Verdict.UNCERTAIN, validated=False, errors=["timeout"]),
                 J("R3", Verdict.ALLOWED, mock=True)]
    assert d(judgments=judgments, **extra) == FAIL


def test_reliable_forbidden_in_scene_audit_fails():
    assert d(judgments=[], scene_audit=audit(J("SCENE", Verdict.FORBIDDEN)), coverage=cov(0, 0)) == FAIL


def test_forbidden_beats_invalid_inputs_flag():
    # documented precedence: decide() checks forbidden first
    assert d(judgments=[J(verdict=Verdict.FORBIDDEN)], inputs_valid=False) == FAIL


# ---- unreliable forbidden must not FAIL, must not PASS ----------------------

@pytest.mark.parametrize("bad", [
    dict(mock=True),
    dict(validated=False),
    dict(errors=["bad json"]),
    dict(evidence="   "),
    dict(rule_ids=["A1"]),          # cites only an allow rule
    dict(rule_ids=[]),
    dict(rule_ids=["ZZ9"]),         # nonexistent rule id
], ids=lambda b: next(iter(b)))
def test_unreliable_forbidden_is_review(bad):
    assert d(judgments=[J(verdict=Verdict.FORBIDDEN, **bad)]) == REVIEW


def test_mock_forbidden_in_audit_is_review():
    assert d(judgments=[], scene_audit=audit(J("SCENE", Verdict.FORBIDDEN, mock=True)), coverage=cov(0, 0)) == REVIEW


# ---- never-PASS conditions --------------------------------------------------

@pytest.mark.parametrize("kw", [
    dict(judgments=[J(verdict=Verdict.UNCERTAIN, rule_ids=[])]),
    dict(judgments=[J(validated=False)]),
    dict(judgments=[J(errors=["timeout"])]),
    dict(judgments=[J(mock=True)]),
    dict(scene_audit=audit(J("SCENE", mock=True))),
    dict(scene_audit=audit(J("SCENE", Verdict.UNCERTAIN, rule_ids=[]))),
    dict(scene_audit=audit(J("SCENE", validated=False))),
    dict(scene_audit=audit(J("SCENE", errors=["x"]))),
    dict(coverage=cov(10, 8, truncated=True)),
    dict(coverage=cov(3, 1)),  # judged < total without truncated flag
    dict(scene_audit=None),
    dict(coverage=cov(audit_ran=False)),
    dict(scene_audit=audit(extra=True)),
    dict(rules=[]),
    dict(alignment=align(AlignmentStatus.UNRELIABLE)),
    dict(alignment=align(AlignmentStatus.FAILED)),
    dict(alignment=None),
    dict(coverage=cov(deadline=True)),
    dict(pipeline_errors=["extractor load failure"]),
    dict(inputs_valid=False),
], ids=lambda k: "|".join(k))
def test_never_pass(kw):
    assert d(**kw) == REVIEW


def test_allowed_alignment_statuses_can_pass():
    for s in (AlignmentStatus.IDENTITY, AlignmentStatus.ALIGNED, AlignmentStatus.RESIZED):
        assert d(alignment=align(s)) == PASS


def test_error_never_flips_fail_to_pass_matrix():
    """For every single-fault perturbation of a forbidden-containing run, result is FAIL, never PASS."""
    fb = [J("R1", Verdict.FORBIDDEN)]
    for kw in (dict(pipeline_errors=["e"]), dict(coverage=cov(5, 1, truncated=True)),
               dict(scene_audit=None), dict(rules=RULES)):
        assert d(judgments=fb, **kw) != PASS


# ---- documented gaps (expected-to-pass checks that probe policy holes) ------

def test_allowed_verdict_citing_deny_rule_is_not_pass():
    """An 'allowed' verdict that cites a deny rule is self-contradictory; PASS would be unsafe."""
    assert d(judgments=[J(verdict=Verdict.ALLOWED, rule_ids=["D1"])]) != PASS


def test_allowed_verdict_with_no_evidence_or_rule_is_not_pass():
    assert d(judgments=[J(verdict=Verdict.ALLOWED, rule_ids=[], evidence="")]) != PASS


def test_conflicting_rules_not_pass():
    """Same description as allow and deny: decision layer receives a conflict; must not PASS silently."""
    conflict = [Rule(id="A1", effect=RuleEffect.ALLOW, description="Trees may disappear"),
                Rule(id="D1", effect=RuleEffect.DENY, description="Trees may disappear")]
    assert d(rules=conflict) != PASS


def test_reason_is_nonempty_and_mentions_review_cause():
    dec, reason = decide(inp(coverage=cov(10, 8, truncated=True)))
    assert dec == REVIEW and "truncated" in reason
