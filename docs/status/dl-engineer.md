# dl-engineer status (2026-10-09)

## Done (implemented AND run for real)
- `src/gameqa/vision/{alignment,features,proposals,judge,prompts,synth,smoke}.py` match D4 signatures. `tests/vision/` (25 CPU tests + 2 `real_model` tests, `GAMEQA_REAL=1`): full suite 163 passed, 6 skipped; real tests passed (DINOv2 GPU + Ollama).
- Real DINOv2 ViT-S/14 (torch.hub, CUDA, fp32) and real Ollama `qwen2.5vl:3b` ran on 7 fixtures and 10 dev pairs. Details/thresholds/prompt history: `docs/MODEL_NOTES.md`. Artifacts: `artifacts/dl_smoke/fixtures_vlm/<case>/`, `artifacts/dl_smoke/dev/<sample>/` (heatmap, boxes overlay, crops, `result.json` with raw judgments).
- Deviations from D4 / contracts (all backward compatible): `Judge` gained `warmup()` and `vlm.*` config keys (`num_ctx`, `keep_alive`, `audit_max_side`, `use_context`, `cache`, `mock_behavior`); `propose` honours new `proposals.*` keys (`min_area_px`, `mask_erode_px`, `global_change_fraction`). Proposal `score` is now "x times the source threshold".
- Edits outside my files (agreed in messages): `configs/default.yaml` (alignment.min_error_gain, proposals.*, vlm.* keys, `timeout_s` 30 -> 75, `crop_max_side` 336, `context_max_side` 512, `num_ctx` 2048) and `pipeline.build_engines` (VLM warmup BEFORE DINOv2 load). Please record in DECISIONS: **timeout_s 75** (CPU-resident VLM; audit call ~35 s) and the **global-change collapse**.

## Fixture outcomes (real DINOv2 + real VLM, prompt v9, `artifacts/dl_smoke/fixtures_vlm/`)
| fixture | proposals | judgments | scene audit | implies (via decision.py, not run here) |
| --- | --- | --- | --- | --- |
| object_removed | R1 union (424,181,521,286) | forbidden D1, validated | uncertain (VLM said allowed A1,A2 for a removal -> contradiction rejected) | FAIL (region) |
| lighting_change | R1 dinov2 tiny box on the sun | uncertain (no visible difference) | allowed A1/A2 | NEEDS_REVIEW (honest) |
| allowed_and_forbidden | R1 union barrel, R2 dinov2 sun | R1 forbidden D1 validated, R2 uncertain | allowed | FAIL |
| small_object_removed (12 px coin) | R1 classical only (DINOv2 max 0.35 = at threshold) | forbidden D1 validated | uncertain | FAIL |
| clothing_color_change | none (neither source fires) | - | allowed A2 (VLM audit, validated) | PASS-capable; semantic content right |
| identical | none | - | deterministic pixel-identical shortcut, allowed | PASS |
| small_translation | none (ALIGNED, mask erode fixes QA-D4) | - | deterministic shortcut | PASS |
Caveat: single runs on synthetic, hand-drawn pairs; the 3B model's rule mapping is not reliable (see below).

## Dev latency / compliance (10 evenly spaced dev pairs, real DINOv2 + real VLM, cache off; data from `artifacts/dl_smoke/dev/*/result.json`)
- Seconds per pair (align+DINOv2+proposals+all VLM calls): **median 84.8, p90 141, max 141** (n=10). VLM calls per pair: 1-5 (mean 3.0): region calls ~20 s each, audit ~35 s, cold load 55-70 s once. DINOv2 alone: 0.03-0.25 s per pair; classical + alignment ~0.1-0.5 s. => E2 subset: median is under 90 s but p90 is not and pairs with 8 regions would take ~200 s; **recommend 40 pairs** or lower `max_regions` (4) for E2 (decision for senior-pm). Before the global-change collapse, YouTube pairs took 224-239 s each (8 regions).
- 30 VLM judgments (20 region + 10 audit): 30/30 parsed as JSON (schema-constrained decoding), 0 malformed, 0 unknown rule IDs, 0 provider errors, 23/30 passed all consistency checks, 7 rejected by the contradiction guards (allowed + disappeared/missing text) -> uncertain. Self-confidence unused.
- Quality on dev (labels read for dev only): 8 Unity bug pairs and 2 cutscene pairs (1 bug, 1 no_bug) all end uncertain/allowed; NO validated `forbidden` appeared on any of the 10 dev pairs, i.e. recall of the VLM on benchmark bugs is ~0 on this sample and `allowed A1` is cited for several bug pairs (A1 = generic "acceptable" bullets). bf32ee28 (bug) got no proposals at all (p95 distance 0). Expect mostly NEEDS_REVIEW / some false PASS risk when audit says allowed on a pair with no proposals: the audit is a 3B heuristic. Report per-source in E2.
- Dev proposal counts (union): Unity 0-4 (except 3 pairs with 33/1/1 at global fraction >=0.2), cutscene 1-40; global-change fraction cut at 0.10 collapses all cutscene pairs.

## Blockers / needs owner (not solvable by me)
1. Ollama runs the VLM on CPU only (fixed 6.7 GiB graph buffer vs 6 GB GPU) -> 20-35 s per call and ~9.3 GiB free RAM needed at load. Free RAM (close browser/other agents) before E2; run serially; one `ollama stop` before long runs. A smaller/GPU-capable VLM would need an owner decision.
2. VLM rule-mapping on real benchmark pairs is weak (see Quality). A stronger cloud/local model is the single biggest lever; prompts are provider-agnostic.

## Notes for others
- python-developer/APP: `judge.warmup()` is called in `build_engines`; keep the order (judge first). `Judge` cache is at `data/cache/vlm/`; `--no-cache` in `python -m gameqa.vision.smoke` for timings. The CLI `batch` jsonl fields request (sample_id, decision, execution_status, engine_mode, n_regions, proposals_judged, seconds_total, prompt_version, feature_model, vlm_model) was routed to me by mistake; it belongs to APP (`cli.py`) and I did not touch it. Versions already expose `prompt_version` = `judge.prompt_version` ("v9").
- QA: QA-D4 fixed (mask erosion + reference fill of invalid border), QA-D5 fixed (`min_area_px` 40, fraction 1e-4), QA-D7 fixed (`no_visible_change` regex replaced by `any_difference`/`change_type` fields), D6 (evidence required for allowed) and D9 (unknown rule id -> validated False) enforced in `validate_response`. Readability H-items: `min_error_gain` in config, shift limit comment, raw-component truncation sets `Coverage.truncated`, scores normalised, dead code removed.
- Prompts were developed only on synthetic fixtures and ~6 dev pairs; eval split untouched.
