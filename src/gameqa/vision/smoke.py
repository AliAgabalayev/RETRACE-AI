"""DL smoke runner: real DINOv2 (+ optional real VLM) on image pairs; saves heatmap/overlay/crops/raw replies.

  python -m gameqa.vision.smoke --pairs data/fixtures/object_removed [...] [--vlm] [--out artifacts/dl_smoke]
  python -m gameqa.vision.smoke --manifest-split dev --limit 3 --vlm
A pair dir needs reference.png, candidate.png and (for --vlm) rules.yaml. Labels are never read here.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np
import yaml

from gameqa.contracts import Rule
from gameqa.vision import alignment, proposals
from gameqa.vision.features import FeatureExtractor
from gameqa.vision.judge import Judge


def _rd(p):
    return cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)


def _wr(p, img):
    cv2.imwrite(str(p), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def run_pair(name, ref, cand, rules, cfg, fx, judge, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    rec = {"name": name, "size": [ref.shape[1], ref.shape[0]]}
    t = time.time(); res, al, mask = alignment.align(ref, cand, cfg); rec["t_align"] = time.time() - t
    rec["alignment"] = res.status.value; rec["align_diag"] = res.diagnostics
    dm = None
    if fx is not None:
        t = time.time(); dm = fx.distance_map(ref, al); rec["t_dino"] = time.time() - t
        rec["dino_max"] = float(dm.max()); rec["dino_p99"] = float(np.percentile(dm, 99))
        hm = cv2.applyColorMap(np.clip(dm / max(0.6, dm.max()) * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
        _wr(out / "heatmap.png", cv2.cvtColor(cv2.addWeighted(cv2.cvtColor(ref, cv2.COLOR_RGB2BGR), 0.5, hm, 0.5, 0), cv2.COLOR_BGR2RGB))
    t = time.time(); props, cov = proposals.propose(ref, al, mask, dm, cfg); rec["t_propose"] = time.time() - t
    rec["proposals"] = [p.model_dump(mode="json") for p in props]; rec["coverage"] = cov.model_dump()
    ov = ref.copy()
    for p in props:
        x1, y1, x2, y2 = p.box
        cv2.rectangle(ov, (x1, y1), (x2 - 1, y2 - 1), (255, 0, 0), 2)
        cv2.putText(ov, f"{p.id} {p.source} {p.score:.1f}", (x1 + 2, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    _wr(out / "boxes_overlay.png", ov)
    if judge is not None and rules is not None:
        (out / "crops").mkdir(exist_ok=True)
        rec["judgments"] = []; tj = time.time(); calls = 0
        for p in props:
            x1, y1, x2, y2 = p.box
            rc, cc = ref[y1:y2, x1:x2], al[y1:y2, x1:x2]
            _wr(out / "crops" / f"{p.id}_ref.png", rc); _wr(out / "crops" / f"{p.id}_cand.png", cc)
            j = judge.judge_region(p, rc, cc, ref, al, rules); calls += 1
            rec["judgments"].append(j.model_dump(mode="json"))
        a = judge.audit_scene(ref, al, rules, props); calls += 1
        rec["audit"] = a.model_dump(mode="json"); rec["t_vlm"] = time.time() - tj; rec["vlm_calls"] = calls
    (out / "result.json").write_text(json.dumps(rec, indent=1, default=str))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", default=[])
    ap.add_argument("--manifest-split", default=None)
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--total", type=int, default=10)  # size of the evenly spaced selection
    ap.add_argument("--start", type=int, default=0)  # skip first N of the selected list (chunked runs)
    ap.add_argument("--vlm", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--no-dino", action="store_true")
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--out", default="artifacts/dl_smoke")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    if a.no_cache:
        cfg["vlm"]["cache"] = False
    # Warm Ollama FIRST: its memory check fails if torch/CUDA already took RAM (CPU-resident 3B VLM needs ~9.7 GiB).
    judge = Judge(cfg) if a.vlm else None
    if judge: print("warmup", judge.warmup())
    fx = None if a.no_dino else FeatureExtractor(cfg)
    items = []
    for d in a.pairs:
        d = Path(d); rules = None
        if (d / "rules.yaml").exists():
            rules = [Rule(**r) for r in yaml.safe_load(open(d / "rules.yaml"))["rules"]]
        items.append((d.name, _rd(d / "reference.png"), _rd(d / "candidate.png"), rules))
    if a.manifest_split:
        man = json.load(open("data/manifests/inference_manifest.json"))
        sel = [m for m in man if m.get("split") == a.manifest_split]
        sel = sel[:: max(1, len(sel) // a.total)][a.start:][: a.limit]  # evenly spaced -> mixed labels without reading them
        for m in sel:
            items.append((m["sample_id"], _rd(m["reference_path"]), _rd(m["candidate_path"]), [Rule(**r) for r in m["rules"]]))
    allrec = []
    for name, r, c, rules in items:
        rec = run_pair(name, r, c, rules, cfg, fx, judge, Path(a.out) / name)
        allrec.append(rec)
        print(name, rec["alignment"], f"dino={rec.get('t_dino', 0):.2f}s vlm={rec.get('t_vlm', 0):.1f}s",
              [(p["id"], p["box"], p["source"], round(p["score"], 1)) for p in rec["proposals"]],
              [(j["region_id"], j["verdict"], j["rule_ids"], j["validated"]) for j in rec.get("judgments", [])],
              (rec.get("audit") or {}).get("judgment", {}).get("verdict"))
    if fx:
        meta = {"feature_model": fx.version, "device": fx.device, "dtype": fx.dtype, "backend": fx.backend}
        print(meta)


if __name__ == "__main__":
    main()
