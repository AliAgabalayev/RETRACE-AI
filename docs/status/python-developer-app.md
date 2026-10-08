# python-developer (APP) status

Updated 2026-10-09. Written code first then tests for most modules (not strict test-first); tests are behavioural.

## Done (verified)
- `src/gameqa/{config,rules,imageio,storage,report,pipeline,cli}.py`, `app.py`, `configs/rules_example.yaml`, `tests/app/*`.
- `.venv/bin/python -m pytest tests/app -q` -> 34 passed (fake extractor/judge/align/propose via monkeypatch; AppTest headless UI test; CLI analyze/batch/approve).
- App starts: python launcher script polling `/_stcore/health` -> 200 "ok", `/` -> 200 (`streamlit run app.py --server.headless true --server.port 8501`).
- AppTest with real engines + MOCK(forbidden) on `synthetic fixture | object_removed`: no exception, loud MOCK banner, NEEDS REVIEW (mock never FAILs).
- CLI real DINOv2 + mock judge: `python -m gameqa.cli analyze ... --mock forbidden` -> NEEDS_REVIEW [MOCK], feature_model dinov2_vits14 on cuda.
- CLI real DINOv2 + real Ollama qwen2.5vl:3b on object_removed: NEEDS_REVIEW [DEGRADED]. R1 judgment rejected by validator ("allowed verdict without an allow rule..."), scene audit ReadTimeout x2 (60 s). Pipeline behaved correctly; VLM quality/latency is dl-engineer's area.
- `batch` rows: sample_id, decision, execution_status, engine_mode, n_regions, proposals_judged, seconds_total, prompt_version, feature_model, vlm_model, run_dir (+split, run_id, reason, errors). `--ids-file` supports list or {sample_ids|ids}. Never reads eval_labels.

## Decisions
- Judge context args: pipeline passes FULL reference and aligned candidate arrays (unmodified, no box drawn) as ref_context/cand_context; judge draws/resizes.
- Mock selection: cfg `vlm.provider=mock`, `vlm.mock_behavior=<name>` (matches judge.py).
- Rules YAML: unquoted non-string `id`/`description` (e.g. `description: no` -> YAML bool) is rejected with a "wrap in quotes" error to keep descriptions verbatim.
- Execution status: COMPLETE only with real judge, no errors; mock/degraded/judge errors -> DEGRADED; judge unavailable/ alignment failure/invalid input -> ERROR.
- Zip export sits beside the run dir: `artifacts/<run_id>.zip` (so it is not zipped into itself). `approve_reference(..., previous_reference_path=)` optional: seeds v1 with the replaced reference if the reference_id is new.
- senior-pm message about xfail markers: not mine (no xfail in tests/app); ignored per correction. D6 policy needs no pipeline change.

## Open
- `--ids-file data/manifests/eval_subset_60.json` not yet present (no file to test against; format assumed).
- Real VLM audit latency (30 s timeout x2) can dominate runs; deadline_s=300 default.
