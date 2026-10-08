# QA Report (qa-engineer)

Status: in progress, 2026-10-09. All numbers below come from commands actually run in this repo.

## 1. Commands run and results

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | see final run: all pass except 4 skipped real_model, xfails QA-D5/D7/D8 |
| `.venv/bin/python scripts/make_fixtures.py` | 13 synthetic cases in `data/fixtures/` (deterministic, seed 1234; md5 of reference.png stable across runs) |
| `GAMEQA_REAL=1 .venv/bin/python -m pytest tests/acceptance/test_real_smoke.py -q` | 4 passed in 270 s, BUT every real VLM call failed (see 3); outcomes in `artifacts/qa_smoke/*.json`; re-run of object_removed: same |
| `scripts/evaluate.py tune-classical` | threshold 0.0, dev has 2 bug / 0 no_bug (interim 20-sample data): degenerate, flagged in output |
| `scripts/evaluate.py predict --method classical --split eval` + `score` | 13 pairs (10 bug / 3 no_bug): always FAIL, balanced accuracy 0.50 = same as always-FAIL row. Plumbing check only, NOT a result |
| `evaluate.py predict --method pipeline|vlm_only` with mock provider, then resume | predictions NEEDS_REVIEW, labelled mock, resume skipped finished IDs |

## 2. Coverage map (brief section 9 checks)

| Check | Where | Mock / real |
| --- | --- | --- |
| decision policy exhaustive | tests/policy/test_decision.py | pure logic |
| identical, small translation, different dims, large misalignment, coordinate bounds, crop identity | tests/acceptance/test_coordinates.py | real alignment + classical proposals, synthetic images, no model |
| VLM timeout / invalid JSON / unknown rule / uncertain / forbidden / allowed | test_pipeline_faults.py (qa MockJudge and dl-engineer `provider: mock`) | MOCK |
| extractor load failure, judge/audit exception, truncation (max_regions=1), deadline, corrupt/missing upload, empty rules, conflicting rules | test_pipeline_faults.py | MOCK / stub (`StubRealJudge` is a test stub, never real inference) |
| artifacts, report, repeated run IDs, approve_reference history + path traversal | test_pipeline_faults.py | no model |
| real DINOv2 + real Ollama smoke | test_real_smoke.py | REAL (gated) |
| scoring maths | test_evaluate_scoring.py | hand-computed |
| Not yet covered: stale cache, duplicate UI submission (Streamlit), oversized image, real-DINOv2 proposal overlap on fixtures | | |

## 3. Defects

See `docs/status/qa-engineer.md` table. Resolved: QA-D1..D4 (verified by re-running tests). Open: QA-D5 (12 px coin gets no classical proposal), QA-D6 (real VLM unusable while system RAM is exhausted: Ollama returns "model requires more system memory (8.8 GiB) than is available").

Blockers (forbidden-change miss or error-to-pass) found by tests: none open. No test showed an error path yielding PASS.

## 4. Real vs mock

No real VLM verdict has been obtained by QA yet. All real smoke results are NEEDS_REVIEW with provider errors. Nothing here measures model quality. Fixtures are SYNTHETIC and say nothing about benchmark performance.

## 5. Evaluation status

E1 classical run on real data (see docs/status/qa-engineer.md): full eval 205 BA 0.516, subset60 BA 0.524, near chance. E2/E4 not run.

Open additions: QA-D7, QA-D8 (decision policy edge cases, xfail strict tests).


Tooling ready; held-out evaluation not run (interim data of 20 samples, dev single-class, VLM unavailable). Protocol and metrics follow docs/EXPERIMENTS.md. Pending: DATA full subset, `eval_subset_60.json`, memory for Ollama.
