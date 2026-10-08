# Experiments

Owner: experiment-tracker-pm. Recommends; senior-pm decides. Last updated 2026-10-09. No experiment results exist yet: every status below is "planned" or "not run". No number in this file comes from a model run unless it is labelled with its source file.

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

All runs use the same eval pair IDs, same rules (generated from the manifest), same seed list, unless stated. Fields `config` / `model` / `prompt` are filled from the run's `artifacts/eval/<exp>/run_meta.json` when it exists (code commit, `configs/default.yaml` hash, data manifest hash, model ids, `prompt_version`).

| ID | What | Data | Config / model / prompt version | Status | Result |
| --- | --- | --- | --- | --- | --- |
| E1 | Classical pixel baseline. Alignment-free grayscale diff, blur, threshold, changed-area fraction; FAIL if fraction >= T, else PASS. No VLM, no rules (cannot read rules). T tuned on dev only. | eval subset; T on dev | `classical_threshold` and area cutoff: PENDING; no model; prompt n/a | not run | `artifacts/eval/e1/` (none yet) |
| E2 | Full pipeline: alignment, DINOv2 (`dinov2_vits14`) + classical proposals (union, max 8) + per-region VLM + whole-scene audit + `decision.py`. | eval subset; thresholds on dev | `configs/default.yaml`; `qwen2.5vl:3b` (Ollama); `prompt_version` v1 (to be recorded from run_meta); DINOv2 threshold PENDING | not run | `artifacts/eval/e2/` (none yet) |
| E2b | Ablation isolating DINOv2: same as E2 with `proposals.sources: [classical]`. This is the arm that actually tests "DINOv2 proposals help"; E2 vs E1 alone confounds proposals with the VLM. | eval subset | as E2 except sources | not run (run if time allows after E2) | `artifacts/eval/e2b/` |
| E3 | Proposal sanity. Does a proposal box overlap the true changed box on synthetic fixtures (true `changed_boxes` in `data/fixtures/*/expected.json`)? Real pairs: visual inspection only, a gallery with a binary "box covers visible change: yes/no/unclear" tally by a human; no IoU from pair labels. | fixtures + <=10 real dev pairs | DINOv2 + classical proposals; no VLM | not run | `artifacts/eval/e3/` |
| E4 | VLM-only whole-image baseline. One call per pair, both full images (downscaled), rule text, no proposals; map JSON `test_pass` to PASS/FAIL, invalid/timeout to NEEDS_REVIEW. Cheap (about 1 call/pair), so recommended after E1/E2. | eval subset | `qwen2.5vl:3b`; prompt version recorded; temp 0 | not run | `artifacts/eval/e4/` |

Run log (one row per run once runs exist; all runs reported, including failures): ID, hypothesis, config hash, data manifest hash, seed, N, runtime, status, notes. Empty today.

Lifecycle: proposed -> designed -> running -> analyzed -> decided. E1-E4 are at "designed".

## 4. Protocol and leakage rules

1. Splits come only from `data/manifests/eval_labels.json` (`demo` / `dev` / `eval`). Demo pairs are never scored. Dev is used for all threshold and prompt choices; eval is touched once per final configuration.
2. Tune on dev only: `dinov2_threshold`, `classical_threshold`, E1's T, prompt wording. Freeze configs (commit hash + `configs/default.yaml` hash recorded) before the first eval run. If a prompt or threshold is changed after seeing eval results, the eval run is discarded from the headline and logged as exploratory.
3. Labels reach only the scoring step. Inference reads `inference_manifest.json`, which has no labels. The eval subset IDs are chosen by a seeded script before any eval result is seen, stratified by `media_source` x label.
4. Decision.py is frozen; no post-hoc changes to the mapping of verdicts to decisions after eval starts.
5. VLM temperature 0; cache enabled does not change results, but cached runs must say so. Repeat runs on the same pair are not independent seeds: Ollama at temperature 0 is nearly deterministic, so extra seeds do not add statistical power; only more pairs do.
6. Report all runs, including errors, timeouts, truncated runs. Excluded pairs are counted and named, never silently dropped.
7. Known leakage/confound risks (see `docs/DATA_CARD.md`): per-sample group IDs mean Unity dev and eval pairs may share a scene; all no_bug pairs are cutscenes (source shortcut: image resolution alone separates most Unity pairs from no_bug); only 2 distinct rule texts exist. Results are therefore reported per source, and rule-awareness is not tested beyond these two texts.
8. Mocks: any run with a mock judge or mock extractor is labelled `mock` and excluded from all registry results.

## 5. Sample size honesty

The eval subset is small (recommended N is in `docs/status/experiment-tracker-pm.md`; interim data has only 13 eval pairs, 10 bug and 3 no_bug). Consequences:
- Report Wilson 95% intervals for every proportion (per-class recall, review rate, coverage, decided accuracy). Example of the width, computed from the formula: 3 correct out of 3 has Wilson 95% CI 0.44 to 1.00; 10 of 20 has 0.30 to 0.70.
- Balanced accuracy and the E2-minus-E1 difference use a stratified percentile bootstrap (resample pairs within class, 10,000 resamples, fixed seed) on the same pairs; the pairwise comparison is paired, not two independent samples.
- Default design target is 95% confidence and 80% power, but a formal power calculation is not possible before knowing the pairwise disagreement rate; as a rough indication (not computed), detecting a moderate paired difference needs tens of pairs per class, while the no_bug class has only 26 pairs in the entire source subset. This evaluation therefore cannot reach that power on the no_bug side. Treat it as a smoke test: it can reveal a gross failure or a gross advantage, not a modest effect. No multiple-comparison correction is applied to the headline (one pre-declared contrast: E2 vs E1); contrasts E2 vs E2b and E2 vs E4 are labelled exploratory and, if all three are quoted, use Holm correction.
- Trade-off made for speed: single config per method, no cross-validation, no repeated splits.

## 6. Results

None. E1, E2, E2b, E3, E4 are not run. This section is updated from `artifacts/eval/` when runs exist, with counts, CIs and a recommendation (supported / not supported / inconclusive). Until then the hypothesis status is **untested**.
