"""Safe image decoding with limits from ``cfg['input']``."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError


class ImageError(ValueError):
    """Raised for missing, oversized, unsupported, or corrupt images."""


@dataclass
class LoadedImage:
    array: np.ndarray  # HxWx3 uint8 RGB
    sha256: str  # of the original file bytes
    format: str
    width: int
    height: int


def decode_image(data: bytes, cfg: dict, name: str = "image") -> LoadedImage:
    limits = cfg["input"]
    if not data:
        raise ImageError(f"{name}: empty file")
    if len(data) > limits["max_file_mb"] * 1024 * 1024:
        raise ImageError(f"{name}: file larger than {limits['max_file_mb']} MB")
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt = (im.format or "").upper()
            if fmt not in {f.upper() for f in limits["allowed_formats"]}:
                raise ImageError(f"{name}: unsupported format {fmt or 'unknown'}")
            w, h = im.size
            if w * h > limits["max_pixels"]:
                raise ImageError(f"{name}: {w}x{h} exceeds {limits['max_pixels']} pixel limit")
            if w < 1 or h < 1:
                raise ImageError(f"{name}: empty image")
            arr = np.asarray(im.convert("RGB"), dtype=np.uint8).copy()
    except ImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ImageError(f"{name}: cannot decode image ({exc.__class__.__name__}: {exc})") from exc
    return LoadedImage(arr, hashlib.sha256(data).hexdigest(), fmt, w, h)


def load_image(path: str | Path, cfg: dict) -> LoadedImage:
    p = Path(path)
    try:
        size = p.stat().st_size
    except OSError as exc:
        raise ImageError(f"{p.name}: cannot read file ({exc.__class__.__name__})") from exc
    if size > cfg["input"]["max_file_mb"] * 1024 * 1024:
        raise ImageError(f"{p.name}: file larger than {cfg['input']['max_file_mb']} MB")
    try:
        data = p.read_bytes()
    except OSError as exc:
        raise ImageError(f"{p.name}: cannot read file ({exc.__class__.__name__})") from exc
    return decode_image(data, cfg, p.name)


def save_png(path: str | Path, array: np.ndarray) -> None:
    """Atomic lossless PNG write (tmp + replace)."""
    import os

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    Image.fromarray(array).save(tmp, format="PNG")
    os.replace(tmp, p)
