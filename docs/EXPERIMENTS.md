# Experiments

Owner: experiment-tracker-pm. Recommends; senior-pm decides. Last updated 2026-10-09 (after E1, E2, E4 runs). Every number below comes from `artifacts/eval/*/predictions.jsonl`, `metrics.json` or `artifacts/eval/paired_comparison.json` (produced by `scripts/compare_runs.py`, CPU only). E2b and E3 were NOT run.

## 1. Hypothesis

**Problem.** Pixel differences alone cannot tell an allowed change (lighting, weather) from a bug. A VLM given two whole screenshots may overlook small changes.

**Hypothesis (from brief section 1; tested, not assumed).** DINOv2 patch-feature change proposals help a VLM do rule-aware comparison: the full pipeline (E2) classifies pairs better than (a) a classical pixel-difference baseline (E1) and, where run, (b) the same pipeline without DINOv2 proposals (E2b) and (c) a whole-image VLM-only call (E4). No accuracy target and no claim of beating the paper (the 45.2% o4-mini figure is not a bound or target).

**Unit of analysis:** one image pair. Ground truth is pair-level `bug`/`no_bug` (see `docs/DATA_CARD.md`). No localization IoU is computed from it.

## 2. Metrics

Prediction values: `PASS`, `FAIL`, `NEEDS_REVIEW` (plus `ERROR`/timeout recorded and counted as `NEEDS_REVIEW`; never dropped). Truth: `bug` = should not pass; `no_bug` = acceptable.

Always reported (all from the 2x3 confusion matrix truth x {PASS, FAIL, NEEDS_REVIEW}):
1. Confusion matrix with the NEEDS_REVIEW column.
2. Review rate = NEEDS_REVIEW / N, and decision coverage = decided / N (decided = PASS or FAIL), per class.
3. Decided-pair accuracy = correct decided / decided (PASS on no_bug, FAIL on bug). Always shown next to coverage; never alone.
4. Bug precision and recall under three explicit review mappings:
   - **M-flag (review -> FAIL):** prediction positive = FAIL or NEEDS_REVIEW. This is "what a human would be asked to look at".
   - **M-pass (review -> PASS):** positive = FAIL only.
   - **M-exclude:** NEEDS_REVIEW removed (equals decided-pair view), with the exclusion count printed.
5. Per-class recall (bug recall, no_bug recall) and balanced accuracy = mean of the two (class prevalence is 90% bug in the source; plain accuracy is misleading).
6. Latency per pair: median, p90, max seconds, and VLM calls per pair; excluded/error counts.
7. Reference points: "always FAIL", "always NEEDS_REVIEW" and "always PASS" scored on the same IDs.
8. Breakdown by `media_source` (Unity vs Cutscene), because source is confounded with label (all no_bug are cutscenes).

**Primary metric:** balanced accuracy under **M-flag** (review -> FAIL) on the eval subset. Rationale: review cases stay in the denominator, a trivial "always flag" system scores exactly 0.50, so any value above 0.50 means the system separates the classes. **Secondary:** M-pass balanced accuracy, bug recall/precision, decided-pair accuracy + coverage, review rate, latency.

**Pre-declared decision rule (set before any run):**
- *Supported* if E2 primary metric minus E1 primary metric has a 95% bootstrap CI entirely above 0 AND E2's primary lower CI bound is above 0.50.
- *Not supported* if E2's point estimate is below E1's, or E2's upper CI bound is at or below 0.50.
- *Inconclusive* otherwise (expected outcome at this sample size; see section 5).
- Practical significance: a difference below 5 balanced-accuracy points is reported as negligible even if the CI excludes 0.

## 3. Registry

All runs use the same 60 eval pair IDs (`data/manifests/eval_subset_60.json`: 18 no_bug / 20 cutscene bug / 22 Unity bug) and the same rules (A1 allow + D1 deny, per D8), except E1-full. VLM temperature 0.

| ID | What | Config / model / prompt (from run_meta.json) | Status | N | Artifacts |
| --- | --- | --- | --- | --- | --- |
| E1 | Classical pixel baseline: grayscale diff, `pixel_thr` 25, changed-area fraction; FAIL if fraction >= T else PASS. No rules, no VLM. T = 0.7821 tuned on dev (`classical_threshold.json`, dev balanced accuracy 0.53). | commit `3022ec8 [was 0b3cc1b]`, no model, no prompt | **done** | 60 (subset) and 205 (full eval split) | `artifacts/eval/e1_classical_eval_subset60/`, `.../e1_classical_eval_full/` |
| E2 | Full pipeline: alignment, DINOv2 + classical proposals (max 8) + per-region VLM + whole-scene audit + `decision.py`. | commit recorded `3022ec8 [was 0b3cc1b]`; `config_hash` 8e6c97c0395c; `ollama:qwen2.5vl:3b` (CPU); prompt v9; `dinov2_vits14` weights_sha256 b938bf1bc15c (CUDA, fp32); DINOv2 threshold 0.35; timeout 75 s, 2 attempts; global-change collapse at >=10 % area. Run 2026-10-08 23:08Z to 2026-10-09 01:03Z, not resumed. | **done** | 60 | `artifacts/eval/e2_pipeline_subset60/` |
| E2b | Ablation isolating DINOv2: E2 with classical-only proposals. | n/a | **NOT RUN** | - | - |
| E3 | Proposal sanity (proposal box vs true changed box). | n/a | **NOT RUN** (needs manual region annotations; pair labels cannot give IoU) | - | - |
| E4 | VLM-only: one whole-scene audit call per pair, no proposals. | recorded commit `58ba189 [was c463a07]`; `config_hash` 8e6c97c0395c (same as E2); `ollama:qwen2.5vl:3b`; prompt v9. Resumed after power loss at 50/60 (D11); same frozen config. | **done** | 60 | `artifacts/eval/e4_vlm_only_subset60/` |

Note on E2's recorded commit (`3022ec8 [was 0b3cc1b]`): the run was launched from a working tree ahead of that commit (D10 freezes config at the later commit). The identical `config_hash` for E2 and E4 is the reliable identity check; the commit field alone is not.

Lifecycle: E1, E2, E4 analyzed; hypothesis verdict below ("decided" rests with senior-pm). E2b, E3 designed, not run.

## 4. Protocol and leakage rules

1. Splits come only from `data/manifests/eval_labels.json` (`demo` / `dev` / `eval`). Demo pairs are never scored. Dev is used for all threshold and prompt choices; eval is touched once per final configuration.
2. Tune on dev only: `dinov2_threshold`, `classical_threshold`, E1's T, prompt wording. Freeze configs (commit hash + `configs/default.yaml` hash recorded) before the first eval run. If a prompt or threshold is changed after seeing eval results, the eval run is discarded from the headline and logged as exploratory.
3. Labels reach only the scoring step. Inference reads `inference_manifest.json`, which has no labels. The eval subset IDs are chosen by a seeded script before any eval result is seen, stratified by `media_source` x label.
4. Decision.py is frozen; no post-hoc changes to the mapping of verdicts to decisions after eval starts.
5. VLM temperature 0; cache enabled does not change results, but cached runs must say so. Repeat runs on the same pair are not independent seeds: Ollama at temperature 0 is nearly deterministic, so extra seeds do not add statistical power; only more pairs do.
6. Report all runs, including errors, timeouts, truncated runs. Excluded pairs are counted and named, never silently dropped.
7. Known leakage/confound risks (see `docs/DATA_CARD.md` and section 6.6): groups are shared-reference-sha groups only (real scene groups unknown); all no_bug pairs are cutscenes; only 2 distinct rule texts exist. Results are reported per source.
8. Mocks: any run with a mock judge or mock extractor is labelled `mock` and excluded from all registry results.

## 5. Sample size honesty

The eval subset is small (final: N = 60, 42 bug / 18 no_bug; the whole eval split has only 18 no_bug). Consequences:
- Report Wilson 95% intervals for every proportion (per-class recall, review rate, coverage, decided accuracy). Example of the width, computed from the formula: 3 correct out of 3 has Wilson 95% CI 0.44 to 1.00; 10 of 20 has 0.30 to 0.70.
- Balanced accuracy and the E2-minus-E1 difference use a stratified percentile bootstrap (resample pairs within class, 10,000 resamples, fixed seed) on the same pairs; the pairwise comparison is paired, not two independent samples.
- Default design target is 95% confidence and 80% power, but a formal power calculation is not possible before knowing the pairwise disagreement rate; as a rough indication (not computed), detecting a moderate paired difference needs tens of pairs per class, while the no_bug class has only 26 pairs in the entire source subset. This evaluation therefore cannot reach that power on the no_bug side. Treat it as a smoke test: it can reveal a gross failure or a gross advantage, not a modest effect. No multiple-comparison correction is applied to the headline (one pre-declared contrast: E2 vs E1); in the executed analysis E2 vs E4 and E4 vs E1 were also computed, so a Bonferroni-3 (98.3%) CI is reported next to the 95% CI; E2 vs E2b was not run. The bootstrap here uses 10,000 resamples (`scripts/compare_runs.py`); `metrics.json` CIs from `evaluate.py` use 2,000, so the single-method CIs differ slightly in the third decimal.
- Trade-off made for speed: single config per method, no cross-validation, no repeated splits.

## 6. Results

Source: `python3 scripts/compare_runs.py` (10,000 paired stratified bootstrap resamples, seed 0) and the `metrics.json` files. N = 60 (42 bug, 18 no_bug). Primary metric = balanced accuracy with review -> FAIL (flag = decision other than PASS).

### 6.1 Per method

| Method | PASS / FAIL / REVIEW | Primary BA (95% bootstrap CI) | Bug false PASS (Wilson 95%) | no_bug flagged (FAIL or REVIEW) | Review rate | Median s/pair |
| --- | --- | --- | --- | --- | --- | --- |
| E1 classical | 58 / 2 / 0 | 0.524 [0.500, 0.560] | **40/42 = 95.2%** [84.2, 98.7] | 0/18 | 0.0% | 0.03 |
| E2 pipeline | 1 / 1 / 58 | 0.488 [0.464, 0.500] | **1/42 = 2.4%** [0.4, 12.3] | 18/18 | 96.7% | 70.5 |
| E4 VLM-only | 43 / 0 / 17 | 0.385 [0.254, 0.516] | **33/42 = 78.6%** [64.1, 88.3] | 8/18 | 28.3% | 42.7 |
| (always NEEDS_REVIEW, reference) | 0 / 0 / 60 | 0.500 | 0/42 = 0% | 18/18 | 100% | - |

E1 on the full eval split (205 pairs, 187 bug / 18 no_bug): BA 0.516 [0.505, 0.529]; false PASS 181/187 = 96.8%; 6 FAIL, 199 PASS. Same picture as the subset.

### 6.2 Paired contrasts (same 60 IDs, difference in primary BA)

| Contrast | Diff (95% CI) | Bonferroni-3 98.3% CI | Bug pairs: PASS in A only / B only | Exact McNemar p (false PASS) | Cutscene-only BA diff |
| --- | --- | --- | --- | --- | --- |
| E2 - E1 (pre-declared headline) | -0.036 [-0.083, 0.000] | [-0.095, 0.000] | 0 / 39 | 3.6e-12 | 0.000 |
| E2 - E4 | +0.103 [-0.028, +0.234] | [-0.052, +0.262] | 0 / 32 | 4.7e-10 | +0.022 |
| E4 - E1 | -0.139 [-0.270, -0.008] | [-0.298, +0.020] | 1 / 8 | 0.039 | -0.022 |

Reading: no contrast shows a BA gain for E2. E2 vs E4 is inconclusive on BA (CI spans 0). E4 is below chance on BA (point 0.385, CI reaches 0.516) because it passes most bugs and also flags 8/18 clean pairs; E4-E1 is marginal and not significant after correction. Differences below 5 BA points are negligible by the pre-declared rule in any case.

### 6.3 Per media_source

| Method | Unity bug: false PASS (n=22) | Cutscene bug: false PASS (n=20) | Cutscene no_bug flagged (n=18) | Cutscene BA |
| --- | --- | --- | --- | --- |
| E1 | 20/22 [72.2, 97.5] | 20/20 [83.9, 100] | 0/18 | 0.500 |
| E2 | 1/22 [0.8, 21.8] | 0/20 [0.0, 16.1] | 18/18 | 0.500 |
| E4 | 21/22 [78.2, 99.2] | 12/20 [38.7, 78.1] | 8/18 | 0.478 |

Unity has no no_bug, so BA is undefined there. On cutscenes, the only source with both classes, every method scores about 0.50: none separates bug from no_bug above chance.

### 6.4 E2 mechanics (why the review rate is 97%)

- 53/60 runs were `truncated`: 37 collapsed to one full-frame region (global-change rule, >=10 % of valid area above the DINOv2 threshold) and 16 hit the 8-region cap. Truncation forces NEEDS_REVIEW (never auto-PASS). Of the 7 non-truncated runs: 1 PASS (the false PASS), 6 NEEDS_REVIEW. Of the 53 truncated: 52 NEEDS_REVIEW, 1 FAIL.
- Therefore the low false-PASS rate is produced mostly by the truncation guard (abstention), not by proposals informing the VLM. E2 is practically identical to the "always NEEDS_REVIEW" reference row (BA 0.500, 0 false PASS), plus one correct FAIL (`vr_36133e80`) and one false PASS (`vr_bcbcf341`, D11).
- All 60 runs: `engine_mode` real, `execution_status` complete, 0 pipeline errors. Mean 3 regions/pair; mean latency 115.7 s, median 70.5 s, p90 238 s.

### 6.5 Hypothesis verdict

**Pre-declared rule applied to E2 vs E1:** "Not supported if E2's point estimate is below E1's, or E2's upper CI bound is at or below 0.50." Both triggers fire (E2 0.488 < E1 0.524; E2 upper bound 0.500). **Verdict: NOT SUPPORTED** at this operating point (qwen2.5vl:3b on CPU, prompt v9, 60 pairs).

Limits of that verdict:
- It is a verdict on the configured system, not on the idea. The 3B VLM almost never commits, so the test has little power to show a benefit of proposals.
- The specific claim "DINOv2 proposals help" is **untested in isolation**: E2b was not run, so E2 vs E1 confounds proposals with the VLM. What E2 vs E4 tests is "proposals + per-region validation + truncation guard vs one whole-scene call": BA inconclusive (+0.10, CI spans 0), false PASS sharply lower (1/42 vs 33/42), but mostly via abstention (6.4).
- The safety finding is real but not evidence of understanding: always-NEEDS_REVIEW has the same safety and BA. A useful system must lower the review rate while keeping false PASS low; E2 did not show that.

### 6.6 Confounds and threats to validity

1. **Source predicts label** (all Unity pairs are bug; all no_bug are cutscenes). Only cutscenes can show a false-positive rate; there N = 20 bug + 18 no_bug.
2. **Only 2 distinct question texts**, one per source. Rule-awareness is not exercised; A1/D1 are fixed. Multi-rule logic is covered by synthetic fixtures only.
3. **Groups.** Group = shared reference image sha (128 groups; 9 Unity scenes in the paper). The 60-pair subset has 55 groups (max 3 pairs/group). The bootstrap resamples pairs, not groups, so CIs are somewhat optimistic for Unity. Same-scene-different-sha leakage cannot be excluded.
4. **Tiny N.** 18 no_bug; Wilson CI for 0/18 or 18/18 is [0, 17.6] / [82.4, 100]. Only gross effects are detectable. Single config per method; temperature 0 means extra seeds add no power.
5. **E1 threshold provenance flag.** `classical_threshold.json` lists 37 "dev" IDs, of which 23 are in the current `eval` split (2 of them, `vr_2b527a6b` and `vr_334bbcc8`, are in the 60-pair subset; both were predicted PASS). The threshold file was probably produced against an earlier split; this is not resolved. Impact on conclusions is negligible (E1 is at chance and could only be flattered), but it violates protocol rule 1 and should be re-tuned on the current dev split (40 pairs, 6 no_bug) before E1 is quoted as clean.
6. **Prompt iteration.** Prompt v9 and the collapse rule were developed on dev + fixtures only, before E2 (D10); no change after eval results (D11). Not tuned on eval labels.
7. **One shared VLM, one shared quantised 3B model** in E2 and E4; results do not transfer to a stronger VLM.

### 6.7 Recommendation to senior-pm

**NO-GO on claiming that DINOv2 proposals improve rule-aware accuracy.** GO on presenting the pipeline as a conservative triage tool: it almost never passes a bug (1/42), at the cost of reviewing ~97 % of pairs; report degraded/abstaining behaviour honestly. Next experiments are ranked in `docs/status/experiment-tracker-pm.md`.
