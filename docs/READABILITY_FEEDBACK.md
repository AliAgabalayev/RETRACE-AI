# Readability feedback

Addressed to the module owners. Nothing here was edited in their code. Reviewed by reading only; I did not run anything. Priority: H = could cause a wrong result or wrong docs, M = hard to follow, L = polish.

## vision/alignment.py (owner: dl-engineer)
- H `alignment.py:77` reads `alignment.min_error_gain` (default 0.7) but `configs/default.yaml` has no such key; the most important guard against aligning away a change is invisible to the config reader. Add it to the config (APP owner edits `alignment:`) or document the hidden default.
- H `alignment.py:109` accepts shifts up to `max_shift_fraction * 2` but `:142` rejects anything above `max_shift_fraction`; the factor 2 looks accidental. Add a comment on why, or use one limit.
- H `alignment.py:99,134,144` return `ones` as the overlap mask for UNRELIABLE results, so `overlap_fraction` is 1.0 on a result that means "do not trust". Fine for the decision (status is checked) but misleading in diagnostics; consider a comment.
- M `alignment.py:145` comment says "identity-warped", but the returned image is the resize-only candidate `cand`; say so.
- M `alignment.py:115,127,137` `best` is an untyped 6-tuple unpacked by position. A small `NamedTuple` (kind, matrix, warped, valid, residual, quality) would make `:137-139` self-explanatory.
- M Magic numbers `2.0` (`:101`), `25.0` and `0.05` (`:132`), `0.5` (`:109`) should be named constants or config keys with the unit (gray levels 0-255).
- M `_mad_masked` is defined at the bottom (`:150`) but used at `:112`; move it up with `_mad`.
- M `align()` has no docstring. State the returned status meanings and that `M` includes the resize step (`Mfull = Mx @ M_resize`, `:146`).
- Test request: a unit test with a known translation to pin the sign of `phaseCorrelate(b, a)` (`:48`); I could not confirm the direction by reading.

## vision/features.py (owner: dl-engineer)
- M `features.py:48` docstring is garbled ("unclipped-to-padding clipped to image"); `patch_to_reference_box` is not called anywhere (grep) - delete or use for diagnostics.
- M `:90-91` reads and hashes the whole checkpoint file at every load just to build a version string; cache it or hash lazily.
- M `:92` records `:main` as the hub revision, which is not a pinned revision; the brief asks for model/revision. Record the commit if available.
- M `:138` uses `assert` for a shape check; asserts disappear under `python -O`. Raise a `ValueError`.
- L `:93,100,106` broad `except Exception` is justified here (fallback chain); keep the `noqa` but add a one-line reason.
- L Document in the class docstring that the transformers fallback is a different model (`dinov2-small`) and thresholds tuned on one are not valid for the other.

## vision/proposals.py (owner: dl-engineer)
- H `proposals.py:14,31` `_MAX_RAW = 200` silently drops components per source before merging and does not set `Coverage.truncated`; a PASS could follow a silent drop. Either flag truncation or comment why 200 is unreachable.
- H `:91-92` sorts DINOv2 and classical boxes together by score although the docstring says the scales differ; classical boxes (0-1 gray fraction) may crowd DINOv2 boxes out of the 8-region cap, or the reverse. Consider ranking per source or by area/score separately.
- M `:43` hard-coded 0.5 containment ratio beside the configurable `merge_iou`; make it a named constant with a comment.
- M `:72` `int(round(min(H,W)*0.01)) | 1` (forces odd kernel, min 3) needs a comment; `:79-80` blur sigma 2.0 is a hidden parameter; `:28` the 4,000,000 switch needs a comment ("avoid full-image mask scan").
- M `_components` returns lists mixing ints, float and a set; a tiny dataclass (`_Box`) would make `_merge` (`:46-62`) readable.
- L `Coverage.proposals_judged` is not set here; note in the docstring that the pipeline owns it.

## rules.py / imageio.py / config.py (owner: python-developer APP)
- M `rules.py:validate_rules` detects duplicate ids only. Brief section 6 and QA-D3 require conflicting-rule handling; decide where it lives and document it.
- L `imageio.decode_image` and `load_image` both check file size; fine, but say in the docstring that `load_image` pre-checks to avoid reading huge files.

## data/manifest.py (owner: python-developer DATA)
- M `manifest.py:32` condition (`startswith(("CONSIDER","ACCEPTABLE"))` and not `UNACCEPTABLE`) is hard to follow; add a one-line example of an ACCEPTABLE block it accepts and one it rejects.
- M `rules_from_question` always makes one deny rule `Q1`; document in the docstring that benchmark runs therefore never exercise multi-rule logic.

## decision.py (frozen; owner senior-pm)
- Readable as is. Suggest a comment above `decide` listing the QA-D1..D3 known gaps so a reader does not assume they are handled.

## Not yet reviewable
`vision/judge.py`, `pipeline.py`, `storage.py`, `cli.py`, `app.py`, `scripts/evaluate.py`: not present when this was written.

## Added after pipeline / judge / storage landed

### pipeline.py (owner: python-developer APP)
- M `pipeline.py:155-318` `_analyze_inner` is ~160 lines with numbered stage comments. Extract `_load_inputs`, `_run_alignment`, `_run_features`, `_judge_all` so each stage is testable and the numbered comments become function names.
- M `:300-308` `mode` and `status` are derived by two overlapping if-chains that also mutate `is_mock`; one small function `_engine_mode_and_status(...)` with a table of cases in its docstring would remove the guesswork.
- M `:233` `coverage.model_copy()` has no comment; say that it is copied because the pipeline mutates it (`:276,293,298`).
- M `:203-208` and `:199-202`: when alignment is `UNRELIABLE` the run continues and spends VLM time before ending in review; either comment this as intentional (show evidence to the human) or skip the judge.
- L `analyze()` and `_Run` have no docstring on what is written where; add the artifact list from brief section 7.
- Doc fix wanted: the `deadline_s` check happens between calls only (`:275,287`); a request in flight can overshoot by up to `timeout_s * max_attempts`. Put this in the config comment.

### vision/judge.py (owner: dl-engineer)
- H `judge.py:244` `p["rule_ids"] if p["validated"] else p["rule_ids"]` has identical branches; and `:246,248` `is_mock_unvalidatable` is a class attribute that is always False. Delete both; the comment at `:248` already says decision.py rejects mocks.
- M `_ask` (`:203`) takes `rules` and `audit` only to feed the mock and validator, and returns a 3-tuple whose meaning (`raw|None, errors, latency`) lives only in the docstring; a small result dataclass would help.
- M `:229` a parsed-but-inconsistent reply (e.g. allowed citing a deny rule) is written to the cache; with a prompt change it is invalidated by `PROMPT_VERSION`, but a validator fix is not. Consider including a validator version in the key or caching only validated replies.
- M `validate_response` is a long chain of `errs.append` + early returns; split into `_parse`, `_check_fields`, `_check_rule_consistency`.
- L `_NO_CHANGE` regex (`:18`) is a safety-relevant escape hatch for "allowed with no rule"; add a comment with example phrases and why it is acceptable.

### storage.py / report.py (owner: python-developer APP)
- M `storage.py:159-215` `approve_reference` mixes input validation, version numbering, baseline storing and history writing; `_next_version` is computed twice (`previous = ...`). Compute once.
- L `export_report` returns `report.md` but also writes the ZIP as a side effect; mention the ZIP path in the docstring (`zip_path_for`).
