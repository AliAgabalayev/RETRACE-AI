# Real-browser UI check + live timing (2026-10-09 ~16:40–17:05 Baku)

Branch `feat/hackathon-vision-evidence` (HEAD af48ead). Fresh Streamlit instance on port 8502 (`.venv/bin/streamlit run app.py --server.port 8502`), driven in Chrome via Claude in Chrome. The owner's own instance on :8501 (started ~11:30, older code) was not touched.

## Live wall time (fresh, empty cache namespace; model already resident in RAM)
Command: `gameqa.cli analyze ... --config <ali_a1_qwen.yaml with cache_dir data/cache_ali_live_<HHMM>>`; 12 VLM calls, 0 cache hits (dump calls.jsonl).

| pair | decision | wall (CLI incl. DINOv2 load) | pipeline total | region judge | scene audit |
|---|---|---|---|---|---|
| vr_4b921c5d | NEEDS_REVIEW | 100.1 s | 83.7 s | 35.7 s | 42.0 s |
| vr_09a066d3 | NEEDS_REVIEW | 92.7 s | 72.8 s | 29.1 s | 42.5 s |
| vr_330651ed | NEEDS_REVIEW | 109.5 s | 85.4 s | 37.3 s | 45.8 s |

Cold model load adds ≈ 55 s (measured 15:20). Decisions identical to A1/A3. Qwen 2.5-VL 3B runs on CPU (D10).

## Browser checks (all PASS unless noted)
| # | Check | Result |
|---|---|---|
| 1 | App loads, sidebar (Engine, Saved runs, Reload models) | PASS |
| 2 | Load saved run vr_4b921c5d (A1) → NEEDS REVIEW banner, engine label real, R1 box on both images, R1 crops (barrel present → absent), observed/evidence text, scene audit, Diagnostics (alignment identity, coverage, timings, versions incl. config_hash 3a144cfcbb67) | PASS |
| 3 | Demo pair → synthetic `object_removed`, real engine, Analyze → **FAIL: R1 (D1)** in ~20 s (VLM answers from disk cache); audit validation error shown in red | PASS |
| 4 | Approve guard on a FAIL run: warning "Approving overrides the tool's verdict", button disabled until both confirm + override ticked; approve → "v1 → v2 (ui_check_ali)"; `references/ui_check_ali/history.json` has both events with sha256 + run_id | PASS |
| 5 | MOCK engine (timeout): sidebar warning + "MOCK ENGINE: … NOT real model inference" banner; NEEDS REVIEW with the injected timeout in the reason | PASS |
| 6 | Upload two images (lighting_change fixture) → previews → Analyze | PASS |
| 7 | Repeated Analyze on identical inputs does not re-run inference (run dirs 122 → 122) | PASS |
| 8 | Browser console errors | none |

## Defects / notes (UI owned by Celal — reported, not changed)
- **Export ZIP on this branch lacks `evidence.json`** (UI export of run 20261009T124155Z-b4f0f1: 11 files, no evidence.json). Expected: the export hook lives on Celal's `feat/hackathon-demo-integration` (0e234d8). Record the video on Celal's branch, or use `artifacts/ali/demo_zips/` (evidence included).
- Loaded saved runs are not labelled as "saved run / replay" in the UI — the video must label them.
- After "Load saved run", the Rules editor still shows the page's current rules, not the loaded run's rules.
- Typing into the Approve "Reference ID" field reruns the page and collapses the Approve expander (value is kept; re-open to continue).
- The ZIP download button itself was not clicked (browser file download needs explicit owner permission); the server-side ZIP was checked instead.
- Test reference `references/ui_check_ali/` was created by this check (local, git-ignored).
