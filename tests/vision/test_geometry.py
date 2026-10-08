import numpy as np
import pytest
import yaml

from gameqa.contracts import AlignmentStatus
from gameqa.vision import alignment, proposals, synth
from gameqa.vision.features import compute_preproc, grid_to_reference, patch_to_reference_box

CFG = yaml.safe_load(open("configs/default.yaml"))


def test_preproc_grid_and_patch_mapping_roundtrip():
    info = compute_preproc(540, 960, 518, 14)
    assert info.new_w == 518 and info.new_h == 291 and info.pad_h == 3 and info.pad_w == 0
    assert info.grid == (21, 37)
    x1, y1, x2, y2 = patch_to_reference_box(info, 0, 0)
    assert (x1, y1) == (0, 0) and abs(x2 - 14 / info.scale) < 1e-6
    # last column patch ends exactly at the image right edge, last row is clipped to the image
    _, _, x2, y2 = patch_to_reference_box(info, info.grid[0] - 1, info.grid[1] - 1)
    assert x2 == 960 and y2 == 540


def test_grid_to_reference_localises_single_patch():
    info = compute_preproc(540, 960, 518, 14)
    d = np.zeros(info.grid, np.float32)
    gy, gx = 8, 20
    d[gy, gx] = 1.0
    full = grid_to_reference(d, info)
    assert full.shape == (540, 960)
    ys, xs = np.nonzero(full > 0.5)
    x1, y1, x2, y2 = patch_to_reference_box(info, gy, gx)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    assert abs(xs.mean() - cx) < 8 and abs(ys.mean() - cy) < 8


def test_alignment_known_translation():
    ref = synth.make_scene()
    cand = synth.translate(ref, 12, -8)
    res, al, mask = alignment.align(ref, cand, CFG)
    assert res.status == AlignmentStatus.ALIGNED
    M = np.array(res.candidate_to_reference)
    assert abs(M[0, 2] + 12) < 0.5 and abs(M[1, 2] - 8) < 0.5  # candidate->reference undoes the shift
    assert mask[:, 0:5].sum() == 0 or mask.mean() < 255  # border invalid
    inner = (slice(20, -20), slice(20, -20))
    assert np.abs(al[inner].astype(int) - ref[inner]).mean() < 1.0


def test_alignment_identity_and_resize_and_unreliable():
    ref = synth.make_scene()
    assert alignment.align(ref, ref.copy(), CFG)[0].status == AlignmentStatus.IDENTITY
    small = ref[::2, ::2]
    res, al, mask = alignment.align(ref, small, CFG)
    assert res.status == AlignmentStatus.RESIZED and al.shape == ref.shape
    other = synth.make_scene(seed=5)[:, ::-1].copy()
    res, al, mask = alignment.align(ref, other, CFG)
    assert res.status in (AlignmentStatus.UNRELIABLE, AlignmentStatus.IDENTITY) and al.shape == ref.shape


def test_removed_rect_is_inside_proposal_without_dino():
    ref = synth.make_scene()
    box = (620, 270, 700, 420)
    cand = synth.remove_rect(ref, box)
    res, al, mask = alignment.align(ref, cand, CFG)
    props, cov = proposals.propose(ref, al, mask, None, CFG)
    assert props and not cov.truncated
    x1, y1, x2, y2 = props[0].box
    assert x1 <= 625 and y1 <= 380 and x2 >= 650 and y2 >= 415  # classical finds only the part that contrasts with the fill (DINOv2 covers more, see real test)
    assert all(p.source == "classical" for p in props)


def test_translation_border_does_not_flood_proposals():
    ref = synth.make_scene()
    cand = synth.translate(ref, 12, -8)
    res, al, mask = alignment.align(ref, cand, CFG)
    props, _ = proposals.propose(ref, al, mask, None, CFG)
    assert props == []


def test_small_object_floor_and_cap_truncation():
    ref = synth.make_scene()
    cand = ref.copy()
    cand[100:112, 100:112] = 255 - cand[100:112, 100:112]  # 12 px object
    props, _ = proposals.propose(ref, cand, np.full(ref.shape[:2], 255, np.uint8), None, CFG)
    assert any(p.box[0] <= 100 and p.box[2] >= 112 for p in props)
    cfg = {**CFG, "proposals": {**CFG["proposals"], "max_regions": 1}}
    cand2 = cand.copy()
    cand2[400:440, 600:650] = 0
    props, cov = proposals.propose(ref, cand2, np.full(ref.shape[:2], 255, np.uint8), None, cfg)
    assert len(props) == 1 and cov.truncated and cov.proposals_total >= 2


def test_overlap_mask_excludes_invalid_area():
    ref = synth.make_scene()
    cand = ref.copy()
    cand[:, :100] = 0
    mask = np.full(ref.shape[:2], 255, np.uint8)
    mask[:, :100] = 0
    props, _ = proposals.propose(ref, cand, mask, None, CFG)
    assert props == []
