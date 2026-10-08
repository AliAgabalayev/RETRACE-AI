# Data card: VideoGameQA-Bench visual-regression subset

Owner: experiment-tracker-pm. Facts below were verified by reading `data/raw/metadata/data/test-00000-of-00001.parquet` and `data/manifests/*.json` on 2026-10-09. Items marked PENDING are not yet verified or depend on the full 250-pair preparation still running (see `docs/status/data-prep.md`). Re-verify when manifests are overwritten.

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
- Only 2 distinct `question` texts exist (one per source), so "rule-aware" behaviour is tested against 2 generic rule sets, not many different rules. Rules in the manifest are derived from that text (`Q1` deny = the whole question text, `A1` allow = the ACCEPTABLE list).

### Prepared so far (interim 20 pairs, verified from manifests)
| split | media_source | bug | no_bug |
| --- | --- | --- | --- |
| demo | Unity | 2 | 0 |
| demo | Cutscene | 1 | 2 |
| dev | Unity | 2 | 0 |
| dev | Cutscene | 0 | 0 |
| eval | Unity | 6 | 0 |
| eval | Cutscene | 4 | 3 |
| total | | 15 | 5 |

Totals: demo 5, dev 2, eval 13. This is interim; the full-subset preparation will overwrite splits (sample IDs stay stable). Final per-split table: PENDING.

Dev concern (reported to senior-pm): the interim dev split has no `no_bug` pair, so no threshold can be tuned against false positives. The final dev split must contain `no_bug` cutscene pairs.

## 5. Image facts (interim 20 pairs)
- Counts: 20 pairs prepared, 0 failed, `validation_status = ok` for 20.
- All 40 raw JPEGs match `sha256_reference` / `sha256_candidate` in the manifest (sha256 is of the **raw JPEG**, not of the working PNG). All 40 working PNGs exist and decode.
- Reference and candidate dimensions are identical in all 20 pairs.
- Dimensions: 10 Unity pairs at 3840x2160; 10 cutscene pairs between about 1139x634 and 1278x718 (several different sizes, e.g. 1278x718, 1274x568, 1139x634). 3840x2160 images are large for a 6 GB GPU pipeline; downscaling is done inside the pipeline (box coordinates stay in original pixels).
- Full-subset statistics (missing files, dimension histogram, mismatched sizes): PENDING.

## 6. Reference/candidate order
- Textual evidence only: both question texts say "the second image" is the one judged against "the first (reference)", and the media files are `question_images_0` then `question_images_1`. Manifest maps `_0` -> reference, `_1` -> candidate.
- Visual spot-check of the order on sample pairs: PENDING (qa-engineer / data-prep). Unity ground truth is all `bug`, so order cannot be inferred from labels.

## 7. Groups and leakage limitations
- Manifest `group_id` is `g_vr_<sample id>`: one group per sample. These are **not** real scene groups; group is unknown, so it is not invented.
- The paper describes 9 Unity scenes behind the 171 Unity pairs (and cutscene frames paired with glitch-free frames). Many pairs therefore share a scene or reference. With per-sample groups, dev and eval pairs from the same scene can leak; thresholds tuned on dev may transfer optimistically to eval for Unity. State this limitation in every result.
- Cutscene `bug` and `no_bug` pairs may derive from the same cutscene source; not verifiable from metadata.
- Demo pairs are hand-selected and are excluded from eval and from any metric.

## 8. Known limitations
- Pair-level labels only; no region annotations. No localization IoU may be computed from them.
- Labels come from the benchmark's own `test_pass` ground truth; label noise unmeasured.
- Small eval subset (see `docs/EXPERIMENTS.md`): smoke test, not significance.
