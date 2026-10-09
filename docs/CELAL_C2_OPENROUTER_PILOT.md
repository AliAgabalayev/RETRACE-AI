# C2 OpenRouter dev12 pilot — READY (engineering), production gate deyil

2026-10-09, 17:00 Asia/Baku cutoff. Hybrid C əvvəl 12/12, sonra optional full-frame B 12/12 tamamlandı. Yeni inference dayandırılıb. Bir düzgün barrel FAIL əldə edildi, lakin pedestal false-PASS və clean PASS olmaması ümumi QA automation iddiasını dəstəkləmir.

## İdentiklik və sərhədlər

Branch `feat/hackathon-demo-integration`; başlanğıc `ec1ccee4aca0823e47d238b83f331159ecb79249`; bütün inference code SHA `c917532ac3161a0886f626985c53307eb2d477d8`. C config hash `eaa371255716`, B `2dfeb64cd673` (ayrı output/cache paths). Final delivery commit Git history və chat-da göstərilir.

Windows, mövcud .venv, RTX 4060 8 GB, Torch/DINO cache təkrar istifadə edildi. Source vision/judge/prompts/report/policy dəyişmədi. Yeni config və serial orchestration/scoring scripts əlavə edildi. Ali arm helper `cac62c7693abdf74b8b9e2b6455c82f148ee0493` commit-dən oxunaraq isolated artifact snapshot kimi işlədildi. Ali pinned HEAD `a5590a50849ace549debff63ad3f3b4e1a1f815a`; frozen label commit `e844aab9239ad6b851ce426b7baba6706693e9f7`. Labels yalnız scorer tərəfindən oxundu, inference prompts-a daxil edilmədi.

Endpoint `https://openrouter.ai/api/v1`, tələb olunan exact model `google/gemini-3.5-flash`, credential Windows User `OPENROUTER_API_KEY`-dən child process-ə verildi, fayla yazılmadı. Public model metadata image input, reasoning_effort və structured output dəstəyini göstərdi. Mövcud adapterin `reasoning_effort: low` və JSON structured output request-i istifadə edildi; səssiz parameter/model substitution edilmədi. [OpenRouter parameters](https://openrouter.ai/docs/api_reference/parameters), [structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs), [reasoning](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens). Response low effort echo etmir; reasoning tokens qeydə alınıb. Returned model bütün çağırışlarda exact ID-dir; upstream routing Google və Google AI Studio arasında dəyişib.

Prompt v9, inventory rules, image representation, alignment, DINO/classical proposals, thresholds, crops, caps və decision policy saxlanılıb. Transport `max_attempts=1`, `transient_retries=0` əvvəlki direct-Gemini config kimidir; frozen Qwen iki attempt config-i ilə bu fərq qeyd olunur. C application pipeline.analyze/export_report, B Ali aligned full-frame scene audit + mövcud policy yoludur; B unconstrained classifier deyil.

## Inputs və fresh smoke

Bundle SHA256 `70089e2499136fdba8a4e1f33c6f3296d5334742c3302f8361af32a8f866ce23`. C1 integrity və 24 hash yoxlaması saxlanılıb; C2 runner hər input hash-i inventory ilə yenidən yoxladı. ZIP `bundle/<id>` prefix-i inventory `artifacts/ali/bundle` prefix-i ilə explicit map olunub. Yeni storage re-encoded PNG binary hashes inventory-dən fərqlənə bilər; decoded pixels və stored evidence hashes ayrı yoxlanır. Frozen labels faylı dəyişməyib (SHA256 `524583859358b6dcea8250325f88fbc12077cf5f0e3516fbe05f2e94a86bb96d`). Input/rule identities və actual observations raw rows/evidence-dədir.

Smoke `vr_4b921c5d`, run `20261009T123704Z-8e4e19`: stage-1 “The large wooden barrel has disappeared from the wooden stand.” Region və scene stage-2 forbidden/D1, validated true. Final FAIL: “Forbidden change with visual evidence: R1 (D1), SCENE (D1).” Dörd actual call, $0.016368, pipeline 30.2167 s, orchestration wall 31.520 s, cache hits 0. Bu smoke C-nin 12 sample-ından biridir; ikinci dəfə inference olunmayıb, reuse explicit qeyd edilib. C1 direct-Gemini 4 call /18.43 s FAIL ayrıca reference nəticəsidir.

## Ölçülmüş nəticələr

Decision coverage = (PASS + FAIL) / tamamlanan pairs. REVIEW doğru bug detection sübutu deyil.

| Model/arm | PASS | FAIL | REVIEW | Coverage | Bug FAIL / REVIEW / false-PASS | Clean PASS / REVIEW / false-FAIL |
|---|---:|---:|---:|---:|---|---|
| Frozen Qwen A pixel |12|0|0|100%|0 / 0 / 5|7 / 0 / 0|
| Frozen Qwen B full-frame |8|0|4|66.7%|0 / 0 / 5|3 / 4 / 0|
| Frozen Qwen C hybrid |0|0|12|0%|0 / 5 / 0|0 / 7 / 0|
| OpenRouter C hybrid |1|4|7|41.7%|3 / 1 / 1|0 / 6 / 1|
| OpenRouter B full-frame |1|4|7|41.7%|2 / 2 / 1|0 / 5 / 2|

Frozen Qwen identity `qwen2.5vl:3b`, v9, config `3a144cfcbb67`; committed A1 raw rows ilə scorer sanity check aparıldı. Qwen 0 false-PASS + 0 coverage general safety guarantee deyil. Bu selected development inputs üzərində provider/model intervention-dur; untouched holdout və model accuracy ölçüsü deyil. Source/class imbalance: bütün üç Unity sample bug-dur, clean nümunələr cutscene-dir.

Subtitle `vr_330651ed` frozen D1 saxlanılır; labels_audit həmin cutscene rules altında zəif D1 support göstərir. Clean sensitivity: C bugs 3 FAIL /0 REVIEW /1 false-PASS, cleans 0 PASS /7 REVIEW /1 false-FAIL; B bugs 2 FAIL /1 REVIEW /1 false-PASS, cleans 0 PASS /6 REVIEW /2 false-FAIL. Coverage dəyişmir. Qwen A/B 4/4 bug false-PASS, C 0/4 amma yenə 0 coverage. Post-freeze audit pedestal description-u missing stone pedestal kimi düzəldir, D1 saxlanılır. Frozen labels post-A1 formalaşıb; diagnostic exposure olduğuna görə blind test sayılmır.

| Source | C PASS / FAIL / REVIEW | B PASS / FAIL / REVIEW |
|---|---|---|
| UnityCapturesDataset (3 bugs) |1 / 2 / 0|1 / 1 / 1|
| Youtube-Cutscene (2 bugs, 7 clean) |0 / 2 / 7|0 / 3 / 6|

## Perception, policy və label problemləri

Ən mühüm blocker: `vr_c1f47c57` missing pedestal həm C, həm B-də PASS alıb. C region observations shadow/lighting, scene “No differences observed.” Actual crop inspection statue altında pedestal-ın itdiyini göstərir. Valid JSON correctness demək deyil. Confirmed perception miss; unsafe approval. Bu task-da prompt/crop/policy tuning edilmədi.

C booth `vr_d07179d5` roof/sign disappearance-u düzgün aşkar edib FAIL verdi; B mailbox/bicycle appeared və booth moved kimi yanlış observation ilə REVIEW verdi (obyektlər əvvəl də mövcuddur). C global collapse toplam 9 sample-da var; 7 REVIEW-in hamısında collapse guard var. Actual region-cap truncation 0; global coverage collapse region-cap ilə qarışdırılmamalıdır. `vr_ef9b073a` unreliable alignment; `vr_330651ed`, `vr_4255ae09` uncertain region; `vr_330651ed`, `vr_ef9b073a` uncertain/invalid scene; `vr_a981c1d3` scene extra changes. Səbəblər overlapping-dir. B yeddi REVIEW-də scene extra_changes, üçündə uncertain scene var; proposals olmadığından scene-outside guard coverage-i məhdudlaşdırır.

C raw error-bearing rows 4255, d071, fec, ef9, 437 semantic rule/response guard errors-dir, provider HTTP failures deyil. Headwear disappearance allowed observation-u existing guard uncertain/validated false edir. FAIL priority bəzi global-collapse nəticələrində valid forbidden region-u saxlayır. Guards dəyişdirilməyib.

Frozen clean `vr_43773eb8` hər iki arm-da FAIL: actual original image-də reference subtitle var, candidate-də yoxdur; observed subtitle absence vizual yoxlandı. Frozen A1 rationale lighting/clothing bu UI fərqini əhatə etmir. Frozen scoring-də false-FAIL saxlanılır, label/rule scope conflict ayrıca göstərilir. B `vr_ef9b073a` frozen clean üçün FAIL verir, floating character/glasses iddia edir; bu observation C2-də human-verified deyil.

Human observation review selected altı case üzrə aparılıb: barrel missing (correct), booth C correct/B incorrect, pedestal C/B incorrect, outfit blue→gray correct, subtitle English→Portuguese correct (rule uncertainty qalır), RDR subtitle absence/lighting correct (label conflict). Digər altı sample və bütün fərdi crops üçün observation accuracy UNVERIFIED-dir. Bu post-hoc inspection-dur, formal blind human accuracy metric deyil.

## Calls, latency, cache və xərc

80 actual generation attempts /120 limit, retries 0, HTTP 200 80/80, unknown cost calls 0. Reported usage.cost total **$0.2871945 /$5 limit**. C 56 calls /$0.1934625, B 24 /$0.093732. Median wall C 39.99005 s, B 19.7196 s. Prompt tokens 75681, completion 19297, reasoning 11781; reasoning completion-a daxil ola bilər, cəmlənmir. Providers {'Google': 46, 'Google AI Studio': 34}. Application stage cache hits 0/80; upstream cached prompt tokens 0. All actual stages fresh; native evidence cache provenance unknown/replay-possible field external call/stage captures ilə tamamlanıb, native field saxtalaşdırılmayıb.

Provider reported cost ölçülüb, invoice independently yoxlanmayıb. Hər actual call-dan əvvəl key limit/remaining yoxlanıb; conservative $2.162688 worst-case reserve estimate idi, charge deyil. İlk runner factory ImportError sıfır API call ilə düzəldilib. Smoke-dən sonra provider/schema transport failure olmayıb. `key-budget-final.json` final server balance-i göstərir. Key/headers outputs-a yazılmayıb.

## Evidence və checks

`pytest -m 'not real_model' -q -ra -p no:cacheprovider`: **186 passed, 6 deselected, 0 skipped**, 18.99 s, exit 0. Model accuracy yoxlaması deyil. Frozen Qwen A/B/C scoring sanity checks keçdi. `git diff --check` yoxlanıldı.

Bütün 12 C exported ZIP opens/testzip, evidence schema v1, analysis decision, rules/input/aligned/crop stored hashes yoxlamaları keçdi. B Ali helper raw scene/predictions verir, AnalysisResult ZIP yaratmır; B üçün native ZIP iddiası edilmir. C ZIPs `artifacts/c2-openrouter-20261009/runs-C/` altındadır. Barrel, pedestal, outfit və headwear representative ZIPs-ə sanitized provider capture, usage və identity əlavə edildi. Bütün 12 ZIP credential-value scan keçdi. `zip-verification.json` hashes və exact paths göstərir. C2 actual browser/download yoxlanılmayıb; C1 UI/export evidence prior-session provenance-dir; non-model AppTest actual fresh UI inference sübutu deyil.

Paylaşılan raw predictions, per-call usage/stages, score, model/key metadata (whitelisted, key yoxdur), identities və ZIP verification `docs/c2_openrouter/` içindədir. Tam raw request/response image captures və images/crops ignored local artifacts içində saxlanılır. Orijinal Qwen/direct-Gemini cache/history dəyişməyib.

## Handoff

Bu bounded pilot tamamlandı; policy/coverage intervention, model sweep, held-out run və deployment edilmədi. Növbəti roadmap üçün birinci qərar unsafe pedestal false-PASS və clean-pair workload-dur. Daha güclü provider bəzi bugs-da useful FAIL gətirdi, amma perception və deterministic coverage problemlərini tam həll etmədi. Tuning-dən əvvəl fresh untouched validation tələb olunur. Automatic reference approval bu nəticələrə əsasən etibarlı deyil. READY burada integration və requested pilot completion deməkdir, product readiness deyil.

## Pair-level nəticələr

| Sample | C | B |
|---|---|---|
| vr_4b921c5d | FAIL | FAIL |
| vr_a981c1d3 | NEEDS_REVIEW | NEEDS_REVIEW |
| vr_330651ed | NEEDS_REVIEW | NEEDS_REVIEW |
| vr_4255ae09 | NEEDS_REVIEW | NEEDS_REVIEW |
| vr_09a066d3 | NEEDS_REVIEW | NEEDS_REVIEW |
| vr_59af7164 | NEEDS_REVIEW | NEEDS_REVIEW |
| vr_41bab231 | NEEDS_REVIEW | NEEDS_REVIEW |
| vr_d07179d5 | FAIL | NEEDS_REVIEW |
| vr_c1f47c57 | PASS | PASS |
| vr_fec26436 | FAIL | FAIL |
| vr_ef9b073a | NEEDS_REVIEW | FAIL |
| vr_43773eb8 | FAIL | FAIL |
