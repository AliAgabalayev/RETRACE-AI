# Runtime inventory (WP0.5), 2026-10-09 ~14:55-15:05

Owner: dl-engineer. No secrets in this file (a `GEMINI_API_KEY` is present in git-ignored `.env`; value never printed).

## Verdict

- Local Ollama `qwen2.5vl:3b`: **does NOT load right now (host RAM short)**.
- Working path: **Gemini via OpenAI-compatible provider, model `gemini-3.5-flash`** (one real request succeeded).
- Not tried: OpenAI/OpenRouter (D16: OpenAI account has no API credits, HTTP 429 `insufficient_quota`).

## Host probe

| Item | Observation |
|---|---|
| RAM at probe | total 15212 MB, used ~10.4 GB, free 239 MB, available ~4.8 GB; swap 3.3 of 8.2 GB used |
| Main RAM users | PyCharm ~1.5 GB, several Brave renderers, Spotify, Claude Code |
| GPU | 391 MiB used / 6144 MiB (not usable by the qwen2.5vl vision graph, D10; DINOv2 ran on `cuda`) |
| Ollama | v0.21.0 reachable at localhost:11434; models: qwen2.5vl:3b (3.2 GB), moondream, qwen2.5:0.5b, gemma2:9b; nothing loaded (`ollama ps` empty) |
| `Judge.warmup()` (default config) | attempt 1: `ok: False, status 500` after 13.5 s; attempt 2 after 60 s: `status 500` after 6.3 s; attempt 3 (raw API, after another 90 s): same |
| Ollama error text | "model requires more system memory (9.1 GiB) than is available (9.0 GiB)"; third try "8.5 GiB than is available (8.5 GiB)" |

Ollama needs about 9.1 GiB for qwen2.5vl:3b; the host had 8.5-9.0 GiB available. It is within roughly 0.1-0.6 GiB of loading, so closing one browser or the IDE would probably be enough (not verified). Retry the warmup once memory is freed. If it loads, Qwen cold load is 55-70 s and ~85 s per pair (D10, measured earlier, not re-measured here).

## One real response (Gemini fallback)

- Pair: `vr_59af7164` (split `dev`, 1139x634 working images; eval-split IDs not used). `configs/ali_dev12.json` does not exist yet, so a dev-split ID was taken from `data/manifests/inference_manifest.json`. Rules from that manifest entry (A1 allow, D1 deny): `artifacts/ali/first_response/rules_vr_59af7164.yaml`.
- Command: `.venv/bin/python -m gameqa.cli analyze --reference data/work/vr_59af7164/reference.png --candidate data/work/vr_59af7164/candidate.png --rules artifacts/ali/first_response/rules_vr_59af7164.yaml --sample-id vr_59af7164 --config configs/ali_runtime_probe_gemini.yaml --json`
- Config `configs/ali_runtime_probe_gemini.yaml` = gemini.yaml settings with `model: gemini-3.5-flash`, `max_attempts: 1`, `transient_retries: 0`, `max_regions: 1` (cap of the probe to at most 2 calls; free tier is 20/day per model), and **`run.cache_dir: data/cache_ali_fresh`** (fresh namespace, empty before the run, so the result is live, not cached).
- Provider/model id recorded in the run: `openai-compatible@generativelanguage.googleapis.com:gemini-3.5-flash`, `is_mock: false`, `engine_mode: real`, prompt v9, config_hash `6918913ae7ba`, DINOv2 `dinov2_vits14` on cuda.
- Duration: wall time 30.8 s for the whole CLI process (includes Python and DINOv2 load); pipeline total 25.8 s: judge call 4.9 s (region), audit call 20.0 s, DINOv2 features 0.26 s. Peak process RSS 1.26 GB (`/usr/bin/time`); system `used` 10.1 GB after.
- Quota: both calls succeeded, no 429 seen. This used 2 of the 20 daily free calls for gemini-3.5-flash (remaining about 18, assuming no other users of that key).
- Raw judgments (validated, no errors):
  - R1 (full frame box [0,0,1139,634], source dinov2, score 2.52): allowed, rule A1: "clothing of the man in the center changed from a grey suit jacket and white shirt to a brown leather jacket and dark shirt".
  - Scene audit: allowed, rule A1, same observation; `extra_changes_reported: true`.
  - Decision: `NEEDS_REVIEW` ("proposals truncated (1/1 judged); scene audit reported changes outside proposals").
- Interpretation caveat: the single full-frame proposal is the D10 global-change collapse (area_fraction 1.0, `truncated=true`), not caused by the probe's `max_regions: 1` cap. NEEDS_REVIEW is policy-correct and says nothing about accuracy. One pair proves the path works, not that results are good. No ground truth was consulted.
- Artifacts: `artifacts/ali/first_response/analysis.json`, `report.md`, `cli_stdout.json`, `cli_stderr.txt`, `rules_vr_59af7164.yaml`. Full run dir (crops, images, diagnostics): `artifacts/20261009T105011Z-fbde6e` (not copied).
- VLM lock `artifacts/ali/vlm.lock` was held during the calls and removed afterwards. Ollama was not running a job.

## Paths that do NOT work (as of this probe)

1. Ollama `qwen2.5vl:3b` default config: HTTP 500, insufficient system memory (9.1 GiB needed). Not a software fault; RAM-bound.
2. `gemini-3.8-flash`: free-tier quota exhausted today (per task note; not re-tested here).
3. `gemini-3.1-pro-preview`: HTTP 429, no free-tier quota (D16).
4. OpenAI `gpt-4o-mini`: HTTP 429 `insufficient_quota`, no API credits (D16). OpenRouter: no key tested.
5. Mock provider is not real inference and is not counted.

## Not measured / caveats

- Qwen latency was not re-measured today (could not load); D10 numbers (84.8 s median per pair) are older.
- gemini-3.5-flash latency is from one pair with `reasoning_effort: low`, 1 region + 1 audit; the real 8-region cost is not measured and would use up to 9 calls per pair, so the 20/day free quota allows only about 2 full pairs. A 12-pair Gemini run is infeasible on this quota. A 12-pair run needs Qwen to load (free RAM) or a quota-backed model.
- Extra files I created: `configs/ali_runtime_probe.yaml` (Ollama probe override, `run.cache_dir: data/cache_ali_fresh`), `configs/ali_runtime_probe_gemini.yaml`, `data/cache_ali_fresh/` (contains the 2 cached Gemini answers; delete or ignore for later fresh runs, use a new namespace).
