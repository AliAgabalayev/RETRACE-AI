# Final implementation freeze — C3

**READY — integration baseline freeze; production accuracy təsdiqi deyil.** 9 oktyabr 2026. Branch `feat/hackathon-demo-integration`. Yeni inference, deployment, UI redesign və model/policy tuning edilmədi.

## Frozen runtime identity

- Implementation code SHA: **`bdd93fb534e8c0e9b574e60d383bc8b14dd03bf3`**. Bu sənəd və verification JSON həmin code commit-in üzərinə gələn documentation-only delivery commit-dədir; final branch SHA normal push nəticəsində chat-da göstərilir.
- Canonical config: `configs/openrouter_gemini_pilot.yaml`, defaults ilə deep-merge edilmiş **config hash `eaa371255716`**. Local file SHA256: `d18ff48f9690d2f8a8643f151deb2890cca08df9c98ae057f9cc5eec3a539210`.
- Provider config enum `openai` — mövcud OpenAI-compatible adapter vasitəsilə **OpenRouter**.
- Base URL `https://openrouter.ai/api/v1`; exact model **`google/gemini-3.5-flash`**; `reasoning_effort: low`; prompt **`v9`**; credential environment **`OPENROUTER_API_KEY`**.
- `temperature: 0`, `image_detail: null`, `timeout_s: 60`, `max_attempts: 1`, `transient_retries: 0`. Alignment, image representation, crops, proposals, thresholds, caps və deterministic policy əvvəlki C2 ilə eynidir.
- Server key limit **$5** saxlanılır; avtomatik top-up/billing dəyişikliyi yoxdur. Son məlum balance C2 `docs/c2_openrouter/key-budget-final.json`-dadır; C3 hesab sorğusu və paid generation işlətməyib.

Tətbiq default olaraq Qwen config yükləyə bilər. Frozen runtime üçün `GAMEQA_CONFIG=configs/openrouter_gemini_pilot.yaml` açıq şəkildə seçilməlidir. Windows User credential child process environment-inə dəyəri göstərilmədən yüklənməlidir. Config-də key value yoxdur. Canonical config C2 run/cache namespace-ni saxlayır; saved-run replay və cache nəticəsi fresh inference kimi təqdim edilməməlidir. Historical C2 pilot runner-in 17:00 cutoff-u uzadılmayıb.

**Bu freeze-dən sonra explicit unblock qərarı olmadan əlavə model və ya policy tuning qadağandır.** Mövcud missing-pedestal failure açıq qalır; freeze onu düzəldilmiş saymır.

## Git reconciliation və Ali fix provenance

Başlanğıc local HEAD `e4a0cf3a92cb3697959b3e99a5ab34a07c10eec4`, parent `c917532ac3161a0886f626985c53307eb2d477d8`; working tree clean idi. `git fetch --all` sonrası:

- Remote integration: `08267787e6cdd34502e1121975d4e8f60c3c07d0`.
- İstənilən Ali checkpoint: `3591f7bcb04cee34c0701d869092f7cb8759e3b6`.
- Actual fetched Ali HEAD: `74f84cf23ff52530f47bbb280429ad6f5e9845ae` — Ali checkpoint-in üzərinə integration `ec1ccee4aca0823e47d238b83f331159ecb79249` merge olunub.

Original push divergence səbəbi **PR #3** merge-dir: `0826778` parents `ec1ccee` və `74f84cf`-dir. Remote Ali docs/tooling və report fix-i gətirmişdi, local isə `ec1ccee` üzərində üç C2 commit əlavə etmişdi. Force-push edilmədi. Local original history `feat/hackathon-c2-pre-c3-preserved` backup branch-də qorunur. Üç unpublished local commit remote HEAD üzərinə normal rebase ilə conflictsiz daşındı:

| Original local | Reconciled |
|---|---|
| `06b80f19dbfc918b6dd85a81ea0321f5e3ce2425` | `4376c925f2ef41017a8062394bb7b71fe7f9a27a` |
| `c917532ac3161a0886f626985c53307eb2d477d8` | `bce8c640b196997d174411ad8d7f0ec3519b22e3` |
| `e4a0cf3a92cb3697959b3e99a5ab34a07c10eec4` | `e2cc14d34ef979a390b5abdb054bb7bdebc36fac` |

Ali `3b794aafebf5429c193da890522c4a0ae4043eec` patch-i importdan əvvəl yoxlanıldı. **Artıq remote ancestor idi**, buna görə duplicate cherry-pick edilmədi. Applicable implementation `src/gameqa/report.py` və `tests/vision/test_report_evidence.py::test_scope_names_global_change_collapse` reconciliation ilə saxlandı. Report file Ali commit ilə byte-for-byte Git diff baxımından eynidir. Scope indi global-change collapse-i actual region-cap dropping-dən ayırır; qərar və model davranışı dəyişmir. Həmin commit-in documentation/images hissəsi artıq shared remote history-də idi; yeni selective import adı ilə təkrarlanmadı və C2 artifacts üzərinə yazılmadı.

Storage export hook (`write_evidence` zipping-dən əvvəl, `render_report(result, run_dir)`) dəyişmədən qorundu. Remote judge diff yalnız opt-in input dump/stage metadata tooling idi, frozen config-də dump aktiv deyil. Yeni stage argument local pilot capture wrapper-i ilə uyğunsuz idi; yalnız observer argument forwarding düzəldildi və offline mock test əlavə edildi. Prompts, defaults, pipeline, policy və storage C2 ilə Git diff baxımından dəyişməyib.

## C2 nəticələri — dəyişmədən saxlanılan development diagnostic

C2 **12-pair development diagnostic**-dir, held-out accuracy deyil. Frozen labels `e844aab9239ad6b851ce426b7baba6706693e9f7`; subtitle-label sensitivity və post-freeze audit limitations C2 report-da qalır. Labels inference prompt-larında istifadə edilməyib.

| Arm | Tamamlanan | PASS / FAIL / REVIEW | Decision coverage | Bug FAIL / REVIEW / false-PASS | Clean PASS / REVIEW / false-FAIL |
|---|---:|---|---:|---|---|
| Hybrid C |12/12|1 / 4 / 7|**41.7%**|3 / 1 / **1**|0 / 6 / 1|
| Full-frame B |12/12|1 / 4 / 7|**41.7%**|2 / 2 / **1**|0 / 5 / 2|

Hybrid **1/5 bug false-PASS**: `vr_c1f47c57` missing stone pedestal. Bu case hər iki arm-da PASS aldı və açıq consequential failure olaraq qalır. Valid JSON visual understanding sübutu deyil; 41.7% coverage useful safe automation iddiası yaratmır. **80 fresh calls, 0 retries, provider-reported cost $0.2871945**. C2 inference code SHA `c917532ac3161a0886f626985c53307eb2d477d8` historical identity kimi raw rows-da saxlanır; yeni freeze SHA ilə əvəzlənmir. B diagnostic config hash `2dfeb64cd673` ayrı namespace üçündür, canonical hybrid config deyil.

## C3 verification və məhdudiyyətlər

- Report/evidence/provider/judge/storage/UI focused suite: **54 passed, 8.02 s**, exit 0. Ali global-collapse test və plain export evidence hook testi daxildir. Offline stage-aware observer test: **1 passed, 0.56 s**, actual provider calls **0**.
- İlk sandbox TEMP run: **14 failed /40 passed, 15.17 s**, atomic rename `WinError 5`. Workspace sandbox run: **1 failed /53 passed, 18.27 s**, reference-history hard-link `WinError 5`. Eyni focused suite normal process-də **54/54** keçdi; source-u tests keçsin deyə dəyişmək lazım olmadı. Bu permission failure-lar uğurlu check kimi təqdim edilmir.
- C2 əvvəlki **186 passed /6 deselected** nəticəsi reuse olunur; full suite və model inference yenidən işlədilməyib.
- Bütün **12 C2 ZIP** read-only integrity check keçdi: `evidence.json`, `analysis.json`, Markdown, rules və inputs mövcuddur; final decision uyğun gəlir; ZIP SHA256 dəyişməyib. Representative barrel/pedestal/outfit/headwear daxil olmaqla credential-value scan təmizdir. Native historical exports yenidən yazılmadı; onların köhnə scope wording-i historical artifact olaraq qalır.
- Saved outfit run üzərində yeni `build_evidence` read-only replay scope-u “global change … collapsed into one full-frame region” deyir və “region cap” demir. Bu fresh inference deyil.
- **225 tracked files** actual environment credential values və key patterns üçün yoxlanıldı; credential material tapılmadı. Final documentation da commitdən əvvəl ayrıca scan edilir. `git diff --check` keçdi.
- C2 config/report/raw rows bütöv qorundu. Verification evidence: `docs/C3_FREEZE_VERIFICATION.json`; local test logs `artifacts/c3-freeze-20261009/`. C3 browser exploration və deployment etmədi. Native C2 evidence-in cache field-i unknown olaraq qalır; fresh-call provenance ayrıca C2 capture records-dadır.

Qalan product blocker missing-pedestal false-PASS və clean samples üçün PASS olmamasıdır. Git conflict və adapter/provider integration blocker aşkarlanmadı. Freeze-dən sonra yeni implementation roadmap və explicit unblock qərarı gözlənilir.
