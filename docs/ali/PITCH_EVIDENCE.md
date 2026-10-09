# Pitch evidence (technical, concise)

Scope: development diagnostic on 12 pairs ("dev12"), 5 bug and 7 clean by Ali's labels, local `qwen2.5vl:3b` (prompt v9, temperature 0). n = 12 is small, mixed-source and was used for the tuning decision D17; it is NOT held-out. The 60-case eval set is a historical regression set only, not a measurement of this build.

Raw sources (cited per claim as short keys):
- A1 = `docs/ali/A1_diagnostic.md`; P = `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`; S = `docs/ali/a1_evidence/score_raw.md`; O = `docs/ali/a1_evidence/obs_review.csv`
- A3 = `docs/ali/A3_review.md` (+ `artifacts/ali/a3/{A,B,C}/predictions.jsonl`); REG = `docs/ali/EXPERIMENT_REGISTRY.md`
- LA = `docs/ali/labels_audit.md`; L = `docs/ali/labels_ali.csv`; QA = `docs/ali/A5_acceptance.md`; D17 = `docs/DECISIONS.md`

## 0. A3 is a replication, not a second sample
A fresh-cache rerun (A3, config `configs/ali_a3_qwen.yaml`, namespace `data/cache_ali_a3`) reproduced A1 on all 36 rows (12 per arm A/B/C): same decision, n_proposals, truncation cause, region boxes and region verdicts; stage-1 text identical in 24/24 VLM rows; 80 fresh VLM calls, 0 cache hits (A3 sec 1-2; REG). Only wall-clock fields differ. Read it as a determinism / regression check (n = 2 runs, same host, temperature 0), not as additional evidence: the effective sample stays 12 pairs. No number below changes between A1 and A3.

## 1. What frozen DINOv2 contributes (operationally)
- Role: localization only. A frozen DINOv2 ViT-S/14 (inference only, no training) compares patch features of reference and aligned candidate and, with a pixel-difference signal, proposes regions (`source: dinov2` or `union` in P).
- Measured on two Unity bug pairs: vr_4b921c5d proposal R1 [2484,1400,3049,1966] vs label [2540,1500,3000,2050]; vr_d07179d5 R1 [1936,1094,2612,2053] vs [1950,1200,2520,2120] (A1 "Failure split"; P arm C). QA-computed IoU 0.60 and 0.71 (QA, "Recompute" table).
- **Independence caveat (QA-D2):** 4 of the 5 bug labels (vr_4b921c5d, vr_d07179d5, vr_c1f47c57, vr_330651ed) were Claude-proposed or Claude-corrected from an abs-diff after balanced-six model outputs existed, and then confirmed by Ali (LA "Independence caveat"; L `label_provenance`). So the IoU 0.60 / 0.71 agreement is not fully independent evidence of localization quality. Say "box agreement with a label that was corrected after an abs-diff check", never "my own independent label".
- Limit: on 9 of 12 pairs (all cutscenes) whole-frame lighting/clothing/pose changes made proposals collapse into one full-frame region ("global-change collapse"; S, A3 sec 3). There DINOv2 gives no useful localization.

## 2. What the VLM does
- For each proposed region it receives paired before/after crops with context and the rules and returns structured JSON (observed change, verdict, rule ids). A second scene-audit call looks at the whole frame. Its text is "VLM-reported, unverified" in the report.
- Measured weakness: on the two Unity bugs Qwen 2.5-VL 3B misdescribed the change ("different texture and lighting effect on the barrels"; "booth replaced by a red mirror") (A1; P).

### Observation accuracy (new signal, with its caveats)
Ali marked the 24 stage-1 observations (12 per arm) y / p / n against the labels (O; A1 "Observation accuracy"):

| Arm | y (strict) | p | n | y+p |
|---|---|---|---|---|
| B full-frame VLM | 1/12 | 3 | 8 | 4/12 |
| C hybrid (region crops + audit) | 1/12 | 8 | 3 | 9/12 |

- Strict target (10/12 y) is met by neither arm.
- Reading: with region crops the VLM moves from mostly wrong (n 8) to mostly partially right (n 3). This is the only measured signal in favour of DINOv2 proposals, and only for the VLM's *observation* text.
- Caveats: one rater (Ali); partial credit is a judgment call; possible anchoring (Ali's marks closely match an example string shown in chat before scoring); n = 12; Claude's independent review disagrees on one row (vr_43773eb8 C: y instead of p, which would make C 2 y / 7 p) (A1; A3 sec 3). Scored on A1 text; A3 text is identical row by row, so the marks carry over by identity, not by a new rating.
- **It did not turn into correct decisions:** C still returns 0 PASS and 0 FAIL (table in section 4). This is not a claim that DINOv2 improves accuracy.

## 3. What code decides
- `src/gameqa/decision.py` `decide()` is deterministic. Policy (D6-D10, `CLAUDE.md`): reliable forbidden change -> FAIL; all stages complete and only allowed changes -> PASS; uncertainty, rule conflict, unreliable alignment, model error, timeout, truncation -> NEEDS REVIEW. A component error never turns a proven FAIL into PASS. The VLM never outputs the final decision.
- Effect visible in the data: the hybrid abstained on all 12 (P arm C; A3 sec 3).

## 4. Measured comparison (n = 12; 5 bug / 7 clean; S, A1, A3 sec 3; identical in A1 and A3)
False-PASS is always read together with coverage.

| Arm | PASS / FAIL / REVIEW | Coverage (PASS+FAIL)/12 | Bug false-PASS (of 5) | Clean PASS (of 7) |
|---|---|---|---|---|
| A pixel diff (threshold 0.782 tuned on dev) | 12 / 0 / 0 | 12/12 | 5/5 | 7/7 |
| B full-frame VLM | 8 / 0 / 4 | 8/12 | 5/5 | 3/7 |
| C hybrid (DINOv2 + VLM + decide) | 0 / 0 / 12 | 0/12 | 0/5 | 0/7 |

In one line: C 0/5 false-PASS at 0/12 coverage; A 5/5 at 12/12; B 5/5 at 8/12. C is "safe" only because it abstains on everything.

Sensitivity, vr_330651ed counted as clean (4 bug / 8 clean; LA; A3 sec 4):

| Arm | Bug false-PASS | Clean PASS | Coverage |
|---|---|---|---|
| A | 4/4 | 8/8 | 12/12 |
| B | 4/4 | 4/8 | 8/12 |
| C | 0/4 | 0/8 | 0/12 |

Conclusion unchanged under the sensitivity: only C avoids false-PASS, at zero coverage. Uncertainty (Clopper-Pearson 95%, A3 sec 3): A/B false-PASS 5/5 lower bound 0.48; C false-PASS 0/5 upper bound 0.52; C coverage 0/12 upper bound 0.26.

Reading: no arm meets all engineering targets (0 bug false-PASS, clean PASS >= 4, coverage >= 6/12, observations 10/12). The two arms with coverage pass every bug; the arm without false-PASS has no coverage. No claim that the hybrid beats the simpler methods.

## 5. Failure example
vr_4b921c5d (Unity, one barrel missing; label D1). Arm C: correct region, VLM says "different texture and lighting effect", verdict uncertain -> `NEEDS_REVIEW: "Needs review: R1: uncertain."` (P, run `20261009T112802Z-c4530d`; same in A3). Arm B on the same pair: PASS ("lighting ... brighter", P arm B). Visual evidence: `docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png`.
- Scene-audit contradiction (QA-D5, in the bug ZIP `report.md`): the whole-scene audit said `allowed` ("barrels ... in a different position", extra changes False) which is wrong for this bug; the region-level verdict was `uncertain`; the region guard caught the contradiction and the final result is NEEDS REVIEW, not FAIL (QA, "Demo ZIPs" remarks and D5).

## 6. Missing cases (state openly)
- No allowed-change PASS from the hybrid: 0/7 clean pairs reached PASS. Example vr_09a066d3 (outfit change): B = PASS, C = REVIEW (global-change collapse) (P).
- No FAIL from any arm on this set: 0/5 bugs produced FAIL.
- Ambiguous case vr_330651ed: the subtitle language changed. This pair's own rules.yaml (cutscene rules) has no text rule, so the label D1 is weakly supported; the rule does not clearly cover the change and label uncertainty is high (QA-D1; LA; ZIP `ambiguous_vr_330651ed_C_20261009T112407Z-355ff0.zip`). It is REVIEW in C, PASS in B and A. Do not describe it as "forbidden by the rules".
- Label caveat: 5 label rows were Claude-proposed corrections confirmed by Ali (3 Unity, vr_330651ed, overlay note on vr_4255ae09); labels were frozen at 15:38 after the first model outputs at 15:21 (S warning; A1 "Limitations"; L). Unity pairs are all bugs, so source is confounded with class.
- Not measured: held-out generalization, live wall-time distribution (CPU reference values: B 37-49 s, C 63-161 s per pair, REG), human usability.
- Report scope: for collapsed runs the demo ZIPs (regenerated after the QA-D6 fix, `artifacts/ali/demo_zips/`) now list "NOT assessed: global change ... collapsed into one full-frame region" in the Scope section (checked by grep of `report.md` in two ZIPs: vr_09a066d3, vr_330651ed).

## 7. Next pilot
- Change one thing: the VLM. Same crop and same stage-1 prompt sent to Gemini `gemini-3.5-flash` described the removal correctly on 2 of 2 pairs (barrel missing; booth roof and TELEPHONE sign missing) vs Qwen 0 of 2 (`stage1_qwen_vs_gemini.json`). n = 2 is a reproducer, not a measurement.
- Blocker: free tier 20 requests/day/model; B+C on 12 pairs needs about 80-120 (D16, D17). Needs a quota/billing decision, not run today.
- Set pass criteria before running (bug false-PASS and coverage on dev12, then a fresh held-out set).

## Wording to use (experiment-tracker's recommended framing, A3 sec 5)
- Supported (dev12, n = 12, one model): localization on the Unity bug pairs matches the labelled boxes (not fully independent labels); the binding constraint is VLM perception; the abstention policy is safe on this set but gives no automatic decision; region crops improve the VLM's partial observation accuracy (9/12 y+p vs 4/12), which has not become better decisions.
- Not supported: that the hybrid improves accuracy, coverage or decisions over the simpler arms; any generalization beyond dev12; any speed-up or QA-workload claim.
- Say: "frozen DINOv2 for localization", "development diagnostic on 12 pairs", "abstains to human review", "A3 replicated A1 exactly".
- Never say: "fine-tuned", "production-ready", "reduces QA workload", "beats the paper", "DINOv2 improves accuracy / is better than a plain VLM".
