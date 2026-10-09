# Data card: VideoGameQA-Bench visual-regression subset

Owner: experiment-tracker-pm. Facts below were verified by reading `data/raw/metadata/data/test-00000-of-00001.parquet` and `data/manifests/*.json` on 2026-10-09. Final facts after the full 250-pair preparation (re-verified against `data/manifests/inference_manifest.json`, `eval_labels.json` and `eval_subset_60.json` on 2026-10-09). No PENDING items remain; re-verify if manifests are regenerated.

## 1. Source
- Dataset: VideoGameQA-Bench, `taesiri/VideoGameQA-Bench` on Hugging Face. Paper: arXiv 2505.15952 (Taesiri, Ghildyal, Zadtootaghaj, Barman, Bezemer).
- License: CC BY 4.0 (dataset card `cardData.license = cc-by-4.0`, verified through the HF API). Attribution in `THIRD_PARTY_NOTICES.md`.
- Revision (commit sha) used: `2afbfdcc9cb84318845f348c023bb2e92b942e29` (HF API `sha`, last modified 2025-05-27; identical to the sha stored in every manifest row and in the local HF download cache for the parquet file).
- Official split: the source publishes these records in its `test` split. The `demo` / `dev` / `eval` split used here is **our internal protocol**, not the dataset's official train/test split.
- Downloaded: only the metadata parquet (3436 rows x 8 columns) plus selected image pairs. The full 33.4 GB repository is NOT downloaded.

## 2. Selection logic
- Schema (actual): `custom_id, question_categories, question, ground_truth, media_path, media_type, media_folder, media_source`.
- `question_categories` is a numpy array of strings, not a single string. The visual-regression records are the rows where the array contains `"VisualRegression"`:
  - `['Unity', 'VisualRegression']`: 171 rows
  - `['VisualRegression', 'Cutscene']`: 79 rows
- Count: expected 250 (brief), actual **250** (171 + 79). No discrepancy.
- All 250 have `media_type = images` and `media_path = ['question_images_0.jpg', 'question_images_1.jpg']`.
- Path mapping: parquet `media_folder` is `./image/<custom_id>/`; the repository folder is `images/<custom_id>/`. Local raw path: `data/raw/images/<custom_id>/question_images_{0,1}.jpg`. Do not concatenate blindly.

## 3. Label mapping
- `ground_truth` is a JSON string. Observed values (all 250): `{"test_pass": false}` and `{"test_pass": true}`. Mapping: `test_pass=false` -> `bug`; `test_pass=true` -> `no_bug`. Any unparseable value -> `label: null` (none observed).
- Labels live only in `data/manifests/eval_labels.json`; the inference manifest contains no labels.

## 4. Label distribution

### Full source subset (250, verified from parquet)
| media_source | bug | no_bug | total |
| --- | --- | --- | --- |
| UnityCapturesDataset | 171 | 0 | 171 |
| Youtube-Cutscene | 53 | 26 | 79 |
| total | 224 (89.6%) | 26 (10.4%) | 250 |

Consequences:
- **Severe class imbalance.** An "always bug" predictor scores 89.6% accuracy on the full subset. Plain accuracy is not a valid headline metric; report per-class recall (bug recall, no-bug recall) and balanced accuracy.
- **Source is confounded with label.** All 26 `no_bug` pairs are cutscene frames; every Unity pair is a `bug`. A method that detects the source/image size (Unity captures are 3840x2160, cutscenes about 1280x720) can score well without detecting changes. Report results per `media_source` and treat cutscene-only no_bug/bug as the only source with both classes.
- Only 2 distinct `question` texts exist (one per source), so "rule-aware" behaviour is tested against 2 generic rule sets.

### Rules mapping (D8, verified: all 250 records have exactly rules A1, D1)
- `A1` effect allow = the "Consider these variations ACCEPTABLE:" block verbatim.
- `D1` effect deny = the "Consider these variations UNACCEPTABLE:" block verbatim.
- The benchmark's own "Provide your assessment as JSON {test_pass}" instruction is excluded from the rules. The full question stays in the manifest `question` field. Fallback when no UNACCEPTABLE block: D1 = whole question (not triggered: 250/250 use the block mapping).
- This replaces the earlier interim mapping (`Q1` deny = whole question).

### Final splits (verified from manifests; 250 pairs, all `validation_status = ok`)
| split | Unity bug | Cutscene bug | Cutscene no_bug | total |
| --- | --- | --- | --- | --- |
| demo | 1 | 2 | 2 | 5 |
| dev | 26 | 8 | 6 | 40 |
| eval | 144 | 43 | 18 | 205 |
| total | 171 | 53 | 26 | 250 |

- Split sizes: demo 5 / dev 40 / eval 205. Demo pairs are never scored; thresholds and prompts were tuned on dev and fixtures only.
- `eval_subset_60` (seeded, chosen before results; `data/manifests/eval_subset_60.json`): 60 pairs = 18 no_bug (all eval no_bug cutscenes) + 20 cutscene bug + 22 Unity bug (42 bug). Used for E1/E2/E4 paired comparison.
- Provenance flag: `artifacts/eval/classical_threshold.json` (E1 threshold) lists 37 dev IDs of which 23 are in the current eval split (2 in the 60-subset); see `docs/EXPERIMENTS.md` 6.6.

## 5. Image facts (all 250 pairs, verified from manifests)
- 250 pairs prepared, 0 failed, `validation_status = ok` for 250. Reference and candidate dimensions are identical in all 250 pairs.
- Dimensions: Unity 148 pairs at 3840x2160 and 23 at 2560x1440 (171); 79 cutscene pairs with 45 distinct sizes, between 1120x627 and 1279x718 (most common 1278x718, 23 pairs; some letterboxed at about 1274x568). Source (and so label for no_bug) can be read from resolution alone.
- Hashes: `sha256_reference` / `sha256_candidate` are of the raw JPEG (not the working PNG). 128 distinct reference hashes; 249 distinct candidate hashes; no pair has identical reference and candidate hash. The 40-image interim check (sha256 and PNG decode) was done earlier; all 250 pairs have their raw JPEGs and working PNGs on disk (checked 2026-10-09).
- 3840x2160 images are downscaled inside the pipeline; box coordinates stay in original reference pixels.

## 6. Reference/candidate order
- Mapping: `question_images_0` -> reference, `question_images_1` -> candidate.
- Evidence: (1) both question texts say the second image is judged against "the first (reference)" and files are `_0` then `_1`; (2) visual spot-check by data-prep (`docs/status/data-prep.md`): `vr_7ec62bb3` (bug) has a lit "AMERICAN" billboard with a red car in image 0 and it is removed in image 1 (missing object in the candidate); `vr_59af7164` (no_bug) is the same shot with the character jacket changed (allowed customization). Two pairs only, so the order is supported, not proven for all 250; Unity labels (all bug) cannot confirm it.

## 7. Groups and leakage limitations
- `group_id` = pairs sharing a **reference image sha256** (`prepare._group_ids`). 128 groups: 77 cutscene singletons, 1 cutscene group of 2, 50 Unity groups of 1 to 9 pairs. Splits never straddle a group (verified: 0 groups and 0 reference hashes cross splits). The 60-pair subset spans 55 groups (max 3 per group).
- This is **sha-grouping only**. Real scene identity is unknown: the paper describes 9 Unity scenes, and different reference captures of the same scene (different sha) can fall in dev and eval. Optimistic transfer from dev to eval on Unity cannot be excluded. Candidate hashes are not used for grouping (249 distinct).
- Cutscene bug and no_bug pairs may derive from the same cutscene source; not verifiable from metadata.
- Bootstrap CIs resample pairs, not groups, and so are somewhat optimistic where groups have several pairs (Unity).

## 8. Known limitations
- Pair-level labels only; no region annotations. No localization IoU may be computed from them.
- Labels come from the benchmark's own `test_pass` ground truth; label noise unmeasured.
- Small eval subset (see `docs/EXPERIMENTS.md`): smoke test, not significance.
