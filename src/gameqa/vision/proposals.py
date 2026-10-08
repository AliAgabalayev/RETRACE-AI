"""Change proposals: DINOv2 distance map + classical pixel-diff fallback, merged and capped.

Score semantics: max of (source signal / source threshold) inside the box, i.e. 'x times the detection
threshold' (dinov2: cosine distance / dinov2_threshold; classical: blurred gray diff / classical_threshold);
union = max of its parts. Comparable across sources for ordering only; never a probability.
"""
from __future__ import annotations

import cv2
import numpy as np

from gameqa.contracts import Coverage, RegionProposal

_MAX_RAW = 200


def _components(mask: np.ndarray, score_map: np.ndarray, min_area: int, close_px: int, source: str, norm: float):
    """Returns (components, truncated). score is divided by `norm` (the source threshold) so that
    scores of different sources are comparable ('x times the detection threshold')."""
    m = (mask > 0).astype(np.uint8)
    if close_px > 1:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_px, close_px))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area:
            continue
        sc = float(score_map[lab == i].max()) / norm if area < 4_000_000 else float(score_map[y:y + h, x:x + w].max()) / norm
        out.append([int(x), int(y), int(x + w), int(y + h), sc, {source}])
    out.sort(key=lambda r: -r[4])
    return out[:_MAX_RAW], len(out) > _MAX_RAW


def _overlaps(a, b, iou_thr: float) -> bool:
    ix = min(a[2], b[2]) - max(a[0], b[0])
    iy = min(a[3], b[3]) - max(a[1], b[1])
    if ix <= 0 or iy <= 0:
        return False
    inter = ix * iy
    aa = (a[2] - a[0]) * (a[3] - a[1])
    bb = (b[2] - b[0]) * (b[3] - b[1])
    iou = inter / (aa + bb - inter)
    return iou > iou_thr or inter / min(aa, bb) > 0.5  # containment also merges


def _merge(boxes: list, iou_thr: float) -> list:
    boxes = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if _overlaps(boxes[i], boxes[j], iou_thr):
                    a, b = boxes[i], boxes[j]
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]),
                                max(a[4], b[4]), a[5] | b[5]]
                    del boxes[j]
                    changed = True
                    break
            if changed:
                break
    return boxes


def propose(reference, aligned_candidate, overlap_mask, dino_map, cfg) -> tuple[list[RegionProposal], Coverage]:
    pc = cfg.get("proposals", {})
    sources = pc.get("sources", ["dinov2", "classical"])
    H, W = reference.shape[:2]
    min_area = max(int(pc.get("min_area_px", 40)), int(pc.get("min_area_fraction", 0.0001) * H * W))
    pad = int(pc.get("box_padding_px", 8))
    valid = overlap_mask > 0
    # Erode the valid region: blur/patch effects at the warp border must not leak into the diff.
    er = int(pc.get("mask_erode_px", 7))
    if er > 0 and not valid.all():
        valid = cv2.erode(valid.astype(np.uint8), np.ones((2 * er + 1, 2 * er + 1), np.uint8)) > 0
    raw_truncated = False
    close_px = max(3, int(round(min(H, W) * 0.01)) | 1)

    raw: list = []
    # Global change guard (tuned on dev only): when a large share of the valid area exceeds the DINOv2 threshold
    # (different shot / camera cut / lighting+layout shift), per-region proposals are meaningless fragments.
    # Collapse to ONE full-frame proposal and mark coverage as truncated (never auto-PASS).
    gfrac = float(pc.get("global_change_fraction", 0.10))
    if dino_map is not None and "dinov2" in sources and gfrac > 0 and valid.any():
        frac = float(((dino_map > float(pc.get("dinov2_threshold", 0.35))) & valid).sum() / valid.sum())
        if frac >= gfrac:
            sc = float(dino_map[valid].max()) / float(pc.get("dinov2_threshold", 0.35))
            prop = RegionProposal(id="R1", box=(0, 0, W, H), score=sc, source="dinov2", area_fraction=1.0)
            return [prop], Coverage(proposals_total=1, truncated=True)
    if "dinov2" in sources and dino_map is not None:
        thr = float(pc.get("dinov2_threshold", 0.35))
        comps, tr = _components((dino_map > thr) & valid, dino_map, min_area, close_px, "dinov2", thr)
        raw += comps; raw_truncated |= tr
    if "classical" in sources:
        g1 = cv2.GaussianBlur(cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
        g2 = cv2.GaussianBlur(cv2.cvtColor(aligned_candidate, cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
        if pc.get("classical_gain_normalize", True):
            # global brightness/contrast change (allowed 'lighting') must not flood the diff: robust
            # median gain+offset fit on the valid area. Local object changes are small => median is unaffected.
            r_, c_ = g1[valid].astype(np.float32), g2[valid].astype(np.float32)
            if r_.size > 100:
                gain = float(np.clip((np.percentile(r_, 90) - np.percentile(r_, 10)) /
                                     max(1.0, np.percentile(c_, 90) - np.percentile(c_, 10)), 0.5, 2.0))
                off = float(np.median(r_) - gain * np.median(c_))
                g2 = np.clip(g2.astype(np.float32) * gain + off, 0, 255).astype(np.uint8)
        diff = cv2.absdiff(g1, g2)
        thr = float(pc.get("classical_threshold", 40))
        comps, tr = _components((diff > thr) & valid, diff.astype(np.float32), min_area, close_px, "classical", thr)
        raw += comps; raw_truncated |= tr

    # pad + clip before merging, so near-adjacent components fuse
    padded = []
    for x1, y1, x2, y2, sc, src in raw:
        padded.append([max(0, x1 - pad), max(0, y1 - pad), min(W, x2 + pad), min(H, y2 + pad), sc, src])
    merged = _merge(padded, float(pc.get("merge_iou", 0.1)))
    merged.sort(key=lambda r: -r[4])
    total = len(merged)
    cap = int(pc.get("max_regions", 8))
    kept = merged[:cap]
    props = []
    for i, (x1, y1, x2, y2, sc, src) in enumerate(kept, 1):
        source = next(iter(src)) if len(src) == 1 else "union"
        props.append(RegionProposal(id=f"R{i}", box=(int(x1), int(y1), int(x2), int(y2)), score=float(sc),
                                    source=source, area_fraction=float((x2 - x1) * (y2 - y1) / (H * W))))
    return props, Coverage(proposals_total=total, truncated=total > cap or raw_truncated)
