#!/usr/bin/env python
"""Held-out evaluation, two strictly separated phases. Owner: qa-engineer.

  predict  : run a method over manifest IDs using ONLY data/manifests/inference_manifest.json
             (this phase never opens eval_labels.json).
  tune-classical : choose the classical baseline's threshold on the DEV split only (uses dev labels).
  score    : join predictions with data/manifests/eval_labels.json and compute metrics.

Methods: pipeline (gameqa.pipeline.analyze, real config), classical (pixel-diff baseline),
         vlm_only (one whole-pair Judge.audit_scene call, no proposals).

Examples:
  .venv/bin/python scripts/evaluate.py tune-classical
  .venv/bin/python scripts/evaluate.py predict --method classical --split eval
  .venv/bin/python scripts/evaluate.py predict --method pipeline --split eval --limit 5
  .venv/bin/python scripts/evaluate.py predict --method pipeline --ids-file data/manifests/eval_subset_60.json \
        --out artifacts/eval/pipeline_x      # re-run same --out to resume
  .venv/bin/python scripts/evaluate.py score --run artifacts/eval/<dir>
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

DECISIONS = ("PASS", "FAIL", "NEEDS_REVIEW")
THRESH_FILE = REPO / "artifacts" / "eval" / "classical_threshold.json"
CLASSICAL_PIXEL_THR = 25  # gray absdiff level counted as "changed pixel" (fixed, not tuned)


def _load_manifest(path=None):
    from gameqa.data.manifest import load_inference_manifest

    return load_inference_manifest(path)  # raises if label keys leaked


def select_records(manifest, split, ids_file, limit):
    recs = manifest
    if ids_file:
        ids = json.loads(Path(ids_file).read_text())
        if isinstance(ids, dict):
            ids = ids.get("ids") or ids.get("sample_ids") or sys.exit("ids-file dict needs 'ids' or 'sample_ids'")
        order = {i: n for n, i in enumerate(ids)}
        recs = sorted((r for r in recs if r["sample_id"] in order), key=lambda r: order[r["sample_id"]])
        missing = set(order) - {r["sample_id"] for r in recs}
        if missing:
            sys.exit(f"ids-file contains {len(missing)} ids absent from the manifest: {sorted(missing)[:5]} (refusing to silently drop)")
            print(f"WARNING: {len(missing)} ids from {ids_file} not in manifest: {sorted(missing)[:5]}", file=sys.stderr)
    elif split:
        recs = [r for r in recs if r.get("split") == split]
    if limit:
        recs = recs[:limit]
    return recs


# ----------------------------------------------------------------------------- methods
def _load_rgb(path):
    import cv2

    img = cv2.imread(str(REPO / path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"cannot decode {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def classical_fraction(ref_path, cand_path) -> float:
    import cv2

    a, b = _load_rgb(ref_path), _load_rgb(cand_path)
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    g1 = cv2.GaussianBlur(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
    g2 = cv2.GaussianBlur(cv2.cvtColor(b, cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
    return float((cv2.absdiff(g1, g2) > CLASSICAL_PIXEL_THR).mean())


def predict_classical(rec, ctx):
    frac = classical_fraction(rec["reference_path"], rec["candidate_path"])
    return {"decision": "FAIL" if frac > ctx["threshold"] else "PASS", "n_regions": 0,
            "changed_fraction": round(frac, 6)}


def predict_pipeline(rec, ctx):
    from gameqa.contracts import PairInput, Rule

    pair = PairInput(reference_path=str(REPO / rec["reference_path"]), candidate_path=str(REPO / rec["candidate_path"]),
                     rules=[Rule(**r) for r in rec["rules"]], sample_id=rec["sample_id"])
    res = ctx["analyze"](pair, ctx["cfg"], judge=ctx["judge"], extractor=ctx["extractor"])
    ctx["versions"].update({k: v for k, v in res.versions.model_dump().items() if v})
    return {"decision": res.final_decision.value, "n_regions": len(res.proposals), "run_id": res.run_id,
            "engine_mode": res.engine_mode, "execution_status": res.execution_status.value,
            "truncated": res.coverage.truncated, "pipeline_errors": res.errors[:3]}


def predict_vlm_only(rec, ctx):
    import cv2

    from gameqa.contracts import (AlignmentResult, AlignmentStatus, Coverage, Rule)
    from gameqa.decision import DecisionInput, decide

    rules = [Rule(**r) for r in rec["rules"]]
    a, b = _load_rgb(rec["reference_path"]), _load_rgb(rec["candidate_path"])
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    audit = ctx["judge"].audit_scene(a, b, rules, [])
    align = AlignmentResult(status=AlignmentStatus.IDENTITY, candidate_to_reference=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                            overlap_fraction=1.0)
    dec, reason = decide(DecisionInput(rules, [], audit, Coverage(scene_audit_ran=True), align))
    return {"decision": dec.value, "n_regions": 0, "reason": reason, "audit_errors": audit.judgment.errors[:2],
            "engine_mode": "mock" if audit.judgment.is_mock else "real"}


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        return None


def build_ctx(method, args):
    ctx = {"threshold": None, "versions": {}}
    if method == "classical":
        if args.threshold is not None:
            ctx["threshold"], ctx["threshold_source"] = args.threshold, "cli"
        elif THRESH_FILE.exists():
            t = json.loads(THRESH_FILE.read_text())
            ctx["threshold"], ctx["threshold_source"] = t["threshold"], f"{THRESH_FILE.relative_to(REPO)} (dev only)"
        else:
            sys.exit("classical needs --threshold or a prior `tune-classical` run")
    else:
        from gameqa.config import config_hash, load_config

        cfg = load_config(args.config, overrides=None)
        ctx["cfg"] = cfg
        ctx["config_hash"] = config_hash(cfg)
        if method == "pipeline":
            from gameqa.pipeline import analyze, build_extractor, build_judge

            ctx.update(analyze=analyze, judge=build_judge(cfg), extractor=build_extractor(cfg))
        else:
            from gameqa.pipeline import build_judge

            ctx["judge"] = build_judge(cfg)
        ctx["versions"]["vlm_model"] = getattr(ctx["judge"], "model_id", None)
        ctx["versions"]["prompt_version"] = getattr(ctx["judge"], "prompt_version", None)
        if ctx["judge"].is_mock:
            print("WARNING: mock judge in use; predictions are NOT real inference and are labelled mock", file=sys.stderr)
    return ctx


# ----------------------------------------------------------------------------- phases
def cmd_predict(args):
    manifest = _load_manifest()
    recs = select_records(manifest, args.split, args.ids_file, args.limit)
    if not recs:
        sys.exit("no records selected")
    out = Path(args.out) if args.out else REPO / "artifacts" / "eval" / f"{args.method}_{args.split or 'ids'}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    out.mkdir(parents=True, exist_ok=True)
    pred_path = out / "predictions.jsonl"
    done = set()
    if pred_path.exists():
        done = {json.loads(l)["sample_id"] for l in pred_path.read_text().splitlines() if l.strip()}
    ctx = build_ctx(args.method, args)
    fn = {"classical": predict_classical, "pipeline": predict_pipeline, "vlm_only": predict_vlm_only}[args.method]
    meta_path = out / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    old_meta = dict(meta)
    meta.update({
        "method": args.method, "split": args.split, "ids_file": args.ids_file, "limit": args.limit,
        "commit": git_commit(), "config_hash": ctx.get("config_hash"), "threshold": ctx.get("threshold"),
        "threshold_source": ctx.get("threshold_source"), "expected_ids": [r["sample_id"] for r in recs],
        "dataset_revision": recs[0].get("dataset_revision"),
        "argv": sys.argv, "started_at": meta.get("started_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "resumed": bool(done),
    })
    if done and old_meta:
        for k, new in (("method", args.method), ("config_hash", ctx.get("config_hash")),
                       ("expected_ids", [r["sample_id"] for r in recs]), ("threshold", ctx.get("threshold"))):
            if old_meta.get(k) != new:
                sys.exit(f"REFUSING to resume {out}: stored {k} differs from this invocation")
    todo = [r for r in recs if r["sample_id"] not in done]
    print(f"{len(recs)} selected, {len(done)} already predicted, {len(todo)} to run -> {out}")
    with pred_path.open("a") as fh:
        for i, rec in enumerate(todo, 1):
            t = time.perf_counter()
            row = {"sample_id": rec["sample_id"], "method": args.method, "media_source": rec.get("media_source"),
                   "error": None}
            try:
                row.update(fn(rec, ctx))
            except Exception as exc:  # noqa: BLE001 - error is a recorded review, never dropped
                row.update(decision="NEEDS_REVIEW", n_regions=0, error=f"{type(exc).__name__}: {exc}")
            row["seconds"] = round(time.perf_counter() - t, 3)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(f"[{i}/{len(todo)}] {rec['sample_id']} {row['decision']} {row['seconds']}s" + (f" ERROR {row['error']}" if row["error"] else ""))
    meta.update(versions=ctx["versions"], finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    meta_path.write_text(json.dumps(meta, indent=2))
    print("predictions:", pred_path)


def balanced(rb, rn):
    return None if rb is None or rn is None else (rb + rn) / 2


def cmd_tune(args):
    """Choose classical T on the DEV split only. This is the only place labels are read before `score`."""
    from gameqa.data.manifest import load_eval_labels

    manifest = _load_manifest()
    labels = load_eval_labels()
    dev = [r for r in manifest if labels.get(r["sample_id"], {}).get("split") == "dev" and labels[r["sample_id"]].get("label") in ("bug", "no_bug")]
    rows = [(classical_fraction(r["reference_path"], r["candidate_path"]), labels[r["sample_id"]]["label"] == "bug", r["sample_id"]) for r in dev]
    if not rows:
        sys.exit("no labelled dev rows")
    nb, nn = sum(b for _, b, _ in rows), sum(not b for _, b, _ in rows)
    if nb == 0 or nn == 0:
        THRESH_FILE.unlink(missing_ok=True)
        sys.exit(f"REFUSING to tune: dev split has {nb} bug / {nn} no_bug; both classes are required. "
                 "Pass --threshold explicitly (and record why) or wait for the full dev split.")
    fr = sorted(f for f, _, _ in rows)
    cands = [0.0] + [(a + b) / 2 for a, b in zip(fr, fr[1:])] + [fr[-1] + 1e-6]
    best, scored = None, []
    for t in cands:
        rb = sum(b and f > t for f, b, _ in rows) / nb if nb else None
        rn = sum((not b) and f <= t for f, b, _ in rows) / nn if nn else None
        sc = balanced(rb, rn)
        if sc is None:  # one class missing: fall back to the available class recall
            sc = rb if rb is not None else rn
        scored.append((sc, t))
    top = max(s for s, _ in scored)
    ties = sorted(t for s, t in scored if s == top)
    thr = ties[len(ties) // 2]
    rec = {"threshold": thr, "criterion": "balanced accuracy on dev (median of ties)", "pixel_thr": CLASSICAL_PIXEL_THR,
           "dev_n": len(rows), "dev_bug": nb, "dev_no_bug": nn, "dev_balanced_accuracy": top, "dev_ids": [i for *_, i in rows],
           "warning": "dev split is tiny / single-class: threshold is weakly determined" if min(nb, nn) < 5 else None,
           "tuned_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    THRESH_FILE.parent.mkdir(parents=True, exist_ok=True)
    THRESH_FILE.write_text(json.dumps(rec, indent=2))
    print(json.dumps({k: v for k, v in rec.items() if k != "dev_ids"}, indent=2))


# ----------------------------------------------------------------------------- scoring
def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def _r(x, nd=4):
    return None if x is None else round(x, nd)


def metrics_for(rows):
    """rows: list of (truth in {'bug','no_bug'}, decision). Returns metric dict; denominators are explicit."""
    cm = {t: {d: 0 for d in DECISIONS} for t in ("bug", "no_bug")}
    for t, d in rows:
        cm[t][d] += 1
    nb, nn = sum(cm["bug"].values()), sum(cm["no_bug"].values())
    n = nb + nn
    rev = cm["bug"]["NEEDS_REVIEW"] + cm["no_bug"]["NEEDS_REVIEW"]
    decided = n - rev
    correct = cm["bug"]["FAIL"] + cm["no_bug"]["PASS"]

    def div(a, b):
        return a / b if b else None

    def mapping(flag_decisions, exclude_review=False):
        tp = sum(cm["bug"][d] for d in flag_decisions)
        fp = sum(cm["no_bug"][d] for d in flag_decisions)
        fn_bug = nb - tp
        tn = nn - fp
        if exclude_review:
            fn_bug -= cm["bug"]["NEEDS_REVIEW"]
            tn -= cm["no_bug"]["NEEDS_REVIEW"]
        rb, rn = div(tp, tp + fn_bug), div(tn, tn + fp)
        return {"positive_means": "+".join(flag_decisions), "excluded_review": (rev if exclude_review else 0),
                "tp": tp, "fp": fp, "fn": fn_bug, "tn": tn, "bug_precision": _r(div(tp, tp + fp)), "bug_recall": _r(rb),
                "no_bug_recall": _r(rn), "balanced_accuracy": _r(balanced(rb, rn)), "bug_recall_ci": wilson(tp, tp + fn_bug),
                "no_bug_recall_ci": wilson(tn, tn + fp)}

    return {
        "n": n, "n_bug": nb, "n_no_bug": nn, "confusion_matrix": cm,
        "review_rate": _r(div(rev, n)), "review_rate_ci": wilson(rev, n), "decision_coverage": _r(div(decided, n)),
        "decided_n": decided, "decided_pair_accuracy": _r(div(correct, decided)),
        "decided_pair_accuracy_ci": wilson(correct, decided),
        "review_to_fail": mapping(("FAIL", "NEEDS_REVIEW")), "review_to_pass": mapping(("FAIL",)),
        "review_excluded": mapping(("FAIL",), exclude_review=True),
    }


def reference_rows(truths):
    out = {}
    for name, d in (("always_FAIL", "FAIL"), ("always_PASS", "PASS"), ("always_NEEDS_REVIEW", "NEEDS_REVIEW")):
        m = metrics_for([(t, d) for t in truths])
        out[name] = {"balanced_accuracy_review_to_fail": m["review_to_fail"]["balanced_accuracy"],
                     "balanced_accuracy_review_to_pass": m["review_to_pass"]["balanced_accuracy"],
                     "bug_recall_review_to_fail": m["review_to_fail"]["bug_recall"]}
    return out


def bootstrap_ci(rows, n_boot=2000, seed=0):
    """Stratified percentile bootstrap CI of primary metric (balanced acc, review->FAIL)."""
    rng = random.Random(seed)
    bug = [d for t, d in rows if t == "bug"]
    nob = [d for t, d in rows if t == "no_bug"]
    if not bug or not nob:
        return [None, None]
    vals = []
    for _ in range(n_boot):
        b = [rng.choice(bug) for _ in bug]
        n = [rng.choice(nob) for _ in nob]
        vals.append((sum(d != "PASS" for d in b) / len(b) + sum(d == "PASS" for d in n) / len(n)) / 2)
    vals.sort()
    return [round(vals[int(0.025 * n_boot)], 4), round(vals[int(0.975 * n_boot) - 1], 4)]


def cmd_score(args):
    from gameqa.data.manifest import load_eval_labels

    run = Path(args.run)
    preds = [json.loads(l) for l in (run / "predictions.jsonl").read_text().splitlines() if l.strip()]
    meta = json.loads((run / "run_meta.json").read_text()) if (run / "run_meta.json").exists() else {}
    labels = load_eval_labels()
    expected = meta.get("expected_ids") or [p["sample_id"] for p in preds]
    pmap = {p["sample_id"]: p for p in preds}
    rows, excluded, per_source = [], [], defaultdict(list)
    dist = Counter()
    for sid in expected:
        lab = labels.get(sid)
        if sid not in pmap:
            excluded.append({"sample_id": sid, "reason": "no prediction (run incomplete)"})
        elif lab is None or lab.get("label") not in ("bug", "no_bug"):
            excluded.append({"sample_id": sid, "reason": "no usable ground-truth label"})
        else:
            dist[lab["label"]] += 1
            rows.append((lab["label"], pmap[sid]["decision"]))
            per_source[pmap[sid].get("media_source") or "unknown"].append((lab["label"], pmap[sid]["decision"]))
    scored_ids = {sid for sid in expected if sid in pmap and labels.get(sid, {}).get("label") in ("bug", "no_bug")}
    unexpected = sorted(set(pmap) - set(expected))
    sp = [p for p in preds if p["sample_id"] in scored_ids]
    errors = [p["sample_id"] for p in sp if p.get("error")]
    secs = [p["seconds"] for p in sp if p.get("seconds") is not None]
    out = {
        "method": meta.get("method"), "run_dir": str(run), "split": meta.get("split"), "ids_file": meta.get("ids_file"),
        "expected_ids": len(expected), "scored": len(rows), "excluded_count": len(excluded), "excluded": excluded,
        "unexpected_prediction_ids": unexpected, "error_count": len(errors), "error_ids": errors, "label_distribution": dict(dist),
        "decision_distribution": dict(Counter(d for _, d in rows)),
        "primary_metric": "balanced accuracy, review->FAIL", "primary_value": None,
        "overall": metrics_for(rows), "primary_bootstrap_ci95": bootstrap_ci(rows),
        "reference_rows": reference_rows([t for t, _ in rows]),
        "per_media_source": {s: metrics_for(r) for s, r in sorted(per_source.items())},
        "latency_s": {"mean": _r(statistics.mean(secs), 3) if secs else None, "median": _r(statistics.median(secs), 3) if secs else None,
                      "p90": _r(sorted(secs)[int(0.9 * (len(secs) - 1))], 3) if secs else None, "max": max(secs) if secs else None},
        "mean_regions_per_pair": _r(statistics.mean(p.get("n_regions", 0) for p in sp), 2) if sp else None,
        "engine_modes": dict(Counter(p.get("engine_mode", "n/a") for p in sp)),
        "run_meta": {k: meta.get(k) for k in ("commit", "config_hash", "threshold", "versions", "dataset_revision")},
    }
    out["primary_value"] = out["overall"]["review_to_fail"]["balanced_accuracy"]
    if "mock" in out["engine_modes"]:
        out["WARNING"] = "contains MOCK predictions; not real inference; exclude from registry"
    (run / "metrics.json").write_text(json.dumps(out, indent=2))
    (run / "metrics.md").write_text(render_md(out))
    print((run / "metrics.md").read_text())


def render_md(m):
    o = m["overall"]
    L = [f"# Evaluation: {m['method']} ({m.get('split') or m.get('ids_file')})", ""]
    if m.get("WARNING"):
        L += [f"**{m['WARNING']}**", ""]
    L += [f"- Expected IDs: {m['expected_ids']}; scored: {m['scored']}; excluded: {m['excluded_count']}; errors (counted as NEEDS_REVIEW): {m['error_count']}",
          f"- Label distribution: {m['label_distribution']}; decisions: {m['decision_distribution']}",
          f"- **Primary ({m['primary_metric']}): {m['primary_value']}**, bootstrap 95% CI {m['primary_bootstrap_ci95']}",
          f"- Review rate {o['review_rate']} (CI {o['review_rate_ci']}); decision coverage {o['decision_coverage']} ({o['decided_n']}/{o['n']}); decided-pair accuracy {o['decided_pair_accuracy']} (CI {o['decided_pair_accuracy_ci']})",
          f"- Latency s: {m['latency_s']}; mean regions/pair {m['mean_regions_per_pair']}; engine modes {m['engine_modes']}", "",
          "## Confusion matrix (truth x decision)", "", "| truth | PASS | FAIL | NEEDS_REVIEW |", "|---|---|---|---|"]
    for t in ("bug", "no_bug"):
        c = o["confusion_matrix"][t]
        L.append(f"| {t} | {c['PASS']} | {c['FAIL']} | {c['NEEDS_REVIEW']} |")
    L += ["", "## Review mappings", "", "| mapping | bug precision | bug recall | no_bug recall | balanced acc | excluded |", "|---|---|---|---|---|---|"]
    for k in ("review_to_fail", "review_to_pass", "review_excluded"):
        x = o[k]
        L.append(f"| {k} (positive={x['positive_means']}) | {x['bug_precision']} | {x['bug_recall']} | {x['no_bug_recall']} | {x['balanced_accuracy']} | {x['excluded_review']} |")
    L += ["", "## Reference rows (same IDs)", "", "| row | BA review->FAIL | BA review->PASS | bug recall (flag) |", "|---|---|---|---|"]
    for k, v in m["reference_rows"].items():
        L.append(f"| {k} | {v['balanced_accuracy_review_to_fail']} | {v['balanced_accuracy_review_to_pass']} | {v['bug_recall_review_to_fail']} |")
    L += ["", "## Per media_source", "", "| source | n | bug/no_bug | confusion (bug: P/F/R ; no_bug: P/F/R) | BA flag |", "|---|---|---|---|---|"]
    for s, x in m["per_media_source"].items():
        b, n = x["confusion_matrix"]["bug"], x["confusion_matrix"]["no_bug"]
        L.append(f"| {s} | {x['n']} | {x['n_bug']}/{x['n_no_bug']} | {b['PASS']}/{b['FAIL']}/{b['NEEDS_REVIEW']} ; {n['PASS']}/{n['FAIL']}/{n['NEEDS_REVIEW']} | {x['review_to_fail']['balanced_accuracy']} |")
    if m["excluded"]:
        L += ["", "## Excluded", ""] + [f"- {e['sample_id']}: {e['reason']}" for e in m["excluded"]]
    L += ["", "Pair-level labels only: no localization IoU is computed. Wilson CIs on proportions; tiny N means wide uncertainty."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--method", required=True, choices=["pipeline", "classical", "vlm_only"])
    p.add_argument("--split", default=None, help="demo|dev|eval (from the inference manifest's split column)")
    p.add_argument("--ids-file", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--out", default=None, help="run dir; re-use to resume")
    p.add_argument("--threshold", type=float, default=None)
    p.add_argument("--config", default=None)
    p.set_defaults(fn=cmd_predict)
    t = sub.add_parser("tune-classical")
    t.set_defaults(fn=cmd_tune)
    s = sub.add_parser("score")
    s.add_argument("--run", required=True)
    s.set_defaults(fn=cmd_score)
    a = ap.parse_args()
    if a.cmd == "predict" and not (a.split or a.ids_file):
        ap.error("predict needs --split or --ids-file")
    a.fn(a)


if __name__ == "__main__":
    main()
