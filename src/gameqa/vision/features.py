"""Frozen DINOv2 patch-feature distance maps (inference only)."""
from __future__ import annotations

import hashlib
import os
import warnings
from dataclasses import dataclass

import cv2
import numpy as np

_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
_STD = np.array([0.229, 0.224, 0.225], np.float32)


class ModelLoadError(RuntimeError):
    """Raised when the frozen feature model cannot be loaded (pipeline -> degraded mode)."""


@dataclass
class PreprocInfo:
    """Geometry of the resize/pad so patch grid <-> reference pixels can be mapped."""
    ref_h: int
    ref_w: int
    new_h: int      # resized (pre-pad) size
    new_w: int
    pad_h: int      # bottom padding in resized pixels
    pad_w: int      # right padding
    patch: int

    @property
    def grid(self) -> tuple[int, int]:
        return (self.new_h + self.pad_h) // self.patch, (self.new_w + self.pad_w) // self.patch

    @property
    def scale(self) -> float:
        return self.new_w / self.ref_w


def compute_preproc(h: int, w: int, long_side: int, patch: int) -> PreprocInfo:
    s = long_side / max(h, w)
    nh, nw = max(1, round(h * s)), max(1, round(w * s))
    ph, pw = (-nh) % patch, (-nw) % patch
    return PreprocInfo(h, w, nh, nw, ph, pw, patch)


def patch_to_reference_box(info: PreprocInfo, gy: int, gx: int) -> tuple[float, float, float, float]:
    """Reference-pixel box (x1,y1,x2,y2, float, unclipped-to-padding clipped to image) of patch (gy, gx)."""
    p, s = info.patch, info.scale
    x1, y1, x2, y2 = gx * p / s, gy * p / s, (gx + 1) * p / s, (gy + 1) * p / s
    return x1, y1, min(x2, info.ref_w), min(y2, info.ref_h)


def grid_to_reference(dist: np.ndarray, info: PreprocInfo) -> np.ndarray:
    """Crop padded patch-grid to valid area and upsample to reference HxW (float32)."""
    p = info.patch
    gh, gw = dist.shape
    vh = int(np.ceil(info.new_h / p))
    vw = int(np.ceil(info.new_w / p))
    d = dist[:vh, :vw].astype(np.float32)
    # patch grid covers vh*p x vw*p resized pixels, of which new_h x new_w are real image.
    up = cv2.resize(d, (vw * p, vh * p), interpolation=cv2.INTER_LINEAR)
    up = up[: info.new_h, : info.new_w]
    return cv2.resize(up, (info.ref_w, info.ref_h), interpolation=cv2.INTER_LINEAR).astype(np.float32)


class FeatureExtractor:
    def __init__(self, cfg: dict):
        import torch
        fc = cfg.get("features", {})
        self.long_side = int(fc.get("input_long_side", 518))
        self.patch = int(fc.get("patch_size", 14))
        dev = fc.get("device", "auto")
        if dev == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = dev
        self.dtype = fc.get("dtype", "float32")
        self._torch = torch
        self.backend = None
        self.version = ""
        name = fc.get("model", "dinov2_vits14")
        errs = []
        try:
            if os.environ.get("GAMEQA_FORCE_HF") == "1":
                raise RuntimeError("forced HF backend")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.model = torch.hub.load(fc.get("hub_repo", "facebookresearch/dinov2"), name, trust_repo=True, verbose=False)
            self.backend = "torch.hub"
            ck = os.path.expanduser(f"~/.cache/torch/hub/checkpoints/{name}_pretrain.pth")
            sha = hashlib.sha256(open(ck, "rb").read()).hexdigest()[:12] if os.path.exists(ck) else "unknown"
            self.version = f"{name}@{fc.get('hub_repo', 'facebookresearch/dinov2')}:main weights_sha256={sha}"
        except Exception as e:  # noqa: BLE001
            errs.append(f"torch.hub: {e!r}")
            try:
                from transformers import AutoModel
                self.model = AutoModel.from_pretrained("facebook/dinov2-small")
                self.backend = "transformers"
                self.version = "facebook/dinov2-small (transformers fallback)"
            except Exception as e2:  # noqa: BLE001
                errs.append(f"transformers: {e2!r}")
                raise ModelLoadError("Could not load DINOv2: " + "; ".join(errs)) from e2
        try:
            self._dt = getattr(torch, self.dtype)
            self.model = self.model.eval().to(self.device, self._dt)
        except Exception as e:  # noqa: BLE001
            raise ModelLoadError(f"Could not move DINOv2 to {self.device}/{self.dtype}: {e!r}") from e
        for p in self.model.parameters():
            p.requires_grad_(False)

    def _prep(self, img: np.ndarray, info: PreprocInfo):
        torch = self._torch
        r = cv2.resize(img, (info.new_w, info.new_h), interpolation=cv2.INTER_AREA if info.scale < 1 else cv2.INTER_CUBIC)
        x = (r.astype(np.float32) / 255.0 - _MEAN) / _STD
        x = np.pad(x, ((0, info.pad_h), (0, info.pad_w), (0, 0)), mode="constant")  # zero == mean colour
        return torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0)

    def _patch_tokens(self, x):
        torch = self._torch
        x = x.to(self.device, self._dt)
        with torch.inference_mode():
            if self.backend == "torch.hub":
                out = self.model.forward_features(x)["x_norm_patchtokens"]
            else:
                out = self.model(pixel_values=x).last_hidden_state[:, 1:]
        return out[0].float()

    def patch_grid_distance(self, reference: np.ndarray, aligned_candidate: np.ndarray):
        """Return (patch-grid cosine distance [gh,gw], PreprocInfo)."""
        torch = self._torch
        h, w = reference.shape[:2]
        if aligned_candidate.shape[:2] != (h, w):
            raise ValueError("reference and aligned_candidate must have identical size")
        info = compute_preproc(h, w, self.long_side, self.patch)
        gh, gw = info.grid
        fa = self._patch_tokens(self._prep(reference, info))
        fb = self._patch_tokens(self._prep(aligned_candidate, info))
        assert fa.shape[0] == gh * gw, (fa.shape, gh, gw)
        fa = torch.nn.functional.normalize(fa, dim=-1)
        fb = torch.nn.functional.normalize(fb, dim=-1)
        d = (1.0 - (fa * fb).sum(-1)).clamp_(min=0).reshape(gh, gw).cpu().numpy()
        return d, info

    def distance_map(self, reference: np.ndarray, aligned_candidate: np.ndarray) -> np.ndarray:
        d, info = self.patch_grid_distance(reference, aligned_candidate)
        return grid_to_reference(d, info)
