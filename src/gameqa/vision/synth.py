"""Synthetic scene generator for DL smoke tests / unit tests. Clearly synthetic, deterministic."""
from __future__ import annotations

import cv2
import numpy as np


def make_scene(w: int = 960, h: int = 540, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, h)[:, None, None]
    sky = np.array([90, 150, 230]) * (1 - y) + np.array([200, 220, 240]) * y
    img = np.broadcast_to(sky, (h, w, 3)).copy()
    img[int(h * 0.7):] = np.array([70, 120, 60])
    noise = rng.normal(0, 6, (h, w, 1))
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    # textured ground + objects
    for i in range(14):
        x = int(rng.integers(0, w - 80)); yy = int(rng.integers(int(h * 0.72), h - 40))
        cv2.circle(img, (x, yy), int(rng.integers(6, 14)), tuple(int(c) for c in rng.integers(30, 120, 3)), -1)
    cv2.rectangle(img, (120, 250), (260, 380), (150, 90, 50), -1)           # house body
    cv2.fillPoly(img, [np.array([[110, 250], [190, 190], [270, 250]])], (120, 40, 40))
    cv2.rectangle(img, (170, 310), (210, 380), (60, 40, 20), -1)            # door
    cv2.rectangle(img, (620, 300), (700, 420), (200, 180, 40), -1)          # character body
    cv2.circle(img, (660, 280), 22, (230, 190, 160), -1)                    # head
    cv2.rectangle(img, (420, 400), (470, 440), (140, 140, 150), -1)         # crate
    cv2.circle(img, (800, 120), 40, (250, 240, 120), -1)                    # sun
    return img


def remove_rect(img: np.ndarray, box) -> np.ndarray:
    """'Remove' an object by painting over with local background (simple inpaint)."""
    x1, y1, x2, y2 = box
    mask = np.zeros(img.shape[:2], np.uint8); mask[y1:y2, x1:x2] = 255
    return cv2.inpaint(img, mask, 5, cv2.INPAINT_TELEA)


def recolor(img: np.ndarray, box, bgr_shift=(60, -40, -40)) -> np.ndarray:
    out = img.copy(); x1, y1, x2, y2 = box
    out[y1:y2, x1:x2] = np.clip(out[y1:y2, x1:x2].astype(int) + np.array(bgr_shift), 0, 255).astype(np.uint8)
    return out


def lighting(img: np.ndarray, gain=0.8, tint=(0, 0, 15)) -> np.ndarray:
    return np.clip(img.astype(np.float32) * gain + np.array(tint), 0, 255).astype(np.uint8)


def translate(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REPLICATE)
