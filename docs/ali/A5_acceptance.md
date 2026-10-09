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
| Observation accuracy | PASS (superseded) | at my first check `obs_review.csv` was unmarked and the docs said "not scored". It is now marked by Ali (16:10): B y1/p3/n8 (y+p 4/12), C y1/p8/n3 (y+p 9/12); strict 10/12 target not met. One rater, possible anchoring, one Claude disagreement (vr_43773eb8 C). Pitch/video must quote these as dev12, n=12, partial credit by hand |

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
Expected / actual: label says "appearance changed (glass/texture differs)". `docs/ali/a1_evidence/vr_d07179d5_R1_vlm_input.png` shows the booth's top roof and the "TELEPHONE" sign visible BEFORE and absent AFTER (and the booth door frame tilted). Gemini's description matches the image, the label does not. Not a rule-class problem (still D1) but "observation correctness" scoring against this label would mark the correct Gemini text wrong. (obs_review is now scored; d07179d5 marks are B n, C p, so check that mark against the image.) Fix the free-text; do not edit the frozen label silently, record it in labels_audit.md.

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

## Continuation QA — 2026-10-09, 17:18 Asia/Baku

Bu section əvvəlki acceptance checks-i qoruyur və current lokal evidence-i yenidən yoxlayır. **0 VLM calls**, **0 git operations**, no experiment/tuning. Read-only recompute script: `/tmp/ali_qa_continuation_20261009.py`; command `.venv/bin/python -I /tmp/ali_qa_continuation_20261009.py` → **exit 0**. Bu scratch script repo delivery-nin hissəsi deyil.

**Verdict: lokal Qwen evidence və regression suite verified; final submission acceptance incomplete.** C2 reported numbers locally verified kimi təqdim edilmir. Mənbə və pending verification gate: [C2_VERIFICATION.md](C2_VERIFICATION.md).

### Raw counts və denominator integrity

Frozen label SHA256 `524583859358b6dcea8250325f88fbc12077cf5f0e3516fbe05f2e94a86bb96d`; dev12 selection SHA256 `28c9f46420320a96845690084a1309ee5ea82e81bd2b097c0965a2a7c14fb030`. 12 selection ID, 12 label ID və hər A1 arm-da 12 row exact equal, unique; 5 D1 bug / 7 A1 clean. No missing, duplicate, extra, row-level error və mock.

| Verified A1 arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Clean PASS |
|---|---|---|---|---|
| A pixel | 12 / 0 / 0 | 5/5 | 12/12 | 7/7 |
| B full-frame Qwen | 8 / 0 / 4 | 5/5 | 8/12 | 3/7 |
| C hybrid Qwen | 0 / 0 / 12 | 0/5 | 0/12 | 0/7 |

All A1 rows config hash `3a144cfcbb67`; B/C model `ollama:qwen2.5vl:3b`, prompt v9. C-də 9 global-change collapse, 3 nontruncated Unity cases. A1 observation marks B y1/p3/n8 → y+p4/12; C y1/p8/n3 → y+p9/12; strict y1/12 each, **one rater / partial credit**. `vr_330651ed` clean sensitivity: A false-PASS4/4, clean PASS8/8, coverage12/12; B4/4,4/8,8/12; C0/4,0/8,0/12. Frozen CSV dəyişdirilməyib.

A3 decisions, proposals, region/audit observation və verdicts A1 ilə **36/36 identical**; latency və run identity ayrıca fərqlənir. A1 və A3 call dumps hərəsi **80 call / 0 cache hit / 0 mock / 0 failed call**. A3 determinism check-dir; effective sample **12** olaraq qalır. Labels A1 start-dan sonra finalized olub; **4/5 bug labels Claude-proposed, Ali-confirmed** caveat qorunur. `vr_c1f47c57`-də missing pedestal D1 qalır; `vr_330651ed` text rule olmayan cutscene-dir.

### Immutable manifests

`sha256sum data/manifests/inference_manifest.json data/manifests/eval_labels.json data/manifests/eval_subset_60.json` nəticəsi expected prefixes ilə match edir:

| File | Full SHA256 |
|---|---|
| inference_manifest.json | `245815f5191e67085b266a80fc4dd4082e348a3a0cc9ac76277e5919404efd6b` |
| eval_labels.json | `a10ab8dd2f936adaef63731f97e1c8ffc59b4b723138c252e0982c8828708585` |
| eval_subset_60.json | `ff765d14428cd94408a45699d9e3fffef911c33b42e3b3de1e67d342eee4f526` |

No `prepare_data.py`; manifests yalnız read/hash edildi.

### Lokal demo ZIP-lər

Üç `artifacts/ali/demo_zips/` archive-i **CRC-valid**, 12 unique/safe member, required report/analysis/evidence/rules + four images + two crops + diagnostics mövcuddur. Hər ZIP-də **6/6 evidence hashes**, image sizes və exclusive bbox crop sizes match-dir; total **18/18**. `evidence.json`, `analysis.json`, report heading/reason və A1 raw run ID/decision eynidir: **hamısı NEEDS_REVIEW**, Gemini FAIL kimi istifadə edilə bilməz. Cache `unknown (replay possible)` / per_stage_recorded=false olaraq qalır; saved-run UI segment REPLAY label-i daşımalıdır.

| Qwen demo archive | Current ZIP SHA256 |
|---|---|
| allowed_vr_09a066d3_C_20261009T113543Z-8a257e.zip | `0c3b5a788cb61e8222c954589fceac81651697005d15a31e0a70afcdab5073ca` |
| ambiguous_vr_330651ed_C_20261009T112407Z-355ff0.zip | `9317fa21fd5ad252ef35c9fa9097bbe3bc98bda6a7b8c8f413ef8b3a0a54a0e2` |
| bug_vr_4b921c5d_C_20261009T112802Z-c4530d.zip | `1ee8852b487b564bfd33445c798e0d4122a0ef51f614d7744e13ccd25b69eeef` |

**Pre-A3 D6 resolved in the current ZIP bytes:** hər iki truncated report və evidence scope artıq global change səbəbilə full-frame collapse və localized region-level check olmadığını açıq yazır. Bu yoxlama current saved exports üçündür; actual UI export ayrıca pending-dir.

C1 `20261009T115633Z-83936b` / config `6cfbba559386` FAIL R1(D1), 4 live calls, CLI25.4442s və replay/download **Celal sənədində verified**; həmin archive Ali host-unda tapılmadı. C2 raw/docs/ZIP search-də yalnız existing `configs/openrouter.yaml` tapıldı; final B/C1P4F7R, coverage5/12 və false-PASS1/5 hələ **reported / pending**.

### Required regression suite

`.venv/bin/python -m pytest -q` → **193 passed, 6 skipped in 5.65 s**, exit0. Bu session-da bir dəfə işlədildi; real-model tests skipped, heç bir real VLM job yoxdur. Celal-in reported C2 **186 passed** başqa checkpoint/host evidence-dir, bu nəticə ilə birləşdirilmir.

### Final acceptance üçün unmet items

- Reconciled Celal integration SHA və ona bağlı C2 raw rows/config/call-cost evidence; C2 table və pedestal false-PASS raw-dan recompute.
- Həmin integrated checkpoint-dən current fresh Streamlit launch; Ali host-unun actual UI export ZIP-ində `evidence.json` və byte/hash/decision verification.
- Final video file, labelled LIVE/REPLAY/PRERECORDED segments, **≤120s** duration; slides və every number/source claim cross-check.
- Second-device check və demo URL varsa onun check-i; final handoff SHA/path status.
- Authorized human submission, confirmation retained **19:30 Asia/Baku**. Bu QA section submission baş verdiyini iddia etmir.

## C2 reconciled evidence QA — 2026-10-09, 17:23 Asia/Baku

Bu update yuxarıdakı **17:18 reported/pending status-u raw counts üçün supersede edir**; actual ZIP/recording/submission gates açılmır. Git-workflow-master exact reconciled delivery SHA **`79a0ef740196cbaa0639579386c6c591d2bfd8ca`**-nı detached `/tmp/ali-c2-79a0ef7.ROajGB/checkout` kimi təsdiqlədi. QA git və VLM əməliyyatı etmədi. Read-only `.venv/bin/python -I /tmp/ali_c2_recompute_20261009.py` → exit0; compact results [C2_RECOMPUTED.json](C2_RECOMPUTED.json), scope [C2_VERIFICATION.md](C2_VERIFICATION.md).

### Raw verification verdict: PASS, bounded to committed records

Hər B/C arm-da 12 unique row, exact dev12/frozen-label set; 5 bugs /7 clean, labels SHA unchanged `524583859358b6dc…`; no missing/duplicate/extra, row-level errors0, mocks0. Model returned/requested80/80 `google/gemini-3.5-flash`; provider OpenRouter, configured reasoning low, prompt v9. C hash **`eaa371255716`**, B hash **`2dfeb64cd673`**; identity configs yalnız artifact/cache namespaces-də fərqlidir.

| Arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Bug FAIL | Clean PASS | Clean false-FAIL |
|---|---|---|---|---|---|---|
| B full-frame | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 2/5 | 0/7 | 2/7 |
| C hybrid | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 3/5 | 0/7 | 1/7 |

**B == C yalnız aggregate counts-dur**, 10/12 per-pair decisions eyni: booth `vr_d07179d5` CFAIL/BREVIEW; `vr_ef9b073a` CREVIEW/BFAIL. “4 bugs caught” wording yanlışdır; C4FAIL-in biri frozen-clean false-FAIL-dir. Clean PASS0/7, false-PASS1/5 və source/class confounding qalır; DINOv2-hybrid advantage demonstrated deyil.

Verified key runs: barrel `vr_4b921c5d` C**FAIL**, `20261009T123704Z-8e4e19`, R1(D1),SCENE(D1); booth C**FAIL**, `20261009T124304Z-580c0b`, B**REVIEW**; missing pedestal `vr_c1f47c57` C/B**PASS**, C run `20261009T124621Z-0b0c2b`. Pedestal false-PASS main failure olaraq demo-da saxlanır. Outfit C REVIEW `20261009T123947Z-584a66`.

**80 unique generation records, HTTP20080/80**, 80 stage rows, cache_hits0; all stage attempts1 → retries0. Cost Decimal sum **$0.2871945** provider-reported: C56calls/$0.1934625, B24calls/$0.0937320; unknown-cost calls0. `calls.attempt` global ordinal1…80-dir, retry sayılmır. Pair float cost roundoff ən çox2e-18-dir; exact per-call sum istifadə edildi. Invoice və full request/image capture label-input audit locally verified deyil. Native export cache unknown qalır; freshness external captures fields əsasında verified-dir.

C9 global-collapse, 7REVIEW hamısı truncated; 5C rows semantic guard errors, provider HTTP failure deyil. Subtitle-as-clean sensitivity false-PASS1/4 both, coverage5/12; CcleanfalseFAIL1/8,B2/8. Frozen labels dəyişdirilməyib; 4/5 assistant-proposed corrections və post-A1 freeze caveat qalır.

**Actual ZIP bytes pending:** committed `zip-verification.json` 12 C IDs/run IDs/decisions raw-la match, Celal80memberhashchecks göstərir; C3 JSON12unchangedZIP SHA verir. Bunlar verification-record checks-dir, local CRC/member hashes deyil. Native B ZIP yoxdur. Actual C2 ZIPs Celal artifact bundle-dan alınmalıdır; daha sonra current UI-exported ZIP checked edilməlidir.

### Exact reconciled checkpoint tests

`PYTHONPATH=/tmp/ali-c2-79a0ef7.ROajGB/checkout/src /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton/.venv/bin/python -m pytest -q` cwd pinned checkout → **194 passed, 6 skipped in 5.14s**, exit0. Bir dəfə həmin SHA-da işlədildi, real-model tests skipped, **0 new model calls**. Initial docs branch193/6 və Celal historical186/6deselected nəticələri bundan ayrıdır.

Provenance: C2 actual inference SHA**c917532…**, freeze implementation SHA**bdd93fb…**, delivery SHA**79a0ef7…** ayrı. LinuxLF config file SHA2e781b54… ilə CelalWindowsCRLF d18ff48f… exact line-ending transform-da match; config contents fərqi yoxdur.

### Remaining gates

- **Recording blocked until separate Celal UI-ready SHA.** `79a0ef7` code/raw source olması bu gate-i açmır; sonradan fresh Streamlit launch və actual UI export ZIP check.
- Actual C2 archive bundle CRC/member/hash verification; full request/image captures varsa inference input label audit.
- Final pitch/video wording audit, generated slides/checks, actual video≤120s və segment labels; second-device/demo URL check.
- Final handoff checkpoint/path və authorized human submission confirmation **19:30**. Final acceptance hələ **incomplete**-dir.

### Pitch/video və slides wording audit — 17:26 continuation

Independent read of final `PITCH_EVIDENCE.md` və `DEMO_VIDEO_NOTES.md`: verified A1/C2 tables, cost split, pairwise differences, exact selected run IDs, C1/C2 distinction, current194/6 versus historical186/6deselected test scope uyğun gəlir. 8 shot intervals continuous0:00–1:53 → **113s planned**, actual exported video duration deyil. Hər shot REPLAY/PRERECORDED label daşıyır; pedestal false-PASS saxlanır, false-PASScoverage ilə yanaşıdır, 4/5label correction və post-A1freeze caveat görünür. **No accuracy/generalization/hybrid-superiority claim**.

Visual inspection: `docs/ali/slides/01_comparison.png`, `02_perception.png`, `03_pedestal_failure.png` və pitch `03_barrel.png`, `06_evidence.png`, `07_next.png`. Metrics/source footers oxunaqlıdır; n=2direct-Gemini perception reproducer C2 batch ilə qarışmır; actual model-input crop UI screenshot kimi göstərilmir; tests və ZIP-transfer pending caption-ları düzgündür. Root-a bir clarity tweak verildi: deck07cost **B+C total$0.2871945 /same12pairs** kimi açıq yazılmalıdır; C-only cost$0.1934625-dir. Documentation owner-a exactinventoryrules/label-input exclusion üçün Celal-report attribution və fullcaptureaudit pending scope refinement verildi. Bu tweaks final-acceptance UI/ZIP/video gates-i açmır.

Documentation input-scope refinement owner tərəfindən tətbiq edildi: exactrules/labelabsence Celal-report attribution-u və fullrequest/imagecapture audit pending-dir; compact JSON link-i əlavə olundu. Export artifact structure: `file` → PDF**7pages**, PPTXtypevalid; `ZipFile.testzip()` → **None**, PPTX**7slideXML entries**. Bu checks slides package-ni təsdiqləyir, finalvideo və actual UI export-u deyil.

Deck07cost clarity fix root tərəfindən regenerated `07_next.png`-də **visually verified**: “B+C:80freshcalls”, “Provider-reported total:$0.2871945”, “Eyni12pair,ikiarm”. Pitch/video/slide claims audit **PASS**; final UI/ZIP/video acceptance hələ pending-dir.

## C4 və repository consolidation QA — 2026-10-09

Latest fetched integration delivery **`68501897746bf674d582fd810cd9d7e2cfb943e6`**; UI code **`be1ea0acce271df994b516f6fa297118e981a3dd`**. Independent QA exact `/tmp/ali-c4-6850189.HyqafP/checkout` source-da offline pytest işlədib: **197 passed, 6 skipped in 8.79s**. Vision/report/decision/pipeline/contracts/storage/canonical OpenRouter config byte hashes `79a0ef7` ilə unchanged-dir. Read-only code review C4 replay early-return, stored rules/run-bound ZIP və FAIL/REVIEW two-confirmation guard üçün blocker tapmayıb. **0 new inference calls**; real-model skips passing sayılmır.

[C4 verification](../C4_DEMO_VERIFICATION.json) və [runbook](../FINAL_DEMO_RUNBOOK.md) **Celal host-da** replay/browser/export readiness göstərir; barrel/subtitle browser ZIP downloads source ilə byte-identical-dir. C4 fresh Analyze edilməyib. OneDrive atomic-rename permission failure və normal TEMP focused27pass ayrıca disclose edilir. Bu evidence Ali local reproduction deyil: Ali active UI hələ79a0ef7, actual C2 bundle/ZIP bytes lokalda absent-dir.

Əvvəlki “UI-ready SHA gözlənir” gate **C4 reported/committed readiness üçün superseded-dir**. Final acceptance hələ incomplete: Ali local fresh C4 launch + actual archive/export check, full captures audit, final≤120s video/narration, second-device check və human19:30submission confirmation qalır. Ali docs→integration→master reviewed PR workflow-u hazırlamaq istəyib; local review/test remote PR approval və ya merge baş verdiyi iddiası deyil.

## C5 combined delivery check — 2026-10-09

Final docs fetched integration **`487f2028461b47013138be124ebf700b86a1c9f1`** üzərinə reconcile edilib. Actual `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/ali-final-pitch.pX8qSQ/checkout/src /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton/.venv/bin/python -m pytest -q`, cwd finaldocs worktree → **199 passed, 6 skipped in 11.20s**, exit0. C4 src ilə source diff (ignored pycache çıxılmaqla) və canonical OpenRouter config diff exit0: vision/model/policy/source unchanged. C5 app delta host-secret missing-key Analyze guard-dur; replay before-inference path saxlanılır. No dependency install/container build/inference/motion render burada edilməyib.

Actual compact barrel replay bytes +4saved requests/responses **`deploy/replay/barrel/`**-də mövcuddur; 20-file manifest/deployment seed regression suite-dədir. Bu complete12ZIP bundle və actual original C2 ZIP-byte transfer deyil. Celal C5 [Docker/CI/browser evidence](../FINAL_GITHUB_STATE.md) öz host/CI attribution-u ilə qalır; Ali local reproduction iddiası yoxdur. Latest combined suite əvvəlki197C4/194C2 nəticələrini ayrı checkpoint kimi saxlayır. Existing master PR#4 və Ali docs PR üçün review/CI/remote merge pending-dir; final acceptance/submission incomplete.
