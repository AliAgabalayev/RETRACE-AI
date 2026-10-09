# Code walkthrough: screenshot to verdict

Written from the working tree after the D11 cleanup (uncommitted changes on top of `871d8b1 [was 1f81dd2]`; I re-checked every line reference below with `grep` on 2026-10-09). Line numbers drift when owners edit; search for the function name if a line is off. What D11 changed in this code (no behaviour change, yaml values unchanged): `contracts.SCENE_REGION_ID` replaces the literal `"SCENE"`; `Judge` fallback defaults now equal the yaml; dead `prep_crop` and unused prompt fields were removed; the yaml `vlm.prompt_version` key is gone (the version is `prompts.PROMPT_VERSION`, v9); mock review reasons now include the injected error; `approve` needs `--force` / an override checkbox for non-PASS or non-real runs; Streamlit has a "Reload models" button. The worked example artifact is older than D11 but its content is unaffected. Run artifacts used as the worked example: `artifacts/20261008T230650Z-1335da/` (synthetic fixture `data/fixtures/object_removed`, real DINOv2 + real `qwen2.5vl:3b`, VLM answers came from the disk cache).

## 1. Conventions everything depends on

- **Image order** is always `(reference, candidate)`. Reference = approved screenshot, candidate = new build.
- **Box** = `[x1, y1, x2, y2]` in ORIGINAL reference pixels, right/bottom exclusive, so `ref[y1:y2, x1:x2]` is the crop. `RegionProposal` rejects bad boxes (`contracts.py`, `_valid_box`).
- **Transform direction**: `AlignmentResult.candidate_to_reference` (3x3) maps a candidate pixel `(x, y, 1)` to a reference pixel. `aligned_candidate = cv2.warpAffine(candidate, M[:2], (W, H))`. To draw a reference box on the raw candidate (the UI does this) apply the inverse: `report.draw_boxes(..., candidate_to_reference)`.
- **Both crops use the same reference box**: `ref_crop = reference[y1:y2, x1:x2]`, `cand_crop = aligned_candidate[y1:y2, x1:x2]` (`pipeline.py:240-251`).
- **Who decides what**: DINOv2 (and the classical diff) only PROPOSE where something differs. The VLM only JUDGES one proposal (and the whole scene) against the rules. `decision.decide()` alone turns judgments into `PASS` / `FAIL` / `NEEDS_REVIEW`. No model output is ever used as the final answer.

## 2. Stage map

| # | Stage | Function | Where |
| --- | --- | --- | --- |
| 0 | entry | `analyze()` -> `_analyze_inner()` | `pipeline.py:113`, `:153` |
| 0a | engines built once | `build_engines()`: Ollama warm-up FIRST, then DINOv2 | `pipeline.py:342` |
| 1 | decode + limits | `load_image` / `decode_image` (25 MB, 16 MP, PNG/JPEG/WEBP/BMP) | `imageio.py:51`, `:27` |
| 2 | identical shortcut | `np.array_equal` -> `decide(identical_images=True)` | `pipeline.py:178` |
| 3 | alignment | `align()` | `vision/alignment.py:70` |
| 4 | DINOv2 map | `FeatureExtractor.distance_map()` | `vision/features.py:144` |
| 5 | proposals | `propose()` | `vision/proposals.py:67` |
| 6 | crops | slicing + `save_image` | `pipeline.py:240-251` |
| 7a | region judgment | `Judge.judge_region()` -> `_two_stage()` -> `validate_response()` | `vision/judge.py:357`, `:296`, `:96` |
| 7b | scene audit | `Judge.audit_scene()` | `vision/judge.py:371` |
| 8 | decision | `decide()` | `decision.py:110` |
| 9 | artifacts | `_finish`, `write_json_atomic`, `render_report` | `pipeline.py:140`, `:135-136`, `report.py:48` |
| 10 | export / approve | `export_report`, `approve_reference` | `storage.py:123`, `:159` |

Stages 1-9 never raise to the caller: every failure is appended to `run.errors` and turned into a decision by `decide()`.

## 3. Alignment (`vision/alignment.py`)

Different size -> candidate is resized to the reference (`RESIZED`); an aspect-ratio mismatch above 2 % is `UNRELIABLE` (`:85-98`). Same size and mean gray residual below 2.0 -> `IDENTITY` and nothing else is tried (`:101`). Otherwise a global translation (`cv2.phaseCorrelate`) and a similarity transform (ORB + RANSAC `estimateAffinePartial2D`) are tried, and a warp is adopted only if its residual is below `alignment.min_error_gain` (0.7) times the identity residual. A shift above `max_shift_fraction` (5 %) or overlap below `min_overlap_fraction` (0.85) gives `UNRELIABLE`. No local warping or optical flow, because it could warp a real bug away.

Pixels outside the valid overlap are filled with reference pixels (they compare equal) and are 0 in `overlap_mask`. Example run: `status: identity`, `residual_identity: 0.63`.

## 4. DINOv2 proposals

### 4.1 Reference coordinates, resize/pad (`vision/features.py`)

`compute_preproc` (`:40`) resizes the long side to `features.input_long_side` = 518 and zero-pads bottom/right to a multiple of 14. `distance_map` returns a map at REFERENCE resolution, so no later code knows the patch grid. For the 640x360 example: scale 0.8094, resized 518x291, `pad_h` 3, grid 21x37 patches; a patch is about 17.3 reference pixels wide. `grid_to_reference` (`:54`) crops the padded cells away, bilinearly upsamples and resizes to 640x360.

Distance per patch = `1 - cos(feature_ref, feature_cand)` on `x_norm_patchtokens` (`patch_grid_distance`, `:128`). The CLS token is never used as a spatial map.

### 4.2 `propose()` (`vision/proposals.py:67`)

1. Valid area = overlap mask eroded by `mask_erode_px` (7) so warp borders do not make features.
2. **Global-change collapse** (D10, `:85-91`): if at least `global_change_fraction` (10 %) of the valid area exceeds `dinov2_threshold` (0.35), return ONE full-frame proposal `R1 = [0,0,W,H]` with `truncated=True`. Truncated coverage can never PASS.
3. DINOv2 source: threshold the map at 0.35, morphological close (about 1 % of the short side), 8-connected components, drop areas below `max(min_area_px 40, min_area_fraction * H*W)`.
4. Classical source: blur both grays (sigma 2), fit a robust global gain/offset (`:99-107`, so allowed global lighting does not flood the diff), threshold the absolute difference at `classical_threshold` (40 gray levels).
5. Pad each box by `box_padding_px` (8), merge boxes with IoU above `merge_iou` (0.1) or containment above 0.5, sort by score, cap at `max_regions` (8). Dropping any sets `Coverage.truncated`.
6. `score` = max(signal / its source threshold) in the box, i.e. "x times the threshold". It orders proposals; it is not a probability. `source` is `dinov2`, `classical` or `union`.

## 5. Worked example: `artifacts/20261008T230650Z-1335da`

Input: `data/fixtures/object_removed` (SYNTHETIC; a barrel is deleted; `expected.json` true box `[444,209,506,271]`), rules from `configs/rules_example.yaml` (A1, A2 allow; D1, D2 deny).

**Stage by stage, with the real values from `analysis.json`:**

| Stage | Value in the artifact |
| --- | --- |
| alignment | `identity`, overlap 1.0 |
| proposals | one: `R1 box=[424,181,521,286] score=3.65 source=union` (both DINOv2 and classical fired) |
| crops | `crops/R1_ref.png`, `crops/R1_cand.png`, 97x105 px each, same box on reference and aligned candidate |
| diagnostics | `diagnostics/heatmap.png` (DINOv2 distance), `diagnostics/overlap_mask.png`, `images/overlay.png` (boxes on reference) |
| R1 judgment | `forbidden`, `rule_ids [D1]`, `validated true`, evidence "The stack of brown blocks that was present in the BEFORE half is no longer visible in the AFTER half." |
| scene audit | `uncertain`, `validated false`, rules `[A1, A2]`, errors: "allowed verdict but the text describes something missing/removed (internal contradiction)" and "...change_type=disappeared (never auto-allowed; needs review)" |
| coverage | 1/1 judged, `truncated false`, `scene_audit_ran true` |
| decision | `FAIL`, "Forbidden change with visual evidence: R1 (D1)." |

Two honest observations. (a) The VLM called the object "a stack of brown blocks" in R1 and "the barrel" in the audit; the verdict is right, the description is not reliable. (b) The scene audit tried to answer `allowed` for a removal and `validate_response` rejected it; that is the guard working, and the audit still ends `uncertain`, so it can neither help nor block this FAIL.

**Status caveat.** This artifact was written before the engine-mode fix in `pipeline.py:297-302` (file edited 03:07, run at 03:06), so it says `execution_status: degraded`, `engine_mode: degraded` although `errors` is empty. The same pair re-run after the fix, `artifacts/20261008T230730Z-818bb9`, has identical proposals and judgments but `complete` / `real`. `latency_s` is 0.0 and `timings.total` is 0.39 s because the replies came from `data/cache/vlm/`.

### 5.1 What the VLM is sent (`vision/judge.py`, prompt `v9`)

`judge_region` (`:357`) builds ONE composite image with `labelled_pair` (`:47`): BEFORE crop on the left, AFTER crop on the right, captions burned in, small crops upscaled (Ollama's qwen2.5vl crashes below 28 px). The whole-scene audit sends one composite of both full frames (long side `audit_max_side` 512) with the already-judged boxes drawn in yellow with their IDs.

`_two_stage` (`:296`):
- **Stage 1** (image, NO rules; `REGION_PROMPT` / `AUDIT_PROMPT` in `prompts.py`): the model only describes. Schema `STAGE1_SCHEMA`: `before_shows, after_shows, observed_change, change_type, any_difference` (+ `other_changes_outside_boxes` for the audit). Reason: with rules in the prompt the 3B model echoed rule text and cited every allow rule (MODEL_NOTES section 7, v2-v7).
- **Stage 2** (text only; `DECIDE_PROMPT`): the stage-1 text plus the rules (IDs verbatim, explicit ALLOW and DENY ID lists) -> `verdict, rule_ids, evidence` (`STAGE2_SCHEMA`).
- Both calls use Ollama `format=<JSON schema>`, temperature 0, `num_ctx` 2048, timeout 75 s, 2 attempts. The merged JSON of both stages is what `validate_response` sees. The reply is cached by hash of images + prompt + schema + model + `PROMPT_VERSION` (`_cache_key`, `:214`); delete `data/cache/vlm/` to force a fresh call.

### 5.2 `validate_response` (`judge.py:96`)

Any failed check forces `verdict=uncertain, validated=False, errors=[...]`. Checks: JSON parses; required keys; `verdict` in the enum; every `rule_id` exists (D9); `forbidden` must cite a deny rule, no allow rule, and have evidence; `allowed` must cite no deny rule, have evidence, cite a rule or declare "no visible change" (`any_difference=false`), must not describe something missing while a deny rule exists (`_DISAPPEAR` regex, `:19`), and must not have `change_type` `disappeared` / `distorted_or_corrupted`. The model's own confidence is not used.

Scene-audit extras (`audit_scene`, `:371`; region id `SCENE_REGION_ID`): (a) a deterministic pixel-identical shortcut (model id `deterministic:pixel-identical`, not a VLM result) only when there are no proposals and at most 8 pixels differ; (b) a validated `forbidden` audit with no pixel residual outside the judged boxes is downgraded to `uncertain` (the 3B model hallucinated `forbidden` on near-identical pairs); (c) an unvalidated audit never sets `extra_changes_reported`.

## 6. The decision (`decision.py:110`, policy in `docs/DECISIONS.md` D3, D6, D9)

Order inside `decide()`:

1. **FAIL first.** `is_reliable_forbidden` (`:59`) needs: verdict `forbidden`, `validated`, not mock, no errors, non-empty evidence, all cited IDs known (D9/QA-D7), and at least one cited ID is a deny rule that is NOT in a rule conflict (D9/QA-D8). Which judgments count: all of them if alignment is not `UNRELIABLE`/`FAILED`/missing; otherwise ONLY the whole-scene one (`:119-127`), because region crops cut the same reference box from both images and a "missing object" under bad alignment may be misregistration (D9). FAIL wins even if other components failed.
2. Invalid inputs -> `NEEDS_REVIEW`. Identical images -> `PASS` (`:135-136`).
3. Collect reasons for `NEEDS_REVIEW`: no rules; rule conflicts (`find_rule_conflicts`, `:75`: duplicate IDs or the same description both allow and deny); alignment unreliable; truncated; deadline exceeded; not all proposals judged; scene audit missing or `extra_changes_reported`; any pipeline error; per judgment: mock, errors or unvalidated, not `allowed`, or `allowed` that fails `is_acceptable_allowed` (`:94`: validated, real, evidence, known IDs, no deny rule cited, D6).
4. No reasons -> `PASS`, worded as "a heuristic result, not proof that no bug exists".

In the example only step 1 runs: R1 is reliable forbidden citing D1 (not conflicted), alignment `identity` -> FAIL.

Why errors become review: a timeout, an invalid JSON reply or a mock is not evidence of a bug and not evidence of safety. The only safe outputs are `NEEDS_REVIEW` (or `FAIL` when a proven forbidden change exists).

## 7. Artifacts, UI, export, approval

`analyze()` writes (`pipeline.py:130-137`): `rules.yaml`, `images/{reference,candidate,aligned_candidate,overlay}.png`, `crops/<id>_{ref,cand}.png`, `diagnostics/{heatmap,overlap_mask}.png`, `analysis.json` (the `AnalysisResult`, `contracts.py`), `report.md`. All writes are atomic (`storage.write_json_atomic`, `save_png`).

`app.py`: `main()` (`:212`) holds source choice (upload or demo pair), the rules editor (`rules_editor`, `:89`), engine choice (real or MOCK), and the **Analyze** button. Results are keyed by an input hash in `st.session_state` (`input_hash`, `:82`) so reruns do not repeat inference. `render_result` (`:107`) shows banner, MOCK/DEGRADED notices, boxes on both images, per-region expanders, scene audit, diagnostics, **Export bug report (ZIP)** (`storage.export_report` writes `report.md` and `artifacts/<run_id>.zip` next to the run dir) and `render_approval` (`:186`).

**Approve as new reference** (`storage.approve_reference`, `:159`) needs a reference ID plus a confirmation checkbox. It stores the run's candidate as the next `references/<id>/versions/vN.png`; if the ID is new, the replaced reference is stored first as `v1` ("baseline: original reference"); `history.json` records run ID, versions and sha256. Older versions are never overwritten (`_link_new`, `:144`). It does not touch benchmark source images. `storage.approve_reference` itself does not check the decision. The guard (D11) lives in the callers: `cli.cmd_approve` (`cli.py:122`) returns exit code 3 unless `--force` is given when the run is not a real-engine `PASS`; `render_approval` (`app.py:186`) shows a warning and requires a second "I reviewed the regions and override the verdict" checkbox in that case. The sidebar "Reload models" button (`reload_engines_button`, `app.py:44`) clears the `st.cache_resource` engine cache (`app.py:39`), so a failed DINOv2 or VLM load no longer leaves every later run `degraded` until restart.

## 8. Where to change things

| Want to change | Where |
| --- | --- |
| VLM model / server / timeout / attempts | `configs/default.yaml` `vlm.model`, `vlm.base_url`, `vlm.timeout_s` (75), `vlm.max_attempts` (2), `vlm.num_ctx`. Another provider needs a branch next to `Judge._ollama_reply` (`judge.py:247`) and `provider:` in `Judge.__init__` (`:180`, provider branch near `:205`) |
| DINOv2 model / input size / device | `features.model`, `input_long_side` (518), `device` (`FeatureExtractor.__init__`, `features.py:68`) |
| Sensitivity of proposals | `proposals.dinov2_threshold` (0.35), `classical_threshold` (40), `min_area_px`, `min_area_fraction`, `box_padding_px`, `merge_iou`, `max_regions` (8), `global_change_fraction` (0.10), `mask_erode_px` (7) |
| Alignment strictness | `alignment.max_shift_fraction`, `min_overlap_fraction`, `min_inlier_ratio`, `min_error_gain`, `mode` |
| Deadline | `run.deadline_s` (300): checked between VLM calls only |
| Prompts | `src/gameqa/vision/prompts.py`: edit `REGION_PROMPT`, `AUDIT_PROMPT`, `DECIDE_PROMPT`, schemas, and **bump `PROMPT_VERSION`** (cache key). Do not add example sentences: the 3B model copies them (MODEL_NOTES v2-v5) |
| Response validation rules | `judge.validate_response` (`judge.py:96`) |
| Final decision policy | `decision.py` only; record every change in `docs/DECISIONS.md`; policy tests: `tests/policy/test_decision.py` |
| Rules | at run time: the UI rules table or a YAML file (`configs/rules_example.yaml` format: `rules: [{id, effect: allow|deny, description}]`, quote values that YAML may turn into booleans, IDs unique). Benchmark rules: `data.manifest.rules_from_question` (`manifest.py:32`, D8) |
| Mock behaviours | `MOCK_BEHAVIORS` (`judge.py:20`, still repeated in `cli.py:15` and `app.py:30`) |

Every config key can be overridden without editing `default.yaml`: `--config extra.yaml` is deep-merged over it (`config.load_config`, `config.py:28`). Config key names that `Judge` reads but `default.yaml` does not list: `vlm.use_context`, `vlm.cache`, `vlm.mock_behavior`, `vlm.identical_max_px`, `vlm.warmup_timeout_s`, `proposals.classical_gain_normalize`. The prompt version is NOT a config key: it is `PROMPT_VERSION` in `prompts.py` (v9). `Judge` fallback defaults now equal the yaml (75 s / 336 / 512 / 2048), so deleting a key no longer silently changes behaviour or cache keys.

## 9. Known limits relevant to the next day

- **Small objects.** DINOv2 patches are about 14 px at 518 px input (17 px in a 640 px frame). A 12 px coin removed gives DINOv2 max 0.35, exactly at threshold (MODEL_NOTES section 4); only the classical diff catches it. Textures that change a little over a small area may be missed by both (the `clothing_color_change` fixture gets no proposal at all).
- **Alignment sensitivity.** With `UNRELIABLE` alignment, region-level FAIL is disabled (D9). Two YouTube dev pairs were `unreliable`; no real pair has needed a warp.
- **Global change.** Cutscene pairs change globally even when labelled `no_bug`; the collapse into one full-frame region keeps runs bounded but removes localisation (and forces `NEEDS_REVIEW`).
- **Uncalibrated 3B judgments.** Weak rule mapping, weak scene audit, no validated `forbidden` on any of the 10 dev pairs (dl-engineer status). Measured consequence (E2, 60 held-out pairs): 58 NEEDS_REVIEW / 1 FAIL / 1 PASS, and the one PASS is wrong (`vr_bcbcf341`: the proposal box was right but the VLM called the missing ground texture "license plate more visible" and the scene audit said "brighter lighting", both validated `allowed A1`; `decide()` behaved as designed). A larger VLM is the biggest lever and needs an owner decision.
- **Abstention, not understanding.** 53 of 60 E2 runs were truncated (37 global-change collapse, 16 region cap) and truncation forces NEEDS_REVIEW, so E2's low false-PASS rate (1/42) is mostly abstention; "always NEEDS_REVIEW" has the same safety (docs/EXPERIMENTS.md 6.4, 6.5). Hypothesis verdict: NOT SUPPORTED (D11, D12); E2b (classical-only proposals + VLM) was not run, so "DINOv2 proposals help" is untested in isolation.
- **Latency.** Ollama runs on CPU: ~20 s per region call, ~35 s per audit, median 70 s / mean 116 s / p90 238 s per uncached E2 pair (benchmark demo pairs 75-262 s), 55-70 s cold load, ~9.3 GiB free RAM needed.
- **Benchmark rules.** Only two distinct question texts exist, so benchmark runs barely exercise multi-rule logic; the synthetic fixtures do.
- **Selective download.** Only metadata plus the selected image pairs are downloaded; never the 33.4 GB repository (DATA_CARD section 1). Manifest `sha256_*` is of the raw JPEG, not the working PNG.
- **Doc/code mismatches still open** are listed in `docs/READABILITY_FEEDBACK.md` section "Mismatches".
