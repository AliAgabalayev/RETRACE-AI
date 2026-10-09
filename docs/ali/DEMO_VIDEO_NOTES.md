# Demo video notes (target 105 s, hard limits 90-120 s)

Status: shot list only. Nothing here has been recorded. All numbers come from `docs/ali/A1_diagnostic.md`, `docs/ali/a1_evidence/` and `docs/ali/A3_review.md` (cited per shot). A3 reproduced A1 exactly (36/36 rows, 80 fresh calls, 0 cache hits), so it is a determinism / regression check, not a second sample: say "replicated", never "two experiments". Build under demo = the frozen Qwen build (decision D17 in `docs/DECISIONS.md`): local Ollama `qwen2.5vl:3b`, prompt v9, `configs/ali_a1_qwen.yaml`.

## Ground rules for the recording
- Do NOT say FAIL for vr_4b921c5d. Today's build returns NEEDS REVIEW there (`predictions_C.jsonl`, reason "Needs review: R1: uncertain.").
- Do NOT say "fine-tuned", "production-ready" or "reduces QA workload". Do NOT claim DINOv2 is better than a plain VLM.
- Whenever false-PASS is spoken or shown, show coverage next to it: C 0/5 at 0/12, A 5/5 at 12/12, B 5/5 at 8/12 (`A3_review.md` sec 3).
- vr_330651ed: never say the rule forbids text changes (its rules.yaml has no text rule, QA-D1). Say it is an ambiguous label.
- Localization: never say "my own independent label" (QA-D2). 4 of 5 bug labels were Claude-proposed corrections confirmed by Ali after model outputs existed.
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
| 0:12-0:40 | vr_4b921c5d: reference vs candidate, then the region box and crop | "Real bug from the VideoGameQA benchmark: one barrel is missing. DINOv2 proposes region R1 [2484,1400,3049,1966]; the label, corrected after an abs-diff check and confirmed by me, is [2540,1500,3000,2050]; overlap IoU 0.60. Four of the five bug labels were Claude-proposed corrections that I confirmed after model outputs existed, so this agreement is not fully independent." Then show the VLM text and the decision. "The small local VLM described it as a texture and lighting change, so the region verdict is uncertain. Note the whole-scene audit said 'allowed' here, which is wrong. The region guard caught that contradiction, and the final result is NEEDS REVIEW, not FAIL. It abstains rather than guess." (On screen: the bug ZIP `report.md` line 'Whole-scene audit: allowed', QA-D5.) | REPLAY of run `20261009T112802Z-c4530d` |
| 0:40-1:00 | vr_09a066d3 (outfit change, allowed A1) | "Allowed change: outfit changed. Full-frame VLM (arm B) says PASS. The hybrid (arm C) says NEEDS REVIEW: the whole frame changed, so proposals collapsed into one full-frame region and the policy refuses to auto-decide. So the hybrid gives no automatic PASS here." | REPLAY (C run `20261009T113543Z-8a257e`); B result shown from `predictions_B.jsonl` (no saved UI run for B), label it |
| 1:00-1:12 | vr_330651ed (subtitle language EN to PT) | "Ambiguous label: only the subtitle language changed. This pair's own rules do not clearly cover a text change, and my label uncertainty is high. The system returns NEEDS REVIEW and a human decides." (Do NOT say D1 forbids text; the rules.yaml in `ambiguous_vr_330651ed_C_20261009T112407Z-355ff0.zip` has no text rule, QA-D1.) | REPLAY (`20261009T112407Z-355ff0`) |
| 1:12-1:28 | Report ZIP: unzip, show `report.md`, `evidence.json`, `crops/`, `images/` | "Each run exports a ZIP: inputs with SHA-256, rules, region crops, the VLM's own words marked as unverified, scope (including 'not assessed: global change collapsed into one full-frame region'), final decision and reason, model and prompt identity." | PRERECORDED (made by `scripts/ali_export_evidence.py`, see below) |
| 1:28-1:45 | A1 table (slide) | "On 12 development pairs, 5 bug and 7 clean by my labels: pixel diff passes all 5 bugs at 12/12 coverage, full-frame VLM passes all 5 bugs at 8/12 coverage, hybrid passes 0 of 5 bugs but gives REVIEW on all 12, coverage 0/12. A fresh-cache rerun reproduced these exactly; that is a replication, not a second sample. Counting the ambiguous pair as clean gives 4/4, 4/4, 0/4, same conclusion. Development diagnostic, not held-out." | PRERECORDED slide from `A1_diagnostic.md` and `A3_review.md` sec 2-4 |
| (optional, 5 s, fold into the row above) | Observation-accuracy line on the same slide | "I marked the models' descriptions: with region crops 9 of 12 are right or partly right, full-frame 4 of 12; strict-correct is 1 of 12 for both. One rater, n = 12, possible anchoring. It did not become correct decisions." | PRERECORDED, source `a1_evidence/obs_review.csv`, `A1_diagnostic.md` |
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
The three demo ZIPs already exist in `artifacts/ali/demo_zips/` and were regenerated after the report-scope fix (QA-D6):
- `allowed_vr_09a066d3_C_20261009T113543Z-8a257e.zip`
- `ambiguous_vr_330651ed_C_20261009T112407Z-355ff0.zip`
- `bug_vr_4b921c5d_C_20261009T112802Z-c4530d.zip`

QA unzipped and checked them (report.md, analysis.json, evidence.json, rules.yaml, images/, crops/ present; evidence.json sha256 matches the files; decisions agree across files; `docs/ali/A5_acceptance.md`, "Demo ZIPs"). The two collapsed runs now state "NOT assessed: global change ... collapsed into one full-frame region" in `report.md` (my grep after regeneration). Cache status reads "unknown (replay possible)" by design. Before filming, still run `unzip -l` on the ZIP shown on screen. Source of these ZIPs: `scripts/ali_export_evidence.py` (bridge). Whether the normal UI/CLI export writes `evidence.json` is a separate question owned by Celal's hook and was not verified by me.

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
- "Hybrid beats full-frame" or "DINOv2 improves accuracy": the data show hybrid 0/5 bug false-PASS but 0/12 coverage; B and A pass all 5 bugs (5/5 at 8/12 and 12/12). No superiority claim.
- Observation accuracy as a success: the 10/12 strict target is NOT met (1/12 y for B and C). Only the y+p numbers (B 4/12, C 9/12) may be quoted, with the one-rater / n = 12 / anchoring caveat.
- "A3 confirms" as if it were new evidence: A3 = A1 exactly, a replication.
- "Rule D1 forbids text changes" for vr_330651ed (QA-D1).
- Any generalization claim: n = 12 dev pairs, mixed sources, not held-out.
