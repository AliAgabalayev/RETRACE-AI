# A0 status for Celal (2026-10-09, Baku)

Format: completed / evidence / blocker / next. Items marked PENDING were not yet present at ~14:52; nothing is inferred. No credentials appear here (env var names only).

## 1. Base SHA chain
`b7aa8b8` (shared, origin/master, your audited base)
-> `08a0c3f` (`feature/gemini-provider`, exactly +1 commit: `judge.py` reasoning_effort, cache-key fix, 429/503 backoff; `configs/gemini.yaml`; `scripts/list_models.py`; `tests/vision/test_openai_provider.py`; `.env.example`; DECISIONS D16)
-> `feat/hackathon-vision-evidence` (Ali's branch): 08a0c3f -> cf861f1 (A0 dev12 selection + sheets, committed 14:47:50) -> 667925f (report evidence sidecar + ZIP exporter).
If you do not want the extra commit, cherry-pick `08a0c3f` onto a branch from `b7aa8b8`. Nothing is merged to master.

## 2. Input IDs (dev split, chosen before any model output)
Source: `configs/ali_dev12.json` (seed 20261009, script `scripts/ali_select_dev12.py`). Strata, formed from (label class, media_source): S0 Youtube-Cutscene 6 of 6 available (the clean pairs), S1 UnityCapturesDataset 3 of 26, S2 Youtube-Cutscene 3 of 8. Dev split only; nothing from eval was used to fill.

dev12, in seeded order:
1. vr_a981c1d3 (Cutscene)
2. vr_330651ed (Cutscene)
3. vr_4255ae09 (Cutscene)
4. vr_09a066d3 (Cutscene)
5. vr_59af7164 (Cutscene)
6. vr_41bab231 (Cutscene)
7. vr_4b921c5d (Unity)
8. vr_d07179d5 (Unity)
9. vr_c1f47c57 (Unity)
10. vr_fec26436 (Cutscene)
11. vr_ef9b073a (Cutscene)
12. vr_43773eb8 (Cutscene)

Counts: 6 clean + 6 bug as targeted, with bugs 3 Unity (S1) + 3 cutscene (S2); all 6 clean are cutscene. Unity is therefore bug-only, so source and clean/bug are confounded: do not read a Unity-vs-cutscene difference as a model effect. Per-ID clean/bug class is intentionally not stored in the json. Availability (6 / 26 / 8) is consistent with the expected 6 clean + 34 bug dev pairs.

Balanced-six fallback (predeclared rule: first 3 of S0, first 2 of S1, first 1 of S2 in seeded order = 3 clean, 2 Unity bug, 1 cutscene bug):
vr_a981c1d3, vr_330651ed, vr_4255ae09, vr_4b921c5d, vr_d07179d5, vr_fec26436.

## 3. Image bundle and hash inventory
`artifacts/ali/bundle/<id>/{reference,candidate}.png` for the 12 IDs, plus `artifacts/ali/inventory.json`. Checked at write time: 12 samples, 24 image rows, 0 sha256 mismatches between bundle files and the inventory. Each image row has bundle_path, source_path, width, height, sha256; each sample has dataset_revision `2afbfdcc9cb84318845f348c023bb2e92b942e29` and its rules (A1 allow, D1 deny).
Reference sizes (w x h): 1278x715, 1279x718, 1278x718, 1278x718, 1139x634, 1278x714, 3840x2160 (x3, the Unity pairs), 1120x627, 1273x717, 1278x574. The three 3840x2160 Unity images are much larger than the rest, so resize/pad mapping and VLM input scaling matter for them.
Copied from `data/work/<id>/`; no download, `prepare_data.py` not run. Re-verify sha256 after you copy the bundle.

## 4. Scope / rules proposal
- Rules: the benchmark's own, per DECISIONS D8: `A1` allow = ACCEPTABLE block verbatim; `D1` deny = UNACCEPTABLE block verbatim (only 2 distinct question texts exist in the subset, so rule-awareness is barely exercised by the benchmark).
- Cutscene and Unity are different families. A mixed-source dev12 is a diagnostic, not a single-game evaluation; HUD is not claimed.
- Out-of-scope cases are marked before inference and kept in the results.
- Human labels (Ali) live only in `docs/ali/labels_ali.csv`, frozen before any model output; they never reach a prompt. Status: PENDING (empty `labeling_sheet.csv` and contact sheets exist).
- The same 12 dev cases after tuning are a development diagnostic, not held-out generalization. The 60-case eval set is a historical regression set.

## 5. Runtime and host
Source: `docs/ali/runtime_inventory.md` (dl-engineer probe, ~14:55-15:05).
- Local Ollama `qwen2.5vl:3b` does NOT load right now: HTTP 500, needs ~9.1 GiB, host had 8.5-9.0 GiB available (total 15.2 GB; browsers and IDE are the main users). It may load after closing apps; not verified. D10 latency (~85 s/pair, CPU) is old, not re-measured today.
- Working path today: Gemini via the OpenAI-compatible provider, model `gemini-3.5-flash`. One real request on `vr_59af7164` (in dev12), config `configs/ali_runtime_probe_gemini.yaml`, fresh cache dir `data/cache_ali_fresh`, `is_mock: false`, `engine_mode: real`, prompt v9, config_hash `6918913ae7ba`, DINOv2 `dinov2_vits14` on cuda. Duration: CLI wall 30.8 s; pipeline 25.8 s (region call 4.9 s, scene-audit call 20.0 s, DINOv2 0.26 s); peak RSS 1.26 GB. Both calls succeeded; 2 of 20 daily calls used.
- Outcome of that one pair: `NEEDS_REVIEW` (single full-frame proposal, the D10 global-change collapse with `truncated=true`; scene audit reported extra changes); judgments `allowed` / A1 (clothing change). This proves the path works, not that results are good; no ground truth was consulted. Artifacts: `artifacts/ali/first_response/` (analysis.json, report.md, cli_stdout.json, rules yaml).
- Quota consequence: up to 9 calls per pair on the Gemini free tier (20/day/model) means about 2 full pairs per day, so a 12-pair run is infeasible on this quota. It needs Qwen to load, or a quota-backed model. Note `configs/gemini.yaml` names `gemini-3.8-flash` (exhausted today); `gemini-3.5-flash` appears only in the probe config.
- Host rules: the single inference host is Ali's machine. One VLM job at a time, guarded by lock file `artifacts/ali/vlm.lock` (held during calls, removed afterwards). Celal must NOT launch VLM jobs on this host or compete for its GPU/Ollama; ask Ali to run them. `qwen3:8b` is not a vision model. Your Windows checkout has no cv2/models/images, so run from the bundle; any mock must be labelled as a mock.

## 6. Manifests unchanged (verified by sha256 prefix at write time)
| file | sha256 prefix |
|---|---|
| `data/manifests/inference_manifest.json` | 245815f5191e6708 |
| `data/manifests/eval_labels.json` | a10ab8dd2f936ada |
| `data/manifests/eval_subset_60.json` | ff765d14428cd944 |
Do not run `prepare_data.py` (it rebuilds them).

## 7. Known facts
- Gemini free tier: 20 requests/day per model; `gemini-3.8-flash` (the model in `configs/gemini.yaml`) is exhausted today. Quota must not be spent on ad-hoc tests.
- The OpenAI key has no credits.
- Historical E2/E4 numbers are not measurements of today's build; do not cite them as current results.
- Audit targets (10/12 observations, 0/6 bug false-PASS, >=4/6 clean PASS, coverage >=6/12) are engineering targets, not promised results.

## 8. Blockers
- No working local VLM: Ollama qwen2.5vl:3b is RAM-bound (needs ~0.1-0.6 GiB more); Gemini `gemini-3.8-flash` exhausted; OpenAI has no credits; `gemini-3.1-pro-preview` has no free quota (D16). Only `gemini-3.5-flash` worked, with about 18 of 20 daily calls left (assuming no other users of the key).
- Human labels not delivered: `docs/ali/labeling_sheet.csv` and 12 `contact_sheet_<id>.png` exist but the label columns are empty; `docs/ali/labels_ali.csv` does not exist yet (PENDING, Ali). A1 scoring cannot start before labels are frozen.
- Verified: `configs/ali_dev12.json` was committed in cf861f1 at 2026-10-09T14:47:50+04:00, before the first model output (Gemini probe run 20261009T105011Z = 14:50:11; earlier Ollama warmups failed and produced no output). The probe pair vr_59af7164 was picked from the dev split without knowledge of the dev12 list; it happens to be in dev12. Ali has not seen that output before labeling.
- If there is no working vision path at 15:15, environment recovery has priority and A1 is reported as not measured.

## 9. What Celal needs to run without a bulk download
1. Check out the branch (base chain in section 1).
2. Copy `artifacts/ali/bundle/` and verify against `artifacts/ali/inventory.json` (sha256).
3. Use `configs/ali_dev12.json` for IDs and the D8 rules; keep labels out of inference.
4. Do not start VLM jobs on Ali's host (section 5); ask Ali for runs.
Next: Ali sends this message himself after the PENDING items are filled.
