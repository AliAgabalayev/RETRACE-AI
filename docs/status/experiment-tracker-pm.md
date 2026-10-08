# experiment-tracker-pm status (2026-10-09)

## Delivered
- `docs/EXPERIMENTS.md`: hypothesis, metrics (primary = balanced accuracy with review->FAIL, pre-declared supported/not-supported/inconclusive rule), registry E1, E2, E2b (new ablation), E3, E4, leakage rules, sample-size honesty. All results: "not run".
- `docs/DATA_CARD.md`: verified from the parquet and the 20-pair interim manifests; PENDING marked.
- `THIRD_PARTY_NOTICES.md`: licenses fetched, not guessed.

## Hypothesis status: UNTESTED (no E1/E2 runs under `artifacts/eval/` yet). Recommendation will be added when runs exist.

## Findings senior-pm should act on (data)
1. **Class imbalance.** Source subset = 250 pairs (matches brief): 224 bug / 26 no_bug (10.4%). Verified from `data/raw/metadata/data/test-00000-of-00001.parquet`. Plain accuracy is meaningless (always-FAIL = 89.6%); I use balanced accuracy and per-class recall.
2. **Source is confounded with label.** All 26 no_bug are Youtube-Cutscene pairs; all 171 Unity pairs are bug. Resolution (3840x2160 Unity vs about 1280x720 cutscene) is a shortcut. Results are reported per source; only cutscenes can show a false-positive rate.
3. **Interim dev split is unusable for threshold tuning:** 2 dev pairs, both Unity bug, zero no_bug. Request to python-developer DATA / senior-pm: final dev must include no_bug cutscene pairs (suggest at least 6 of the 26 no_bug in dev, at least 12 in eval, rest in demo/spare) and stratify by source x label. Decision is yours; I did not edit the manifests.
4. **Groups are per-sample** (`g_vr_<id>`), so real scene groups are unknown; Unity pairs share 9 scenes per the paper. Leakage between dev and eval scenes is possible; documented as a limitation.
5. Only 2 distinct rule texts exist (one per source). The manifest rules are Q1 deny = whole question, A1 allow = acceptable list. "Rule-aware" is therefore barely tested; say so in the final report.
6. **Qwen license conflict:** HF repo says Qwen Research License (non-commercial); the Ollama package bundles Apache-2.0 text. Treated as non-commercial until verified (see `THIRD_PARTY_NOTICES.md`).
7. Manifest `sha256_*` is of the raw JPEG (all 40 verified), not of the working PNG.

## Inference budget (estimate; dl-engineer has not yet reported a latency in docs/status; no `dl-engineer.md` exists)
My own measurement (one Ollama `/api/chat` call to `qwen2.5vl:3b`, temp 0, two 448x448 solid-colour images, 556 prompt tokens, 27 output tokens, 3 repeats):
- Cold model load: 68 s (first call 91 s total). Warm calls: 2.5 s, 2.3 s.
- This is a lower bound: real crops carry more image tokens and the judgment JSON has reasoning text. Assumption (not measured): 4-7 s per real call.
Per pair: up to 8 region calls + 1 audit = 9 calls, plus alignment/DINOv2 on possibly 4K inputs (assume 3-5 s) -> planning figure **about 60 s per pair** (range roughly 25-70 s; many pairs will have fewer than 8 regions). Planning only; replace with dl-engineer's measured median.

2 h = 7200 s -> about 120 pairs at 60 s, about 290 at 25 s. GPU is shared, so runs are sequential.

**Recommendation:** eval subset **N = 60 pairs**, chosen by a seeded script before any run, stratified by source x label:
- all available eval-split no_bug cutscene pairs (aim at 12-20 depending on the final split), plus bug pairs in about equal Unity and Cutscene numbers to reach 60 (for example 20 no_bug, 20 cutscene bug, 20 Unity bug).
- Cost: E2 about 60 min; E4 (1 call/pair) about 7 min; E1 minutes on CPU; E2b (optional) another about 60 min; dev tuning of 15 pairs about 15 min plus proposal-only tuning without the VLM (cheap). Total about 2.5 h sequential without E2b, about 3.5 h with E2b.
- If measured latency is above 90 s/pair, cut E2 to N = 40 and drop E2b. If latency is below 30 s/pair, run E2 on all eval pairs available.
- Natural prevalence (90% bug) is deliberately NOT preserved, because it would leave under 10 no_bug pairs; per-class rates are reported instead of accuracy, and the sampling design is stated in every table.
- Recommended order: (1) pilot E2 on the 20 interim pairs for latency and sanity (that run is not a result); (2) E1 and E4 on eval; (3) E2; (4) E2b if time.

## Needs from others
- python-developer DATA: final manifests (update DATA_CARD tables) and an order spot-check; stratified dev per item 3.
- dl-engineer: record median/p90 seconds per pair and VLM calls per pair, `prompt_version`, DINOv2 threshold in the run output.
- qa-engineer: `scripts/evaluate.py` must emit the confusion matrix with NEEDS_REVIEW, the three review mappings, balanced accuracy, Wilson CIs, per-source breakdown, and `run_meta.json`, as specified in `docs/EXPERIMENTS.md` section 2. A paired bootstrap for the E2-minus-E1 difference is also needed; I can run it from the per-pair prediction files if they are saved as `artifacts/eval/<exp>/predictions.json` (`sample_id`, `decision`, `n_regions`, `seconds`).
