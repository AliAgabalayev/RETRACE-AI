# data-prep status (python-developer DATA)

## STATE: DONE. Full visual-regression subset (250/250) downloaded, verified, manifests final (D7 splits).

## Facts
- Dataset: `taesiri/VideoGameQA-Bench` (CC BY 4.0), pinned revision **2afbfdcc9cb84318845f348c023bb2e92b942e29**.
- Metadata: `data/test-00000-of-00001.parquet` -> `data/raw/metadata/data/`. 3436 rows x 8 cols: custom_id, question_categories (numpy array of str), question, ground_truth (str), media_path (array of str), media_type, media_folder, media_source.
- Category: rows where `'VisualRegression' in question_categories`. Category combos: `['Unity','VisualRegression']` 171 (media_source UnityCapturesDataset) + `['VisualRegression','Cutscene']` 79 (Youtube-Cutscene) = **250**, matches expected ~250. custom_id unique.
- Only 2 distinct question templates (one per source); no per-sample rule text.
- `ground_truth` is a JSON string: `{"test_pass": false}` 224, `{"test_pass": true}` 26. **Mapping: test_pass false -> `bug`, true -> `no_bug`** (null if unparsable; none occurred). All 26 no_bug are Youtube-Cutscene.
- Images: 2 JPGs per record. Repo path `images/<custom_id>/question_images_{0,1}.jpg` (parquet `media_folder` `./image/<id>/` is NOT the repo path; verified via `get_paths_info`, `image/...` does not exist). Total remote size 0.724 GB for 250 pairs (~1.5 MB per 4K JPG).
- **Order: question_images_0 = reference, question_images_1 = candidate.** Evidence: question text says "the second image represents an acceptable variation of the first (reference) image"; visually checked: vr_7ec62bb3 (bug): image_0 has a lit "AMERICAN" billboard with a red car, image_1 has it removed (missing object in candidate); vr_59af7164 (no_bug): same shot, character jacket changed (allowed customization).
- Downloaded 250, failed 0, validation_status ok for all. Reference and candidate sizes are identical for every pair; no identical reference/candidate pairs.
- Image sizes (reference): 3840x2160 148 pairs (all Unity), 1278x718 23, 2560x1440 23, 1279x718 6, 1261x718 3, other cutscene sizes (~1140-1280 x ~634-720) the rest.
- Layout: raw JPGs `data/raw/images/<custom_id>/question_images_{0,1}.jpg` (694 MB); working PNG copies `data/work/<sample_id>/{reference,candidate}.png` (RGB, 2.7 GB). sample_id = `vr_<first 8 chars of custom_id>` (collision-free on all 250).
- Manifests: `data/manifests/inference_manifest.json` (no labels; also has `custom_id`, `*_raw_path`, `media_source`, `reference_width/height`, `candidate_width/height`), `data/manifests/eval_labels.json` (`{sample_id: {ground_truth_raw,label,split}}`), `data/manifests/eval_subset_60.json` (60 eval sample_ids, no labels).

## Rules (`rules_from_question`)
- `Q1` DENY: `"Report a regression: " + original question verbatim` (the question includes a JSON-output instruction block; the VLM prompt owner may want to ignore it).
- `A1` ALLOW: the question's "...ACCEPTABLE:" header plus its bullet lines, copied verbatim (present in all 250 questions). The UNACCEPTABLE list stays only inside Q1. No labels used.

## Splits (seed 13, `gameqa.data.prepare.assign_splits`)
- Strata = media_source x label. Labels read ONLY to build strata and pick the balanced demo set; they never enter inference_manifest.
- Groups: samples sharing any image sha256 (reference or candidate) are unioned into one `group_id` (`g_<min sample_id>`) and never split across splits. 128 groups: 88 singletons, 40 multi-sample (sizes 2-9). Limitation: groups only reflect byte-identical shared images; same scene with different captures is undetected, so some near-duplicate leakage across splits is possible.
- demo 5 (2 no_bug cutscene, 2 bug cutscene, 1 bug Unity): vr_73635d70(no_bug), vr_2ada9903(no_bug), vr_536596f0, vr_b5647b43, vr_9aa8a337 (bug). Singleton groups only.
- dev 40: 6 no_bug (cutscene), 34 bug (26 Unity, 8 cutscene). Meets D7 (>=6 no_bug, >=10 bug, both sources).
- eval 205: 18 no_bug (cutscene), 187 bug (144 Unity, 43 cutscene).
- `eval_subset_60.json`: all in eval; 18 no_bug (all remaining), 20 cutscene bug, 22 Unity bug (20 + 2 top-up because no_bug fell 2 short of 20).
- Label distribution is heavily skewed to bug (224/250 = 90%); a constant "FAIL" predictor scores 90% on full set; use balanced metrics.

## Order/prefix note
`--limit N` takes a seeded, label-interleaved prefix (every 4th is no_bug). Interim 20-pair manifests were replaced by the final ones; sample_ids unchanged.

## Code
- `src/gameqa/data/prepare.py`, `src/gameqa/data/manifest.py`, `scripts/prepare_data.py`, `tests/data/test_manifest.py` (6 tests, no network).

## Commands run
- `.venv/bin/python scripts/prepare_data.py --limit 20`
- `.venv/bin/python scripts/prepare_data.py` (full; run twice: second run reused files and rebuilt manifests with D7 split rules)
- `.venv/bin/python -m pytest tests/data -q` -> 6 passed
- Re-run: `.venv/bin/python scripts/prepare_data.py [--limit N] [--revision SHA]` (idempotent; existing raw/work files are reused).

## Notes
- Idempotence checks existence of raw/work files (re-hashes raw files each run); it does not re-download if a file exists, even if corrupted (decode failure would be recorded as `validation_status: failed`).
- No schema changes, dependencies added, or git operations.
