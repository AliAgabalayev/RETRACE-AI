# Pitch evidence (technical, concise)

Scope: development diagnostic on 12 pairs ("dev12"), 5 bug and 7 clean by Ali's own labels, local `qwen2.5vl:3b`. n = 12 is small, mixed-source and was used for tuning decisions; it is NOT held-out. Sources: `docs/ali/A1_diagnostic.md` (A1), `docs/ali/a1_evidence/score_raw.md` (S), `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl` (P), `docs/ali/labels_ali.csv` (L), `docs/DECISIONS.md` D17.

## 1. What frozen DINOv2 contributes (operationally)
- Role: localization only. A frozen DINOv2 ViT-S/14 (no training, no fine-tuning) compares patch features of reference and aligned candidate, and with a pixel-difference signal proposes regions (`source: dinov2` or `union` in P).
- Measured on the Unity bug pairs: proposals matched Ali's boxes. vr_4b921c5d: proposal R1 [2484,1400,3049,1966] vs label [2540,1500,3000,2050]; vr_d07179d5: R1 [1936,1094,2612,2053] vs [1950,1200,2520,2120] (A1, "Failure split"; P arm C; L). These are 2 of the 3 non-collapsed Unity pairs, compared by eye/coordinates, no IoU metric computed.
- Limit: on 9 of 12 pairs (all cutscenes) whole-frame lighting/clothing/pose changes made proposals collapse into one full-frame region ("global-change collapse", S column "truncation causes": 9 collapse, 3 none). There DINOv2 gives no useful localization.

## 2. What the VLM does
- For each proposed region it receives paired before/after crops with context and the rules, and returns structured JSON (observed change, verdict, rule ids). A second scene-audit call looks at the whole frame. Its text is "VLM-reported, unverified" in the report.
- Measured weakness: on the two Unity bugs Qwen 2.5-VL 3B misdescribed the change ("different texture and lighting effect on the barrels"; "booth replaced by a red mirror") (A1, P). Observation accuracy was NOT scored (`obs_review.csv` unmarked, S shows "0 marked"), so no accuracy number is claimed.

## 3. What code decides
- `src/gameqa/decision.py` `decide()` is deterministic. Policy (D6-D10, `CLAUDE.md`): reliable forbidden change -> FAIL; all stages complete and only allowed changes -> PASS; uncertainty, rule conflict, unreliable alignment, model error, timeout, truncation -> NEEDS REVIEW. A component error never turns a proven FAIL into PASS. The VLM never outputs the final decision.
- Effect visible in the data: the hybrid abstained on all 12 (P arm C, final decision NEEDS_REVIEW 12/12).

## 4. Measured comparison (n = 12; 5 bug / 7 clean by Ali's labels; S and A1)

| Arm | PASS / FAIL / REVIEW | Coverage (PASS+FAIL)/12 | Bug false-PASS (of 5) | Clean PASS (of 7) |
|---|---|---|---|---|
| A pixel diff (threshold 0.782 tuned on dev) | 12 / 0 / 0 | 12/12 | 5/5 | 7/7 |
| B full-frame VLM | 8 / 0 / 4 | 8/12 | 5/5 | 3/7 |
| C hybrid (DINOv2 + VLM + decide) | 0 / 0 / 12 | 0/12 | 0/5 | 0/7 |

Reading: A and B are unsafe (pass every bug). C is safe on this set but useless as an automatic decision (no PASS, no FAIL). No arm met the engineering targets together; the 10/12 observation target is unscored. No claim that the hybrid is better than the simpler methods.

## 5. Failure example
vr_4b921c5d (Unity, one barrel missing; label D1). Arm C: correct region, VLM says "different texture and lighting effect", verdict uncertain -> `NEEDS_REVIEW: "Needs review: R1: uncertain."` (P, run `20261009T112802Z-c4530d`). Arm B on the same pair: PASS ("lighting ... brighter", `predictions_B.jsonl`). Visual evidence: `docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png`.

## 6. Missing cases (state openly)
- No allowed-change PASS from the hybrid: 0/7 clean pairs reached PASS. Example vr_09a066d3 (outfit change): B = PASS, C = REVIEW (global-change collapse) (P).
- No FAIL from any arm on this set: 0/5 bugs produced FAIL.
- Observation accuracy not scored. Ambiguous case vr_330651ed (subtitle language change; label uncertainty high) is REVIEW in C, PASS in B.
- Label caveat: 5 label rows were Claude-proposed corrections confirmed by Ali; labels finalized 15:38 after the first model outputs at 15:21 (S warning; A1 "Limitations"; `label_provenance` in L).
- Not measured: held-out generalization, live wall-time distribution (A1 gives B about 38-48 s, C about 69-160 s per pair on CPU), human usability.

## 7. Next pilot
- Change one thing: the VLM. Same crop and same stage-1 prompt sent to Gemini `gemini-3.5-flash` described the removal correctly on 2 of 2 pairs (barrel missing; booth roof and TELEPHONE sign missing) vs Qwen 0 of 2 (`stage1_qwen_vs_gemini.json`). n = 2 is a reproducer, not a measurement.
- Blocker: free tier 20 requests/day/model; B+C on 12 pairs needs about 80-120 (D16, D17). Needs quota/billing decision, not run today.
- Pass criteria for the pilot should be set before running (e.g. bug false-PASS and coverage on dev12, then a fresh held-out set).

## Phrases to avoid
Never: "fine-tuned", "production-ready", "reduces QA workload", "beats the paper", "DINOv2 improves accuracy". Say instead: "frozen DINOv2 for localization", "development diagnostic on 12 pairs", "abstains to human review".
