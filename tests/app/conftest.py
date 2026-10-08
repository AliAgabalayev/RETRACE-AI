"""Fakes for the APP tests. Everything here is a labelled stand-in, never real inference."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from gameqa import pipeline
from gameqa.config import load_config
from gameqa.contracts import (
    AlignmentResult,
    AlignmentStatus,
    Coverage,
    PairInput,
    RegionJudgment,
    RegionProposal,
    Rule,
    RuleEffect,
    SceneAudit,
    Verdict,
)

RULES = [
    Rule(id="A1", effect=RuleEffect.ALLOW, description="Lighting may change."),
    Rule(id="D1", effect=RuleEffect.DENY, description="Objects must not disappear."),
]


class FakeExtractor:
    version, device, dtype = "fake-dino", "cpu", "float32"

    def __init__(self, raises: Exception | None = None):
        self.raises = raises

    def distance_map(self, reference, aligned):
        if self.raises:
            raise self.raises
        return np.zeros(reference.shape[:2], np.float32)


class FakeJudge:
    model_id = "fake:test"
    prompt_version = "vtest"

    def __init__(self, verdict=Verdict.ALLOWED, rule_ids=("A1",), *, is_mock=False, validated=True,
                 errors=(), audit_extra=False, audit_verdict=Verdict.ALLOWED, delay=0.0, raises=False):
        self.verdict, self.rule_ids, self.is_mock = verdict, list(rule_ids), is_mock
        self.validated, self.errors, self.audit_extra = validated, list(errors), audit_extra
        self.audit_verdict, self.delay, self.raises = audit_verdict, delay, raises
        self.calls = 0

    def _j(self, rid, verdict, rule_ids):
        return RegionJudgment(
            region_id=rid, observed_change="something changed", verdict=verdict,
            rule_ids=rule_ids, evidence="visible in crop", model=self.model_id,
            is_mock=self.is_mock, errors=list(self.errors), validated=self.validated,
        )

    def judge_region(self, proposal, ref_crop, cand_crop, ref_ctx, cand_ctx, rules):
        import time

        self.calls += 1
        if self.raises:
            raise RuntimeError("boom")
        time.sleep(self.delay)
        return self._j(proposal.id, self.verdict, self.rule_ids)

    def audit_scene(self, reference, aligned, rules, proposals):
        return SceneAudit(
            judgment=self._j("SCENE", self.audit_verdict, ["A1"] if self.audit_verdict == Verdict.ALLOWED else ["D1"]),
            extra_changes_reported=self.audit_extra,
        )


@pytest.fixture
def cfg(tmp_path):
    c = load_config()
    c["run"]["artifacts_dir"] = str(tmp_path / "artifacts")
    c["run"]["references_dir"] = str(tmp_path / "references")
    return c


def _png(path, arr):
    Image.fromarray(arr).save(path)
    return str(path)


@pytest.fixture
def pair(tmp_path):
    ref = np.full((120, 160, 3), 100, np.uint8)
    cand = ref.copy()
    cand[20:60, 30:80] = 200
    return PairInput(
        reference_path=_png(tmp_path / "ref.png", ref),
        candidate_path=_png(tmp_path / "cand.png", cand),
        rules=RULES,
        sample_id="s1",
    )


@pytest.fixture
def patch_vision(monkeypatch):
    """Replace alignment/proposals with deterministic fakes; returns a settings dict."""
    state = {"proposals": [RegionProposal(id="R1", box=(30, 20, 80, 60), score=0.9, source="dinov2",
                                          area_fraction=0.1)],
             "coverage": Coverage(proposals_total=1), "align_status": AlignmentStatus.IDENTITY}

    def fake_align(ref, cand, cfg):
        res = AlignmentResult(status=state["align_status"], candidate_to_reference=np.eye(3).tolist(),
                              overlap_fraction=1.0)
        return res, cand.copy(), np.full(ref.shape[:2], 255, np.uint8)

    def fake_propose(ref, aligned, mask, dino_map, cfg):
        state["dino_map_seen"] = dino_map
        return list(state["proposals"]), state["coverage"].model_copy()

    monkeypatch.setattr(pipeline, "_align", fake_align)
    monkeypatch.setattr(pipeline, "_propose", fake_propose)
    return state
