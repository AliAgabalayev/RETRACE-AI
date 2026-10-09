# Game Visual QA — final demo runbook

**C4: video üçün UI hazırdır; model accuracy/release gate təsdiqi deyil.**

## Checkout və təhlükəsiz startup

Branch `feat/hackathon-demo-integration`; exact runnable UI checkout SHA **`be1ea0acce271df994b516f6fa297118e981a3dd`**. Runbook və verification həmin checkpoint-in documentation-only descendant delivery commit-indədir; final pushed SHA chat-da qeyd edilir. Başlanğıc freeze `79a0ef740196cbaa0639579386c6c591d2bfd8ca`; model/policy implementation, configs və C2 results həmin freeze ilə dəyişməyib.

Config **`configs/openrouter_gemini_pilot.yaml`**, merged hash **`eaa371255716`**. OpenAI-compatible adapter → **OpenRouter**, `https://openrouter.ai/api/v1`, **`google/gemini-3.5-flash`**, reasoning **low**, prompt **v9**. Credential yalnız environment-dədir. Mövcud $5 key limit saxlanılır, automatic top-up yoxdur.

PowerShell-də key-i göstərmədən startup:

```powershell
Set-Location 'C:\Users\celal\OneDrive\Belgeler\ChatGPT\Hackaton\neuroscience-runtime-eval'
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
if (-not $env:OPENROUTER_API_KEY) { throw 'OPENROUTER_API_KEY is missing; use saved replay' }
$env:GAMEQA_CONFIG = 'configs/openrouter_gemini_pilot.yaml'
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:TORCH_HOME = Join-Path (Get-Location) 'models/torch'
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8524 --server.headless true --browser.gatherUsageStats false
```

Hazır C4 instance `http://127.0.0.1:8524`-də işləyir; eyni portda ikinci server başlatmayın. Mövcud .venv və Torch/DINO cache istifadə edilir. Key/environment dump, .env yaradılması və reinstall tələb olunmur. Key yoxdursa da saved replay offline işləyə bilər: credential olmadan eyni config ilə app-i başlatmaq olar, **Analyze basılmamalıdır**. Real/MOCK seçimi videoda açıq görünməlidir; əsas demo Real (config)-dir.

## Üç demo nümunəsi

| Case | Exact recorded C2 run | Recorded hybrid result | Nə göstərmək lazımdır |
|---|---|---|---|
| `vr_4b921c5d` — barrel removal | `20261009T123704Z-8e4e19` | **FAIL** | R1 barrel var → yoxdur; region və scene forbidden/D1, validated true |
| `vr_09a066d3` — allowed outfit change | `20261009T123947Z-584a66` | **NEEDS_REVIEW** | Blue denim → gray suit observation allowed/A1; global-change collapse coverage guard REVIEW verir |
| `vr_330651ed` — subtitle-language change | `20261009T123852Z-72dbc0` | **NEEDS_REVIEW** | English → Portuguese observation; rule uncertainty və full-frame collapse |

Subtitle case ambiguous **demonstration**-dır, yeni ambiguous ground-truth class deyil. Frozen label D1 qalır; `labels_audit.md` cutscene rules altında onun support-unun zəif olduğunu bildirir. Outfit-a PASS uydurulmur. C1 direct-Gemini barrel FAIL ayrıca provider reference nəticəsidir; burada C2 OpenRouter run göstərilir.

Primary live UI üçün **Compare new screenshots → Pair source: Demo pair → Frozen dev demo | vr_4b921c5d**. Images `artifacts/c1-demo-20261009/bundle/vr_4b921c5d/{reference,candidate}.png`-dən, rules exact verified `inventory.json`-dan gəlir. Rule text-i dəyişməyin. Input hashes fərqlənsə Analyze disabled olur. Digər iki frozen demo eyni selector-da var. Missing-media legacy demo entries gizlədilib; synthetic fixtures ayrıca etiketlidir.

**Analyze** yalnız operator live analysis istəyəndə basılır. Frozen demonstrated barrel result FAIL-dir; yeni run-un eyni qərarı verməsinə zəmanət yoxdur. Mövcud C2 VLM cache istifadə oluna bilər: yeni pipeline run və ya “Engine: real” fresh paid generation sübutu deyil. Fresh claim üçün actual provider-call/cache provenance lazımdır. C4-də live Analyze və API çağırışı işlədilməyib; model/policy freeze dəyişməyib. Recorded smoke 4 call/$0.016368 və 30.22 s pipeline idi, live latency/cost üçün zəmanət deyil.

## Replay fallback və evidence

API/network unavailable və ya live nəticə qeyri-müəyyəndirsə nəticəni olduğu kimi göstərin. Sidebar **Saved runs → exact run ID → Load saved run**. **“Saved run replay — no new inference”** label-i kadrda saxlayın. Dropdown seçimi təkbaşına loaded result-u dəyişmir; Load saved run basılmalıdır. Replay-də stored rules read-only-dir; cari upload/demo rules göstərilmir. Run/sample ID banner altında görünür. Plain rerun və download yeni inference etmir.

Primary ZIP:

`C:\Users\celal\OneDrive\Belgeler\ChatGPT\Hackaton\neuroscience-runtime-eval\artifacts\c2-openrouter-20261009\runs-C\20261009T123704Z-8e4e19.zip`

**Download evidence ZIP** bu loaded run-un ZIP-ini verir. Browser download yoxlanmış yol: `C:\Users\celal\Downloads\20261009T123704Z-8e4e19.zip`; source ZIP ilə byte-identical-dir. `evidence.json`, `analysis.json`, `report.md`, rules, inputs/crops və representative provider captures var. Subtitle run-a keçəndə ZIP `20261009T123852Z-72dbc0.zip` olaraq dəyişdi və source ilə byte-identical endi. Hər download-u yeni inference kimi təqdim etməyin. Native historical ZIP-lər plain rerun zamanı yenidən yazılmır; historical scope wording saxlanıla bilər.

## 90–120 saniyə video planı

| Vaxt | Kadr və danışıq |
|---|---|
| 0–12 s | “QA engineer approved və new-build screenshots-u öz rules-u ilə müqayisə edir.” Product adı, provider/model və limitation note |
| 12–25 s | Frozen barrel Demo pair: Reference/Candidate və unchanged A1/D1 rules. Live analysis seçilərsə Analyze; cache/fresh status barədə iddia etməyin |
| 25–60 s | Hazır barrel result: FAIL + run ID, R1 expander, reference/candidate crops, actual disappeared-barrel observation və D1 evidence. Replay istifadə olunursa onu səsdə və label-də açıq deyin |
| 60–75 s | Download evidence ZIP; `evidence.json`, `analysis.json`, inputs/crops-u göstərin |
| 75–95 s | Outfit replay: allowed visual observation **amma final REVIEW**; coverage limitation-u deyin. Subtitle replay: rule uncertainty |
| 95–110 s | Approve expander: Reference ID saxlanır, FAIL üçün iki confirmation tələb olunur; demo zamanı approval düyməsini basmayın |
| 110–120 s | “Development diagnostic; human review remains necessary.” Missing-pedestal false-PASS açıqdır |

Live run video vaxtını aşırsa gözləmə hissəsini montajda açıq göstərmək və ya saved replay fallback istifadə etmək olar. Failed/REVIEW cavabı FAIL ilə əvəz etmək, Analyze-i təkrar-təkrar basmaq və ya fresh kimi replay göstərmək olmaz. C4-də tam 90–120 s video çəkilməyib; bu sequence runbook-dur.

## C4 verification və qalan UI məhdudiyyətləri

Actual browser: startup, frozen model identity, replay label, stored rules, barrel FAIL/crops, outfit/subtitle REVIEW, exact ZIP download, Reference ID expander persistence və iki confirmation guard yoxlanıldı. Browser console error logs boş idi, server-də application exception görülmədi. Approval **icra edilmədi**; confirmation-lar söndürüldü, reference history dəyişdirilmədi. Primary barrel replay browser-də açıq saxlanılıb.

Focused UI/storage/report tests və final result `docs/C4_DEMO_VERIFICATION.json`-dadır. C4 provider calls **0**, new paid cost **$0**. Bütün 12 C2 ZIP SHA256-ları C3 ilə eynidir; config və model/policy source unchanged. Key material scan commitdən əvvəl aparılır. Browser screenshots/test logs ignored `artifacts/c4-demo-20261009/`-dədir.

Long rules table kiçik viewport-da visually truncated ola bilər; table Fullscreen və horizontal scroll ilə oxuyun. Approval expander field interaction-dan sonra açıq qalır və sonrakı rerun-da yenidən açıla bilər; bu confirmation guard-u dəyişmir. Üç frozen preset yalnız verified local bundle olduqda görünür. C4 actual fresh UI inference sınanmayıb; yalnız replay, input readiness və offline tests yoxlanılıb.

## İddia etməyin

- “Held-out accuracy”, “all bugs detected”, “production-ready release gate” və ya “almost no bugs missed”.
- REVIEW-in bug detection və yaxud automation success olduğunu.
- Frozen clean outfit üçün PASS və ya subtitle üçün yeni invented label olduğunu.
- Replay/cached response-un fresh inference olduğunu; new live run-un həmişə FAIL verəcəyini.
- Missing pedestal-in düzəldildiyini: C2 hybrid **1/5 bug false-PASS** saxlanılır. 12 development pair-də B/C coverage **41.7%**, total **80 calls/$0.2871945** provider-reported cost-dur.

Model/policy tuning, deployment və pitch-deck işi bu task-a daxil deyil; freeze explicit unblock olmadan saxlanılır.
