# Code walkthrough: screenshot to verdict

Status legend: **[exists]** file read and described from source; **[pending]** module not yet in the repo when this was written (interface taken from `docs/DECISIONS.md` D4, may change).

## 1. Conventions that everything depends on

- **Image order** is always `(reference, candidate)`. Reference = approved screenshot, candidate = new build.
- **Box** = `[x1, y1, x2, y2]` in ORIGINAL reference pixels, right/bottom exclusive (like NumPy slicing: `ref[y1:y2, x1:x2]`). `RegionProposal` validates `x2 > x1`, `y2 > y1`, `x1,y1 >= 0` (`contracts.py`, `_valid_box`).
- **Transform direction**: `AlignmentResult.candidate_to_reference` is a 3x3 matrix mapping a *candidate* pixel `(x, y, 1)` to *reference* pixel coordinates. Warping the candidate into the reference frame uses this matrix; to draw a reference box on the raw candidate you apply the inverse.
- **Crops**: both crops use the same reference box: `ref_crop = reference[y1:y2, x1:x2]`, `cand_crop = aligned_candidate[y1:y2, x1:x2]` (D4). That is why both crops show the same place even if the candidate was shifted.
- Resize/pad: DINOv2 sees a resized+padded image; `FeatureExtractor.distance_map` must undo that and return a map at reference resolution (D4), so proposals never need to know the patch grid.

## 2. The stages [contracts: exists, stages: see status]

| # | Stage | Function (D4) | File | Status |
| --- | --- | --- | --- | --- |
| 1 | Validate input, decode, size limits | `analyze()` -> `_analyze_inner()` | `src/gameqa/pipeline.py:115,155` | [exists] |
| 1a | Decode + limits | `load_image`, `decode_image` (file size, format whitelist, pixel cap; raises `ImageError`) | `src/gameqa/imageio.py:173,197` | [exists] |
| 2 | Align candidate to reference | `align(reference, candidate, cfg)` -> `(AlignmentResult, aligned_candidate, overlap_mask)` | `vision/alignment.py:70` | [exists] |
| 3 | DINOv2 distance map | `FeatureExtractor.distance_map(ref, aligned)` | `vision/features.py:144` | [exists] |
| 4 | Region proposals | `propose(ref, aligned, overlap_mask, dino_map, cfg)` -> `(list[RegionProposal], Coverage)` | `vision/proposals.py:65` | [exists] |
| 5 | VLM verdict per region | `Judge.judge_region(...)` -> `RegionJudgment` | `vision/judge.py:255` | [exists] |
| 6 | Whole-scene audit | `Judge.audit_scene(...)` -> `SceneAudit` | `vision/judge.py:269` | [exists] |
| 7 | Final decision | `decide(DecisionInput)` -> `(FinalDecision, reason)` | `src/gameqa/decision.py:53` | [exists] |
| 8 | Artifacts, report, approve reference | `new_run_dir`, `write_json_atomic`, `export_report`, `approve_reference` | `storage.py:69,43,123,159`; report text `report.py:48` | [exists] |

### Alignment (stage 2) [exists] (`vision/alignment.py`, read, not run by me)
What `align()` actually does, in order:
1. If candidate size differs, resize it to the reference size (`alignment.py:85-91`). If aspect ratios differ by more than 0.02 the result is `UNRELIABLE` immediately (`:97-99`).
2. Compute `residual_identity` (mean absolute gray difference, `_mad`). If the mode is `identity` or the residual is below 2.0 gray levels, stop: status `identity` or `resized` (`:101-102`).
3. Otherwise try a global translation (`cv2.phaseCorrelate`, `:44-49`) and a restricted affine (ORB features + RANSAC `estimateAffinePartial2D`: rotation, uniform scale, translation only, `:52-67`). A warp is adopted only if it cuts the residual to less than `min_error_gain` (0.7) of the identity residual (`:114,127`); this is the guard against "aligning away" a real change.
4. If an adopted warp shifts more than `max_shift_fraction` or leaves less than `min_overlap_fraction` valid pixels -> `UNRELIABLE` (`:142-145`). If no warp helps and the residual is large (>25) with no reliable transform -> `UNRELIABLE` (`:132-134`).
5. On success returns `ALIGNED`, the warped candidate and the valid-overlap mask (255 = valid). Direction: `M` maps candidate -> reference and is passed to `cv2.warpAffine` (`_warp`, `:35`). Whether the sign of the phase-correlation shift is right is not covered by a test I have seen (UNVERIFIED; see READABILITY_FEEDBACK).

### Image decoding [exists] (`imageio.py`)
`decode_image` rejects empty files, files over `input.max_file_mb`, formats outside `allowed_formats`, images over `max_pixels`, and anything PIL cannot decode, all as `ImageError`. Output is RGB uint8.

### Rules [exists] (`rules.py`)
`parse_rules(text)` / `load_rules(path)` accept YAML `{rules: [...]}` and reject duplicate ids. There is no conflict detection between an allow and a deny rule yet (QA defect QA-D3 in `docs/status/qa-engineer.md`).
`AlignmentStatus` values (`contracts.py`): `identity` (same size, no warp), `aligned` (translation/affine estimated and passed checks), `resized` (dimensions differed, candidate resized to reference), `unreliable`, `failed`. Config keys: `alignment.max_shift_fraction`, `min_overlap_fraction`, `min_inlier_ratio`. Alignment must not hide a vanished object by "fixing" it; if quality is low the status is `unreliable` and the decision becomes review.

### DINOv2 features [exists] (`vision/features.py`, read, not run by me)
`compute_preproc` (`:40`) scales the longer side to `features.input_long_side` (518), then pads right/bottom (zeros after normalisation = mean colour) to a multiple of 14. `FeatureExtractor.patch_grid_distance` (`:128`) runs the frozen model on reference and aligned candidate, L2-normalises patch tokens, and returns `1 - cos` on the patch grid. `grid_to_reference` (`:54`) crops away the padded cells, upsamples bilinearly and resizes to reference HxW; this is the "undo resize/pad" step. Loading tries `torch.hub` `dinov2_vits14`, then a `transformers` fallback `facebook/dinov2-small` (a different model: `version` string records which one). Failure raises `ModelLoadError` (the pipeline should then report degraded mode; pipeline not yet present).

### Proposals [exists] (`vision/proposals.py:65`, read, not run by me)
Threshold the DINOv2 map (`dinov2_threshold`) and the blurred gray diff (`classical_threshold`), both restricted to the valid-overlap mask; morphological close, connected components, drop components under `min_area_fraction`; pad each box by `box_padding_px`; merge overlapping boxes (IoU > `merge_iou` or one box mostly inside another); sort by score; keep `max_regions`. `Coverage.truncated` is set when merged count exceeds the cap. A box found by both sources gets `source="union"`. Scores from the two sources are on different scales and are only used for ordering (stated in the module docstring). `Coverage.proposals_judged` is left at 0 here; the pipeline must fill it.

### Three different kinds of output, kept apart

1. **DINOv2 patch distance** (stage 3): `1 - cosine_similarity` of L2-normalised patch features between reference and aligned candidate. It says "these patches look semantically different". It is not a bug probability; a small vanished object can be invisible at 14-pixel patch scale.
2. **Proposals** (stage 4): the DINOv2 map thresholded (`proposals.dinov2_threshold`), cleaned, merged, padded (`box_padding_px`) and capped (`max_regions`: 8) are unioned with **classical** pixel-diff boxes (`classical_threshold`). Each proposal records `source` (`dinov2`/`classical`/`union`). If the cap drops regions, `Coverage.truncated=True` and PASS is blocked.
3. **VLM judgment** (stages 5-6): for each region the VLM sees before/after crops, context, region location and the rules, and returns `observed_change`, `verdict` (`allowed`/`forbidden`/`uncertain`), `rule_ids`, `evidence`. Its self-reported confidence is not used as a probability. The judgment is only `validated=True` after schema, rule-ID and consistency checks (validation lives in the judge, [pending]).
4. **Deterministic decision** (stage 7): `decide()` in `decision.py`. The VLM never outputs PASS/FAIL; code does.

### Orchestration [exists] (`pipeline.py`, read, not run by me)
`analyze()` (`:115`) creates the run dir, writes `rules.yaml`, calls `_analyze_inner`, then always writes `report.md` and `analysis.json`. `_analyze_inner` (`:155`) order:
1. `:159-175` load both images (`ImageError` is recorded in `errors`); if either is missing -> `decide(inputs_valid=False)` -> NEEDS_REVIEW, `execution_status=error`.
2. `:180` pixel-identical shortcut: no model is loaded, `decide(identical_images=True)` -> PASS.
3. `:191-208` alignment; an exception becomes status `FAILED` and the run stops with review. An `UNRELIABLE` alignment does NOT stop the run (models still run); the policy turns it into review.
4. `:213-227` DINOv2 `distance_map`; any exception -> `degraded=True`, classical-only proposals, error text appended (this is the "DINOv2 unavailable" fallback; it is visible in `errors`, `engine_mode="degraded"`).
5. `:231-237` `propose`; on exception no proposals and an error (error forces review, so an empty proposal list caused by a crash cannot PASS).
6. `:241-253` crops: `ref[y1:y2, x1:x2]` and `aligned[y1:y2, x1:x2]` with the same box; saved to `crops/<id>_ref.png`, `crops/<id>_cand.png`; `images/overlay.png` has boxes drawn on the reference.
7. `:256-296` judge each region then `audit_scene`, checking the `run.deadline_s` clock BETWEEN calls (a single in-flight request is not interrupted). Exceptions from the judge become `uncertain` judgments with `errors`.
8. `:298-318` fill `coverage.proposals_judged`, compute `engine_mode`/`execution_status`, call `decide`. `mock` judge -> `engine_mode="mock"`.

### The VLM layer [exists] (`vision/judge.py`, `vision/prompts.py`, read, not run by me)
- `Judge.__init__` (`:133`): `provider: ollama` -> `model_id="ollama:<model>"`, `is_mock=False`; `provider: mock` -> `model_id="mock:<behavior>"`, `is_mock=True`. Mock behaviours: `allowed, forbidden, uncertain, timeout, invalid_json, unknown_rule` (`MOCK_BEHAVIORS`, `:19`). Mock replies say "no image was examined".
- `judge_region` (`:255`) sends three images in order: reference crop, candidate crop, and a side-by-side context image (left reference, right candidate, region outlined) plus the rules text. `audit_scene` (`:269`) sends the full reference and aligned candidate with the already-proposed boxes outlined in yellow and asks whether anything changed outside them (`other_changes_outside_boxes`).
- Requests: Ollama `/api/chat`, JSON-schema `format`, temperature 0 (`:192-201`). `_ask` (`:203`) retries only on provider errors or malformed JSON, at most `max_attempts`; timeout is per request (`timeout_s`). Replies are cached on disk under `<cache_dir>/vlm/` keyed by image bytes, prompt, schema, model id, prompt version (`:159`). A cache hit reports latency 0.0.
- `validate_response` (`:62`) is the gatekeeper for `RegionJudgment.validated`. It forces `uncertain` and `validated=False` on: malformed JSON, missing keys, invalid verdict, unknown rule IDs, `forbidden` without a cited deny rule or evidence or citing an allow rule, `allowed` citing a deny rule, `allowed` with no rule and not saying "no visible change", `allowed` with rule but no evidence. This catches QA-D1 and most of QA-D2 at the judge level (as read; not re-tested by me).
- The model's own confidence is not requested or used.

## 3. The decision policy, line by line [exists] (`src/gameqa/decision.py`; `is_reliable_forbidden` at line 40, `decide` at line 53)

`is_reliable_forbidden(j, rules)` is true only if ALL hold: verdict is `forbidden`, `validated`, not `is_mock`, no `errors`, non-empty `evidence`, and at least one cited `rule_id` is a `deny` rule. This is the only way to FAIL.

`decide(DecisionInput)` order:
1. Collect region judgments plus the scene-audit judgment. If any is a reliable forbidden -> `FAIL`. This comes first on purpose: a timeout or truncation elsewhere cannot turn a proven fail into pass.
2. `inputs_valid=False` -> `NEEDS_REVIEW`.
3. `identical_images=True` -> `PASS` (documented shortcut).
4. Otherwise collect reasons for review: no rules; alignment missing/`unreliable`/`failed`; `coverage.truncated`; `deadline_exceeded`; fewer judged than proposed; scene audit did not run or reported `extra_changes_reported`; any pipeline error; per judgment: mock, errors/not validated, or verdict not `allowed` (so `uncertain` and `forbidden`-but-unreliable land here).
5. Any reason -> `NEEDS_REVIEW` with the joined reasons; none -> `PASS` with the heuristic disclaimer.

Why errors become review: the pipeline cannot know whether the part that failed (model down, bad JSON, timeout) hid a bug. Treating that as PASS would be a false pass, the dangerous outcome. Treating it as FAIL would invent a defect without evidence. So uncertainty is surfaced to a human.

### Worked example (small, hand-computed from `decide`; not a measured run)
Rules: `A1 allow` weather/lighting may change; `D1 deny` objects must not disappear. Two regions:
- R1 (sky), verdict `allowed`, rule `A1`, validated, real -> contributes no reason.
- R2 (crate gone), verdict `forbidden`, rule `D1`, evidence "crate present in reference, absent in candidate", validated, real -> reliable forbidden.
Result: `FAIL`, reason "Forbidden change with visual evidence: R2 (D1)." If instead R2's JSON was malformed (`validated=False`, `errors` set): no reliable forbidden, reasons = ["R2: invalid or failed model response"], result `NEEDS_REVIEW`. If R2 is `allowed` too, scene audit ran clean, nothing truncated, alignment `identity`: `PASS`.

## 4. Where to change things

| Want to change | Edit |
| --- | --- |
| Thresholds, caps, timeouts, model name, deadline | `configs/default.yaml` (record changes in `docs/DECISIONS.md`) |
| Decision policy | `src/gameqa/decision.py` (frozen; via senior-pm) |
| Prompt / VLM provider | `src/gameqa/vision/judge.py`, `vlm.*` config [pending] |
| Rules | `configs/rules_example.yaml` or the UI editor [pending] |

## 5. One traced real pair
[pending] `artifacts/` was empty when last checked. No `artifacts/<run_id>/analysis.json` existed when this section was written. To be filled with the actual function path and fields of a real run.

## 5b. Data manifest [exists] (`src/gameqa/data/manifest.py`)
`load_inference_manifest` raises if a record contains `label`, `ground_truth`, `ground_truth_raw` or `test_pass` (`FORBIDDEN_INFERENCE_KEYS`), so labels cannot leak into inference. `load_eval_labels` is the only reader of labels. `rules_from_question` turns every benchmark question into one deny rule `Q1` ("Report a regression: <question>") plus an optional allow rule `A1` copied from an ACCEPTABLE block in the question. Consequence: benchmark runs use a single broad deny rule, unlike the demo A1/A2/D1/D2 rules. Preparation code is in `src/gameqa/data/prepare.py` (not run by me; no data-prep status file existed when checked).

## 6. Known limitations to state in the final version
Known open policy defects (QA-D1..D3, `docs/status/qa-engineer.md`: an `allowed` verdict citing a deny rule, allowed with no evidence, and conflicting rules all currently PASS). Small-object misses at patch resolution; alignment sensitivity; VLM verdicts uncalibrated; qwen2.5vl:3b JSON compliance unmeasured; selective-download constraints for the dataset not yet observed. All to be updated from QA / data status.
