#!/usr/bin/env python
"""A1 scoring (Ali, WP1.1). POST-HOC ONLY: reads predictions + Ali's human labels; never used by inference.

Step 1 (writes obs_review.csv for Ali to mark `obs_correct` = y / n / p(artial), blank = unscored):
  .venv/bin/python scripts/ali_a1_score.py [--a1-dir artifacts/ali/a1] [--labels docs/ali/labels_ali.csv]
Step 2: Ali fills obs_correct; re-run the same command to get score.md / score.json (marks are preserved
across re-runs).

Truth for bug/clean = Ali's own label (rule column D1 = forbidden change = bug; A1 = allowed change = clean),
NOT the benchmark label. Labels must be frozen BEFORE model outputs; a warning is printed if the label file is
newer than the first prediction.

Failure classes (per arm, per case, flags can co-occur; `primary_class` takes the first that applies):
  missing_proposal     (arm C) human bbox exists but no proposal overlaps it (full-frame collapse overlaps, so is not 'missing')
  wrong_perception     obs_correct == n (model's stage-1 observation does not match the human-visible change)
  wrong_rule_mapping   observation OK (y/p) but the final decision is wrong (bug->PASS or clean->FAIL)
  policy_abstention    observation OK (y/p) and final decision NEEDS_REVIEW
  ok                   decision matches truth (bug->FAIL, clean->PASS)
  unscored             obs_correct blank and decision not already correct
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARMS = ("A", "B", "C")
TARGETS = {"obs_correct": 10, "bug_false_pass_max": 0, "clean_pass_min": 4, "coverage_min": 6}
REVIEW_COLS = ["sample_id", "arm", "source", "human_visible_primary_change", "human_rule", "human_bbox", "out_of_scope",
               "human_uncertainty", "model_observation", "model_verdicts", "final_decision", "obs_correct", "obs_note"]


def load_preds(d):
    out = {}
    for arm in ARMS:
        p = d / arm / "predictions.jsonl"
        out[arm] = {}
        if p.exists():
            for l in p.read_text().splitlines():
                if l.strip():
                    r = json.loads(l)
                    out[arm][r["sample_id"]] = r  # later row wins (resume never duplicates; manual edits do)
    return out


def load_labels(path):
    if not path.exists():
        return None
    rows = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["sample_id"]] = r
    return rows


def rule_col(r):
    for k in r:
        if k.startswith("rule_allowed_or_forbidden"):
            return (r[k] or "").strip().upper()
    return ""


def parse_bbox(s):
    n = [int(x) for x in re.findall(r"-?\d+", s or "")]
    return tuple(n[:4]) if len(n) >= 4 else None


def overlaps(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def model_observation(row):
    if row["arm"] == "B":
        a = row.get("audit") or {}
        return a.get("observed_change", "") if a else ""
    if row["arm"] == "C":
        parts = [f"{g['region_id']} {g['box']}: {g['observed_change']}" for g in
                 sorted(row.get("regions") or [], key=lambda g: -(g.get("score") or 0))]
        a = row.get("audit")
        if a:
            parts.append(f"SCENE: {a['observed_change']}")
        return " || ".join(parts)
    return ""


def old_marks(path):
    marks = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("obs_correct") or "").strip() or (r.get("obs_note") or "").strip():
                    marks[(r["sample_id"], r["arm"])] = (r.get("obs_correct", ""), r.get("obs_note", ""))
    return marks


def write_review(path, preds, labels, ids):
    marks = old_marks(path)
    rows = []
    for sid in ids:
        lab = (labels or {}).get(sid, {})
        for arm in ("B", "C"):
            r = preds[arm].get(sid)
            if not r:
                continue
            m = marks.get((sid, arm), ("", ""))
            rows.append({"sample_id": sid, "arm": arm, "source": r.get("media_source"),
                         "human_visible_primary_change": lab.get("visible_primary_change", ""),
                         "human_rule": rule_col(lab) if lab else "", "human_bbox": lab.get("approx_bbox_x1y1x2y2_reference_px", ""),
                         "out_of_scope": lab.get("out_of_scope", ""), "human_uncertainty": lab.get("uncertainty", ""),
                         "model_observation": model_observation(r), "model_verdicts": ",".join(r.get("verdicts") or []),
                         "final_decision": r["decision"], "obs_correct": m[0], "obs_note": m[1]})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=REVIEW_COLS)
        w.writeheader()
        w.writerows(rows)
    return rows


def classify(arm, row, truth, obs, bbox):
    """Return (primary_class, flags)."""
    dec = row["decision"]
    ok = (truth == "bug" and dec == "FAIL") or (truth == "clean" and dec == "PASS")
    flags = []
    if arm == "C" and bbox and row.get("proposals") is not None:
        if not any(overlaps(tuple(p["box"]), bbox) for p in row["proposals"]):
            flags.append("missing_proposal")
    o = (obs or "").strip().lower()
    if o.startswith("n"):
        flags.append("wrong_perception")
    elif o[:1] in ("y", "p"):
        if dec == "NEEDS_REVIEW":
            flags.append("policy_abstention")
        elif not ok:
            flags.append("wrong_rule_mapping")
    if ok:
        return "ok", flags
    if not flags:
        return ("unscored" if not o else "unclassified"), flags
    return flags[0], flags


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a1-dir", default=str(REPO / "artifacts/ali/a1"))
    ap.add_argument("--labels", default=str(REPO / "docs/ali/labels_ali.csv"))
    ap.add_argument("--ids", choices=["balanced6", "dev12", "run"], default="run",
                    help="'run' = ids present in the predictions (default); others restrict to ali_dev12.json lists")
    args = ap.parse_args()
    d = Path(args.a1_dir)
    mock = "MOCK" in d.name.upper()
    preds = load_preds(d)
    labels = load_labels(Path(args.labels))

    ids_json = json.loads((REPO / "configs/ali_dev12.json").read_text())
    six = [r["sample_id"] for r in ids_json["balanced_six"]]
    dev = [r["sample_id"] for r in ids_json["dev12"]]
    order = six + [i for i in dev if i not in six]
    if args.ids == "balanced6":
        order = six
    seen = set().union(*[set(preds[a]) for a in ARMS])
    ids = [i for i in order if i in seen] if args.ids == "run" else order
    ids += sorted(seen - set(ids))

    warnings = []
    if labels is None:
        warnings.append(f"{args.labels} does not exist: bug/clean truth, bbox and observation text are unknown; "
                        "only label-free numbers (coverage, decisions, truncation) are reported.")
    else:
        starts = [r["started_at"] for a in ARMS for r in preds[a].values() if r.get("started_at")]
        lp = Path(args.labels)
        from datetime import datetime, timezone
        lt = datetime.fromtimestamp(lp.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
        if starts and lt > min(starts):
            warnings.append(f"label file mtime {lt} is NEWER than the first prediction {min(starts)}: labels may not have been frozen before outputs.")
        missing_lab = [i for i in ids if i not in labels or not rule_col(labels[i])]
        if missing_lab:
            warnings.append(f"no usable human rule label (A1/D1) for: {missing_lab}")

    review = write_review(d / "obs_review.csv", preds, labels, ids)
    marks = {(r["sample_id"], r["arm"]): r["obs_correct"] for r in review}

    result = {"a1_dir": str(d), "mock": mock, "n_ids": len(ids), "ids": ids, "warnings": warnings, "targets": TARGETS,
              "labels_sha256": hashlib.sha256(Path(args.labels).read_bytes()).hexdigest()[:16] if labels is not None else None,
              "arms": {}}
    for arm in ARMS:
        P = preds[arm]
        miss = [i for i in ids if i not in P]
        n = len(P)
        dec = Counter(r["decision"] for r in P.values())
        cases, bug_fp, clean_pass, n_bug, n_clean, obs_y, obs_scored = [], 0, 0, 0, 0, 0, 0
        trunc = Counter((r.get("truncation_cause") or "none") for r in P.values()) if arm != "A" else None
        for sid in ids:
            r = P.get(sid)
            if not r:
                continue
            lab = (labels or {}).get(sid)
            rc = rule_col(lab) if lab else ""
            truth = "bug" if rc == "D1" else "clean" if rc == "A1" else None
            if truth == "bug":
                n_bug += 1
                bug_fp += r["decision"] == "PASS"
            elif truth == "clean":
                n_clean += 1
                clean_pass += r["decision"] == "PASS"
            obs = marks.get((sid, arm), "")
            if arm != "A" and obs.strip():
                obs_scored += 1
                obs_y += obs.strip().lower()[:1] in ("y",)
            bbox = parse_bbox(lab.get("approx_bbox_x1y1x2y2_reference_px")) if lab else None
            cls, flags = classify(arm, r, truth, obs, bbox) if truth else ("no_truth", [])
            cases.append({"sample_id": sid, "truth": truth, "decision": r["decision"], "class": cls, "flags": flags,
                          "obs_correct": obs or None, "truncation_cause": r.get("truncation_cause"),
                          "out_of_scope": (lab or {}).get("out_of_scope"), "error": r.get("error"),
                          "cache": (r.get("cache") or {}).get("status")})
        covered = n - dec.get("NEEDS_REVIEW", 0)
        result["arms"][arm] = {
            "rows": n, "missing_ids": miss, "decisions": dict(dec), "coverage": f"{covered}/{n}",
            "obs_correct": None if arm == "A" else f"{obs_y}/{obs_scored} marked 'y' of {n} rows ({obs_scored} marked)",
            "bug_false_pass": f"{bug_fp}/{n_bug}" if labels else "unknown (no labels)",
            "clean_pass": f"{clean_pass}/{n_clean}" if labels else "unknown (no labels)",
            "truncation_causes": dict(trunc) if trunc is not None else None,
            "class_counts": dict(Counter(c["class"] for c in cases)),
            "flag_counts": dict(Counter(f for c in cases for f in c["flags"])),
            "n_errors": sum(1 for r in P.values() if r.get("error")), "cases": cases,
            "target_check": {
                "n_is_12": n == 12,
                "obs_correct_ge_10": (arm != "A") and obs_y >= TARGETS["obs_correct"] if n == 12 else None,
                "bug_false_pass_eq_0": (bug_fp == 0) if labels and n_bug else None,
                "clean_pass_ge_4": (clean_pass >= TARGETS["clean_pass_min"]) if labels and n_clean else None,
                "coverage_ge_6": covered >= TARGETS["coverage_min"] if n == 12 else None,
            }}

    (d / "score.json").write_text(json.dumps(result, indent=2))
    L = [f"# A1 score ({'MOCK - NOT REAL INFERENCE' if mock else 'real'})", ""]
    L += [f"WARNING: {w}" for w in warnings] + [""] if warnings else []
    L += ["Targets (engineering targets, not promised results): 10/12 correct primary observations; 0/6 bug false-PASS; >=4/6 clean PASS; coverage >=6/12.",
          "Target flags are only evaluated for n=12 (observations, coverage); at n=6 compare counts by hand. `unknown` = not computable yet.", "",
          "| arm | rows | PASS/FAIL/REVIEW | coverage | obs correct | bug false-PASS | clean PASS | truncation causes | classes |", "|---|---|---|---|---|---|---|---|---|"]
    for arm in ARMS:
        a = result["arms"][arm]
        dd = a["decisions"]
        L.append(f"| {arm} | {a['rows']} | {dd.get('PASS',0)}/{dd.get('FAIL',0)}/{dd.get('NEEDS_REVIEW',0)} | {a['coverage']} | {a['obs_correct']} | "
                 f"{a['bug_false_pass']} | {a['clean_pass']} | {a['truncation_causes']} | {a['class_counts']} |")
    for arm in ARMS:
        L += ["", f"## Arm {arm} cases", "", "| sample | truth | decision | class | flags | obs | truncation | OOS | cache | error |", "|---|---|---|---|---|---|---|---|---|---|"]
        for c in result["arms"][arm]["cases"]:
            L.append(f"| {c['sample_id']} | {c['truth']} | {c['decision']} | {c['class']} | {','.join(c['flags'])} | {c['obs_correct']} | "
                     f"{c['truncation_cause']} | {c['out_of_scope']} | {c['cache']} | {c['error']} |")
        if result["arms"][arm]["missing_ids"]:
            L.append(f"\nMissing ids (not run): {result['arms'][arm]['missing_ids']}")
    (d / "score.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nobs_review.csv: {d / 'obs_review.csv'}  ({sum(1 for r in review if not r['obs_correct'].strip())} of {len(review)} rows still unmarked)")


if __name__ == "__main__":
    sys.exit(main())
