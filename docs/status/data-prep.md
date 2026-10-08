# data-prep status (python-developer DATA)

## STATE: first 20 pairs READY (interim; full subset download in progress, will overwrite manifests and splits)
- `data/manifests/inference_manifest.json`, `data/manifests/eval_labels.json` exist (20 samples, 0 failed). Split assignment will CHANGE when the full 250 are prepared (sample_ids are stable: `vr_<first 8 of custom_id>`).
- Working copies: `data/work/<sample_id>/{reference.png,candidate.png}`.
