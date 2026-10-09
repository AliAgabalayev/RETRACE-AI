# Readability feedback (refreshed against commit `c463a07`)

Addressed to the module owners. I edited none of their code. Reviewed by reading; `pytest -q` (163 passed, 6 skipped) and the mock CLI were the only things I ran. Priority: H = can cause a wrong result or wrong docs, M = hard to follow, L = polish.

Fixed since the first review and therefore removed: `alignment.min_error_gain` now in config; the 2x shift evaluation now has a comment; known-translation sign is tested; `_MAX_RAW` truncation now sets `Coverage.truncated`; proposal scores are normalised per source; `_NO_CHANGE` regex and `is_mock_unvalidatable` are gone; `export_report` docstring mentions the ZIP; the cache stores raw replies only and re-validates on every read (so a validator fix does not need a cache bust); `rules_from_question` follows D8.

## Mismatches between docs/config and code (treat as bugs)

| # | Where | Mismatch | Suggested fix | Owner |
| --- | --- | --- | --- | --- |
| 1 | `configs/default.yaml:43` | `vlm.prompt_version: v1` is read by nothing; the real version is `PROMPT_VERSION = "v9"` (`vision/prompts.py:11`, copied into `Judge.prompt_version`, `judge.py:214`). A reader tuning this key changes nothing | delete the key or read it from prompts | python-developer / dl-engineer |
| 2 | `vision/judge.py:200-205` vs `configs/default.yaml:38-48` | code fallbacks differ from the yaml: `timeout_s` 30 vs 75, `crop_max_side` 448 vs 336, `context_max_side` 768 vs 512, `num_ctx` 4096 vs 2048. Deleting a key silently changes behaviour and cache keys | make the fallbacks equal to the yaml, or require the keys | dl-engineer |
| 3 | `decision.py:1-9` | module docstring says "a reliable forbidden judgment -> FAIL, even if other components failed" and omits the D9 rules now in `:111-122` (under unreliable/failed/missing alignment only the `SCENE` judgment counts) and in `is_reliable_forbidden` (known rule IDs, no conflicted deny rule) | extend the docstring with the two caveats | senior-pm (frozen file) |
| 4 | `artifacts/20261008T230650Z-1335da/analysis.json` (`execution_status`, `engine_mode`) | says `degraded` with `errors: []`, but senior-pm records this pair as `real/complete`. The run (03:06:51) predates the engine-mode fix in `pipeline.py:298-303` (edited 03:07). Re-run `artifacts/20261008T230730Z-818bb9` is `complete`/`real` with identical judgments | none in code; do not cite 1335da as "complete" | senior-pm |
| 5 | `pipeline.py:34` | `SCENE_ID = "SCENE"` is defined and unused; the literal `"SCENE"` appears in `decision.py:120` and `judge.py:397,402,411` | import one constant (put it in `contracts.py`) | python-developer |
| 6 | `docs/EXPERIMENTS.md:45,75` | says E1/E2 "not run" and `prompt_version v1`; E1 was run (qa-engineer status) and the frozen prompt is v9 | refresh the registry | experiment-tracker-pm |
| 7 | `docs/DATA_CARD.md:37,39-59` | still describes the interim 20-pair split and the old `Q1` deny rule; D8 made it `A1`/`D1`, final splits are demo 5 / dev 40 / eval 205 | refresh tables | experiment-tracker-pm |
| 8 | `docs/QA_REPORT.md:8,9,11,38,46` | says "xfails QA-D5/D7/D8", "4 skipped", "No real VLM verdict obtained", "E2/E4 not run"; current suite is 163 passed, 6 skipped and D1-D8 are resolved | refresh | qa-engineer |
| 9 | `docs/DECISIONS.md` D4 vs `pipeline.py:114-121` | D4 lists `analyze(pair, cfg, *, judge, extractor)`; the code also has `run_dir=` | add to D4 | senior-pm |
| 10 | `decision.py:158-160` + mock `timeout` | a MOCK timeout run's reason reads "mock judgment (not real inference)"; the timeout text is only in the judgment `errors`. Correct (mock never decides) but a demo viewer may not see why | optional: also list the error | python-developer |
| 11 | `cli.py:122-139`, `app.py:179-197` | `approve` and the UI button accept any run, including MOCK / DEGRADED / FAIL runs. By design (explicit human action) but not stated anywhere except my runbook | state in the brief/README or add a warning when `engine_mode != "real"` | senior-pm decision |
| 12 | `rules.py:42-48` vs `decision.py:70-86` | `validate_rules` already raises on duplicate IDs, so the "duplicate rule id" branch in `find_rule_conflicts` is only reachable by building `Rule` objects directly (tests). Fine as defence in depth; comment it | comment | python-developer |

## vision/alignment.py (dl-engineer)
- M `:99,136,147` (UNRELIABLE results return `ones` as the mask) gives `overlap_fraction = 1.0` on a result meaning "do not trust"; the decision checks `status`, but diagnostics mislead. Add a comment or report the real overlap.
- M `:147` comment says "identity-warped"; the returned image is the resize-only candidate `cand`. Say so.
- M `best` is an untyped 6-tuple unpacked by position (`:117,130,139`); a `NamedTuple` (kind, matrix, warped, valid, residual, quality) is clearer.
- M Magic numbers `2.0` (`:101`), `25.0` and `0.05` (`:134`), `0.5` and `0.05` (`:111`): name them or move to config, state the unit (gray levels 0-255).
- M `_mad_masked` (`:155`) is defined after its use; `align()` has no docstring (state status meanings and that the returned matrix includes the resize step, `Mfull = Mx @ M_resize`).

## vision/features.py (dl-engineer)
- M `patch_to_reference_box` (`:47`) has a garbled docstring and is used only by tests (`tests/vision/test_geometry.py`); say that it is a test/diagnostic helper.
- M `:68-110` hashes the whole checkpoint file at every load to build a version string; hash once and cache, or read the sha from `torch.hub` metadata.
- M The recorded revision is `:main`, not a pinned commit (known, MODEL_NOTES section 1); record the hub commit when available.
- M `patch_grid_distance` (`:128`) uses `assert` for a shape check; asserts vanish under `python -O`.
- L `FeatureExtractor` has no class docstring: say the transformers fallback is a different model (`dinov2-small`) so thresholds tuned on one do not transfer.

## vision/proposals.py (dl-engineer)
- M `_components` and `_merge` pass boxes as lists mixing ints, float and a set (`[x1,y1,x2,y2,score,{source}]`); a tiny dataclass makes `_merge` (`:48-64`) readable.
- M Unexplained constants: containment ratio `0.5` (`:45`), close kernel `int(round(min(H,W)*0.01)) | 1` (`:79`, forces odd, min 3), blur sigma `2.0` (`:97-98`), the `4_000_000` switch (`:30`, avoids a full-image scan on large components).
- L `Coverage.proposals_judged` is set by the pipeline, not here; one line in the docstring.

## vision/judge.py (dl-engineer)
- H `:345` `rule_ids=p["rule_ids"] if p["validated"] else p["rule_ids"]` has identical branches; replace by `p["rule_ids"]`.
- M `_rule_fields(rules, audit)` (`:350-355`) returns `ex_deny` and `ex_other` that nothing uses, and `audit` is unused; remove.
- M `prep_crop` (`:39`) is dead code (no caller); `side_by_side` (`:83`) is used only when `vlm.use_context` is true, which is off by default. Mark or remove so readers do not trace them.
- M `labelled_pair` (`:63-80`) computes `s` twice with a hard-to-read `max(min(...))` expression and then overwrites it when `boxes` is empty; one `if boxes:` branch is clearer.
- M `_ask` (`:274`) calls `validate_response` on a stage-1 reply (which has none of the stage-2 keys) only to detect malformed JSON; use `json.loads` there and say why. It also returns a 3-tuple (`raw|None, errors, latency`) whose meaning lives in a docstring; a small dataclass helps.
- M `validate_response` (`:112-191`) is a long chain of `errs.append` + early returns; split into parse / field checks / rule-consistency checks, and put the table of accepted `allowed` cases in its docstring.
- L `MOCK_BEHAVIORS` is defined three times (`judge.py:20`, `cli.py:15`, `app.py:30`); import one.
- L `_DISAPPEAR` (`:19`) is safety-relevant (it blocks `allowed` for removals); add two example phrases it catches and one it deliberately lets through.

## pipeline.py (python-developer)
- M `_analyze_inner` (`:154-320`, about 165 lines) has numbered stage comments; extract `_load_inputs`, `_run_alignment`, `_run_features`, `_judge_all` so each is testable.
- M `:297-310` `mode` and `status` come from two overlapping if-chains that also reassign `is_mock`; one `_engine_mode_and_status(...)` with a case table in its docstring would remove guesswork.
- M `:335-340` `_is_component_failure` classifies errors by substring ("provider error", "failure:", "timeout", "unavailable"). It silently depends on the exact wording in `judge.py:293,385,412`; a typed error flag on `RegionJudgment` would be robust.
- M `:232` `coverage.model_copy()` has no comment (copied because the pipeline mutates it at `:276,293,297`).
- M When alignment is `UNRELIABLE` the run continues and spends VLM time (about 20-35 s per call) before ending in review; comment that this is intentional (show evidence to the human) or skip the judge.
- L `analyze()` and `_Run` have no docstring listing the artifacts written (see walkthrough section 7). The `deadline_s` check runs between calls only, so a call in flight can overshoot by up to `timeout_s * max_attempts` (150 s now); say so in the config comment.
- L App engines are cached per process (`app.py:39-41`, `st.cache_resource`): if DINOv2 fails to load once, `UnavailableExtractor` (`pipeline.py:323`) is cached and every later run is `degraded` until Streamlit is restarted. Document or add a "reload engines" button.

## storage.py / report.py / cli.py / app.py (python-developer)
- M `approve_reference` (`storage.py:159-215`) mixes validation, version numbering, baseline storing and history writing; `_next_version` is computed twice (`:195`). Compute once.
- L `cli.py:96` re-reads `--ids-file` for every manifest row inside a comprehension; read it once.
- L `cli.py:18-22` loads the config twice when `--mock` is set.

## rules.py / imageio.py / config.py
- L `imageio.load_image` pre-checks the file size before reading; one docstring line saying so.
- L `config.load_config` silently ignores a missing key in an override file; there is no schema check, so a typo in `--config` (for example `proposals.dino_threshold`) changes nothing. Consider warning on unknown keys.

## data/manifest.py (data owner)
- Readable after D8. One docstring example of an ACCEPTABLE/UNACCEPTABLE block would help `_ACCEPTABLE_BLOCK` (`:17`). `src/gameqa/data/prepare.py` (294 lines) and `scripts/evaluate.py` were not reviewed in this pass.

## decision.py (frozen; senior-pm)
- Readable. Beyond mismatch 3, a comment above `decide` listing the order (FAIL first, inputs, identical, reasons) would match the walkthrough.
