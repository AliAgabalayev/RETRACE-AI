# A5 acceptance (QA): Ali's half

Owner: qa-engineer. Date 2026-10-09 (Baku). No git, no VLM calls were made for these checks. Scripts used live outside the repo in `/tmp/qa_scripts/` (`recompute.py`, `zipcheck.py`, `zipcheck2.py`); commands below are the exact invocations. ZIPs were extracted into a fresh temp dir and read with `python3 -I`.

## Pre-A3 checks

Verdict: numbers in PITCH_EVIDENCE.md, A1_diagnostic.md and labels_audit.md reproduce exactly from the raw rows. The three demo ZIPs are structurally complete, hashes match, decisions agree and cache status is not falsely "live". Defects found are wording / traceability problems, none changes a number. No blocker.

### 1. Recompute of PITCH_EVIDENCE.md / A1_diagnostic.md

Command: `python3 -I /tmp/qa_scripts/recompute.py` (reads `configs/ali_dev12.json`, `docs/ali/labels_ali.csv`, `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`; truth = rule column, D1 = bug, A1 = clean).

| Check | Result | Evidence |
|---|---|---|
| 12 IDs, no duplicates; label IDs == dev12 IDs | PASS | 12 unique; `set(labels)==set(dev12)` True |
| Each arm has exactly the 12 IDs, no missing, no duplicate, no extra | PASS | A, B, C each: dups [], missing {}, extra {} |
| Truth counts 5 bug (D1) / 7 clean (A1) | PASS | D1: 330651ed, 4b921c5d, d07179d5, fec26436, c1f47c57; A1: the other 7 |
| Arm A: 12 PASS / 0 / 0; bug false-PASS 5/5; clean PASS 7/7; coverage 12/12 | PASS | recompute output |
| Arm B: 8 PASS / 0 FAIL / 4 REVIEW; bug false-PASS 5/5; clean PASS 3/7 (clean REVIEW 4); coverage 8/12 | PASS | recompute output |
| Arm C: 0 / 0 / 12 REVIEW; bug false-PASS 0/5; clean PASS 0/7; coverage 0/12 | PASS | recompute output |
| C truncation: 9 global_change_collapse, 3 none (3 none = 4b921c5d, d07179d5, c1f47c57, all Unity) | PASS | `truncation_cause` counter |
| No REVIEW deleted (B has 4 REVIEW rows, C 12, all in the raw files, all counted in denominators of 12) | PASS | row counts 12/12/12 |
| False-PASS always reported together with coverage | PASS | PITCH sec 4 table and A1 Results table both carry a coverage column; A1 text states "C: 0/5 but coverage 0/12" |
| No arm errors, no mocks | PASS | `error` null for all 36 rows; `is_mock` False for all |
| B and C same model / prompt / config_hash / rules | PASS | both `ollama:qwen2.5vl:3b`, prompt `v9`, config_hash `3a144cfcbb67` (also A), `rule_ids_given == [A1, D1]` for all 36 rows |
| B and C same aligned input | PASS | `b_input = aligned` 12/12; alignment status identical per ID (11 identity, 1 unreliable = ef9b073a, in both) |
| Cache honesty in A1 runs | PASS | all 12+12 rows `cache.status = fresh`; `calls.jsonl` in `artifacts/ali/a1_inputs/a1/*/*`: 80 calls, 0 cache hits, all `is_mock` False |
| Latency claims (B 38-48 s, C 69-160 s) | PASS | min/max/median B 38.1 / 47.8 / 42.2 s; C 68.9 / 159.7 / 79.3 s |
| Localization claims for vr_4b921c5d and vr_d07179d5 | PASS (with note) | proposals R1 [2484,1400,3049,1966] and [1936,1094,2612,2053] equal the cited values. My IoU against the labelled boxes: 0.60 and 0.71. Pitch correctly says "no IoU metric computed"; see D3 for the label-circularity caveat |
| Quoted Qwen texts and decisions (4b921c5d, d07179d5, 09a066d3, 330651ed) | PASS | match `observed_change`, `decision`, run_ids in predictions_C |
| labels_audit.md sensitivity table (330651ed counted clean: 4 bug / 8 clean) | PASS | A: false-PASS 4/4, clean PASS 8/8, coverage 12/12. B: 4/4, 4/8, 8/12. C: 0/4, 0/8, 0/12. All identical to my recompute (`sens` lines) |
| Observation accuracy not claimed | PASS | `obs_review.csv` has 24 rows, `obs_correct` empty; docs say "not scored" |

Remarks (not failures):
- B scene-audit input is not byte-identical to C's. Same size and same prompt, except C's audit prompt line lists `Regions already checked are outlined in yellow ...: R1=[...]` and C's audit PNG draws those outlines (B: "none"). This is by design (the audit is the second stage of the hybrid) but the docs say "same aligned input"; it is the same aligned frames, not the same audit image. Verified by `diff` of `artifacts/ali/a1_inputs/a1/{B,C}/*/SCENE_audit_1.txt`.
- Guard-driven REVIEWs: B has 2 `degraded` rows (59af7164, 43773eb8: "allowed verdict but change_type=... never auto-allowed") and 2 plain REVIEWs (41bab231: scene audit `uncertain`; ef9b073a: alignment `unreliable`, audit said allowed). C has 5 rows with guard errors (330651ed, d07179d5, 59af7164, c1f47c57, ef9b073a). All are kept in the denominators. Do not describe B's 4 REVIEWs as "model failures": two are guard contradictions, one is uncertainty, one is alignment.

### 2. Demo ZIPs

Command: `T=$(mktemp -d); for z in artifacts/ali/demo_zips/*.zip; do unzip -q $z -d $T/$(basename $z .zip); done; python3 -I /tmp/qa_scripts/zipcheck.py $T; python3 -I /tmp/qa_scripts/zipcheck2.py $T`

| Check | allowed_vr_09a066d3 | ambiguous_vr_330651ed | bug_vr_4b921c5d |
|---|---|---|---|
| report.md, analysis.json, evidence.json, rules.yaml present | PASS | PASS | PASS |
| images/ (reference, candidate, aligned_candidate, overlay) | PASS (4) | PASS (4) | PASS (4) |
| crops/ (R1_ref, R1_cand) | PASS (2) | PASS (2) | PASS (2) |
| diagnostics/ (heatmap, overlap_mask) | present (extra) | present | present |
| evidence.json sha256 matches extracted files (6 paths each: 3 images, rules.yaml, 2 crops) | PASS 6/6 | PASS 6/6 | PASS 6/6 |
| decision: evidence.json == analysis.json == report.md heading; reason strings equal | PASS NEEDS_REVIEW | PASS NEEDS_REVIEW | PASS NEEDS_REVIEW |
| `engine_mode` real, `execution_status` complete in both JSONs, `is_mock` False | PASS | PASS | PASS |
| run_id matches `predictions_C.jsonl` | PASS 8a257e | PASS 355ff0 | PASS c4530d |
| cache status honest | PASS `unknown (replay possible)`, `per_stage_recorded: false`, note "do not read this run as live" | same | same |
| No invented root cause / repro steps / build id | PASS: the only hits are the disclaimer "carries no engine/build metadata and no gameplay reproduction steps" and Limitations "No root cause ... known" | PASS | PASS |
| Crop box vs crop size | R1 [0,0,1278,718], crop 1278x718 | R1 [0,0,1279,718], crop 1279x718 | R1 [2484,1400,3049,1966], crop 565x566 (box-exclusive width/height = 565 x 566, correct) |
| Scope section | truncated True, "not assessed" lists only cap-dropped 0 | same | truncated False, nothing not assessed |

Remarks:
- Cache status reads "unknown (replay possible)" although `calls.jsonl` and `predictions_C.jsonl` prove these three runs were fresh (`cache: fresh, hits 0`; 4 calls each for these three runs). That is the conservative choice and is honest; the DEMO notes must say "REPLAY of a saved run" (they do). Not a defect.
- In the bug ZIP the whole-scene audit says verdict `allowed`, "barrels ... in a different position", `extra changes reported: False`, while the region R1 is `uncertain`. The final decision is correctly REVIEW. A viewer of the report can read "Whole-scene audit: allowed" for a true D1 case. Worth saying aloud in the video (see D4).

### 3. DEMO_VIDEO_NOTES.md

| Check | Result | Evidence |
|---|---|---|
| Every shot has a matching artifact / run_id | PASS | run_ids `20261009T112802Z-c4530d`, `20261009T112407Z-355ff0`, `20261009T113543Z-8a257e` exist as `artifacts/<run_id>/` and as ZIPs; B result is `predictions_B.jsonl`; slide sources `A1_diagnostic.md`, `stage1_qwen_vs_gemini.json`, both `*_R1_vlm_input.png` exist |
| Every cached/replay/prerecorded segment labelled | PASS | shots 2,3,4 `REPLAY`, shots 1,5,6,7 `PRERECORDED`; rule "every saved/cached segment carries an on-screen label". Shot 8 closing has segment type `--` (unlabelled, but it is only a caption) |
| Numbers on shots match raw rows | PASS | 5 bug / 7 clean, 5/5, 5/5, 0/5, 0/12, 2 of 2 Gemini; all reproduced |
| "Do NOT say FAIL for 4b921c5d" respected by script text | PASS | script says NEEDS REVIEW |
| UI/CLI references exist | PASS | app.py line 231 "Open a saved run", line 234 "Load saved run"; `cli.py` has `analyze` subparser and `__main__` guard (line 188); scripts `ali_export_evidence.py`, `ali_a1_run.py`, `ali_a1_score.py` exist |
| Stale statement | FAIL (minor) | Notes say "I did not run this script" for `ali_export_evidence.py` and that the ZIP claim must be unzipped first. The ZIPs now exist and were verified above, so update the note |
| Statement of D1 for vr_330651ed | FAIL (important) | see D1 |
| "my own label" wording | FAIL (minor) | see D2 |

### Defects

Priority: important
Case and checkpoint: D1. DEMO_VIDEO_NOTES.md shot 4 (vr_330651ed), run `20261009T112407Z-355ff0`.
Repro: `grep -n "D1 forbids" docs/ali/DEMO_VIDEO_NOTES.md; cat <unzipped ambiguous ZIP>/*/rules.yaml`
Expected / actual: the voice-over says "Rule D1 forbids text changes unless expected". The `rules.yaml` actually used for this pair has D1 = missing/corrupt UI elements, graphical glitches, major scene composition changes, background structure differences. No text rule. (`labels_audit.md` already says "this pair's own D1 list does not include text changes".) The claim is false for the run on screen and would be visible next to the report's rules section. The text rule exists only in the Unity pairs' rules.
Evidence artifact: `rules.yaml` in `ambiguous_vr_330651ed_C_20261009T112407Z-355ff0.zip`.
Likely affected component: docs only (Ali's notes).
Required verification after fix: re-read the shot text against that `rules.yaml`; suggest wording "the human label calls it D1 but this pair's rules do not mention text; truly ambiguous".

Priority: minor
Case and checkpoint: D2. DEMO_VIDEO_NOTES.md shot 2, PITCH sec 1.
Expected / actual: "my own label is [2540,1500,3000,2050]". `labels_ali.csv` provenance for vr_4b921c5d and vr_d07179d5 is `claude_correction; confirmed by Ali`, and the correction was derived from an abs-diff (the same kind of signal the proposal stage uses). Saying "my own label ... the localization matches" overstates independence. Say "label corrected after an abs-diff check" or say IoU 0.60 / 0.71. Same caveat applies to the PITCH sec 1 "proposals matched Ali's boxes" (it is disclosed in sec 6 but not in sec 1).
Required verification after fix: wording only.

Priority: minor
Case and checkpoint: D3. docs/ali/labels_audit.md first row.
Reproduction: count the IDs in the first table row.
Expected / actual: row says "10 pairs" but lists 9 IDs (a981c1d3, 41bab231, 09a066d3, 59af7164, 4255ae09, ef9b073a, 43773eb8, 4b921c5d, d07179d5). 9 + c1f47c57 + fec26436 + 330651ed = 12, so "9 pairs" is correct.
Likely affected component: docs only.

Priority: minor
Case and checkpoint: D4. Label text vs. image, vr_d07179d5, `labels_ali.csv`.
Expected / actual: label says "appearance changed (glass/texture differs)". `docs/ali/a1_evidence/vr_d07179d5_R1_vlm_input.png` shows the booth's top roof and the "TELEPHONE" sign visible BEFORE and absent AFTER (and the booth door frame tilted). Gemini's description matches the image, the label does not. Not a rule-class problem (still D1) but "observation correctness" scoring against this label would mark the correct Gemini text wrong. Fix the free-text before obs_review is ever scored; do not edit the frozen label silently, record it in labels_audit.md.

Priority: minor
Case and checkpoint: D5. Bug ZIP report wording.
Expected / actual: Whole-scene audit prints `Verdict: allowed`, `extra changes outside proposals: False` for a D1 case. Final decision is correct (REVIEW). For the video, say it explicitly; otherwise a viewer sees an "allowed" verdict on the bug. Candidate for a future audit-vs-region disagreement flag; not for today (freeze).

Priority: minor
Case and checkpoint: D6. ZIP Scope section for truncated runs.
Expected / actual: for 09a066d3 and 330651ed `truncated: True` (global_change_collapse) but "NOT assessed" lists only "proposals dropped by the region cap: 0". The report heading does include "proposals truncated" in the decision reason, so no false PASS risk, but the scope section does not say that localization collapsed into one full-frame region.

### Items I could not verify
- Commit hashes cited in A1_diagnostic.md (cf861f1 at 14:47:50, e844aab at 15:38:44) were not checked (no git allowed). The label-mtime warning in `score_raw.md` (labels newer than first prediction) is real and disclosed.
- The label freeze caveat is the largest integrity point of the whole dev12 set: 4 of 5 bug labels (330651ed, 4b921c5d, d07179d5, c1f47c57) were proposed or corrected after model outputs existed. Docs disclose this; it must stay in the pitch.
- Live UI replay was not exercised; only ZIP contents were.
