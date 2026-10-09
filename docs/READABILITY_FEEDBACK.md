# Readability feedback (refreshed against the post-D11 working tree)

Addressed to the module owners. I edited none of their code. Reviewed by reading; `pytest -q` (164 passed, 6 skipped, 5.0 s) and the mock CLI were the only things I ran. Priority: H = can cause a wrong result or wrong docs, M = hard to follow, L = polish.

Fixed since the first review and therefore removed: `alignment.min_error_gain` now in config; the 2x shift evaluation now has a comment; known-translation sign is tested; `_MAX_RAW` truncation now sets `Coverage.truncated`; proposal scores are normalised per source; `_NO_CHANGE` regex and `is_mock_unvalidatable` are gone; `export_report` docstring mentions the ZIP; the cache stores raw replies only and re-validates on every read (so a validator fix does not need a cache bust); `rules_from_question` follows D8.

Resolved by D11 and removed from this file: yaml `vlm.prompt_version` dead key; `Judge` fallback defaults differing from the yaml; `decision.py` docstring now states the D9 caveats; `SCENE_ID` unused constant (now `contracts.SCENE_REGION_ID`, used by `decision.py` and `judge.py`); mock review reason now includes the injected error; `approve` of non-PASS / non-real runs is guarded (`--force`, override checkbox, README/walkthrough state it); judge.py identical-branch expression, unused `_rule_fields` outputs and dead `prep_crop`; app engine cache stuck in `degraded` after a load failure ("Reload models" button); `docs/EXPERIMENTS.md` and `docs/DATA_CARD.md` registry/tables refreshed by their owner.

## Mismatches between docs/config and code (treat as bugs)

| # | Where | Mismatch | Suggested fix | Owner |
| --- | --- | --- | --- | --- |
| 1 | `artifacts/20261008T230650Z-1335da/analysis.json` (`execution_status`, `engine_mode`; I did not re-open it after D11) | says `degraded` with `errors: []`, but senior-pm records this pair as `real/complete`. The run (03:06:51) predates the engine-mode fix in `pipeline.py:297-302` (edited 03:07). Re-run `artifacts/20261008T230730Z-818bb9` is `complete`/`real` with identical judgments | none in code; do not cite 1335da as "complete" | senior-pm |
| 2 | `docs/QA_REPORT.md:8,9,37,41,46` | (still stale when I checked; qa-engineer is working on it) says "xfails QA-D5/D7/D8", "4 skipped", "No real VLM verdict obtained", "E2/E4 not run"; current suite is 164 passed, 6 skipped and D1-D8 are resolved | refresh | qa-engineer |
| 3 | `docs/DECISIONS.md` D4 vs `pipeline.py:113-120` | D4 lists `analyze(pair, cfg, *, judge, extractor)`; the code also has `run_dir=` | add to D4 | senior-pm |
| 4 | `rules.py:42-48` vs `decision.py:75-92` | `validate_rules` already raises on duplicate IDs, so the "duplicate rule id" branch in `find_rule_conflicts` is only reachable by building `Rule` objects directly (tests). Fine as defence in depth; comment it | comment | python-developer |

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
- L `side_by_side` (`:67`) is used only when `vlm.use_context` is true, which is off by default; mark it as optional so readers do not trace it.
- M `labelled_pair` (`:47-65`) computes `s` twice with a hard-to-read `max(min(...))` expression and then overwrites it when `boxes` is empty; one `if boxes:` branch is clearer.
- M `_ask` (`:259`) calls `validate_response` on a stage-1 reply (which has none of the stage-2 keys) only to detect malformed JSON; use `json.loads` there and say why. It also returns a 3-tuple (`raw|None, errors, latency`) whose meaning lives in a docstring; a small dataclass helps.
- M `validate_response` (`:96-177`) is a long chain of `errs.append` + early returns; split into parse / field checks / rule-consistency checks, and put the table of accepted `allowed` cases in its docstring.
- L `MOCK_BEHAVIORS` is defined three times (`judge.py:20`, `cli.py:15`, `app.py:30`); import one.
- L `_DISAPPEAR` (`:19`) is safety-relevant (it blocks `allowed` for removals); add two example phrases it catches and one it deliberately lets through.

## pipeline.py (python-developer)
- M `_analyze_inner` (`:154-320`, about 165 lines) has numbered stage comments; extract `_load_inputs`, `_run_alignment`, `_run_features`, `_judge_all` so each is testable.
- M `:297-310` `mode` and `status` come from two overlapping if-chains that also reassign `is_mock`; one `_engine_mode_and_status(...)` with a case table in its docstring would remove guesswork.
- M `:335-340` `_is_component_failure` classifies errors by substring ("provider error", "failure:", "timeout", "unavailable"). It silently depends on the exact wording in `judge.py:293,385,412`; a typed error flag on `RegionJudgment` would be robust.
- M `:232` `coverage.model_copy()` has no comment (copied because the pipeline mutates it at `:276,293,297`).
- M When alignment is `UNRELIABLE` the run continues and spends VLM time (about 20-35 s per call) before ending in review; comment that this is intentional (show evidence to the human) or skip the judge.
- L `analyze()` and `_Run` have no docstring listing the artifacts written (see walkthrough section 7). The `deadline_s` check runs between calls only, so a call in flight can overshoot by up to `timeout_s * max_attempts` (150 s now); say so in the config comment.

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
- Readable. A comment above `decide` listing the order (FAIL first, inputs, identical, reasons) would match the walkthrough.
