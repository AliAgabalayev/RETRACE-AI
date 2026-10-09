# experiment-tracker-pm status (2026-10-09, after E1/E2/E4)

## Delivered
- `docs/EXPERIMENTS.md`: registry with actual runs, paired comparison, hypothesis verdict, confounds.
- `docs/DATA_CARD.md`: final facts (250 pairs; demo 5 / dev 40 / eval 205; subset-60 = 18 no_bug / 20 cutscene bug / 22 Unity bug; D8 rules; order evidence; sha-grouping limitation).
- `scripts/compare_runs.py` (CPU only): paired stratified bootstrap and false-PASS Wilson CIs; writes `artifacts/eval/paired_comparison.json`.
- `THIRD_PARTY_NOTICES.md` (earlier).

## Hypothesis verdict: NOT SUPPORTED at this operating point (qwen2.5vl:3b CPU, prompt v9, N=60)
Pre-declared rule fires on both triggers: E2 BA 0.488 [0.464, 0.500] is below E1 0.524, and its upper CI bound is 0.50. Paired E2-E1 = -0.036 [-0.083, 0.000]; E2-E4 = +0.103 [-0.028, +0.234] (inconclusive); E4-E1 = -0.139 [-0.270, -0.008].
E2b was NOT run, so "DINOv2 proposals help" is untested in isolation.

## Safety result (what is real)
False PASS on bug pairs: E1 40/42 (95.2%), E4 33/42 (78.6%), E2 1/42 (2.4%, Wilson 0.4-12.3%). Caveat: 53/60 E2 runs were truncated (37 global-change collapse, 16 hit the 8-region cap) and truncation forces NEEDS_REVIEW, so E2 behaves almost like "always NEEDS_REVIEW" (review rate 96.7%, no_bug 18/18 flagged). The safety comes mostly from abstention, not from better understanding.

## Flags for senior-pm
1. E1 threshold provenance: `classical_threshold.json` dev_ids contain 23 IDs that are now in the eval split (2 in the 60-subset, both predicted PASS). Likely produced against an earlier split. Effect on conclusions negligible, but re-tune E1 on current dev (CPU, minutes) before quoting E1 as clean.
2. E2 `run_meta.commit` says `0b3cc1b` although config was frozen later; `config_hash` 8e6c97c0395c is identical in E2 and E4 and is the reliable identity.
3. Source predicts label; 2 question texts; Unity scene groups unknown (sha-grouping only); N = 18 no_bug. Say so in any result slide.

## Ranked next experiments (expected value per cost; do not run VLM jobs while demos use Ollama)
1. **Stronger VLM, same pipeline and same 60 IDs (E2-strong and E4-strong).** Highest value: the verdict is limited by a 3B CPU model that rarely commits. Use a working API key if one exists (lawful, within existing credentials per the brief), else a larger local model only if free RAM allows (currently about 3 GB available of 14 GB, so a 7B is not feasible until other apps close). Cost: 60-100 min local, or minutes by API. Pre-declare the same rule; compare to current E2/E4 in a paired way.
2. **E2b (classical-only proposals + VLM), same 60 IDs.** The only run that isolates DINOv2. Cost about 90-120 min on the 3B CPU model (about 20-35 s per VLM call). Run only after item 1 or when Ollama is free; with the 3B model it is likely to show review rate near 97 % again, so its value is highest together with item 1's stronger VLM.
3. **Calibrate the global-change collapse (CPU/GPU-proposal only, no VLM).** 52 of 53 truncated runs end in NEEDS_REVIEW; measure on dev only how the collapse threshold (10 % area) and the 8-region cap change truncation rate and proposal count, and report a dev-only sweep. Cost: minutes, no Ollama. Any new setting needs a fresh eval run on untouched eval pairs (outside the 60 subset: 145 spare eval pairs), not a re-score of the 60.
4. **Re-tune E1 on the current dev split** (flag 1). Minutes, CPU. Removes a protocol blemish.
5. **E3 with manual region annotations** (about 10 cutscene + 10 Unity pairs, a human draws the changed box). Cost: roughly 30-60 min of human time; enables proposal recall/IoU for DINOv2 vs classical without any VLM, the cleanest test of the proposal half of the hypothesis. Lower priority only because it needs human time.
6. **Larger no_bug sample.** The source has only 26 no_bug; this cannot be fixed by running more. Instead use fixtures or synthetic allowed changes (lighting, weather) as an additional, labelled-synthetic false-positive check.

## Not recommended
More seeds/repeats at temperature 0 (no extra power); further prompt tuning against eval labels (would invalidate the held-out set; use dev only).
