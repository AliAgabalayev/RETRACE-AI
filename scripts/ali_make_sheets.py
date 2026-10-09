"""Contact sheets (before | after | abs-diff) and an empty labeling CSV for Ali. Fills no labels."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "ali"
SHEET_W = 1600
HEADER_H = 150

COLUMNS = [
    "sample_id", "source", "contact_sheet", "reference_size_wh", "visible_primary_change",
    "valid_comparison_conditions", "source_scene", "rule_allowed_or_forbidden (A1/D1)",
    "approx_bbox_x1y1x2y2_reference_px", "uncertainty", "out_of_scope", "notes",
]


def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])


def make_sheet(sample: dict, dst: Path) -> None:
    ref = Image.open(REPO / sample["images"]["reference"]["bundle_path"]).convert("RGB")
    cand = Image.open(REPO / sample["images"]["candidate"]["bundle_path"]).convert("RGB")
    pw = SHEET_W // 3
    ph = round(ref.height * pw / ref.width)
    ref_s = ref.resize((pw, ph), Image.LANCZOS)
    cand_s = cand.resize((pw, ph), Image.LANCZOS)
    diff = np.abs(np.asarray(ref_s, dtype=np.int16) - np.asarray(cand_s, dtype=np.int16)).astype(np.uint8)
    diff_img = Image.fromarray(diff)
    sheet = Image.new("RGB", (pw * 3, HEADER_H + ph), "white")
    for i, im in enumerate((ref_s, cand_s, diff_img)):
        sheet.paste(im, (i * pw, HEADER_H))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    rules = " | ".join(f"{r['id']} ({r['effect']}): " + " ".join(r["description"].split()) for r in sample["rules"])
    head = [f"{sample['sample_id']}  source={sample['source']}  reference={ref.width}x{ref.height}"]
    head += _wrap(rules, 260)[:9]
    d.multiline_text((6, 4), "\n".join(head), fill="black", font=font)
    for i, name in enumerate(("before (reference)", "after (candidate)", "abs-diff")):
        d.text((i * pw + 6, HEADER_H - 14), name, fill="black", font=font)
    sheet.save(dst)


def main() -> int:
    inv = json.loads((REPO / "artifacts/ali/inventory.json").read_text())["samples"]
    cfg = json.loads((REPO / "configs/ali_dev12.json").read_text())
    by_id = {s["sample_id"]: s for s in inv}
    six = [r["sample_id"] for r in cfg["balanced_six"]]
    order = six + [r["sample_id"] for r in cfg["dev12"] if r["sample_id"] not in six]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for sid in order:
        s = by_id[sid]
        name = f"contact_sheet_{sid}.png"
        make_sheet(s, OUT / name)
        ref = s["images"]["reference"]
        rows.append({"sample_id": sid, "source": s["source"], "contact_sheet": f"docs/ali/{name}",
                     "reference_size_wh": f"{ref['width']}x{ref['height']}"})
    with (OUT / "labeling_sheet.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    print(f"wrote {len(rows)} contact sheets + labeling_sheet.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
