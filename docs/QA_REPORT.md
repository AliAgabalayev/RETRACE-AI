# QA Report (qa-engineer) - final acceptance pass

Date: 2026-10-09. Tree: HEAD 1f81dd2 plus uncommitted post-eval cleanup (D11). Every number below comes from a command actually run or an artifact actually read in this pass. Held-out labels were used only by `scripts/evaluate.py` / `scripts/compare_runs.py` scoring, never at inference (checked: `load_inference_manifest` rejects label keys; `grep eval_labels` over `src/` and `app.py` finds only `src/gameqa/data/`).

## 1. Commands run and results

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | 164 passed, 6 skipped (the 6 are `real_model`), 6.5 s. MOCK / pure logic / synthetic images. |
| `GAMEQA_REAL=1 .venv/bin/python -m pytest -q -m real_model -rA` | 6 passed in 7.3 s: 4x `test_real_smoke` (object_removed, lighting_change, allowed_and_forbidden, identical), `test_real_dinov2_localises_removed_object`, `test_real_vlm_returns_schema_valid_json`. Real DINOv2 and real Ollama qwen2.5vl:3b were used, but 7 s total means the VLM answers came from the disk cache (`data/cache/vlm/`, 790 entries), so this confirms reproducibility, NOT fresh latency. No Ollama RAM failure occurred. |
| Smoke outcomes (`artifacts/qa_smoke/*.json`, SYNTHETIC fixtures, real engines) | object_removed FAIL (R1 [424,181,521,286]); allowed_and_forbidden FAIL; identical PASS (deterministic shortcut, no model); lighting_change NEEDS_REVIEW (R1 uncertain; expected PASS by fixture label, so a miss that errs safe). |
| `.venv/bin/python scripts/ui_smoke.py object_removed` | OK: Analyze -> FAIL rendered, plain rerun did not re-run inference (1 analysis.json), approve gave `v1.png, v2.png` history. Streamlit AppTest with real engines (cache-served, 5 s). |
| CLI repro of vr_bcbcf341 (section 5) | Reproduced PASS, identical proposals/judgments/audit to the original run. Cache-served (9 s). |
| Independent rescoring of E1/E2/E4 from `predictions.jsonl` + `eval_labels.json` | Matches `metrics.json` exactly (section 4). |
| `code-reviewer` agent on `git diff` + decision/pipeline/judge | No blocker; 3 important, 3 minor (section 3). |

## 2. Real vs mock separation

- MOCK (labelled `is_mock=True`, never evidence of model quality): `tests/policy`, `tests/acceptance/test_pipeline_faults.py`, `tests/app`, `StubRealJudge` (test stub posing as validated VLM), `--mock` CLI option, `provider: mock`.
- REAL: `tests/acceptance/test_real_smoke.py`, `tests/vision/test_real_models.py` (gated by `GAMEQA_REAL=1`), E2/E4 runs (all 60 predictions `engine_mode=real`, 60 `complete`), demo runs, `scripts/ui_smoke.py`.
- Fixtures in `data/fixtures/` are SYNTHETIC and say nothing about benchmark accuracy.
- Not covered by any test: stale cache invalidation, duplicate UI submission in a real browser, oversized image.

## 3. Defect table

| ID | Priority | Description | Status / evidence |
| --- | --- | --- | --- |
| QA-D1 | important | allowed verdict citing a deny rule PASSed | RESOLVED (D6); tests pass |
| QA-D2 | minor | allowed without rule/evidence PASSed | RESOLVED (D6) |
| QA-D3 | important | conflicting rules undetected | RESOLVED (D6) |
| QA-D4 | important | translation -> full-frame classical proposal | RESOLVED; test passes without xfail |
| QA-D5 | important | 12 px coin got no proposal | RESOLVED; test passes |
| QA-D6 | important (env) | Ollama "requires more system memory" under parallel load | RESOLVED operationally (D9: serial runs). Not reproduced in this pass, serial use. |
| QA-D7 | medium | allowed verdict citing unknown rule id PASSed | RESOLVED (D9) |
| QA-D8 | medium | reliable forbidden on a conflicted deny rule gave FAIL | RESOLVED (D9) |
| QA-D9 | blocker-class, NOT a code bug | Dangerous false PASS on `vr_bcbcf341` (bug -> PASS) caused by VLM judgment quality | OPEN, known, not fixable by tuning without using an eval label (D11). Repro in section 5. |
| QA-D10 | important | Retry history pollutes `errors`: after attempt 1 fails and attempt 2 succeeds, `RegionJudgment.errors` keeps attempt-1 text (`judge.py` ~274-293, 330), so `is_reliable_forbidden` / `is_acceptable_allowed` reject a valid answer. The good answer is cached and a rerun gets `[]` errors, so first run NEEDS_REVIEW, rerun FAIL/PASS. Safe direction but lost FAILs and non-reproducible runs. Reviewer-found, QA did not reproduce with real Ollama (reasoned from code). | OPEN, owner dl-engineer |
| QA-D11 | important | Uncompared border strip: for ALIGNED status, reference pixels are pasted outside the overlap, so proposals and the scene residual see zero difference there; up to ~15% of the frame (min overlap 0.85) can hide a bug and still PASS, with Coverage implying full coverage (`alignment.py:146-148`). Pre-existing. Reviewer-found, QA did not reproduce end to end. | OPEN, owner dl-engineer / decision.py; suggested fix: review reason or review when overlap < 1 |
| QA-D12 | minor | Provider `mock` + pixel-identical-within-tolerance audit shortcut yields `PASS` with `engine_mode=mock`; the shortcut judgment has `is_mock=False` (`judge.py` ~378-384). Violates "mock never shown as real" in a corner (tiny change under `min_area_px` and `identical_max_px`). | OPEN, owner dl-engineer |
| QA-D13 | minor | Judge exception text (`judge raised X`) is not a component-failure marker, so such a run is labelled real/COMPLETE (still NEEDS_REVIEW). Real `Judge` never raises. | OPEN |
| QA-D14 | minor (model quality) | A "no visible change"/allowed answer with no rule is accepted on a proposed region; before/after agreement is not checked. Documented in MODEL_NOTES. | OPEN |
| QA-D15 | minor (provenance) | `e2_pipeline_subset60/run_meta.json` records commit 0b3cc1b while D10 says config was frozen at c463a07 (E4 records c463a07; both `config_hash` 8e6c97c0395c, identical). Treat E2 commit field as unreliable. | OPEN, docs note |

No open error-to-PASS defect and no forbidden-change miss attributable to code logic was found. QA-D11 is the one plausible code-level false-PASS path; no failing test was written because it was not reproduced end to end by QA in this pass (I did not edit non-test code). senior-pm should decide whether to schedule a reproduction test.

## 4. Evaluation results (held-out, from `artifacts/eval/*/metrics.json`, independently recomputed)

Primary metric: balanced accuracy with NEEDS_REVIEW counted as flagged/FAIL (review->FAIL), with bootstrap CI. Pair-level labels only; no localization IoU (no region annotations). Subset: 60 stratified eval IDs (42 bug / 18 no_bug; 22 Unity all bug, 38 YouTube-Cutscene 20 bug / 18 no_bug). All 60 expected IDs scored, 0 excluded, 0 duplicates.

| Run | Decisions | Confusion (bug P/F/R; no_bug P/F/R) | BA review->FAIL (CI) | Review rate | Notes |
| --- | --- | --- | --- | --- | --- |
| E1 classical, subset60 | 58 PASS / 2 FAIL | 40/2/0 ; 18/0/0 | 0.524 [0.500, 0.560] | 0.00 | bug recall 0.048 |
| E1 classical, full eval 205 | 199 PASS / 6 FAIL | 181/6/0 ; 18/0/0 (187 bug / 18 no_bug) | 0.516 [0.505, 0.529] | 0.00 | threshold re-tuned on final dev (D12) |
| E2 DINOv2 + VLM pipeline, subset60 | 58 REVIEW / 1 FAIL / 1 PASS | 1/1/40 ; 0/0/18 | 0.488 [0.464, 0.500] | 0.967 | coverage 2/60; median 70 s, p90 238 s per pair; 53/60 runs truncated (37 global-change collapse, 16 region cap) |
| E4 VLM-only scene audit, subset60 | 43 PASS / 17 REVIEW / 0 FAIL | 33/0/9 ; 10/0/8 | 0.385 [0.254, 0.516] | 0.283 | 33 of 42 bug pairs PASSed |

Reading: every method is at or below chance (always-FAIL / always-PASS rows are 0.5). E2 cuts false PASS on bug pairs from 33/42 (E4) and 40/42 (E1) to 1/42, but mostly by abstaining (96.7% review, 100% review on no_bug). The hypothesis "DINOv2 proposals help a VLM do rule-aware comparison" is NOT SUPPORTED at this operating point (D11/D12). Only 2 distinct benchmark question texts exist, so rule-awareness is barely exercised. E2b (classical-only proposals + VLM) was NOT run. E3 (proposal recall on dev) is not reported by QA.

Demo split (5 benchmark pairs, `artifacts/demo/demo_split.jsonl`, exists, 5 lines): all 5 NEEDS_REVIEW, engine real/complete. Synthetic real-engine demos (senior-pm status): object_removed FAIL, allowed_and_forbidden FAIL, small_object_removed FAIL, clothing_color_change PASS, lighting_change NEEDS_REVIEW, identical PASS. QA re-confirmed object_removed, allowed_and_forbidden, identical, lighting_change via the real_model tests.

## 5. Known failure with repro: vr_bcbcf341 (dangerous false PASS)

Unity pair, label bug (ground texture missing in candidate), 3840x2160.
```
python3 - <<'E'   # writes rules from manifest record (identical to artifacts/20261009T003250Z-58905e/rules.yaml)
import json,yaml
r=[a for a in json.load(open('data/manifests/inference_manifest.json')) if a['sample_id']=='vr_bcbcf341'][0]
yaml.safe_dump({'rules':r['rules']},open('/tmp/qa_repro/rules_vr_bcbcf341.yaml','w'),sort_keys=False)
E
.venv/bin/python -m gameqa.cli analyze --reference data/work/vr_bcbcf341/reference.png \
  --candidate data/work/vr_bcbcf341/candidate.png --rules /tmp/qa_repro/rules_vr_bcbcf341.yaml --json
```
(If the manifest top level is a dict, take its `records` list; in this repo it is a list.) Expected correct verdict: FAIL or NEEDS_REVIEW. Actual (original run and rerun, identical): `PASS`, engine real/complete, one proposal R1 `[1213,1973,3003,2160]` (correctly covers the road), R1 judged `allowed A1` with evidence "license plate ... more visible", scene audit `allowed A1` "brighter lighting". Policy behaved as designed; the VLM is wrong twice with validated outputs. Rerun was served from the VLM cache, so it proves determinism of the stored answers, not a fresh model sample. Evidence: `artifacts/20261009T003250Z-58905e/`, rerun `artifacts/20261009T071427Z-904723/`. After any fix, re-run this and the 60-pair E2 on a frozen config.

## 6. UI verification limitation

No real browser was used (the Chrome extension was not connected). UI behaviour is verified through `streamlit.testing.v1.AppTest` against `app.py` with REAL engines (`scripts/ui_smoke.py`), plus `streamlit run` starting with a healthy `/_stcore/health` (reported by python-developer; QA did not re-launch it). Not verified: visual layout, box overlays as rendered, file upload widget with a real browser, duplicate-click behaviour, "Reload models" button in a live session.

## 7. Acceptance verdict against brief section 12 (Definition of Done)

| # | Item | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Fresh-process local app via documented command | PARTIAL | README/runbook give `.venv/bin/streamlit run app.py`; AppTest ok; `streamlit run` health ok per other agents; QA did not do a fresh-process launch and no real browser |
| 2 | Upload and ready demo pair selection | PARTIAL | Demo-pair selection exercised by ui_smoke; upload covered at pipeline level (corrupt/missing upload tests), not via browser widget |
| 3 | Editable rules, correct region/evidence display | PARTIAL | Rules editing and report evidence/crops exist in artifacts; rendered overlays not visually verified in a browser |
| 4 | At least one real DINOv2 + real VLM artifact | MET | E2 60 real runs, demo runs, `artifacts/qa_smoke`, real_model tests |
| 5 | Three reproducible demo cases (forbidden, allowed, uncertain/error), synthetic labelled | MET | object_removed FAIL, clothing_color_change PASS, lighting_change / benchmark demos NEEDS_REVIEW; synthetic and labelled |
| 6 | Fail/pass/review policy and error-to-pass regression coverage | MET | 164 tests; no error-to-PASS path found by tests or code review. Caveat: QA-D11 (uncompared border strip) and QA-D12 open |
| 7 | Local report export and audit/history reference update | MET | `report.md` per run; approve v1+v2 history verified by ui_smoke and tests; non-PASS approval needs override |
| 8 | Actual data count/revision/attribution, leak-free manifests | MET | 250 pairs, revision 2afbfdcc..., inference manifest rejects label keys, labels only in eval manifest, no label read in `src/` inference. DATA_CARD present (QA did not audit attribution text) |
| 9 | QA commands/results; measured evaluation or exact reason | MET | This report, section 1 and 4. E2b not run (stated) |
| 10 | Tested environment/model/config versions | PARTIAL | Versions recorded in analysis.json/MODEL_NOTES (DINOv2 hub main, no commit pin; qwen2.5vl:3b id fb90415cde1e; config_hash); E2 run_meta commit field inconsistent (QA-D15) |
| 11 | Stable git checkpoint / versioned snapshot | UNMET (at time of QA) | Working tree has uncommitted changes (cleanup, docs, scripts/ui_smoke.py, compare_runs.py); QA does not commit. senior-pm must commit via git-workflow-master |
| 12 | HANDOFF.md, QA_REPORT, DATA_CARD, MODEL_NOTES, CODE_WALKTHROUGH, DEMO_RUNBOOK | PARTIAL | All exist except `HANDOFF.md` (only `docs/HANDOFF_DRAFT.md`) |

Overall verdict: ACCEPT AS A HONEST PROTOTYPE, NOT AS A WORKING DETECTOR. The end-to-end flow, policy safety and evidence trail are in place; model quality is at chance and the hypothesis is not supported. Unmet: item 11 (commit), item 12 (`HANDOFF.md`). Recommended before the owner demo: commit; write HANDOFF.md; fix or at least document QA-D10 and QA-D11; label every demo of vr_bcbcf341-type cases as the known false PASS. The cleanup diff (D11) introduced no regression (164/6 unchanged, reviewer found it behaviour-neutral).

## Addendum by senior-pm (after this QA pass)
- QA-D10 and QA-D11 were fixed by senior-pm (DECISIONS D13) with regression tests; `pytest -q` → 168 passed, 6 skipped. Not re-reviewed by QA.
