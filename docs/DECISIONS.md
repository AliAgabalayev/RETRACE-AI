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
def analyze(pair: PairInput, cfg: dict, *, judge: Judge | None = None, extractor: FeatureExtractor | None = None, run_dir: Path | None = None) -> AnalysisResult:  # run_dir added by APP
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

## D8 — Benchmark question → rules (session 2)
- Original mapping put the whole question (including the ACCEPTABLE list and the benchmark's own "Provide your assessment as JSON {test_pass}" instruction) into one deny rule — contradictory and likely to hijack the VLM's output format.
- New mapping (`gameqa.data.manifest.rules_from_question`): `A1` allow = ACCEPTABLE block verbatim; `D1` deny = UNACCEPTABLE block verbatim; fallback D1 = whole question verbatim if no UNACCEPTABLE block. Full question stays in the manifest `question` field. All 250 records → (A1, D1). Manifest rules regenerated in place (no re-download). Only 2 distinct question texts exist in the subset, so rule-awareness is barely exercised by the benchmark; fixtures with A1/A2/D1/D2 cover multi-rule logic.

## D9 — QA-D7/D8 and alignment-dependent FAIL (session 2)
- QA-D7: a judgment citing any unknown rule ID can support neither PASS nor FAIL (→ NEEDS_REVIEW).
- QA-D8: a forbidden judgment counts toward FAIL only if it cites a deny rule that is NOT part of a detected rule conflict. Conflicted deny rule → NEEDS_REVIEW (brief §6: conflicts → review).
- Alignment: region crops cut the same reference box from both images, so under UNRELIABLE / FAILED / missing alignment a region-level "missing object" may be misregistration. In that case only the whole-scene audit (full images) can establish FAIL; region forbidden → NEEDS_REVIEW. This tightens the earlier "reliable forbidden always FAILs" reading: with bad alignment the forbidden evidence is not "reliable" in the brief's sense. Tests in `tests/policy/test_decision.py` updated accordingly by senior-pm (documented policy change, not a test weakened to fit a bug).
- QA-D6 (Ollama "requires more system memory"): transient RAM pressure from parallel agents (swap 6 GB used). Mitigation: real-VLM runs (smoke, E2, E4) run serially, one Ollama client at a time; the owner's desktop apps are not touched.

## D10 — Real-VLM operating point, frozen before E2 (session 2)
- Ollama runs qwen2.5vl:3b on **CPU** (its vision graph needs ~6.7 GiB, more than the 6 GB GPU; DINOv2 runs on CUDA). Measured on 10 dev pairs: median 84.8 s / p90 141 s per pair, ~20 s per region call, ~35 s per scene audit, cold load 55–70 s.
- `vlm.timeout_s` raised 30 → 75 s (brief default 30 s is infeasible on CPU; audit call alone ≈ 35 s). Max attempts stays 2.
- Prompt v9: one BEFORE|AFTER composite image; two stages (describe change without rules → text-only verdict against rules). Developed on fixtures + ~6 dev pairs only.
- Global-change collapse: if ≥10 % of the valid area exceeds the DINOv2 threshold, `propose` returns one full-frame region with `truncated=True` → never auto-PASS (tuned on dev). DINOv2 threshold 0.35 unchanged.
- Engine mode: only component failures (provider error / timeout / exception) mark a run `degraded`; a real answer rejected by validation stays `real/complete` and becomes NEEDS_REVIEW via `decide`.
- E2 runs on all 60 IDs of `eval_subset_60.json` (not cut to 40: cutting would need label-based re-selection; ~85–100 min is affordable). Config and prompt frozen at this commit; no changes during or after based on eval results.

## D11 — E2 result, known false PASS, post-eval cleanup (session 3, after power loss)
- Power loss during E4 (50/60 done). E2 had completed 60/60; prediction files validated line by line, E4 resumed with `--out` (resume) on the same frozen config.
- E2 (real DINOv2 + qwen2.5vl:3b, prompt v9, 60 eval pairs): 58 NEEDS_REVIEW, 1 FAIL (bug, correct), 1 PASS (bug → **false PASS**). Balanced accuracy (review→FAIL) 0.488, CI [0.464, 0.500]; review rate 0.967; median 70 s/pair. Hypothesis not supported at this operating point: the 3B VLM almost never commits.
- Known failure `vr_bcbcf341` (Unity, bug): DINOv2+classical proposal R1 `[1213,1973,3003,2160]` correctly covers the road where the ground texture is missing in the candidate, but the VLM described it as "license plate more visible" → `allowed A1`, and the scene audit said "brighter lighting" → `allowed A1`. Both validated → PASS. Policy behaved as designed; the failure is VLM judgment quality. NOT fixed by tuning (would use an eval label). Repro: `.venv/bin/python -m gameqa.cli analyze --reference data/work/vr_bcbcf341/reference.png --candidate data/work/vr_bcbcf341/candidate.png --rules <A1/D1 from manifest>` (see HANDOFF).
- Post-eval cleanup (no behaviour change; yaml values unchanged): `contracts.SCENE_REGION_ID`; judge fallback defaults now mirror yaml (75 s / 336 / 512 / 2048); dead `prep_crop` and unused prompt fields removed; misleading `vlm.prompt_version: v1` yaml key replaced by a pointer to `prompts.PROMPT_VERSION` (v9); mock review reason now includes the injected error; Streamlit sidebar "Reload models" clears cached engines after a load failure.
- E4 (VLM-only whole-scene audit, same 60 IDs, same model/prompt v9): 43 PASS, 17 NEEDS_REVIEW, 0 FAIL; **33/42 bug pairs → PASS** (false PASS); balanced accuracy (review→FAIL) 0.385. Interpretation: proposals + per-region validation do not raise accuracy over chance, but cut dangerous false PASS from 33/42 (E4) to 1/42 (E2), at the price of a 97 % review rate.

## D12 — E1 threshold re-tuned on the final dev split (session 3)
- experiment-tracker-pm found `classical_threshold.json` had been tuned on an interim split: 23 of its 37 "dev" IDs are now in eval (2 in the 60-subset). Old threshold/runs kept as `*.stale_*` for audit.
- Re-tuned with `scripts/evaluate.py tune-classical` on the current dev split (40 IDs, all verified `split=dev`): threshold 0.782 changed-pixel fraction (pixel_thr 25), dev BA 0.515. Re-ran E1: subset60 BA 0.524 (58 PASS / 2 FAIL), full eval BA 0.516 (199 PASS / 6 FAIL) — identical to the stale runs, so conclusions are unchanged; numbers are now leakage-clean. `paired_comparison.json` regenerated.
- Hypothesis verdict (experiment-tracker-pm, pre-declared rule): **NOT SUPPORTED** at this operating point. Caveat recorded: 53/60 E2 runs were truncated (37 global-change collapse, 16 region cap), so E2's low false-PASS rate is mostly abstention.

## D13 — QA final pass: QA-D10/D11 fixed, D12–D15 recorded (session 3)
- QA-D10: `Judge._ask` no longer returns earlier-attempt notes when a retry produced a usable answer (they made valid answers NEEDS_REVIEW and runs non-reproducible). Test `tests/vision/test_judge.py::test_recovered_retry_leaves_no_judgment_errors`.
- QA-D11: alignment fills pixels outside the valid overlap with reference pixels, so that strip is never compared. `decision.MIN_OVERLAP_FOR_PASS = 0.98`: below it, PASS is blocked with reason "N% of the reference was not compared"; FAIL from compared regions still stands. Consequence: shifted captures (e.g. `small_translation` fixture, overlap ≈ 0.97) now end NEEDS_REVIEW (its expected.json allows it). Tests in `tests/policy/test_decision.py`.
- Open (minor, documented in HANDOFF): QA-D12 mock provider + pixel-identical audit shortcut can yield PASS labelled engine `mock`; QA-D13 a judge exception is labelled real/COMPLETE; QA-D14 a "no visible change" answer is accepted as allowed without a rule ID; QA-D15 E2 `run_meta.json` commit field says 3022ec8 [was 0b3cc1b] (written by evaluate.py from HEAD at start) — the frozen identity is `config_hash 8e6c97c0395c` + prompt v9, identical for E2 and E4.
- E1/E2/E4 numbers were produced before D13; D10/D11 would only change runs with retries (E2: 0 provider errors) or partial-overlap alignment (all E2 dev/eval runs were identity/unreliable per dl-engineer), so the reported numbers stand.

## D14 — OpenAI-compatible VLM provider (owner request, 2026-10-09)
- Owner asked for a GPT API option next to the local Qwen. This is an explicit owner decision overriding the brief's "no new paid providers" default for this provider only; default config stays `ollama` / `qwen2.5vl:3b`, so all reported results (E1/E2/E4) are unchanged.
- `vlm.provider: openai` = any OpenAI-compatible Chat Completions endpoint (`judge.Judge._openai_reply`): images as base64 PNG `image_url`, `response_format: json_schema`, same prompts v9, same validation, same decision policy, same disk cache (keyed by model id). Ready configs: `configs/openai.yaml` (`OPENAI_API_KEY`, `gpt-4o-mini`), `configs/openrouter.yaml` (`OPENROUTER_API_KEY`, `openai/gpt-4o-mini`).
- Keys come from environment variables, loaded from the git-ignored `.env` (`config.load_env_file`, python-dotenv; real env vars win). `.env.example` is committed with placeholders. A missing or placeholder key never calls the API: it becomes a provider error → judgment `uncertain` → NEEDS_REVIEW, engine `degraded`.
- Config selection without code changes: `$GAMEQA_CONFIG` (e.g. `GAMEQA_CONFIG=configs/openai.yaml .venv/bin/streamlit run app.py`) or CLI `--config configs/openai.yaml`.
- Not yet measured with a real key. Before any claim: dev split first, then the same `eval_subset_60.json` for E2/E4 comparison with Qwen.
- Privacy: screenshots are sent to the provider. Fine for the CC BY 4.0 benchmark; consider before using confidential game screenshots.

## D15 — Attribution trailers removed; commit hashes changed (2026-10-09)
- Owner request: no `Co-Authored-By` / AI attribution in commits or PRs (rule in CLAUDE.md). All existing commits were rewritten (`git filter-branch --msg-filter`; trees verified identical, 8 commits) and force-pushed by the owner. Local backup tag: `backup/pre-trailer-strip` (not pushed).
- Old → new hashes: 9c09345→d4b85af, 0b3cc1b→3022ec8, c463a07→58ba189, 1f81dd2→871d8b1, 5f4fb4a→1c2f1ca, 9e9eb16→2349860, 9a34339→2663d6f, eab6514→004d997. Docs now show `new [was old]`; untracked `artifacts/eval/*/run_meta.json` keep the old hashes.

## D16 — Gemini via the OpenAI-compatible provider; free-tier quota blocks evaluation (2026-10-09)
- OpenAI key: valid, but the account has no API credits (HTTP 429 `insufficient_quota`); a ChatGPT subscription does not include API credits. No OpenAI run was possible.
- Gemini added without new client code: `configs/gemini.yaml` (endpoint `generativelanguage.googleapis.com/v1beta/openai`, key `GEMINI_API_KEY`). `scripts/list_models.py` lists the models an endpoint offers (key never printed).
- Model choice (owner asked for newer than 2.5): `gemini-3.1-pro-preview` → HTTP 429, no free-tier quota. `gemini-3.8-flash` works and is the newest usable model. Default reasoning ≈ 29 s per call; `reasoning_effort: low` (new optional `vlm.reasoning_effort`) ≈ 7 s per call.
- Smoke results with gemini-3.8-flash (synthetic fixtures, real API): `object_removed` → FAIL (R1 forbidden D1, validated); `lighting_change` → NEEDS_REVIEW (R1 uncertain, audit allowed A1); `clothing_color_change` → NEEDS_REVIEW (0 proposals, audit reported a change outside proposals; Qwen gave PASS here).
- Code fixes found while integrating:
  - the VLM cache key now includes `reasoning_effort` (a stale default-effort answer was being reused — measurement bug);
  - HTTP 429/503 are treated as transient: up to `vlm.transient_retries` (default 4) extra retries with 5→10→20→40 s backoff, not counted as regular attempts;
  - provider error text is kept to 800 chars so quota details stay visible;
  - `vlm.image_detail: null` omits the OpenAI-only `detail` field.
- **Blocker:** Gemini free tier = **20 requests/day per model** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`). The 60-pair comparison needs ≈600 requests (E2 ≈ 8/pair, E4 ≈ 2/pair). E2-Gemini was stopped after 1 pair; its quota-error row was dropped (`artifacts/eval/e2g_pipeline_gemini_subset60/dropped_provider_errors.txt`). No Gemini metrics exist yet. Options: enable billing (paid tier) or accept a much smaller sample.

## D17 — A1 result and the single intervention: freeze Qwen build, no vision change (2026-10-09 15:50, owner Ali)
- dev12, Ali's frozen labels (5 bug / 7 clean), Qwen 2.5-VL 3B, fresh cache: A pixel 12 PASS (5/5 bug false-PASS); B full-frame VLM 8 PASS/4 REVIEW (5/5 bug false-PASS); C hybrid 12 REVIEW (0/5 false-PASS, coverage 0; 9 global-change collapse). Details: docs/ali/A1_diagnostic.md.
- Root cause on Unity bugs: correct localization, wrong VLM perception (reproducer: same crop+prompt → Gemini 3.5 Flash describes the removal correctly, 2/2).
- Decision (Ali): freeze the current Qwen build for A3; no vision/prompt/threshold change; A2 goes to report/evidence. Model change is recorded as the evidenced next step; not run at scale (free-tier quota, no new paid provider).

## D18 — Final runtime evidence və recording gate (2026-10-09 ~17:30, Ali/Celal handoff)

- Confirmed integration source: `79a0ef740196cbaa0639579386c6c591d2bfd8ca`. Celalın C2 pilot-u owner-provided final runtime evidence-dir: OpenRouter / `google/gemini-3.5-flash` / reasoning low / prompt v9; canonical `configs/openrouter_gemini_pilot.yaml`, config hash `eaa371255716`. D17 Qwen A1/A3 freeze və baseline evidence saxlanılır; Ali vision/prompt/proposal/policy davranışı dəyişdirilmədi. `3b794aa` report scope fix final history-də mövcuddur.
- C2 committed raw files exact source SHA-dan müstəqil yenidən hesablandı: hər arm 1 PASS/4 FAIL/7 REVIEW, bug false-PASS 1/5 **coverage 5/12 ilə birlikdə**, clean PASS 0/7. C: 3 bug FAIL +1 clean false-FAIL; B: 2 bug FAIL +2 clean false-FAIL. 10/12 pair eyni qərardır; identical counts identical predictions demək deyil. DINOv2 advantage/QA workload reduction iddiası yoxdur. Missing pedestal false-PASS video/pitch-də saxlanılır.
- 80 fresh call/stage records, 0 application cache hits, 0 retries; B+C provider-reported toplam cost $0.2871945, invoice yoxlanmayıb. Historical inference SHA `c917532…` raw rows-da saxlanılır; final delivery SHA ilə əvəz edilmir. Local recomputation: `docs/ali/C2_RECOMPUTED.json`, `C2_VERIFICATION.md`. Exact final source-da offline suite 194 passed/6 skipped.
- **Final UI recording yalnız Celalın ayrıca UI-ready SHA-sından sonra.** Qwen branch UI final recording üçün istifadə edilmir. Code freeze confirmation UI/download verification-i əvəz etmir. Actual C2 ZIP bytes/full request captures və final browser download transfer-i hələ gözlənir; Celalın verification records-u lokal ZIP-byte check kimi təqdim edilmir.
- Presentation seçimi: 7-slide PDF/PPTX +3 science PNG; 110 s silent motion evidence draft ayrıca `PRERECORDED / DRAFT` label daşıyır. Bu draft final UI recording deyil. Daha güclü framing konkret problem → crop/rule/FAIL → measured comparison → known failure → evidence ZIP-dir; nəticələr şişirdilmir.
- 17:30-dan sonra presentation, docs, verification və submission; yeni feature, model experiment və threshold tuning yoxdur. Submission **19:30** olaraq qalır.

## D19 — C4 readiness və repository consolidation (2026-10-09 ~18:02, owner Ali)

- Ali completed branches-i Celalın `feat/hackathon-demo-integration` branch-inə, sonra reviewed PR ilə `master`-ə toplamağı istədi. Yeni target icazəsi əvvəlki “master-ə merge etmə” stopping rule-unu bu final delivery üçün supersede edir; feature→reviewed PR, no attribution trailers, explicit staging və no force-push qaydaları qüvvədədir. Agentlər push/create PR edə bilmir; authorized human exact commands işlədəcək. Remote merge hələ baş verməyib.
- Latest fetched integration `68501897746bf674d582fd810cd9d7e2cfb943e6`, runnable C4 UI `be1ea0acce271df994b516f6fa297118e981a3dd`. C4 runbook/verification Celal-host replay/browser export READY göstərir;0fresh C4 provider calls. Ali local app hələ79a0ef7 və actual C2 ZIP bundle absent-dir. C2 metrics/raw historical identities və canonical config hash `eaa371255716` dəyişmir.
- Audit: vision/Gemini/runtime-eval/team-git-workflow branches artıq integration-da var. Yeganə meaningful unmerged delivery Ali final pitch/docs branch-i və original `.gitignore` cache pattern/CLAUDE resume-link housekeeping-dir; stale docs/backups blindly merge edilmir. Backup branches, local evidence, manifests və credentials qorunur; branch/artifact deletion edilmir. [Plan](ali/GIT_FINALIZATION.md).
- Independent latest C4 offline suite197passed6skipped; runtime/model/policy/config byte-identicaldir. Local delivery review GitHub reviewed PR və final acceptance ilə qarışdırılmır. Final video, Ali local archive/export verification və submission confirmation pending; internal deadline19:30 dəyişmir.

## D20 — C5 follow-up və existing master PR reuse (2026-10-09, owner Ali)

- Consolidation zamanı Celalın deployment/replay/CI follow-up source-u fetch edildi: `487f2028461b47013138be124ebf700b86a1c9f1`. Ali final docs unpublished branch həmin source-a conflictsiz reconcile edildi. C4 UI-ready685/be1 və C2 raw79 identities historical saxlanılır; source/model/policy/canonical config hash `eaa371255716` dəyişməyib. Actual combined offline suite **199passed6skipped11.20s**, no new paid calls.
- Existing integration→master **PR#4** var: duplicate master PR açılmır. Ali son mesajda docs PR-in integration-a açılmasını explicit istədi. Normal approval path icazə verərsə git-workflow-master explicit docs push/PR create edir; actual permission block varsa bypass etmədən human terminal commands verilir. Reviewed PR/CI tələbini explicit PR-open request ləğv etmir; remote merge tamamlandığı iddia edilmir.
- Compact barrel saved-run bytes +4 provider captures `deploy/replay/barrel/`-də tracked/localdır; all12C2ZIP/pedestal bundle transfer və Ali fresh local UI/export verification pending-dir. Native historical source ZIP ilə reconstructed portable replay ZIP eyni artifact deyil; source IDs/bytes provenance saxlanılır. Ignored motion MP4 Git backup deyil. Final video/human19:30submission gate dəyişmir.
- **Later read-only PR-state update:** PR#4 external actor tərəfindən MERGED oldu; agent PR4merge/edit etmədi. Yuxarıdakı existing-open-PR reuse planı həmin snapshot üçün historical-dır. Ali docs əvvəl integration-a reviewed merge olunacaq, sonra bu yeni dəyişikliklər üçün yeni integration→master follow-up PR açılmalıdır. Exact remote/master SHA və PR status [Git finalization](ali/GIT_FINALIZATION.md)-dəki snapshot/actual delivery ilə verilir; Ali docs və submission complete deyil.
