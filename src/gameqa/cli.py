"""Command line: analyze one pair, batch over the inference manifest, approve a reference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gameqa.config import REPO_ROOT, load_config
from gameqa.contracts import PairInput
from gameqa.rules import RulesError, load_rules

DEFAULT_MANIFEST = REPO_ROOT / "data" / "manifests" / "inference_manifest.json"
MOCK_BEHAVIORS = ("allowed", "forbidden", "uncertain", "timeout", "invalid_json", "unknown_rule")


def _config(args) -> dict:
    cfg = load_config(args.config)
    if args.mock:
        cfg = load_config(args.config, {"vlm": {"provider": "mock", "mock_behavior": args.mock}})
    return cfg


def _summary(result) -> dict:
    return {
        "sample_id": result.sample_id,
        "run_id": result.run_id,
        "final_decision": result.final_decision.value,
        "decision_reason": result.decision_reason,
        "execution_status": result.execution_status.value,
        "engine_mode": result.engine_mode,
        "coverage": result.coverage.model_dump(),
        "errors": result.errors,
        "timings": result.timings,
    }


def cmd_analyze(args) -> int:
    from gameqa import pipeline
    from gameqa.config import resolve_dir

    cfg = _config(args)
    try:
        rules = load_rules(args.rules)
    except (RulesError, OSError) as exc:
        print(f"error: cannot load rules: {exc}", file=sys.stderr)
        return 2
    pair = PairInput(reference_path=args.reference, candidate_path=args.candidate, rules=rules,
                     sample_id=args.sample_id)
    extractor, judge = pipeline.build_engines(cfg)
    result = pipeline.analyze(pair, cfg, judge=judge, extractor=extractor)
    run_dir = resolve_dir(cfg, "artifacts_dir") / result.run_id
    if args.json:
        print(json.dumps({**_summary(result), "run_dir": str(run_dir)}, indent=2))
    else:
        banner = "  [MOCK: not real inference]" if result.engine_mode == "mock" else (
            "  [DEGRADED]" if result.engine_mode == "degraded" else "")
        print(f"Decision: {result.final_decision.value}{banner}")
        print(f"Reason:   {result.decision_reason}")
        print(f"Mode:     {result.engine_mode} / {result.execution_status.value}")
        for e in result.errors:
            print(f"Error:    {e}")
        print(f"Run dir:  {run_dir}")
    return 0


def _load_ids(path: str) -> set[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("sample_ids") or data.get("ids") or []
    return {d["sample_id"] if isinstance(d, dict) else d for d in data}


def _batch_row(res, split, run_dir) -> dict:
    return {
        "sample_id": res.sample_id, "split": split, "run_id": res.run_id,
        "decision": res.final_decision.value, "decision_reason": res.decision_reason,
        "execution_status": res.execution_status.value, "engine_mode": res.engine_mode,
        "n_regions": res.coverage.proposals_total, "proposals_judged": res.coverage.proposals_judged,
        "seconds_total": res.timings.get("total"), "prompt_version": res.versions.prompt_version,
        "feature_model": res.versions.feature_model, "vlm_model": res.versions.vlm_model,
        "run_dir": str(run_dir), "errors": res.errors,
    }


def cmd_batch(args) -> int:
    from gameqa import pipeline
    from gameqa.config import resolve_dir
    from gameqa.rules import rules_from_dicts

    cfg = _config(args)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    rows = [m for m in manifest if m.get("split") == args.split]
    if args.ids_file:
        rows = [m for m in rows if m["sample_id"] in _load_ids(args.ids_file)]
    if args.limit is not None:
        rows = rows[: args.limit]
    extractor, judge = pipeline.build_engines(cfg)
    out = open(args.out, "w", encoding="utf-8") if args.out else None
    try:
        for m in rows:  # only inference fields are read; labels live in a separate file
            def _abs(p):
                return str(p if Path(p).is_absolute() else REPO_ROOT / p)

            pair = PairInput(
                reference_path=_abs(m["reference_path"]), candidate_path=_abs(m["candidate_path"]),
                rules=rules_from_dicts(m["rules"]), sample_id=m["sample_id"],
            )
            res = pipeline.analyze(pair, cfg, judge=judge, extractor=extractor)
            line = json.dumps(_batch_row(res, m.get("split"), resolve_dir(cfg, "artifacts_dir") / res.run_id))
            print(f"{res.sample_id}\t{res.final_decision.value}\t{res.engine_mode}")
            if out:
                out.write(line + "\n")
                out.flush()
    finally:
        if out:
            out.close()
    return 0


def cmd_approve(args) -> int:
    from gameqa.config import resolve_dir
    from gameqa.storage import StorageError, approve_reference, load_run, run_dir_for

    cfg = load_config(args.config)
    try:
        run_dir = run_dir_for(args.run_id, cfg)
        result = load_run(args.run_id, cfg)
        info = approve_reference(
            args.reference_id, run_dir / "images" / "candidate.png", args.run_id, cfg,
            previous_reference_path=run_dir / "images" / "reference.png",
        )
    except StorageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(info, indent=2))
    print(f"(approved from run decision {result.final_decision.value})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gameqa", description="Rule-aware visual regression")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--config", default=None, help="YAML merged over configs/default.yaml")
        p.add_argument("--mock", choices=MOCK_BEHAVIORS, default=None,
                       help="use the labelled MOCK judge with this behaviour (not real inference)")

    a = sub.add_parser("analyze", help="analyze one reference/candidate pair")
    a.add_argument("--reference", required=True)
    a.add_argument("--candidate", required=True)
    a.add_argument("--rules", required=True)
    a.add_argument("--sample-id", default=None)
    a.add_argument("--json", action="store_true")
    common(a)
    a.set_defaults(func=cmd_analyze)

    b = sub.add_parser("batch", help="run over an inference manifest split (never reads labels)")
    b.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    b.add_argument("--split", required=True, choices=["dev", "eval", "demo"])
    b.add_argument("--ids-file", default=None,
                   help="JSON list of sample_ids (or {'sample_ids'|'ids': [...]}) to restrict the split")
    b.add_argument("--limit", type=int, default=None)
    b.add_argument("--out", default=None, help="results.jsonl path")
    common(b)
    b.set_defaults(func=cmd_batch)

    c = sub.add_parser("approve", help="approve a run's candidate as a new reference version")
    c.add_argument("--reference-id", required=True)
    c.add_argument("--run-id", required=True)
    c.add_argument("--config", default=None)
    c.set_defaults(func=cmd_approve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
