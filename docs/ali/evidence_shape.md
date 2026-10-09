# evidence.json shape (frozen, schema_version 1)

Producer: `gameqa.report.build_evidence(result, run_dir=None, cfg=None)` / `write_evidence(result, run_dir, cfg=None)`.
Markdown: `render_report(result, run_dir=None, cfg=None)` appends sections "Input IDs", "Scope",
"Model identity and cache", "Limitations" (existing sections unchanged). Without `run_dir`, hashes show "not computed".

```
schema_version: 1
run_id, sample_id, created_at, engine_mode (real|degraded|mock), execution_status
inputs: {note, reference|candidate|aligned_candidate|rules_yaml: {path, sha256, width, height}}
        # sha256/size of the STORED copies in the run dir, not of the original uploads
expected: [{id, effect: allow|deny, description}]            # the rules
regions: [{region_id, box [x1,y1,x2,y2] ref px exclusive, proposal_source, proposal_score,
           verdict, expected_rules: [{id, effect, description}],
           observed_change_vlm_reported, evidence_text_vlm_reported,
           reference_crop {path,sha256,width,height}, candidate_crop {...},
           model, is_mock, validated, errors}]
scene_audit: null | {verdict, observed_change_vlm_reported, rule_ids, evidence_text_vlm_reported,
                     extra_changes_reported, model, is_mock, validated, errors}
alignment: {status, overlap_fraction}
scope: {proposals_total, proposals_judged, truncated, scene_audit_ran, deadline_exceeded,
        assessed: [str], not_assessed: [str]}   # cap drops, unjudged, deadline, no audit,
                                                # unreliable alignment, uncompared border, unlocalized extra changes
decision: {final, reason, pipeline_errors}
identity: {vlm_model, prompt_version, config_hash, feature_model, device, dtype,
           reasoning_effort (only when cfg passed), reasoning_effort_note}
cache: {status, per_stage_recorded: false, note?}
limitations: str
```

## Cache status rules
- mock engine: "not applicable (mock engine, no provider call)".
- `cfg` passed and `vlm.cache` false: "live (vlm.cache disabled in config)".
- otherwise: **"unknown (replay possible)"**. `Judge.last_cache_hit` is per call and not stored in analysis.json,
  so live is never claimed. Per-stage provenance would need dl-engineer/Celal to record hits (e.g. a per-judgment field).
  For measured fresh runs use a new empty `run.cache_dir` (see configs/ali_runtime_probe.yaml).

## Not provided (by design)
Build IDs, engine metadata, root cause, gameplay reproduction steps. Observed facts are VLM-reported, unverified.

## Required additive hook (Celal; not made by me)
`report.py` cannot write into the run dir by itself: `render_report` gets no `run_dir`. Minimal change:
- `storage.export_report`: `from gameqa.report import render_report, write_evidence`; call `write_evidence(result, run_dir)`
  before zipping and use `render_report(result, run_dir)`.
- `pipeline.analyze`: same two calls next to its `write_text_atomic(rdir / "report.md", ...)` (optionally pass `cfg`).
Until then the ZIP lacks evidence.json and hashes in report.md; the strict xfail test
`test_plain_export_report_writes_evidence` will flip to XPASS (fail) when the hook lands, then drop the marker.
