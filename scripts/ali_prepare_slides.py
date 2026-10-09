"""Render three evidence slides from existing artifacts; makes no model calls.

Run: .venv/bin/python scripts/ali_prepare_slides.py
C2 uses the independent, pinned-SHA recomputation in C2_RECOMPUTED.json.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BG = "#101826"
FG = "#f2f5fa"
MUTED = "#b3c1d3"
ACCENT = "#6ee7cf"
WARNING = "#ffc978"
FINAL_SHA = "79a0ef740196cbaa0639579386c6c591d2bfd8ca"


def c2_metrics():
    data = json.loads((ROOT / "docs/ali/C2_RECOMPUTED.json").read_text())
    if data["status"] != "verified_raw" or data["source_integration_sha"] != FINAL_SHA:
        raise ValueError("C2 metrics must be independently verified from the exact frozen SHA")
    return data


def canvas(title: str, subtitle: str):
    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor=BG)
    fig.text(0.05, 0.92, title, color=FG, fontsize=28, weight="bold")
    fig.text(0.05, 0.875, subtitle, color=MUTED, fontsize=15)
    return fig


def text(fig, x, y, value, *, size=16, color=FG):
    fig.text(x, y, value, fontsize=size, color=color, va="top", linespacing=1.45)


def image_panel(fig, box, path):
    ax = fig.add_axes(box)
    with Image.open(path) as img:
        ax.imshow(img)
    ax.set_axis_off()


def baseline_rows():
    with (ROOT / "docs/ali/labels_ali.csv").open(newline="") as stream:
        labels = {r["sample_id"]: r["rule_allowed_or_forbidden (A1/D1)"]
                  for r in csv.DictReader(stream)}
    expected_ids = {r["sample_id"] for r in json.loads(
        (ROOT / "configs/ali_dev12.json").read_text())["dev12"]}
    if set(labels) != expected_ids:
        raise ValueError("Frozen labels and dev12 IDs disagree")
    names = {"A": "A / pixel", "B": "B / full-frame VLM", "C": "C / hybrid"}
    table = []
    for arm in "ABC":
        path = ROOT / f"docs/ali/a1_evidence/predictions_{arm}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        if len(rows) != len(expected_ids) or {r["sample_id"] for r in rows} != expected_ids:
            raise ValueError(f"Missing, duplicate or extra IDs in arm {arm}")
        counts = Counter(r["decision"] for r in rows)
        bug_pass = sum(r["decision"] == "PASS" and labels[r["sample_id"]] == "D1"
                       for r in rows)
        clean_pass = sum(r["decision"] == "PASS" and labels[r["sample_id"]] == "A1"
                         for r in rows)
        n_bug = sum(v == "D1" for v in labels.values())
        n_clean = sum(v == "A1" for v in labels.values())
        table.append([names[arm],
                      f'{counts["PASS"]} / {counts["FAIL"]} / {counts["NEEDS_REVIEW"]}',
                      f'{counts["PASS"] + counts["FAIL"]}/{len(rows)}',
                      f"{bug_pass}/{n_bug}", f"{clean_pass}/{n_clean}"])
    return table


def comparison(out):
    c2 = c2_metrics()
    b, c = c2["arms"]["B"], c2["arms"]["C"]
    fig = canvas("Qwen baseline / development diagnostic",
                 "12 pairs · 5 bug / 7 clean · Qwen 2.5-VL 3B · prompt v9")
    ax = fig.add_axes([0.05, 0.48, 0.9, 0.34])
    ax.set_axis_off()
    table = ax.table(cellText=baseline_rows(),
                     colLabels=["Arm", "PASS / FAIL / REVIEW", "Coverage", "Bug false-PASS", "Clean PASS"],
                     colWidths=[0.24, 0.28, 0.15, 0.19, 0.14], cellLoc="center", bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(17)
    for (row, col), cell in table.get_celld().items():
        cell.set_facecolor("#23334a" if row == 0 else "#172437")
        cell.set_edgecolor("#425671")
        cell.get_text().set_color(ACCENT if row == 3 else FG)
    text(fig, 0.05, 0.44, "Qwen C: 0/5 false-PASS, coverage 0/12 — bütün cütlər REVIEW.", color=ACCENT, size=20)
    text(fig, 0.05, 0.375,
         "C2 / OpenRouter Gemini — raw rows yoxlanıb · SHA 79a0ef7", color=ACCENT, size=19)
    text(fig, 0.05, 0.325,
         f'B və C: {c["PFR"][0]} PASS / {c["PFR"][1]} FAIL / {c["PFR"][2]} REVIEW · '
         f'coverage {c["coverage"]["decided"]}/12 (41.7%) · bug false-PASS 1/5\n'
         f'C: bug FAIL {c["bug_FAIL"]}/5, clean false-FAIL {c["clean_false_FAIL"]["count"]}/7; '
         f'B: bug FAIL {b["bug_FAIL"]}/5, clean false-FAIL {b["clean_false_FAIL"]["count"]}/7. Clean PASS 0/7 hər ikisində.\n'
         "Saylar eyni; iki pair-də qərarlar fərqlidir. DINOv2 üstünlüyü ayrıca sübut edilməyib.", size=16)
    text(fig, 0.05, 0.185,
         "A3 = A1: 36/36 qərar eyni, 80 fresh calls; determinism check, ikinci sample deyil.\n"
         "Labels A1 başladıqdan sonra dondurulub; 4/5 bug label assistant təklifindən Ali təsdiqinə gəlib.\n"
         "Dev12 held-out deyil. Mənbə: a1_evidence/predictions_A,B,C.jsonl; A3_review.md; C2_RECOMPUTED.json.",
         size=14, color=MUTED)
    fig.savefig(out / "01_comparison.png", facecolor=BG)
    plt.close(fig)


def perception(out):
    samples = json.loads((ROOT / "docs/ali/a1_evidence/stage1_qwen_vs_gemini.json").read_text())
    fig = canvas("Eyni crop + prompt / VLM perception",
                 "Gemini 3.5 Flash direct endpoint · əvvəlki n=2 reproducer · C2 batch deyil")
    labels = ["vr_4b921c5d / barrel", "vr_d07179d5 / booth"]
    summaries = [("Qwen: texture və lighting dəyişikliyi", "Gemini: böyük barrel yox olub"),
                 ("Qwen: booth red mirror ilə əvəz edilib", "Gemini: dam və TELEPHONE sign yox olub")]
    for i, (sample, label, summary) in enumerate(zip(samples, labels, summaries)):
        x = 0.05 + i * 0.475
        text(fig, x, 0.82, label, size=20, color=ACCENT)
        image_panel(fig, [x, 0.38, 0.425, 0.39], ROOT / sample["input_image"])
        text(fig, x, 0.34, summary[0], size=16)
        text(fig, x, 0.295, summary[1], size=16, color=ACCENT)
    text(fig, 0.05, 0.2,
         "İki seçilmiş case: daha güclü VLM dəyişikliyi təsvir edir. Bu, accuracy measurement deyil.\n"
         "Qwen A1 observation marks: B y+p 4/12; C 9/12; strict y 1/12 hər ikisində.\n"
         "Bir rater, partial credit, possible anchoring. Mənbə: stage1_qwen_vs_gemini.json; obs_review.csv.",
         size=15, color=MUTED)
    fig.savefig(out / "02_perception.png", facecolor=BG)
    plt.close(fig)


def failure(out):
    c2 = c2_metrics()
    fig = canvas("Əsas failure / missing pedestal",
                 "vr_c1f47c57 · D1 qalır · BEFORE stone pedestal → AFTER floating slab")
    image_panel(fig, [0.05, 0.4, 0.9, 0.4],
                ROOT / "docs/ali/a3_evidence/vr_c1f47c57_pedestal_zoom_ref_vs_cand.png")
    text(fig, 0.15, 0.835, "BEFORE / reference", size=15, color=ACCENT)
    text(fig, 0.59, 0.835, "AFTER / candidate", size=15, color=WARNING)
    text(fig, 0.05, 0.365, "C2 B və C: PASS — yanlış avtomatik təsdiq", color=WARNING, size=25)
    text(fig, 0.05, 0.305,
         f'Raw rows verified · run {c2["arms"]["C"]["run_ids"]["vr_c1f47c57"]} · config {c2["c_config_hash"]}\n'
         "C2 hər arm: bug false-PASS 1/5 · coverage 5/12 (41.7%). Bu PASS uğur nümunəsi deyil.", size=17)
    text(fig, 0.05, 0.215,
         "Yoxlanmış Qwen baseline: B PASS; C REVIEW. C: false-PASS 0/5, coverage 0/12.\n"
         "Şəkil post-freeze audit-də yoxlanıb; frozen label mətni dəyişdirilməyib.\n"
         "Labels A1 başlayandan sonra dondurulub; 4/5 bug label assistant təklifi + Ali təsdiqidir.\n"
         "Mənbə: labels_audit.md; A3_review.md; C2_RECOMPUTED.json (source SHA 79a0ef7).",
         size=15, color=MUTED)
    fig.savefig(out / "03_pedestal_failure.png", facecolor=BG)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "docs/ali/slides")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    comparison(args.out)
    perception(args.out)
    failure(args.out)
    print(f"3 slides rendered at {args.out}; no VLM calls; C2 from verified frozen raw rows")


if __name__ == "__main__":
    main()
