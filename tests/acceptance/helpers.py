"""Acceptance-test helpers. Everything here that fakes a model is labelled MOCK (never real inference)."""

from __future__ import annotations

import numpy as np

from gameqa.contracts import RegionJudgment, SceneAudit, Verdict


def iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua else 0.0


def overlaps(a, b) -> bool:
    return iou(a, b) > 0


class MockJudge:
    """QA MOCK judge (is_mock=True). Provides deterministic judgments for fault injection.

    behaviour: allowed | forbidden | uncertain | timeout | invalid_json | unknown_rule
    All judgments are labelled is_mock=True, so the policy must never turn them into FAIL or PASS.
    """

    model_id = "mock:qa-fault-injection"
    prompt_version = "mock"
    is_mock = True

    def __init__(self, behaviour: str = "allowed", audit_extra: bool = False):
        self.behaviour = behaviour
        self.audit_extra = audit_extra
        self.calls: list[str] = []

    def _j(self, region_id: str) -> RegionJudgment:
        b = self.behaviour
        kw = dict(region_id=region_id, observed_change="mock", model=self.model_id, is_mock=True)
        if b == "allowed":
            return RegionJudgment(verdict=Verdict.ALLOWED, rule_ids=["A1"], evidence="mock", validated=True, **kw)
        if b == "forbidden":
            return RegionJudgment(verdict=Verdict.FORBIDDEN, rule_ids=["D1"], evidence="mock", validated=True, **kw)
        if b == "uncertain":
            return RegionJudgment(verdict=Verdict.UNCERTAIN, validated=True, **kw)
        if b == "timeout":
            return RegionJudgment(verdict=Verdict.UNCERTAIN, errors=["timeout after 30s"], validated=False, **kw)
        if b == "invalid_json":
            return RegionJudgment(verdict=Verdict.UNCERTAIN, errors=["invalid JSON"], validated=False, **kw)
        if b == "unknown_rule":
            return RegionJudgment(verdict=Verdict.FORBIDDEN, rule_ids=["ZZ99"], evidence="mock",
                                  errors=["unknown rule id ZZ99"], validated=False, **kw)
        raise ValueError(b)

    def judge_region(self, proposal, ref_crop, cand_crop, ref_context, cand_context, rules):
        self.calls.append(proposal.id)
        assert ref_crop.shape == cand_crop.shape, "ref/cand crops must come from the same reference box"
        return self._j(proposal.id)

    def audit_scene(self, reference, aligned_candidate, rules, proposals):
        return SceneAudit(judgment=self._j("SCENE"), extra_changes_reported=self.audit_extra)


class ZeroExtractor:
    """QA MOCK feature extractor (no model): returns an all-zero distance map."""

    version = "mock:zero"
    device = "cpu"
    dtype = "float32"

    def distance_map(self, reference, aligned_candidate):
        return np.zeros(reference.shape[:2], np.float32)
