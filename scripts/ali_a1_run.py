#!/usr/bin/env python
"""A1 perception diagnostic runner (Ali, WP1.1). Does NOT edit evaluate.py / pipeline.py; imports them read-only.

Arms (same config, same model/provider, each sample's own A1/D1 rules from the INFERENCE manifest):
  A  pixel-diff control (existing classical method from scripts/evaluate.py, dev-tuned threshold); no VLM
  B  full-frame, VLM only (Judge.audit_scene on the aligned pair, no proposals, as evaluate.py vlm_only)
  C  hybrid (gameqa.pipeline.analyze: DINOv2 proposals -> per-region VLM -> scene audit -> decide)

Labels (eval_labels.json, labels_ali.csv) are never opened here.

Output: <out-root>/<arm>/predictions.jsonl (+ run_meta.json); resumable (re-run the same command).
Real runs hold artifacts/ali/vlm.lock. Mock runs go to a separate dir (default artifacts/ali/a1_MOCK_tmp).

  .venv/bin/python scripts/ali_a1_run.py --config configs/ali_a1_qwen.yaml --ids balanced6 --arms A,B,C
  .venv/bin/python scripts/ali_a1_run.py --config configs/ali_a1_qwen.yaml --ids dev12   # resumes, adds the other six
"""

from __future__ import annotations

import argparse
import atexit
import copy
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

IDS_JSON = REPO / "configs" / "ali_dev12.json"
LOCK = REPO / "artifacts" / "ali" / "vlm.lock"
DEFAULT_OUT = REPO / "artifacts" / "ali" / "a1"
MOCK_OUT = REPO / "artifacts" / "ali" / "a1_MOCK_tmp"
FULL_FRAME_FRAC = 0.98


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        return None


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_lock(note):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        info = LOCK.read_text().strip()
        try:
            pid = int(json.loads(info).get("pid", -1))
        except Exception:  # noqa: BLE001
            pid = -1
        sys.exit(f"REFUSING: VLM lock {LOCK} is held ({info}). pid alive={_pid_alive(pid)}. "
                 "Remove it manually only if you are sure nobody is running.")
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps({"pid": os.getpid(), "since": now(), "owner": "ali_a1_run", "note": note}))

    def release():
        try:
            if json.loads(LOCK.read_text()).get("pid") == os.getpid():
                LOCK.unlink()
        except Exception:  # noqa: BLE001
            pass

    atexit.register(release)


def select_ids(which):
    d = json.loads(IDS_JSON.read_text())
    six = [r["sample_id"] for r in d["balanced_six"]]
    dev = [r["sample_id"] for r in d["dev12"]]
    if which == "balanced6":
        return six
    return six + [i for i in dev if i not in six]  # balanced six first, then the other six


def truncation_info(proposals, cov, cfg):
    """Split global-change collapse from max-region cap (and deadline)."""
    cap = int(cfg["proposals"]["max_regions"])
    total, judged, n = cov.proposals_total, cov.proposals_judged, len(proposals)
    collapse = bool(cov.truncated and n == 1 and proposals[0].area_fraction >= FULL_FRAME_FRAC)
    capped = bool(total > n and not collapse)
    cause = []
    if collapse:
        cause.append("global_change_collapse")
    if capped:
        cause.append("max_region_cap")
    if cov.deadline_exceeded:
        cause.append("deadline")
    if cov.truncated and not cause:
        cause.append("other")
    return {"truncated": bool(cov.truncated), "truncation_cause": "+".join(cause) or None,
            "global_collapse": collapse, "max_region_cap_hit": capped, "max_regions": cap,
            "proposals_total": total, "proposals_judged": judged}


def j_dict(j, box=None, source=None, score=None):
    return {"region_id": j.region_id, "box": list(box) if box else None, "source": source, "score": score,
            "observed_change": j.observed_change, "verdict": j.verdict.value, "rule_ids": list(j.rule_ids),
            "evidence": j.evidence, "validated": j.validated, "errors": list(j.errors), "latency_s": j.latency_s,
            "model": j.model, "is_mock": j.is_mock}


def read_calls(dump_dir, skip):
    f = Path(dump_dir) / "calls.jsonl"
    if not f.exists():
        return None
    lines = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    return lines[skip:]


def calls_len(dump_dir):
    f = Path(dump_dir) / "calls.jsonl"
    return len(f.read_text().splitlines()) if f.exists() else 0


def cache_summary(calls):
    if calls is None:
        return {"status": "unknown (no calls.jsonl; dump disabled)", "calls": None, "hits": None}
    if not calls:
        return {"status": "none (no VLM call)", "calls": 0, "hits": 0}
    hits = sum(bool(c.get("cache_hit")) for c in calls)
    st = "cached" if hits == len(calls) else "fresh" if hits == 0 else "mixed"
    return {"status": st, "calls": len(calls), "hits": hits}


def make_judge(cfg, arm, sid, build_judge):
    c = copy.deepcopy(cfg)
    base = c["vlm"].get("dump_tag") or "a1"
    if c["vlm"].get("dump_inputs_dir"):
        c["vlm"]["dump_tag"] = f"{base}/{arm}/{sid}"
    j = build_judge(c)
    return j, (j.dump_dir if getattr(j, "dump_dir", None) else None)


# --------------------------------------------------------------------------- arms
def run_A(rec, ctx):
    ev = ctx["evaluate"]
    frac = ev.classical_fraction(rec["reference_path"], rec["candidate_path"])
    return {"decision": "FAIL" if frac > ctx["threshold"] else "PASS", "reason": f"changed_fraction {frac:.5f} vs threshold {ctx['threshold']:.5f}",
            "changed_fraction": round(frac, 6), "threshold": ctx["threshold"], "n_proposals": 0, "is_mock": False}


def run_B(rec, ctx):
    import cv2
    from gameqa.contracts import AlignmentResult, AlignmentStatus, Coverage, Rule
    from gameqa.decision import DecisionInput, decide
    from gameqa.imageio import load_image
    from gameqa.vision.alignment import align

    cfg = ctx["cfg"]
    rules = [Rule(**r) for r in rec["rules"]]
    ref = load_image(str(REPO / rec["reference_path"]), cfg).array
    cand = load_image(str(REPO / rec["candidate_path"]), cfg).array
    if ctx["b_input"] == "aligned":
        try:
            alignment, used, _ = align(ref, cand, cfg)
        except Exception as exc:  # noqa: BLE001
            alignment = AlignmentResult(status=AlignmentStatus.FAILED, candidate_to_reference=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], overlap_fraction=0.0)
            used = cand if cand.shape == ref.shape else cv2.resize(cand, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA)
    else:  # evaluate.py vlm_only behaviour
        used = cand if cand.shape == ref.shape else cv2.resize(cand, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA)
        alignment = AlignmentResult(status=AlignmentStatus.IDENTITY, candidate_to_reference=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], overlap_fraction=1.0)
    judge, dump_dir = make_judge(cfg, "B", rec["sample_id"], ctx["build_judge"])
    skip = calls_len(dump_dir) if dump_dir else 0
    audit = judge.audit_scene(ref, used, rules, [])
    dec, reason = decide(DecisionInput(rules, [], audit, Coverage(scene_audit_ran=True), alignment))
    j = audit.judgment
    return {"decision": dec.value, "reason": reason, "n_proposals": 0, "truncated": False, "truncation_cause": None,
            "global_collapse": False, "max_region_cap_hit": False, "proposals_total": 0, "proposals_judged": 0,
            "regions": [], "audit": j_dict(j), "extra_changes_reported": audit.extra_changes_reported,
            "verdicts": [j.verdict.value], "rule_ids": list(j.rule_ids), "validated": bool(j.validated),
            "errors": list(j.errors), "model": judge.model_id, "prompt_version": judge.prompt_version,
            "is_mock": bool(judge.is_mock), "engine_mode": "mock" if judge.is_mock else ("degraded" if j.errors else "real"),
            "b_input": ctx["b_input"], "alignment_status": alignment.status.value, "run_id": f"B-{rec['sample_id']}",
            "cache": cache_summary(read_calls(dump_dir, skip) if dump_dir else None), "dump_dir": str(dump_dir) if dump_dir else None}


def run_C(rec, ctx):
    from gameqa.contracts import PairInput, Rule

    cfg = ctx["cfg"]
    pair = PairInput(reference_path=str(REPO / rec["reference_path"]), candidate_path=str(REPO / rec["candidate_path"]),
                     rules=[Rule(**r) for r in rec["rules"]], sample_id=rec["sample_id"])
    judge, dump_dir = make_judge(cfg, "C", rec["sample_id"], ctx["build_judge"])
    skip = calls_len(dump_dir) if dump_dir else 0
    res = ctx["analyze"](pair, cfg, judge=judge, extractor=ctx["extractor"])
    by_id = {p.id: p for p in res.proposals}
    regions = [j_dict(j, by_id[j.region_id].box if j.region_id in by_id else None,
                      by_id[j.region_id].source if j.region_id in by_id else None,
                      by_id[j.region_id].score if j.region_id in by_id else None) for j in res.judgments]
    audit = j_dict(res.scene_audit.judgment) if res.scene_audit else None
    allj = res.judgments + ([res.scene_audit.judgment] if res.scene_audit else [])
    t = truncation_info(res.proposals, res.coverage, cfg)
    return {"decision": res.final_decision.value, "reason": res.decision_reason, "n_proposals": len(res.proposals),
            **t, "proposals": [{"id": p.id, "box": list(p.box), "source": p.source, "score": p.score, "area_fraction": p.area_fraction}
                               for p in res.proposals],
            "regions": regions, "audit": audit,
            "extra_changes_reported": bool(res.scene_audit.extra_changes_reported) if res.scene_audit else None,
            "verdicts": [j.verdict.value for j in allj], "rule_ids": sorted({r for j in allj for r in j.rule_ids}),
            "validated": bool(allj) and all(j.validated for j in allj),
            "errors": list(res.errors) + [e for j in allj for e in j.errors],
            "model": res.versions.vlm_model, "prompt_version": res.versions.prompt_version,
            "is_mock": res.engine_mode == "mock", "engine_mode": res.engine_mode, "execution_status": res.execution_status.value,
            "alignment_status": res.alignment.status.value if res.alignment else None,
            "run_id": res.run_id, "timings": res.timings,
            "cache": cache_summary(read_calls(dump_dir, skip) if dump_dir else None), "dump_dir": str(dump_dir) if dump_dir else None}


# --------------------------------------------------------------------------- driver
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--ids", choices=["balanced6", "dev12"], required=True)
    ap.add_argument("--arms", default="A,B,C", help="comma list of A,B,C (order of execution per sample)")
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--threshold", type=float, default=None, help="arm A pixel-diff threshold (default: dev-tuned file)")
    ap.add_argument("--b-input", choices=["aligned", "resized"], default="aligned",
                    help="arm B candidate: aligned (same as C) or only resized (evaluate.py vlm_only behaviour)")
    ap.add_argument("--retry-errors", action="store_true", help="move rows with errors to predictions_errors.jsonl and re-run them")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    arms = [a.strip().upper() for a in args.arms.split(",") if a.strip()]
    if not set(arms) <= {"A", "B", "C"}:
        sys.exit("--arms must be a subset of A,B,C")

    from gameqa.config import config_hash, load_config
    from gameqa.data.manifest import load_inference_manifest

    cfg = load_config(args.config)
    manifest = {r["sample_id"]: r for r in load_inference_manifest()}  # raises if label keys leaked
    ids = select_ids(args.ids)
    if args.limit:
        ids = ids[: args.limit]
    missing = [i for i in ids if i not in manifest]
    if missing:
        sys.exit(f"ids absent from inference manifest: {missing}")

    ctx = {"cfg": cfg, "b_input": args.b_input}
    is_mock = cfg["vlm"].get("provider") == "mock"
    out_root = Path(args.out_root) if args.out_root else (MOCK_OUT if is_mock else DEFAULT_OUT)
    if is_mock and out_root == DEFAULT_OUT:
        sys.exit("mock provider must not write into the real A1 dir")
    if is_mock:
        print("*** MOCK PROVIDER: output is NOT real inference, written to", out_root, file=sys.stderr)
        cfg["run"]["cache_dir"] = str(out_root / "cache_mock")
        cfg["run"]["artifacts_dir"] = str(out_root / "runs")
        if cfg["vlm"].get("dump_inputs_dir"):
            cfg["vlm"]["dump_inputs_dir"] = str(out_root / "inputs")
    chash = config_hash(cfg)

    if "A" in arms:
        ev_spec = importlib.util.spec_from_file_location("evaluate_ro", REPO / "scripts" / "evaluate.py")
        ev = importlib.util.module_from_spec(ev_spec)
        ev_spec.loader.exec_module(ev)
        ctx["evaluate"] = ev
        if args.threshold is not None:
            ctx["threshold"], tsrc = args.threshold, "cli"
        elif ev.THRESH_FILE.exists():
            ctx["threshold"], tsrc = json.loads(ev.THRESH_FILE.read_text())["threshold"], "artifacts/eval/classical_threshold.json (dev only)"
        else:
            sys.exit("arm A needs --threshold or artifacts/eval/classical_threshold.json")
        ctx["threshold_source"] = tsrc

    from gameqa.pipeline import analyze, build_extractor, build_judge
    ctx.update(build_judge=build_judge, analyze=analyze)
    if "C" in arms:
        ctx["extractor"] = build_extractor(cfg)
    uses_vlm = bool({"B", "C"} & set(arms)) and not is_mock
    if uses_vlm:
        acquire_lock(f"ali_a1_run arms={args.arms} ids={args.ids}")

    fns = {"A": run_A, "B": run_B, "C": run_C}
    done, files = {}, {}
    for arm in arms:
        d = out_root / arm
        d.mkdir(parents=True, exist_ok=True)
        p = d / "predictions.jsonl"
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
        meta_p = d / "run_meta.json"
        if rows and meta_p.exists():
            old = json.loads(meta_p.read_text())
            if old.get("config_hash") != chash:
                sys.exit(f"REFUSING to resume {d}: config_hash differs ({old.get('config_hash')} vs {chash}); use a new --out-root")
        if args.retry_errors and rows:
            bad = [r for r in rows if r.get("error") or r.get("errors")]
            if bad:
                with (d / "predictions_errors.jsonl").open("a") as fh:
                    fh.writelines(json.dumps(r) + "\n" for r in bad)
                rows = [r for r in rows if r not in bad]
                p.write_text("".join(json.dumps(r) + "\n" for r in rows))
        done[arm] = {r["sample_id"] for r in rows}
        files[arm] = p
        meta_p.write_text(json.dumps({
            "arm": arm, "config": args.config, "config_hash": chash, "ids": args.ids, "expected_ids": ids, "commit": git_commit(),
            "mock": is_mock, "b_input": args.b_input if arm == "B" else None,
            "threshold": ctx.get("threshold") if arm == "A" else None, "threshold_source": ctx.get("threshold_source") if arm == "A" else None,
            "vlm": {k: cfg["vlm"].get(k) for k in ("provider", "model", "base_url", "crop_max_side", "context_max_side", "audit_max_side", "num_ctx")},
            "max_regions": cfg["proposals"]["max_regions"], "cache_dir": cfg["run"]["cache_dir"], "argv": sys.argv,
            "updated_at": now()}, indent=2))

    for n, sid in enumerate(ids, 1):
        rec = manifest[sid]
        for arm in arms:
            if sid in done[arm]:
                print(f"[{n}/{len(ids)}] {arm} {sid} already done, skip")
                continue
            t = time.perf_counter()
            row = {"sample_id": sid, "arm": arm, "media_source": rec.get("media_source"), "started_at": now(),
                   "rule_ids_given": [r["id"] for r in rec["rules"]], "config_hash": chash, "error": None}
            try:
                row.update(fns[arm](rec, ctx))
            except Exception as exc:  # noqa: BLE001 - kept as NEEDS_REVIEW, never dropped
                row.update(decision="NEEDS_REVIEW", reason="runner exception",
                           error=f"{type(exc).__name__}: {exc}", n_proposals=0)
            row["latency_s"] = round(time.perf_counter() - t, 3)
            if is_mock:
                row["is_mock"] = True
            with files[arm].open("a") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"[{n}/{len(ids)}] {arm} {sid} {row['decision']} {row['latency_s']}s trunc={row.get('truncation_cause')}"
                  + (f" ERROR {row['error']}" if row["error"] else ""))
    print("done ->", out_root)


if __name__ == "__main__":
    main()
