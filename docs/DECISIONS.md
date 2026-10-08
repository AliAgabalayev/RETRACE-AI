# Decisions log

Owner: senior-pm. Agents propose changes; senior-pm records them here.

## D1 — Environment (2026-10-09, hour 0)
- Python 3.13, `.venv` created with `--system-site-packages` to reuse the already-installed `torch 2.12.0+cu130` / `torchvision 0.27` (avoids a multi-GB download). Streamlit 1.65 installed into `.venv`.
- GPU: NVIDIA RTX 3060 Laptop, 6 GB VRAM, CUDA available. 16 cores, 14 GB RAM. Disk: ~40 GB free → never download the full 33.4 GB dataset.
- Run everything with `.venv/bin/python`.

## D2 — VLM provider (hour 0)
- Probed credentials (values never printed): `OPENROUTER_API_KEY` → HTTP 401 "API key expired". `NVIDIA_NIM_API_KEY` and `KIMI_API_KEY` → 401, values look like placeholders. No working cloud VLM.
- Decision: use a **local Ollama VLM** (free, real inference, no new purchases). Primary: `qwen2.5vl:3b` (pulled hour 0). Already installed fallback: `moondream:latest` (weaker, no reliable JSON).
- VLM adapter must stay provider-agnostic (`provider: ollama | mock`) so a cloud provider can be added later via config.

## D3 — Frozen contracts (hour 0)
- `src/gameqa/contracts.py` is frozen. Image order = (reference, candidate). Boxes `[x1,y1,x2,y2]` reference pixels, right/bottom exclusive. Transform = 3x3 candidate→reference.
- `src/gameqa/decision.py` is the single decision policy. FAIL requires a real, validated judgment citing a deny rule with evidence. Mock / invalid / uncertain / truncated / missing audit / unreliable alignment → NEEDS_REVIEW.
- `configs/default.yaml` holds all thresholds, caps, timeouts.

## D4 — Module interfaces (hour 0)

```python
# src/gameqa/vision/alignment.py  (dl-engineer)
def align(reference: np.ndarray, candidate: np.ndarray, cfg: dict) -> tuple[AlignmentResult, np.ndarray, np.ndarray]:
    """RGB uint8 HxWx3 inputs. Returns (result, aligned_candidate in reference frame, overlap_mask uint8 HxW 0/255)."""

# src/gameqa/vision/features.py  (dl-engineer)
class FeatureExtractor:
    def __init__(self, cfg: dict): ...           # loads frozen DINOv2, eval(), records version/device/dtype
    version: str; device: str; dtype: str
    def distance_map(self, reference: np.ndarray, aligned_candidate: np.ndarray) -> np.ndarray:
        """float32 map in REFERENCE pixel resolution (HxW), 1 - cosine similarity, upsampled from patch grid
        with resize/pad undone."""

# src/gameqa/vision/proposals.py  (dl-engineer)
def propose(reference, aligned_candidate, overlap_mask, dino_map: np.ndarray | None, cfg: dict) -> tuple[list[RegionProposal], Coverage]:
    """Union of dinov2 + classical proposals, merged, padded, capped (cfg.proposals.max_regions). Coverage.truncated set if capped."""

# src/gameqa/vision/judge.py  (dl-engineer)
class Judge:
    def __init__(self, cfg: dict): ...
    model_id: str; prompt_version: str; is_mock: bool
    def judge_region(self, proposal, ref_crop, cand_crop, ref_context, cand_context, rules) -> RegionJudgment: ...
    def audit_scene(self, reference, aligned_candidate, rules, proposals) -> SceneAudit: ...
    # Never raises on provider errors: returns verdict=uncertain with errors filled.

# src/gameqa/pipeline.py  (python-developer)
def analyze(pair: PairInput, cfg: dict, *, judge: Judge | None = None, extractor: FeatureExtractor | None = None) -> AnalysisResult:
    """Validates input, aligns, extracts, proposes, crops, judges, audits, calls decision.decide, writes artifacts."""

# src/gameqa/storage.py  (python-developer)
def new_run_dir(cfg) -> tuple[str, Path]; def write_json_atomic(path, obj); def export_report(result, run_dir) -> Path (report.md + zip)
def approve_reference(reference_id: str, candidate_path: str, run_id: str, cfg) -> dict  # new version, history.json audit event
```

Crops: `ref_crop = reference[y1:y2, x1:x2]`, `cand_crop = aligned_candidate[y1:y2, x1:x2]` (same reference box). Crops are saved under `artifacts/<run_id>/crops/<region_id>_{ref,cand}.png`.

## D5 — Data responsibilities (no Data Engineer)
- `python-developer`: download/prepare utilities (`src/gameqa/data/`), manifest writer.
- `experiment-tracker-pm`: selection criteria, dev/eval split protocol, `docs/DATA_CARD.md`, experiment registry.
- `qa-engineer`: label/order checks, evaluation-only manifest consumption, scoring.

## D6 — Policy fixes from QA (session 2)
- QA-D1/D2: an `allowed` judgment supports PASS only if validated, non-mock, error-free, has non-empty evidence and cites no deny rule (`decision.is_acceptable_allowed`). Otherwise NEEDS_REVIEW.
- QA-D3: `decision.find_rule_conflicts` flags duplicate rule IDs and identical descriptions declared both allow and deny → NEEDS_REVIEW. Deeper semantic conflicts are delegated to the VLM (must answer `uncertain`). Computed inside `decide`, so no pipeline change.

## D7 — Splits and evaluation budget (session 2)
- Data facts (verified by DATA/experiment-tracker): 250 visual-regression pairs, revision `2afbfdcc9cb84318845f348c023bb2e92b942e29`; 224 bug / 26 no_bug; all no_bug are Youtube-Cutscene; all 171 Unity pairs are bug. Source confounds label → results reported per source; primary metric = balanced accuracy (review→FAIL), per experiment-tracker protocol in `docs/EXPERIMENTS.md`.
- Final splits (seeded, stratified by media_source × label): demo 5 (≥2 no_bug), dev ≥ 6 no_bug + ≥ 10 bug (both sources), eval = everything else. Thresholds/prompts tuned on dev + synthetic fixtures only.
- E2 (real pipeline) runs on a stratified 60-pair eval subset (≈20 no_bug, 20 cutscene bug, 20 Unity bug), chosen by seeded script before any result is seen; cut to 40 if >90 s/pair. E1 classical and E4 VLM-only run on the same IDs (E1 also on full eval). E2b (classical-only proposals + VLM) only if time remains.
- Qwen2.5-VL-3B license treated as non-commercial (Qwen Research License) until verified; noted in THIRD_PARTY_NOTICES.
