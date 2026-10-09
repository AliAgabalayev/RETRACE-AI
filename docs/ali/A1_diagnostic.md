# A1 — perception diagnostic (dev12) and the single intervention decision

Date: 2026-10-09, Baku. Branch `feat/hackathon-vision-evidence`. Owner: Ali (vision/judge/report). Status: **done; decision = freeze Qwen build, no vision change (D17)**.

## Setup (identical across arms)
- Inputs: `configs/ali_dev12.json` (12 dev pairs, seeded selection committed cf861f1 at 14:47:50, before any model output). Rules: each pair's benchmark A1 (ACCEPTABLE) / D1 (UNACCEPTABLE) text (D8).
- Truth: Ali's frozen human labels `docs/ali/labels_ali.csv` (commit e844aab, 15:38:44): 5 forbidden (D1) / 7 allowed (A1). Benchmark labels were not used for scoring.
- Arms: **A** pixel-diff control (dev-tuned threshold 0.782), **B** full-frame VLM (scene audit only), **C** hybrid (alignment → DINOv2 + pixel proposals → per-region VLM → scene audit → `decision.decide`).
- Model: local Ollama `qwen2.5vl:3b` (CPU), prompt v9, config `configs/ali_a1_qwen.yaml`, fresh cache namespace `data/cache_ali_a1` (all calls live; per-call provenance in the input dump `calls.jsonl`). Runner `scripts/ali_a1_run.py`, scorer `scripts/ali_a1_score.py` (tooling commit cac62c7). Wall time: B ≈ 38–48 s/pair, C ≈ 69–160 s/pair.

## Results (n = 12; 5 bug / 7 clean by Ali's labels)

| Arm | PASS / FAIL / REVIEW | Coverage (PASS+FAIL)/N | Bug false-PASS | Clean PASS | Truncation |
|---|---|---|---|---|---|
| A pixel | 12 / 0 / 0 | 12/12 | **5/5** | 7/7 | – |
| B full-frame VLM | 8 / 0 / 4 | 8/12 | **5/5** | 3/7 | none |
| C hybrid | 0 / 0 / 12 | 0/12 | **0/5** | 0/7 | 9 global-change collapse, 3 none |

Engineering targets (not promised): 0/6 bug false-PASS → only C meets it; ≥4/6 clean PASS → no arm safely (A/B pass everything incl. bugs); coverage ≥6/12 → only A/B, which are unsafe; 10/12 correct primary observations → **not met** (see Observation accuracy below). Raw rows: `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`, `score_raw.md`.

## Observation accuracy (stage-1 text vs Ali's labels; scored 16:10)
Ali marked each model observation y (main change described) / p (partial: secondary real change, or right object with wrong description) / n (wrong or invented). Raw: `a1_evidence/obs_review.csv`.

| Arm | y | p | n | y+p |
|---|---|---|---|---|
| B full-frame VLM | 1 | 3 | 8 | 4/12 |
| C hybrid (region crops + audit) | 1 | 8 | 3 | 9/12 |

- Strict target (10/12 'y') is not met by either arm.
- Region crops move the VLM from mostly wrong to mostly partially right (n 8 → 3). This is the one measured signal that DINOv2 proposals help the VLM's *perception*; it does not yet translate into correct automatic decisions.
- Caveats: n = 12; partial credit is a judgment call; Ali's marks closely match an example string shown in chat before scoring (possible anchoring); Claude independently reviewed all 24 rows and disagrees on one (#24 vr_43773eb8 C: y rather than p), which would make C 2 y / 7 p.

## Failure split (C, hybrid)
- **Global-change collapse (9/12, all cutscene pairs):** whole-frame lighting/clothing/pose differences exceed the collapse fraction → one full-frame region, truncated → REVIEW by policy. Safe, but zero coverage on cutscenes.
- **Unity bug pairs (3/12, no truncation):** localization is correct — proposals match Ali's boxes (vr_4b921c5d R1 [2484,1400,3049,1966] vs label [2540,1500,3000,2050]; vr_d07179d5 R1 [1936,1094,2612,2053] vs [1950,1200,2520,2120]). Final REVIEW comes from **wrong perception** caught by guards: Qwen called the missing barrel "a different texture and lighting effect" (uncertain) and the booth "replaced by a red mirror" (disappeared + allowed → contradiction guard → review). No missing proposal, no wrong-rule-mapping case observed on these.
- B (full-frame) passes every bug: at 1032×288 audit resolution the 3B model reports "lighting/colour" for real removals.

## Perception reproducer (model vs crop)
Same composite PNG and same stage-1 prompt that Qwen saw in arm C, sent once to Gemini `gemini-3.5-flash` (free tier, cache off) — `docs/ali/a1_evidence/stage1_qwen_vs_gemini.json`, inputs `vr_4b921c5d_R1_vlm_input.png`, `vr_d07179d5_R1_vlm_input.png`:

| Pair | Qwen 2.5-VL 3B | Gemini 3.5 Flash |
|---|---|---|
| vr_4b921c5d | "different texture and lighting effect on the barrels" | "the large barrel is missing; the stand is empty" |
| vr_d07179d5 | "telephone booth replaced by a red mirror" | "booth roof and TELEPHONE sign are missing" |

The crop clearly shows the change (barrel present → absent). So crop representation is adequate and localization works; the binding constraint is the VLM's perception. n = 2 — a reproducer, not a measurement.

## Decision (D17)
Exactly one intervention was to be chosen. The evidence points to **model/provider change**, but it cannot be run at scale today (Gemini free tier = 20 requests/day/model; B+C on 12 pairs needs ≈80–120; no new paid provider per the assignment). Crop change is not the root cause; loosening the collapse/coverage policy would turn B-like false PASSes into automatic decisions. Therefore: **freeze the current Qwen build for A3**; no vision code change; A2 time goes to report/evidence. The Gemini result is presented as a reproducible next step, not as a measured improvement.

## Demo candidates (human-labelled, comparable views)
1. Clear real bug: **vr_4b921c5d** (Unity, barrel missing; D1, bbox [2540,1500,3000,2050]). Today's build returns REVIEW, not FAIL — show the correct region/crop and the honest REVIEW.
2. Non-identical allowed change: **vr_09a066d3** (GTA V, outfit change; A1). B: PASS, C: REVIEW (global collapse).
3. Ambiguous: **vr_330651ed** (subtitle language changed; D1 vs "expected dynamic text", uncertainty high).

## Limitations
- Labels were finalized at 15:38, after the A1 runs started (15:21). Ali did not see model outputs before confirming. However, 5 rows (3 Unity, vr_330651ed, overlay note on vr_4255ae09) are **Claude-proposed corrections confirmed by Ali**, made by an assistant that had already seen the balanced-six run outputs; marked in `label_provenance`.
- 12 mixed-source dev pairs = development diagnostic, not held-out generalization; Unity pairs are all bugs (source confounds class).
- Observation correctness (obs_review.csv) is not marked; no observation-accuracy number is claimed.
