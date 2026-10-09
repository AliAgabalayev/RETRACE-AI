# Demo video notes (target 105 s, hard limits 90-120 s)

Status: shot list only. Nothing here has been recorded. All numbers come from `docs/ali/A1_diagnostic.md` and `docs/ali/a1_evidence/` (cited per shot). Build under demo = the frozen Qwen build (decision D17 in `docs/DECISIONS.md`): local Ollama `qwen2.5vl:3b`, prompt v9, `configs/ali_a1_qwen.yaml`.

## Ground rules for the recording
- Do NOT say FAIL for vr_4b921c5d. Today's build returns NEEDS REVIEW there (`predictions_C.jsonl`, reason "Needs review: R1: uncertain.").
- Do NOT say "fine-tuned", "production-ready" or "reduces QA workload".
- Every segment taken from a saved run, a cached result or a pre-made file carries an on-screen label: `REPLAY (saved run <run_id>)` or `PRERECORDED`. Live segments carry `LIVE`.
- Live wall time is NOT read from the video. Measure separately (section "Live timing" below). Cuts in the video must be visible (cut marker or a "time cut" caption). Measured per-pair wall time in A1 (CPU Ollama): B about 38-48 s, C about 69-160 s (`A1_diagnostic.md`), so a live C run does not fit in 120 s without a visible cut.
- Mocks are never shown as real inference. Do not select the "MOCK" engine.

## Prep (before recording; not part of the video)
1. Ollama running with `qwen2.5vl:3b` pulled (runtime notes: `docs/ali/runtime_inventory.md`, RAM was a blocker for larger Qwen).
2. Inputs for the three pairs live in `data/work/<sample_id>/reference.png` and `candidate.png` (paths from `data/manifests/inference_manifest.json`; these pairs are `split: dev`, so they do NOT appear in the UI "Demo pair" list, which only shows `split == "demo"` plus synthetic fixtures; use "Upload two images").
3. Rules: the UI needs the pair's A1 (allow) and D1 (deny) text. The per-run `rules.yaml` is saved inside each existing run dir, e.g. `artifacts/20261009T112802Z-c4530d/rules.yaml`; upload or paste that. (How to paste rules in the UI form: not re-verified by me; check the sidebar when preparing.)
4. Saved A1 runs (arm C, fresh cache, all calls were live when created, 2026-10-09):

| Pair | run_id (saved dir under `artifacts/`) | Final decision |
|---|---|---|
| vr_4b921c5d | `20261009T112802Z-c4530d` | NEEDS_REVIEW |
| vr_330651ed | `20261009T112407Z-355ff0` | NEEDS_REVIEW |
| vr_09a066d3 | `20261009T113543Z-8a257e` | NEEDS_REVIEW |

   Source: `docs/ali/a1_evidence/predictions_C.jsonl`. Loading one of these in the UI is a REPLAY of a stored result, not a new inference; label it so.

## Shot list

| Time | Shot | Say (short) | Segment type |
|---|---|---|---|
| 0:00-0:12 | Title card, then two screenshots side by side (any pair) | "After every game build, QA compares screenshots by eye. Some differences are allowed (lighting, clothing), some are bugs (a missing object). We test whether a rule-aware pipeline can help." | PRERECORDED slide |
| 0:12-0:40 | vr_4b921c5d: reference vs candidate, then the region box and crop | "Real bug from the VideoGameQA benchmark: one barrel is missing. DINOv2 proposes region R1 [2484,1400,3049,1966]; my own label is [2540,1500,3000,2050]. The localization matches." Then show the VLM text and the decision. "But the small local VLM described it as a texture and lighting change, so the verdict is uncertain and the system returns NEEDS REVIEW, not FAIL. It abstains rather than guess." | REPLAY of run `20261009T112802Z-c4530d` |
| 0:40-1:00 | vr_09a066d3 (outfit change, allowed A1) | "Allowed change: outfit changed. Full-frame VLM (arm B) says PASS. The hybrid (arm C) says NEEDS REVIEW: the whole frame changed, so proposals collapsed into one full-frame region and the policy refuses to auto-decide. So the hybrid gives no automatic PASS here." | REPLAY (C run `20261009T113543Z-8a257e`); B result shown from `predictions_B.jsonl` (no saved UI run for B), label it |
| 1:00-1:12 | vr_330651ed (subtitle language EN to PT) | "Ambiguous: a subtitle changed language. Rule D1 forbids text changes unless expected; my label uncertainty is high. The system returns NEEDS REVIEW and a human decides." | REPLAY (`20261009T112407Z-355ff0`) |
| 1:12-1:28 | Report ZIP: unzip, show `report.md`, `evidence.json`, `crops/`, `images/` | "Each run exports a ZIP: inputs with SHA-256, rules, region crops, the VLM's own words marked as unverified, scope (what was not assessed), final decision and reason, model and prompt identity." | PRERECORDED (made by `scripts/ali_export_evidence.py`, see below) |
| 1:28-1:45 | A1 table (slide) | "On 12 development pairs, 5 bug and 7 clean by my labels: pixel diff passes all 5 bugs, full-frame VLM passes all 5 bugs, hybrid passes 0 of 5 bugs but also gives REVIEW on all 12, so coverage is 0/12. This is a development diagnostic, not held-out." | PRERECORDED slide from `A1_diagnostic.md` |
| 1:45-1:55 | Qwen vs Gemini slide with the two crop images | "Next step: same crop and prompt sent to a stronger VLM. It names the missing barrel and the missing booth roof, 2 of 2. Two cases are a reproducer, not a measurement." | PRERECORDED slide from `stage1_qwen_vs_gemini.json` |
| 1:55-2:00 | Closing | "Honest status: localization works on Unity bugs; perception is the bottleneck." | -- |

If the total exceeds 120 s, cut the vr_330651ed shot first, then shorten the title.

## Reproduce each shot

### Shared: start the UI
```
cd /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton
.venv/bin/streamlit run app.py
```
(`.venv/bin/streamlit run app.py` is the project's launch command; I did not launch it while writing these notes, so it is unverified in this session.)

### Shot 2, 3, 4: replay a saved run
Sidebar -> "Open a saved run" (selectbox, `app.py` ~line 230) -> pick the run_id from the table above -> "Load saved run". Overlay caption `REPLAY - saved run <run_id>`. The page shows what was stored at A1 time.

### Shot 2, 3, 4: fresh live run (only for the timing measurement or if replay is not wanted)
UI: "Pair source" -> "Upload two images" -> upload `data/work/<id>/reference.png` and `candidate.png`; engine "Real (config)"; config must be `configs/ali_a1_qwen.yaml`. Whether the UI picks that config is NOT verified; the CLI form below is the exact one:
```
.venv/bin/python -m gameqa.cli analyze --config configs/ali_a1_qwen.yaml \
  --reference data/work/vr_4b921c5d/reference.png \
  --candidate data/work/vr_4b921c5d/candidate.png \
  --rules artifacts/20261009T112802Z-c4530d/rules.yaml --sample-id vr_4b921c5d
```
(Subcommand name `analyze` and flags are from `src/gameqa/cli.py` argparse; the module invocation `-m gameqa.cli` is unverified. A repeat run on `data/cache_ali_a1` will hit the cache; it is then a REPLAY of cached model answers. Use a new `run.cache_dir` in a copy of the config for a truly fresh run.)

### Full A/B/C reproduction (all 12 pairs, source of the table)
```
.venv/bin/python scripts/ali_a1_run.py --config configs/ali_a1_qwen.yaml --ids dev12 --arms A,B,C
.venv/bin/python scripts/ali_a1_score.py
```
Takes roughly 20-30 min of CPU Ollama time (sum of per-pair times above; estimate, not measured as one block).

### Shot 5: ZIP with evidence.json
The normal UI/CLI export does not yet write `evidence.json`: the hook is described as "required additive hook (Celal)" in `docs/ali/evidence_shape.md`, and at time of writing `write_evidence` is called from no file except its own definition in `src/gameqa/report.py` (grep). Use the bridge script on a finished run:
```
.venv/bin/python scripts/ali_export_evidence.py 20261009T112802Z-c4530d --config configs/ali_a1_qwen.yaml
```
Then `unzip -l artifacts/20261009T112802Z-c4530d.zip` and check `evidence.json`, `report.md`, `crops/`, `images/` are listed. I did not run this script; the on-screen claim "ZIP contains evidence.json" must be verified by unzipping before recording. Note: evidence cache status will read "unknown (replay possible)" by design.

### Shot 6: A1 table
Static slide copied from `docs/ali/A1_diagnostic.md`. Raw rows: `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`, `score_raw.md`.

### Shot 7: Qwen vs Gemini
Show `docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png` and `vr_d07179d5_R1_vlm_input.png`, plus the quotes in `stage1_qwen_vs_gemini.json`. Gemini model used: `gemini-3.5-flash`, free tier, cache off, 1 call each (latencies 3.4 s and 2.6 s in the file). Re-running needs `GEMINI_API_KEY` in the environment (name only; never show it) and `configs/gemini.yaml`/`ali_runtime_probe_gemini.yaml`; free tier is 20 requests/day/model (D16), so do not rerun on camera.

## Live timing (measured separately, not from the video)
1. Use a stopwatch or `time` around the CLI command above on a new empty cache dir, with no other load on Ollama.
2. Record per pair: B (full-frame) and C (hybrid) wall time, machine, model. Report as measured values with n; A1 reference values are B about 38-48 s, C about 69-160 s (CPU).
3. State in the video or slide: "recorded segments were shortened; live wall time was measured separately: <value, n>". Until measured: unknown.

## Claims that must NOT appear
- "FAIL" for vr_4b921c5d, or any claim that the system caught the barrel.
- "Hybrid beats full-frame" or "DINOv2 improves accuracy": the data show hybrid 0/5 bug false-PASS but 0/12 coverage; B and A pass all 5 bugs. No superiority claim.
- Observation accuracy (10/12 target): not scored (`obs_review.csv` unmarked).
- Any generalization claim: n = 12 dev pairs, mixed sources, not held-out.
