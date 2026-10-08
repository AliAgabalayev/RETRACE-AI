# qa-engineer status (updated after evaluate.py + reviewer pass pending)

## Done
- tests/conftest.py (`real_model` marker, skipped unless GAMEQA_REAL=1), tests/policy/test_decision.py, tests/acceptance/{helpers,test_coordinates,test_pipeline_faults,test_real_smoke,test_evaluate_scoring}.py
- scripts/make_fixtures.py -> data/fixtures/ (13 SYNTHETIC cases incl. extra `translation_object_removed`)
- scripts/evaluate.py (predict / tune-classical / score; methods pipeline, classical, vlm_only)
- Real smoke run recorded in artifacts/qa_smoke/*.json

## Defects
| ID | Sev | Owner | State |
| --- | --- | --- | --- |
| QA-D1 allowed verdict citing deny rule PASSed | important | decision.py | RESOLVED (D6), markers removed, tests pass |
| QA-D2 allowed w/o rule+evidence PASSed | minor | decision.py | RESOLVED |
| QA-D3 conflicting rules not detected | important | decision.py | RESOLVED (also pipeline test passes) |
| QA-D4 translation -> full-frame classical proposal | important | dl-engineer | RESOLVED (test passes without xfail) |
| QA-D5 12 px coin zero proposals | important | dl-engineer | RESOLVED (test passes) |
| QA-D6 real VLM run unusable under memory pressure | important (env) | senior-pm | OPEN, see below |

### QA-D6 real smoke: every real VLM call failed (timeouts / HTTP 500)
Repro: `GAMEQA_REAL=1 .venv/bin/python -m pytest tests/acceptance/test_real_smoke.py -q` (4 passed in 270 s, but outcomes in artifacts/qa_smoke/*.json): object_removed, lighting_change, allowed_and_forbidden all NEEDS_REVIEW because every judgment had errors (ReadTimeout at 30 s x2 attempts; HTTP 500). Direct probe: `curl localhost:11434/api/generate` -> `{"error":"model requires more system memory (9.6 GiB) than is available (9.6 GiB)"}` after 32 s. RAM: 14 GiB total, ~1.5 GiB free (parallel agents + browser). No real VLM verdict has been obtained yet by QA. Safe behaviour confirmed: errors -> NEEDS_REVIEW, never PASS; identical -> PASS without models. Re-run when memory is free; consider 30 s timeout vs cold model load (first call loads 3.2 GB) and `keep_alive`/warm-up call.
Also observed: lighting_change produced one full-frame proposal [0,0,640,360] (global change; expected for global lighting but means region crop == scene).

### QA-D7 (medium) allowed verdict citing nonexistent rule id (or "same/unchanged" escape in judge.py _NO_CHANGE) PASSes
Repro: tests/policy/test_decision.py::test_allowed_citing_unknown_rule_id_is_not_pass (xfail strict). Owner: decision.py (require a cited ALLOW rule present in rules) + judge.py regex tightening.
### QA-D8 (medium) conflicting rules + reliable forbidden citing the conflicted deny rule -> FAIL (brief: conflict -> review). Judgement call; test xfail strict. Owner senior-pm.
### Reviewer note (policy question) FAIL under UNRELIABLE alignment is allowed by current policy and tested; senior-pm to confirm in DECISIONS.

## Evaluation (E1 classical, real data, run by QA)
- Threshold tuned on dev (37 usable: 33 bug / 4 no_bug) -> artifacts/eval/classical_threshold.json (dev BA 0.53, weakly determined). tune-classical now REFUSES single-class dev.
- artifacts/eval/e1_classical_eval_full (205: 187 bug/18 no_bug): PASS 199, FAIL 6; BA(review->FAIL)=0.516 CI [0.505,0.529]; bug recall 0.032, no_bug recall 1.0.
- artifacts/eval/e1_classical_eval_subset60 (42 bug/18 no_bug): BA 0.524, bug recall 0.048. Essentially chance; a fixed global pixel-fraction cannot separate classes at 3840x2160.
- E2 pipeline not run: Ollama needs ~9 GB free system RAM (QA-D6) and dl-engineer latency pending.
- evaluate.py fixes after code-review: resume guard (method/config/ids/threshold), unexpected/missing IDs reported, side stats over scored set.
