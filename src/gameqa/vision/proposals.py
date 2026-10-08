"""Change proposals: DINOv2 distance map + classical pixel-diff fallback, merged and capped.

Score semantics: dinov2 = max cosine distance in the box; classical = max blurred gray diff / 255;
union = max of its parts. Scores of different sources are on different scales -> use for ordering
only, never as a probability.
"""
from __future__ import annotations

import cv2
import numpy as np

from gameqa.contracts import Coverage, RegionProposal

_MAX_RAW = 200


def _components(mask: np.ndarray, score_map: np.ndarray, min_area: int, close_px: int, source: str):
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
        sc = float(score_map[lab == i].max()) if area < 4_000_000 else float(score_map[y:y + h, x:x + w].max())
        out.append([int(x), int(y), int(x + w), int(y + h), sc, {source}])
    out.sort(key=lambda r: -r[4])
    return out[:_MAX_RAW]


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
    min_area = max(1, int(pc.get("min_area_fraction", 0.0005) * H * W))
    pad = int(pc.get("box_padding_px", 8))
    valid = overlap_mask > 0
    close_px = max(3, int(round(min(H, W) * 0.01)) | 1)

    raw: list = []
    if "dinov2" in sources and dino_map is not None:
        thr = float(pc.get("dinov2_threshold", 0.35))
        raw += _components((dino_map > thr) & valid, dino_map, min_area, close_px, "dinov2")
    if "classical" in sources:
        g1 = cv2.GaussianBlur(cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
        g2 = cv2.GaussianBlur(cv2.cvtColor(aligned_candidate, cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
        diff = cv2.absdiff(g1, g2)
        thr = float(pc.get("classical_threshold", 40))
        diff_n = diff.astype(np.float32) / 255.0
        raw += _components((diff > thr) & valid, diff_n, min_area, close_px, "classical")

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
    return props, Coverage(proposals_total=total, truncated=total > cap)
