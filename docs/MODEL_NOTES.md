# MODEL_NOTES (dl-engineer)

Status vocabulary: implemented = code exists; loaded = model loaded for real; ran = executed on real input; measured = number recorded below.
Everything below marked MEASURED comes from real runs in this repo (`artifacts/dl_smoke/`). Dev/synthetic data only; the eval split was never used.

## 1. Models actually used
| Component | What | Revision / identity | Device / dtype | Status |
| --- | --- | --- | --- | --- |
| Features | frozen DINOv2 ViT-S/14 via `torch.hub.load("facebookresearch/dinov2","dinov2_vits14")` | repo `main` (hub zip, no commit pin available offline), weights `dinov2_vits14_pretrain.pth` sha256 `b938bf1bc15c...` (prefix recorded in `FeatureExtractor.version`) | cuda (RTX 3060 6 GB), float32 | loaded + ran + measured. Works on Python 3.13 / torch 2.12 (only an xFormers-not-available warning). transformers `facebook/dinov2-small` fallback is implemented but was NOT exercised. |
| VLM | Ollama `qwen2.5vl:3b` (id `fb90415cde1e`, 3.2 GB), `/api/chat`, JSON-schema `format`, temperature 0 | local | **CPU only** (see 6) | loaded + ran + measured |
| Mock VLM | `provider: mock`, `mock:<behavior>`, `is_mock=True` | - | - | tests only |

DINOv2 cost: load ~6 s, first call 0.25-0.6 s (CUDA init), steady state 0.03-0.1 s per pair (518 long side, ~37x21 patches).

## 2. Preprocessing and coordinate mapping (identical for both images)
1. `aligned_candidate` has exactly the reference HxW (alignment resizes/warps candidate into the reference frame).
2. Resize so the long side = `features.input_long_side` (518; `scale = 518/max(H,W)`), INTER_AREA down / CUBIC up.
3. ImageNet mean/std normalisation, zero-pad bottom/right to a multiple of 14 (`PreprocInfo`: new_h/new_w, pad_h/pad_w, grid).
4. `forward_features(x)["x_norm_patchtokens"]` -> (gh*gw, 384); L2-normalise; distance = `1 - cos` per patch -> (gh, gw) grid. CLS token is never used as a spatial map.
5. Back to reference pixels: crop grid to the valid (unpadded) cells, bilinear-upsample by 14 px, crop to new_h x new_w, resize to (W,H). Patch (gy,gx) covers reference box `[gx*14/s, gy*14/s, (gx+1)*14/s, (gy+1)*14/s]` (`patch_to_reference_box`); tested in `tests/vision/test_geometry.py`.
6. Transform direction (alignment): `candidate_to_reference` 3x3, `aligned = warpAffine(candidate, M[:2], (W,H))`. Pixels outside the valid overlap are filled with the reference pixels (so they compare equal and create no border features) and are 0 in `overlap_mask`; proposals additionally erode the mask by `mask_erode_px` (7) before thresholding (fixes QA-D4: blur leaking the black warp border into a full-frame box).

## 3. Alignment (`alignment.py`)
Identity when same size and residual (mean abs gray diff) < 2. Different size -> resize candidate to reference (status RESIZED; aspect-ratio mismatch > 2% -> UNRELIABLE). Otherwise global phase-correlation translation and ORB+RANSAC `estimateAffinePartial2D` (rotation + uniform scale + translation; never local warps / optical flow). A warp is adopted only if its residual < `min_error_gain` (0.7) x identity residual, shift <= `max_shift_fraction` (translations up to 2x the limit are evaluated so over-limit shifts are reported as UNRELIABLE with diagnostics), overlap >= `min_overlap_fraction`. Unreliable -> identity-warped candidate is returned. Tests: known (12,-8) shift recovered to <0.5 px; residual 0 inside overlap. Not measured on real pairs with drift (none of the real pairs needed warping: all 38 non-failed dev pairs were `identity`, 2 YouTube pairs `unreliable`).

## 4. Proposals (`proposals.py`) and thresholds
- Sources: DINOv2 map > `dinov2_threshold` (0.35); classical = |blur(gray ref) - blur(gray cand)| > `classical_threshold` (40) with a robust global gain/offset fit first (so a global lighting change does not flood the diff; the gain is estimated from 10-90 percentile spread, local object changes do not move it). Morphology close (~1% of the short side), 8-connected components, `min_area = max(min_area_px 40, min_area_fraction 0.0001 * H*W)` (QA-D5: 12 px coin = 113 px area is now kept), box padding 8 px, merge when IoU > 0.1 or containment > 0.5, clip, sort by score, cap `max_regions` (8).
- Score = max(signal / its source threshold) in the box, i.e. "x times the threshold"; comparable across sources (fixes the crowd-out problem), still not a probability. Source = `dinov2` / `classical` / `union` (merged across sources).
- `Coverage.truncated` is set if the cap drops proposals OR the raw component limit (200/source) is hit OR the global-change collapse below fires.
- **Global-change collapse** (dev-tuned): if >= 10% of the valid area is above the DINOv2 threshold, return ONE full-frame proposal with `truncated=True` (cannot PASS automatically). On the 40 dev pairs, every YouTube cutscene pair (6 no_bug + 8 bug dev pairs) had 12-72% of pixels above 0.35 (except one at 22%... all >= 11.7%) and several produced 20-40 merged fragments (-> 8 capped VLM calls ~ 4 min per pair, measured 224-239 s); fixed-camera Unity pairs mostly had 0-4%.
- How thresholds were chosen: dev split only (40 pairs) + synthetic fixtures. Varying the DINOv2 threshold 0.35/0.45/0.55 changed fragment counts but gave no better separation on dev (counts per dev pair are in `docs/status/dl-engineer.md`), so the default 0.35 was kept. NOT a calibrated detector.
- Synthetic fixture findings (MEASURED): removed barrel -> dinov2+classical union box around it (DINOv2 max distance 0.82); 12 px coin removed -> DINOv2 max 0.35 (right at threshold, NOT reliably detected), classical catches it (score 1.8x threshold) -> classical fallback is justified; global lighting -> no full-frame box after gain normalisation (1 tiny DINOv2 box on the sun); small clothing recolour -> no proposal from either source (allowed change, but it also shows a real recolour can be missed); 12 px translation -> ALIGNED, zero proposals.

## 5. VLM judge (`judge.py`, `prompts.py`), `PROMPT_VERSION = v9`
- Input to the VLM per region (changed from the first plan, see 7): ONE composite image BEFORE|AFTER of the crops (captions burned in, small crops upscaled to >= 160 px short side, hard minimum 28 px because Ollama crashes below that), plus the region box in reference coordinates in the text. Whole-scene audit: one composite of both full images (<= 512 px per half) with yellow boxes + IDs for already-judged regions. Context image is optional (`vlm.use_context`, default off).
- Two stages: stage 1 (image, no rules) -> `before_shows, after_shows, observed_change, change_type, any_difference` (+ `other_changes_outside_boxes` for the audit); stage 2 (text only) -> `verdict, rule_ids, evidence` given the stage-1 text and the rules with IDs verbatim plus explicit ALLOW/DENY ID lists. Both stages use Ollama `format=<JSON schema>`, temperature 0, `num_ctx 2048`, `keep_alive 30m`, `use_mmap`.
- Validation (`validate_response`): JSON parse (code fences stripped), required keys, verdict enum, every rule_id exists, `forbidden` must cite >= 1 deny rule and no allow rule and have evidence; `allowed` must cite no deny rule, have evidence, cite an allow rule OR (no rule and `any_difference=false`, change_type none/other = "no visible change"); `allowed` with change_type `disappeared`/`distorted_or_corrupted`, or whose text matches missing/removed/gone/... while a deny rule exists, is an internal contradiction -> uncertain (an explicit allow rule for removals would be blocked too: documented trade-off, review is the safe side). Any failed check -> `verdict=uncertain, validated=False, errors=[...]`. Provider errors/timeouts/malformed JSON never raise (`attempts` = `max_attempts`, 3 s back-off). Self-reported confidence is not used.
- Scene audit safeguards: (a) deterministic shortcut `model="deterministic:pixel-identical"` (NOT a VLM result, `is_mock=False`) only if there are no proposals, <= 8 pixels differ by > 6 gray levels in any channel, and no blurred residual; (b) a validated `forbidden` audit verdict with no pixel residual outside the judged boxes is downgraded to `uncertain` (3B hallucinated "forbidden" on identical pairs: MEASURED); (c) an unvalidated audit never sets `extra_changes_reported`.
- Cache: `data/cache/vlm/<sha256(image arrays, prompt, schema, model, prompt_version, temperature, num_ctx)>.json` stores the raw reply only (re-validated on every read); errors are not cached.
- `warmup()` loads the model (cold load 55-70 s). `pipeline.build_engines` calls it BEFORE loading DINOv2 (see 6).

## 6. Hardware / Ollama findings (MEASURED, important)
- Ollama (system service, v0.21) runs `qwen2.5vl:3b` **100% on CPU**: its qwen2.5vl graph reservation is a fixed 6.7 GiB compute buffer (+3.2 GiB weights) that never fits the 6 GB GPU (CUDA OOM at 7.3 GiB), independent of `num_ctx`, `num_batch`, `num_gpu` or request options. A private `ollama serve` with `OLLAMA_FLASH_ATTENTION=1` showed the same 6.7 GiB graph (tested, removed). Fixing it needs a different/smaller VLM or server-level changes the owner must make.
- Consequence 1: each VLM call costs 17-35 s (region stage 1+2 ~ 20 s, audit ~ 35 s) and the model needs ~9.3 GiB of free RAM at load. With Brave/Spotify/other agents running the load failed repeatedly with "model requires more system memory (9.x GiB) than is available". Loading the VLM first (before torch/CUDA take ~1.5 GiB), `num_ctx 2048` and serial runs made it succeed. Run `ollama stop` / free RAM before long runs.
- Consequence 2: the brief's 30 s request timeout is below the audit call (~35 s); `vlm.timeout_s` was raised to 75 in `configs/default.yaml` (record in DECISIONS).
- Tiny crops (< 28 px side) make Ollama's qwen2.5vl preprocessing panic (HTTP 500, runner restart) -> crops are upscaled (found from the Ollama log).

## 7. Prompt development (synthetic fixtures + dev only; each variant measured on 3-7 fixtures, not statistically meaningful)
| version | change | observation |
| --- | --- | --- |
| v1 | 3 separate images, rules + schema in one prompt | invalid/unknown IDs ("A21: "), cited allow rule for a removed object, 25-70 s calls (cold load + timeouts) |
| v2-v5 | explicit allow/deny ID lists, JSON example, "evidence always" | model **copied the example text** ("character is gone") onto every pair incl. identical ones; echoes rule descriptions (A2 "clothing colour") |
| v6 | describe each image first | both crops described identically ("red and black bar"): the 3B model does not compare several separate images |
| v7 | ONE composite BEFORE\|AFTER image | model now sees changes (observed_change correct, 17-20 s), but still maps them to rules badly (cites A1+A2 for a removed barrel) |
| v8 | `change_type`, `any_difference` fields + contradiction checks | contradictions caught -> uncertain; still false `allowed` when the model calls a deletion "replaced" |
| v9 | two-stage (image without rules, then text-only rule decision) | removed barrel -> forbidden D1 (validated); removed 12 px coin -> forbidden D1; allowed_and_forbidden R1 -> forbidden D1; tiny lighting region -> uncertain. Scene audit remains the weakest part. |

## 8. Measured results
See `docs/status/dl-engineer.md` for the fixture table and the dev latency table (filled from `artifacts/dl_smoke/`).

## 9. Known misses / next bounded experiment
- A uniform clothing/colour change of a small region is not proposed by either source at the current thresholds (fine for allowed changes, bad for e.g. texture corruption of a similar magnitude).
- The 3B VLM: weak rule mapping, hallucinates on whole-scene audits, always very slow on CPU. Next bounded experiment: run the same prompts with a larger/GPU-capable VLM (needs owner decision) and compare on dev; or shrink the stage-1 image further and measure the quality/latency trade-off.
- Cutscene (YouTube) pairs differ globally even for no_bug pairs: DINOv2 patch distance cannot localise anything there; the global-change collapse only keeps the run bounded.
- Dev-tuned global-change fraction (0.10) is a coarse cut: 3 of 22 Unity dev pairs exceed it too.
