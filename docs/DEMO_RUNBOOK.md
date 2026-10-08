# Demo runbook (skeleton)

Nothing here is verified yet. Every case below is a placeholder until QA fixtures exist and real runs have produced artifacts. Fill in only observed outcomes.

Data provenance of each demo must be stated: **synthetic fixture** (`data/fixtures/<case>/`), **real benchmark** (VideoGameQA-Bench record id), real model vs mock.

## Prerequisites
See README Setup. Ollama must be running with `qwen2.5vl:3b`. Launch: `.venv/bin/streamlit run app.py` (UNVERIFIED).

## Case 1: forbidden change -> expected FAIL
- Pair: TBD (candidate: fixture `object_removed`, SYNTHETIC)
- Rules: TBD (`D1` deny object disappearance)
- Command / UI steps: TBD
- Expected by policy: FAIL only if the real VLM returns a validated forbidden verdict with evidence; otherwise NEEDS_REVIEW.
- Observed: not run. Artifact: none.

## Case 2: allowed change -> expected PASS
- Pair: TBD (candidate: `lighting_change` or `clothing_color_change`, SYNTHETIC)
- Expected: PASS only if all regions allowed and scene audit clean.
- Observed: not run.

## Case 3: uncertain / error -> expected NEEDS_REVIEW
- Pair: TBD (candidate: VLM unavailable, `large_misalignment`, or `conflicting_rules`)
- To force VLM unavailable: stop Ollama or use the labelled mock fault-injection provider (mock output must be shown as MOCK).
- Expected: NEEDS_REVIEW with the reason from `decide()`.
- Observed: not run.

## Reproduce a known failure
TBD after QA/DL report one (e.g. small-object miss).

## Real benchmark pairs
`docs/status/data-prep.md` reports 20 prepared real pairs (`data/work/<sample_id>/`, ids `vr_<8 chars>`, manifest `data/manifests/inference_manifest.json`; split assignment still changing). No demo-split pair has been chosen or run; fill after the full manifest lands.
