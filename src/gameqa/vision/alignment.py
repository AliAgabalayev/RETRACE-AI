"""Cautious global alignment (identity / translation / affine). Never local warping.

Transform direction: ``candidate_to_reference`` maps candidate pixel (x, y, 1) -> reference pixel.
``aligned_candidate = cv2.warpAffine(candidate, M[:2], (W_ref, H_ref))`` with M = candidate->reference.
"""
from __future__ import annotations

import cv2
import numpy as np

from gameqa.contracts import AlignmentResult, AlignmentStatus

_I3 = np.eye(3)


def _gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def _mad(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute gray difference (0-255)."""
    return float(np.mean(np.abs(_gray(a).astype(np.float32) - _gray(b).astype(np.float32))))


def _result(status, M, mask, diag) -> AlignmentResult:
    return AlignmentResult(
        status=status,
        candidate_to_reference=np.asarray(M, dtype=float).tolist(),
        overlap_fraction=float((mask > 0).mean()),
        overlap_mask_path=None,
        diagnostics=diag,
    )


def _warp(candidate: np.ndarray, M: np.ndarray, hw: tuple[int, int]):
    h, w = hw
    warped = cv2.warpAffine(candidate, M[:2], (w, h), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    valid = cv2.warpAffine(np.full(candidate.shape[:2], 255, np.uint8), M[:2], (w, h),
                           flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return warped, valid


def _estimate_translation(ref: np.ndarray, cand: np.ndarray):
    a = _gray(ref).astype(np.float32)
    b = _gray(cand).astype(np.float32)
    win = cv2.createHanningWindow((a.shape[1], a.shape[0]), cv2.CV_32F)
    (dx, dy), resp = cv2.phaseCorrelate(b, a, win)  # shift taking cand -> ref
    return float(dx), float(dy), float(resp)


def _estimate_affine(ref: np.ndarray, cand: np.ndarray):
    orb = cv2.ORB_create(2000)
    k1, d1 = orb.detectAndCompute(_gray(cand), None)
    k2, d2 = orb.detectAndCompute(_gray(ref), None)
    if d1 is None or d2 is None or len(k1) < 8 or len(k2) < 8:
        return None, 0.0, 0
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(d1, d2)
    if len(matches) < 8:
        return None, 0.0, len(matches)
    src = np.float32([k1[m.queryIdx].pt for m in matches])
    dst = np.float32([k2[m.trainIdx].pt for m in matches])
    # similarity/affine restricted (partial = rotation+uniform scale+translation): no local warps
    A, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    if A is None:
        return None, 0.0, len(matches)
    return A, float(inl.mean()), len(matches)


def align(reference: np.ndarray, candidate: np.ndarray, cfg: dict) -> tuple[AlignmentResult, np.ndarray, np.ndarray]:
    acfg = cfg.get("alignment", {})
    mode = acfg.get("mode", "auto")
    max_shift = float(acfg.get("max_shift_fraction", 0.05))
    min_overlap = float(acfg.get("min_overlap_fraction", 0.85))
    min_inl = float(acfg.get("min_inlier_ratio", 0.5))
    # a warp is only adopted if it reduces residual by this factor (guards against warping away a change)
    min_gain = float(acfg.get("min_error_gain", 0.7))
    H, W = reference.shape[:2]
    ones = np.full((H, W), 255, np.uint8)
    diag: dict = {}

    status_resized = False
    cand = candidate
    M_resize = _I3.copy()
    if candidate.shape[:2] != (H, W):
        ch, cw = candidate.shape[:2]
        diag["original_candidate_size"] = f"{cw}x{ch}"
        diag["aspect_ratio_mismatch"] = abs((cw / ch) - (W / H)) > 0.02
        cand = cv2.resize(candidate, (W, H), interpolation=cv2.INTER_AREA)
        M_resize = np.array([[W / cw, 0, 0], [0, H / ch, 0], [0, 0, 1.0]])
        status_resized = True

    err0 = _mad(reference, cand)
    diag["residual_identity"] = round(err0, 3)
    ok_status = AlignmentStatus.RESIZED if status_resized else AlignmentStatus.IDENTITY

    if diag.get("aspect_ratio_mismatch"):
        # resize across different aspect ratios cannot be trusted as alignment
        return _result(AlignmentStatus.UNRELIABLE, M_resize, ones, {**diag, "reason": "aspect ratio mismatch"}), cand, ones

    if mode == "identity" or err0 < 2.0:
        return _result(ok_status, M_resize, ones, diag), cand, ones

    # try global translation
    dx, dy, resp = _estimate_translation(reference, cand)
    diag.update(shift_dx=round(dx, 2), shift_dy=round(dy, 2), phase_response=round(resp, 4))
    best = None
    shift_frac = max(abs(dx) / W, abs(dy) / H)
    if 0.5 <= max(abs(dx), abs(dy)) and shift_frac <= max_shift * 2 and resp > 0.05:
        Mt = np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1.0]])
        w_t, v_t = _warp(cand, Mt, (H, W))
        e = _mad_masked(reference, w_t, v_t)
        diag["residual_translation"] = round(e, 3)
        if e < err0 * min_gain:
            best = ("translation", Mt, w_t, v_t, e, resp)

    # try affine (ORB + RANSAC)
    A, inl, nm = _estimate_affine(reference, cand)
    diag.update(orb_matches=nm, inlier_ratio=round(inl, 3))
    if A is not None and inl >= min_inl:
        Ma = np.vstack([A, [0, 0, 1.0]])
        # reject near-identity (nothing to fix) and wild transforms
        if not np.allclose(Ma, _I3, atol=1e-3):
            w_a, v_a = _warp(cand, Ma, (H, W))
            e = _mad_masked(reference, w_a, v_a)
            diag["residual_affine"] = round(e, 3)
            if e < err0 * min_gain and (best is None or e < best[4] * 0.9):
                best = ("affine", Ma, w_a, v_a, e, inl)

    if best is None:
        # no warp improves things: either already aligned (content changes) or unmatched
        if err0 > 25.0 and (resp < 0.05 and (A is None or inl < min_inl)):
            diag["reason"] = "large residual and no reliable global transform"
            return _result(AlignmentStatus.UNRELIABLE, M_resize, ones, diag), cand, ones
        return _result(ok_status, M_resize, ones, diag), cand, ones

    kind, Mx, warped, valid, e, q = best
    tx, ty = Mx[0, 2], Mx[1, 2]
    diag.update(model=kind, shift_fraction=round(max(abs(tx) / W, abs(ty) / H), 4),
                residual_after=round(e, 3))
    overlap = float((valid > 0).mean())
    if (max(abs(tx) / W, abs(ty) / H) > max_shift) or overlap < min_overlap:
        diag["reason"] = "shift or overlap beyond limits"
        res = _result(AlignmentStatus.UNRELIABLE, M_resize, ones, diag)
        return res, cand, ones  # identity-warped so crops can still be shown
    Mfull = Mx @ M_resize
    # pixels outside the valid overlap carry no candidate information: copy reference there so they
    # compare equal (no spurious border features); overlap_mask marks them invalid.
    warped = np.where((valid > 0)[..., None], warped, reference)
    return _result(AlignmentStatus.ALIGNED, Mfull, valid, diag), warped, valid


def _mad_masked(a: np.ndarray, b: np.ndarray, valid: np.ndarray) -> float:
    d = np.abs(_gray(a).astype(np.float32) - _gray(b).astype(np.float32))
    v = valid > 0
    return float(d[v].mean()) if v.any() else 255.0
