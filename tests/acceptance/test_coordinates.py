"""Coordinate / crop acceptance tests on synthetic fixtures (SYNTHETIC; classical proposals only, no model)."""

from __future__ import annotations

import numpy as np
import pytest

from tests.acceptance.helpers import iou, overlaps

pytest.importorskip("gameqa.vision.proposals")
pytest.importorskip("gameqa.vision.alignment")
from gameqa.config import load_config  # noqa: E402
from gameqa.imageio import load_image  # noqa: E402
from gameqa.vision.alignment import align  # noqa: E402
from gameqa.vision.proposals import propose  # noqa: E402


def run_props(case):
    cfg = load_config()
    ref = load_image(case["reference"], cfg).array
    cand = load_image(case["candidate"], cfg).array
    res, aligned, mask = align(ref, cand, cfg)
    props, cov = propose(ref, aligned, mask, None, cfg)  # classical only: dino_map=None
    return cfg, ref, aligned, res, props, cov


@pytest.mark.parametrize("name", [
    "object_removed", "translation_object_removed",
    "small_object_removed",
])
def test_proposal_overlaps_true_changed_box(case, name):
    c = case(name)
    cfg, ref, aligned, res, props, cov = run_props(c)
    H, W = ref.shape[:2]
    for p in props:
        x1, y1, x2, y2 = p.box
        assert 0 <= x1 < x2 <= W and 0 <= y1 < y2 <= H, f"box out of reference bounds: {p.box}"
    truth = c["expected"]["changed_boxes"][0]
    best = max((iou(p.box, truth) for p in props), default=0.0)
    assert best > 0, f"{name}: no proposal overlaps true box {truth}; proposals={[p.box for p in props]}"


def test_small_translation_does_not_flood_proposals(case):
    c = case("small_translation")
    cfg, ref, aligned, res, props, cov = run_props(c)
    assert res.status.value in {"aligned", "identity", "unreliable"}
    if res.status.value == "aligned":
        total_area = sum(p.area_fraction for p in props)
        assert total_area < 0.10, f"translation not compensated: {total_area:.2f} of frame proposed"


def test_crops_use_same_reference_box_on_both_images(case):
    c = case("object_removed")
    cfg, ref, aligned, res, props, cov = run_props(c)
    assert props
    for p in props:
        x1, y1, x2, y2 = p.box
        rc, cc = ref[y1:y2, x1:x2], aligned[y1:y2, x1:x2]
        assert rc.shape == cc.shape == (y2 - y1, x2 - x1, 3)
    # the removed barrel region must differ between crops, an unchanged corner must not
    t = c["expected"]["changed_boxes"][0]
    diff_changed = np.abs(ref[t[1]:t[3], t[0]:t[2]].astype(int) - aligned[t[1]:t[3], t[0]:t[2]].astype(int)).mean()
    diff_static = np.abs(ref[0:20, 300:400].astype(int) - aligned[0:20, 300:400].astype(int)).mean()
    assert diff_changed > 5 * max(diff_static, 0.5)


def test_different_dimensions_aligned_to_reference_frame(case):
    c = case("different_dimensions")
    cfg, ref, aligned, res, props, cov = run_props(c)
    assert aligned.shape == ref.shape, "aligned candidate must be in reference frame"
    assert res.status.value in {"resized", "aligned", "unreliable"}


def test_large_misalignment_is_unreliable(case):
    c = case("large_misalignment")
    cfg, ref, aligned, res, props, cov = run_props(c)
    assert res.status.value == "unreliable", f"expected unreliable alignment, got {res.status.value}"


def test_identical_has_no_proposals(case):
    c = case("identical")
    cfg, ref, aligned, res, props, cov = run_props(c)
    assert props == [] and not cov.truncated
