#!/usr/bin/env python
"""Generate deterministic SYNTHETIC fixtures under data/fixtures/<case>/. Owner: qa-engineer.

These are hand-drawn OpenCV scenes. They exercise pipeline behaviour and failure paths;
they say NOTHING about benchmark (VideoGameQA-Bench) performance.

Usage: .venv/bin/python scripts/make_fixtures.py [--out data/fixtures] [--seed 1234]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

W, H = 640, 360

# Ground-truth object boxes [x1, y1, x2, y2] (right/bottom exclusive), reference coordinates.
BOXES = {
    "tree": [60, 110, 160, 262],
    "house": [250, 120, 400, 262],
    "barrel": [450, 215, 500, 265],
    "character": [530, 170, 580, 270],
    "coin": [330, 300, 342, 312],
    "hud": [10, 10, 210, 34],
}

RULES_STD = [
    {"id": "A1", "effect": "allow", "description": "Weather and lighting may change if scene objects remain present."},
    {"id": "A2", "effect": "allow", "description": "Character clothing color may change; the character must remain visible."},
    {"id": "D1", "effect": "deny", "description": "Existing scene objects must not disappear."},
    {"id": "D2", "effect": "deny", "description": "Visible geometry or textures must not become corrupted."},
]


def _rgb(c):  # drawing in RGB arrays
    return tuple(int(v) for v in c)


def render(seed: int, remove=(), clothing=(200, 40, 40)) -> np.ndarray:
    """Return an RGB uint8 HxWx3 scene. Same seed -> same texture; `remove` drops objects."""
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W, 3), np.uint8)
    # sky gradient
    top, bot = np.array([70, 130, 220]), np.array([200, 225, 250])
    t = np.linspace(0, 1, 270)[:, None, None]
    img[:270] = (top * (1 - t) + bot * t).astype(np.uint8)
    # ground with texture noise (seeded, identical across variants)
    img[270:] = (90, 150, 70)
    noise = rng.integers(-18, 19, size=(H, W, 1))
    # distant hills for alignment texture
    cv2.ellipse(img, (200, 270), (260, 60), 0, 180, 360, _rgb((60, 120, 90)), -1)
    cv2.ellipse(img, (520, 270), (220, 45), 0, 180, 360, _rgb((70, 135, 100)), -1)
    img[270:] = (np.clip(img[270:].astype(int) + noise[270:], 0, 255)).astype(np.uint8)
    # path stones (alignment features)
    for i in range(14):
        x = int(rng.integers(20, W - 20)); y = int(rng.integers(275, H - 8))
        cv2.circle(img, (x, y), int(rng.integers(2, 5)), _rgb((120, 110, 100)), -1)
    if "tree" not in remove:
        x1, y1, x2, y2 = BOXES["tree"]
        cv2.rectangle(img, (x1 + 40, y1 + 90), (x1 + 60, y2), _rgb((100, 65, 30)), -1)
        cv2.circle(img, (x1 + 50, y1 + 50), 50, _rgb((30, 110, 40)), -1)
        cv2.circle(img, (x1 + 30, y1 + 70), 25, _rgb((40, 130, 50)), -1)
    if "house" not in remove:
        x1, y1, x2, y2 = BOXES["house"]
        cv2.rectangle(img, (x1, y1 + 40), (x2 - 1, y2), _rgb((190, 150, 110)), -1)
        cv2.fillPoly(img, [np.array([(x1 - 10, y1 + 42), (x2 + 9, y1 + 42), ((x1 + x2) // 2, y1)])], _rgb((150, 50, 40)))
        cv2.rectangle(img, (x1 + 55, y1 + 85), (x1 + 95, y2), _rgb((80, 50, 30)), -1)
        cv2.rectangle(img, (x1 + 15, y1 + 65), (x1 + 40, y1 + 90), _rgb((200, 230, 250)), -1)
    if "barrel" not in remove:
        x1, y1, x2, y2 = BOXES["barrel"]
        cv2.rectangle(img, (x1, y1), (x2 - 1, y2 - 1), _rgb((120, 75, 35)), -1)
        for yy in (y1 + 10, y1 + 38):
            cv2.line(img, (x1, yy), (x2 - 1, yy), _rgb((40, 40, 40)), 3)
    if "character" not in remove:
        x1, y1, x2, y2 = BOXES["character"]
        cv2.circle(img, (x1 + 25, y1 + 14), 13, _rgb((240, 200, 160)), -1)
        cv2.rectangle(img, (x1 + 10, y1 + 28), (x1 + 40, y1 + 70), _rgb(clothing), -1)
        cv2.rectangle(img, (x1 + 12, y1 + 70), (x1 + 22, y2 - 1), _rgb((40, 40, 120)), -1)
        cv2.rectangle(img, (x1 + 28, y1 + 70), (x1 + 38, y2 - 1), _rgb((40, 40, 120)), -1)
    if "coin" not in remove:
        x1, y1, x2, y2 = BOXES["coin"]
        cv2.circle(img, ((x1 + x2) // 2, (y1 + y2) // 2), 6, _rgb((250, 210, 30)), -1)
        cv2.circle(img, ((x1 + x2) // 2, (y1 + y2) // 2), 6, _rgb((160, 120, 0)), 1)
    if "hud" not in remove:
        x1, y1, x2, y2 = BOXES["hud"]
        cv2.rectangle(img, (x1, y1), (x2 - 1, y2 - 1), _rgb((30, 30, 30)), -1)
        cv2.rectangle(img, (x1 + 3, y1 + 3), (x1 + 3 + 140, y2 - 4), _rgb((200, 30, 30)), -1)
    return img


def lighting(img: np.ndarray, gain=0.62, tint=(0.9, 0.85, 1.15)) -> np.ndarray:
    """Global dusk-like brightness + colour shift."""
    out = img.astype(np.float32) * gain * np.array(tint, np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def shift(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, m, (W, H), borderMode=cv2.BORDER_REPLICATE)


def save_png(path: Path, img: np.ndarray) -> None:
    cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def pad(box, p=6):
    x1, y1, x2, y2 = box
    return [max(0, x1 - p), max(0, y1 - p), min(W, x2 + p), min(H, y2 + p)]


def build_cases(seed: int) -> dict:
    base = render(seed)
    cases = {}

    def case(ref, cand, decision, boxes, notes, rules=None, forbidden=None, **extra):
        cases[notes.split(":")[0]] = None  # placeholder to detect dupes
        return dict(ref=ref, cand=cand, decision=decision, boxes=boxes, notes=notes,
                    rules=RULES_STD if rules is None else rules, forbidden=forbidden or [], extra=extra)

    out = {}
    out["identical"] = case(base, base.copy(), "PASS", [], "identical: byte-identical frames, expected PASS via identical shortcut.")
    out["object_removed"] = case(base, render(seed, remove=("barrel",)), "FAIL", [pad(BOXES["barrel"])],
                                 "object_removed: barrel deleted (rule D1).", forbidden=[pad(BOXES["barrel"])])
    out["lighting_change"] = case(base, lighting(base), "PASS", [],
                                  "lighting_change: global brightness/tint, all objects present (rule A1). changed_boxes empty because the change is global.")
    cb = BOXES["character"]
    out["clothing_color_change"] = case(base, render(seed, clothing=(40, 80, 220)), "PASS",
                                        [[cb[0] + 10, cb[1] + 28, cb[0] + 40, cb[1] + 70]],
                                        "clothing_color_change: character shirt red -> blue (rule A2); character still visible.")
    out["allowed_and_forbidden"] = case(base, lighting(render(seed, remove=("barrel",))), "FAIL", [pad(BOXES["barrel"])],
                                        "allowed_and_forbidden: global lighting change (allowed) plus barrel removed (forbidden). Must FAIL.",
                                        forbidden=[pad(BOXES["barrel"])])
    out["small_translation"] = case(base, shift(base, 4, 3), "PASS", [],
                                    "small_translation: whole frame shifted by (+4,+3) px, content unchanged. Pipeline should align or send to review; a FAIL is a false positive. changed_boxes empty (no real change).",
                                    rules=RULES_STD, alt_decisions=["NEEDS_REVIEW"])
    small = cv2.resize(base, (480, 270), interpolation=cv2.INTER_AREA)
    out["translation_object_removed"] = case(base, shift(render(seed, remove=("barrel",)), 4, 3), "FAIL", [pad(BOXES["barrel"])],
                                             "translation_object_removed: frame shifted by (+4,+3) AND barrel deleted (rule D1). Box must be reported in REFERENCE coordinates after alignment. NEEDS_REVIEW acceptable, PASS is a blocker.",
                                             forbidden=[pad(BOXES["barrel"])], alt_decisions=["NEEDS_REVIEW"], must_not=["PASS"])
    out["different_dimensions"] = case(base, small, "PASS", [],
                                       "different_dimensions: candidate downscaled to 480x270, same content. Expect RESIZED alignment; NEEDS_REVIEW also acceptable.",
                                       alt_decisions=["NEEDS_REVIEW"])
    # camera change: crop right-bottom 70% and zoom back
    crop = base[60:300, 140:600]
    out["large_misalignment"] = case(base, cv2.resize(crop, (W, H), interpolation=cv2.INTER_LINEAR), "NEEDS_REVIEW", [],
                                     "large_misalignment: different crop/zoom (camera moved). Alignment unreliable -> must be NEEDS_REVIEW, never PASS.",
                                     must_not=["PASS"])
    out["small_object_removed"] = case(base, render(seed, remove=("coin",)), "FAIL", [pad(BOXES["coin"], 4)],
                                       "small_object_removed: 12 px coin deleted (rule D1). Hard for patch-14 features; a miss must not become PASS silently.",
                                       forbidden=[pad(BOXES["coin"], 4)])
    out["corrupt_upload"] = case(base, base, "NEEDS_REVIEW", [],
                                 "corrupt_upload: candidate.png is truncated PNG bytes; must be NEEDS_REVIEW (or clean input error), never a crash or PASS.",
                                 must_not=["PASS"])
    out["empty_rules"] = case(base, render(seed, remove=("barrel",)), "NEEDS_REVIEW", [pad(BOXES["barrel"])],
                              "empty_rules: no rules supplied; must not PASS.", rules=[], must_not=["PASS"])
    conflict = [{"id": "A1", "effect": "allow", "description": "Barrels may disappear from the scene."},
                {"id": "D1", "effect": "deny", "description": "Barrels may disappear from the scene."}]
    out["conflicting_rules"] = case(base, render(seed, remove=("barrel",)), "NEEDS_REVIEW", [pad(BOXES["barrel"])],
                                    "conflicting_rules: identical text is both allowed (A1) and denied (D1); must be NEEDS_REVIEW, never PASS.",
                                    rules=conflict, must_not=["PASS"])
    return out


def yaml_rules(rules) -> str:
    if not rules:
        return "rules: []\n"
    lines = ["rules:"]
    for r in rules:
        lines += [f"  - id: {r['id']}", f"    effect: {r['effect']}", f"    description: {json.dumps(r['description'])}"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/fixtures")
    ap.add_argument("--seed", type=int, default=1234)
    a = ap.parse_args()
    root = Path(a.out)
    for name, c in build_cases(a.seed).items():
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        save_png(d / "reference.png", c["ref"])
        save_png(d / "candidate.png", c["cand"])
        if name == "corrupt_upload":
            raw = (d / "candidate.png").read_bytes()
            (d / "candidate.png").write_bytes(raw[: len(raw) // 3])
        (d / "rules.yaml").write_text(yaml_rules(c["rules"]))
        exp = {
            "expected_decision": c["decision"],
            "changed_boxes": c["boxes"],
            "forbidden_boxes": c["forbidden"],
            "synthetic": True,
            "notes": c["notes"] + " SYNTHETIC hand-drawn fixture (seed %d); does not measure benchmark performance." % a.seed,
        }
        exp.update(c["extra"])
        (d / "expected.json").write_text(json.dumps(exp, indent=2) + "\n")
        print("wrote", d)


if __name__ == "__main__":
    main()
