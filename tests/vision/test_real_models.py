import os

import numpy as np
import pytest
import yaml

from gameqa.vision import alignment, proposals, synth

pytestmark = [pytest.mark.real_model,
              pytest.mark.skipif(os.environ.get("GAMEQA_REAL") != "1", reason="set GAMEQA_REAL=1 to run real-model tests")]
CFG = yaml.safe_load(open("configs/default.yaml"))


def test_real_dinov2_localises_removed_object():
    from gameqa.vision.features import FeatureExtractor
    fx = FeatureExtractor(CFG)
    ref = synth.make_scene()
    cand = synth.remove_rect(ref, (620, 270, 700, 420))
    d = fx.distance_map(ref, cand)
    assert d.shape == ref.shape[:2] and d.dtype == np.float32
    assert d[270:420, 620:700].max() > 3 * d[:200, :500].max() + 0.05
    props, _ = proposals.propose(ref, cand, np.full(ref.shape[:2], 255, np.uint8), d, CFG)
    assert any(p.box[0] <= 640 and p.box[2] >= 680 for p in props)


def test_real_vlm_returns_schema_valid_json():
    from gameqa.contracts import RegionProposal, Rule
    from gameqa.vision.judge import Judge
    j = Judge(CFG)
    w = j.warmup()
    assert w["ok"], w
    ref = synth.make_scene(); cand = synth.remove_rect(ref, (620, 270, 700, 420))
    rules = [Rule(id="A1", effect="allow", description="lighting may change"),
             Rule(id="D1", effect="deny", description="objects must not disappear")]
    p = RegionProposal(id="R1", box=(609, 282, 704, 425), score=1.0, source="union", area_fraction=0.02)
    r = j.judge_region(p, ref[282:425, 609:704], cand[282:425, 609:704], ref, cand, rules)
    assert not r.is_mock and r.model.startswith("ollama:") and r.verdict.value in ("allowed", "forbidden", "uncertain")
