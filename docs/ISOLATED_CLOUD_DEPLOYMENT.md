# RETRACE-AI — ayrıca Render deployment hazırlığı

Tarix: 11 oktyabr 2026, Asia/Baku. Status: **PARTIAL — hazırlıq və lokal replay yoxlanıb; cloud xidmət yaradılmayıb.** Yeni cloud URL yoxdur.

## Qərar və sərhəd

Mövcud Dockerfile tam Streamlit tətbiqini CPU-da işlətmək üçün uyğun development base-dir. Render Docker Web Service real seçimdir, lakin bu sessiyada Render hesabına giriş yoxdur və ödənişli compute təsdiqlənməyib. Render-də startup, memory limit və live inference hələ **UNVERIFIED**-dır. Repository-dəki hazır immutable public replay ilkin, credentials-siz nümayiş üçün seçilib. Bu rejim tam tətbiqin live Analyze və persistent approval funksiyalarını açmır; onları aktivləşdirmək ayrıca aşağıdakı əməliyyatdır.

Laptop demosu dəyişdirilməyib: `https://wax-coleman-meat-invention.trycloudflare.com/`, server `127.0.0.1:8525`, mövcud tunnel əmri `cloudflared tunnel --url http://127.0.0.1:8525 --no-autoupdate`. Server PID 35060 və tunnel PID 23444 müşahidə edilib. Həm lokal health, həm public URL-nin `/_stcore/health` cavabı 200 olub. Heç bir proses dayandırılmayıb/restart edilməyib; link switch, Cloudflare və Drive dəyişikliyi edilməyib. Bu yalnız yoxlama anının availability sübutudur.

## Git və dəyişikliklər

- Remote: `https://github.com/AliAgabalayev/RETRACE-AI.git`; actual default branch: `master`.
- Ayrıca checkout: `retrace-cloud-isolated`; feature branch: `feat/cloud-deployment`.
- Audit/base və dəyişməyən application code SHA: `538e1b149cb75ae691888ecf23a4277fa792ad73`.
- Base parent (GitHub commit metadata): `3d7dbf7db57e244846546cf99b360ae760710e2c`.
- Deployment assets verified commit: `618f6f303b4f662b1dcc2f9bd598ed344baec3f6`; [draft PR #10](https://github.com/AliAgabalayev/RETRACE-AI/pull/10). Sonrakı report-only commit həmin yoxlamaların nəticəsini qeyd edir; blueprint/source dəyişmir.
- Shallow, public clone istifadə edilib. Əvvəlki dayandırılmış clone `retrace-cloud-deployment` qovluğunda saxlanılıb; onu işlək checkout kimi istifadə etmirik.
- Yalnız `render.yaml` və bu report əlavə olunur. Source, tests, dependencies, Dockerfile, frozen configs, prompts və policy dəyişmir.
- Branch commit-i `git log -1 --format=%H feat/cloud-deployment` ilə alınır və delivery cavabında qeyd olunur. Default branch-ə merge və auto deployment yoxdur.

`AGENTS.md`, `CLAUDE.md`, README, HANDOFF, deployment docs/scripts, dependency/config/container/CI declarations oxunub; 294 tracked file inventarı nəzərdən keçirilib. Historical Claude team və tapşırıqları davam etdirilməyib. Əvvəlki Qwen handoff iddiaları yeni runtime sübutu kimi götürülməyib.

## Faktiki arxitektura və resurslar

Docker entrypoint: `python scripts/start_deployment.py`. Script repository root-dan frozen config-i seçir, replay package-i yoxlayır və `streamlit run app.py --server.address 0.0.0.0 --server.port <PORT>` başladır. `PORT` host tərəfindən verilərsə həmin port istifadə olunur; Docker default-u 8501-dir. `EXPOSE 8501` Render-in başqa PORT verməsinə mane olmur. Health endpoint `/_stcore/health`-dır; health təkbaşına bütün UI/model funksiyalarının işlədiyini sübut etmir.

Python image `3.12-slim-bookworm`; CPU Torch 2.6.0, torchvision 0.21.0, Streamlit 1.61.1 və pinned direct requirements. Torch əvvəlcə official CPU wheel index-dən yüklənir. Build DINOv2 source və checkpoint-i cache edir, runtime non-root UID 1000 ilə işləyir. `/app/artifacts`, `/app/references`, `/opt/torch-cache` yazıla bilir. Render üçün Windows absolute path tələb edilmir.

Application upload/decode → alignment → classical və frozen DINOv2 proposals → OpenAI-compatible OpenRouter VLM observations/judgments → deterministic policy → stored analysis/report/evidence ZIP yolunu saxlayır. Replay yolu həmin inference-i təkrarlamır. OpenRouter HTTPS access tələb olunur; Ollama və Qwen download-u aktiv runtime üçün tələb edilmir.

Frozen identity: `configs/openrouter_gemini_pilot.yaml`, hash **eaa371255716**; `google/gemini-3.5-flash`, `reasoning_effort=low`, prompt v9; endpoint `https://openrouter.ai/api/v1`. Bir stage çağırışı üçün max_attempts=1, transient_retries=0 dəyişmir. Storage yolları frozen relative config-də qalır; ayrıca cloud filesystem köhnə laptop storage-dan müstəqildir.

DINO build source SHA: `7764ea0f912e53c92e82eb78a2a1631e92725fc8`; `dinov2_vits14_pretrain.pth`, təxminən 88.3 MB, SHA256 `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`. Build PyPI, PyTorch wheel index, GitHub codeload və `dl.fbaipublicfiles.com` access tələb edir. Source/weights image-ə daxil edilir; runtime-da normal halda yenidən download lazım deyil. Cache build script-i checksum yoxlayır və mövcud cache-i overwrite etmir.

## Render planı, qiymət və environment

`render.yaml` **hazırlanıb, Render-də apply edilməyib**. Service `retrace-ai-isolated`; Docker runtime; branch `feat/cloud-deployment`; Frankfurt; single instance; plan **2c-4g (4 GB RAM, 2 CPU)**; `autoDeployTrigger: off`; health path `/_stcore/health`. Blueprint yaradılması ilk deployment-i başlada və ödəniş yarada bilər; autoDeploy off bunu pulsuz etmir.

Web Service compute təxmini **$85/ay**; workspace, bandwidth, disk, tax və OpenRouter usage əlavə xərc ola bilər. Dashboard checkout-da aktual qiymət owner tərəfindən yoxlanmalı və ayrıca təsdiqlənməlidir. Free 512 MB plan bu full image/model runtime üçün seçilməyib. [Render qiymətlər](https://render.com/pricing), [compute plans](https://render.com/docs/compute-plans), [Blueprint specification](https://render.com/docs/blueprint-spec).

Environment names və davranış:

| Ad | Tələb / mənbə |
| --- | --- |
| `PORT` | Render tərəfindən verilən listener port; script oxuyur. |
| `GAMEQA_PUBLIC_REPLAY` | İlkin blueprint-də `1`: immutable replay, live və approval disabled. |
| `OPENROUTER_API_KEY` | Yalnız live mode üçün Render secret; replay üçün lazım deyil. Dəyərini Git/log-a yazmaq olmaz. |
| `GAMEQA_CONFIG` | Docker/script canonical frozen config-i seçir. Başqa config seçərək freeze-i bypass etməmək. |
| `TORCH_HOME` | Docker image-də `/opt/torch-cache`; yoxlanmış model cache. |
| `PYTHONPATH` | Docker image-də `/app/src`. |
| `GAMEQA_PUBLIC_STATIC` | Bu Render planında qoyulmur; Vercel/static media rejimi üçün nəzərdə tutulub. |

İlkin deployment-də provider key əlavə etməmək. Live açılarsa `GAMEQA_PUBLIC_REPLAY` silinməli/0 edilməli və key host secret kimi verilməlidir. Public live UI-də authentication yoxdur: internet istifadəçiləri paid key-i işlədə bilər. Mövcud $5 key limitini və no-auto-top-up qaydasını qorumaq; bunu bu sessiyada provider dashboard-da ayrıca yoxlamamışıq. Limit quota/access control əvəzi deyil. Həmin açılış owner-in ayrıca təsdiqi və məhdud smoke yoxlaması ilə edilməlidir.

## İcra sübutları

| Check | Nəticə / provenance |
| --- | --- |
| Lokal offline suite | **218 passed, 6 deselected, 87.07 s**; `pytest -m 'not real_model' -q -ra`, ayrıca writable basetemp, mövcud venv. Deselected real-model checks icra edilməyib. |
| İlkin sandbox test | **73 failed, 145 passed, 6 deselected, 102.38 s**. Müvəqqəti atomic rename-lərdə WinError 5 və environment config təsiri; sonra ayrı writable temp və inherited config olmadan yuxarıdakı clean rerun. Bu ilk nəticə gizlədilmir və cloud xətası kimi sayılmır. |
| Base GitHub CI | Run [37955492597](https://github.com/AliAgabalayev/RETRACE-AI/actions/runs/37955492597), exact base SHA: checks/container success; **218 passed, 6 deselected, 39.71 s**. Saved CI log birbaşa oxunub. |
| Yeni feature PR CI | Run [38136686460](https://github.com/AliAgabalayev/RETRACE-AI/actions/runs/38136686460): **checks PASS (1m38s), container PASS (1m27s), GitGuardian PASS**. GitHub runner-də yeni Docker build/startup, keyless replay/evidence və CPU DINO check icra olunub; Render deyil. Log ayrıca saxlanılıb. |
| Docker build/startup | Lokal Linux Docker engine pipe yoxdur, ona görə **lokal build BLOCKED**. Eyni dəyişməyən Dockerfile GitHub CI-də build edilib; image 1,734,729,871 bytes (~1.62 GiB). Health ilk connection reset-lərdən sonra retry ilə uğurlu, keyless replay və CPU DINO load verified. Render build nəticəsi deyil. |
| Ayrıca lokal app | `scripts/start_deployment.py`, yalnız yeni checkout, port **8537**, public replay, credentials boş; health **200**. stderr-də `Uvicorn server started on 0.0.0.0:8537`, 15:33:50 local log vaxtı. Launch-to-ready duration ayrıca ölçülməyib. |
| Browser | Reference/Candidate, recorded replay/no-new-inference label, stored read-only rules, run/sample, **FAIL**, region və scene forbidden observations, crops və ZIP button görüldü. DOM-də 8 image loaded, browser warn/error siyahısı boş idi. Public mode-da live və approvals disabled. |
| Browser ZIP | Download tamamlandı; 24 entry, CRC test uğurlu; `evidence.json`, `analysis.json`, Markdown, rules, inputs/crops var. Canonical replay ZIP ilə byte-identical; package-dəki bütün **20 original file** hash-i ZIP içində də uyğun gəldi. |
| CPU model | Existing cached weights ilə ayrıca Python process, verification-only in-memory CPU device: **3.729 s**, torch.hub, weights hash prefix `b938bf1bc15c`, model load-dan sonra RSS **618.4 MiB**. Frozen file dəyişməyib. Local Torch CUDA wheel istifadə etdiyi üçün Docker CPU build ilə eyni memory profile sayılmır. Full forward/end-to-end peak RAM ölçülməyib. |
| API / real inference | **0 yeni VLM call**, 0 bu task-a aid provider spend. Fresh cloud inference və connectivity **UNVERIFIED**. |
| Blueprint və secret scan | Blueprint fields lokal YAML parse/assert ilə yoxlanıb; Render server-side validation apply edilməyib. Tracked text və yeni deployment fayllarında OpenRouter/Gemini/GitHub token və private-key pattern scan aparılıb; credential tapılmayıb. Bu scan formal secret-audit zəmanəti deyil. |
| Hosting access | Browser `dashboard.render.com/login` göstərdi; Windows User `RENDER_API_KEY` presence false. Heç bir billable resurs yaradılmayıb. |

Lokal venv Python 3.12.3, Torch 2.6.0+cu124, torchvision 0.21.0+cu124, Streamlit 1.61.1. Dependency installation, model download və global system dəyişiklikləri edilməyib. Testlər semantic VLM accuracy sübutu deyil. 4 GB RAM/2 CPU uyğun ilkin seçimdir, ancaq full workload memory/latency və concurrent uploads məhdudiyyətləri Render-də ölçülməlidir.

Audit log/script/JSON faylları tracked source xaricində `../drive-link-update/cloud-*` saxlanılıb. Browser download `Downloads/20261009T123704Z-8e4e19-replay.zip`-dir. Yeni replay server port 8537-də müstəqil işləyir; bu mövcud 8525 serverini əvəz etmir.

## Replay evidence və məhsul məhdudiyyətləri

Recorded run **20261009T123704Z-8e4e19**, sample **vr_4b921c5d**; model observation: “The large wooden barrel has disappeared from the wooden stand.” Region və scene judgment forbidden/D1, final **FAIL**. Bu yeni inference deyil.

`deploy/replay/barrel-replay.zip`: **19,478,122 bytes**, SHA256 **7399de171e5c1514a057a466e4b3bc0535a24e2b2a56bee0a1d418a6c1942e9b**. Original inputs/crops/observations qorunub; portable Markdown/evidence index reconstructed-dır, original run ZIP unavailable. UI bunu açıq göstərir. `package.json` historical inference code SHA-sını `c917532ac3161a0886f626985c53307eb2d477d8` kimi saxlayır; bug observation-a yeni deployment SHA aid etmək olmaz.

C2 12-pair development diagnostic-dir: B və C decision coverage 41.7%, hybrid bug false-PASS 1/5; missing-pedestal failure açıq qalır. Cloud hosting bu problemi həll etmir. DINO contribution, held-out accuracy və production readiness iddiası yoxdur. Tam dev12/raw datasets və laptop-a sonradan əlavə edilmiş şəxsi screenshot-lar deployment üçün tələb olunmur və bu task-da cloud bundle-a əlavə edilməyib.

## Əsas risklər və manual addımlar

1. **Owner təsdiqi və giriş:** Render account login, repository access və 2c-4g qiymət təsdiqi lazımdır. Secret-i chat-a yazmayın. Blueprint-də Create/Apply düyməsini pricing təsdiqindən əvvəl basmayın.
2. **Ayrıca service:** təsdiqdən sonra Render New Blueprint və ya Docker Web Service; repository RETRACE-AI, branch `feat/cloud-deployment`, Dockerfile `./Dockerfile`, context `.`, Frankfurt, 2c-4g, one instance, auto deploy off. Existing Docker CMD-ni saxlayın; custom build/start override lazım deyil. Health `/_stcore/health`.
3. **İlkin replay:** `GAMEQA_PUBLIC_REPLAY=1`; key verməyin, `GAMEQA_PUBLIC_STATIC` qoymayın. Build/start logs və actual cloud URL-ni saxlayın. HTTP 200-dən sonra browser-də replay label, stored rules, FAIL, crops və ZIP hash yoxlamalarını təkrarlayın. URL-ni köhnə submission linkinə avtomatik tətbiq etməyin.
4. **CPU/RAM smoke:** container-də `python -c "from gameqa.config import load_config; from gameqa.vision.features import FeatureExtractor; f=FeatureExtractor(load_config()); assert f.device=='cpu'; print(f.backend)"`. Bu loading check-dir, fresh VLM deyil. İlk full image workload-da peak RSS, latency və oom/restart logs ölçülməlidir. 4 GB limitdə zəmanət verilməyib.
5. **Live mode ayrıca:** yalnız təsdiqlənmiş key/budget və access siyasəti olduqda host secret əlavə edin, public replay flag-i çıxarın, manual redeploy edin. Frozen config-ə toxunmadan bir bounded live smoke; actual calls, usage/cost və evidence provenance saxlayın. Bu report-da belə run yoxdur.
6. **Storage:** Render default filesystem ephemeral-dır. Yeni uploads/runs/reference history redeploy zamanı itə bilər. Saved immutable barrel image daxilində qalır. Live persistence tələb olunarsa ayrıca disk qiyməti təsdiqlənməli, config-i dəyişmədən frozen relative storage-nin uyğun `/app/artifacts/c2-openrouter-20261009` yerinə mount/backup strategiyası yoxlanmalıdır. İlkin blueprint disk yaratmır.
7. **Build risk:** təxminən 1.62 GiB image və dependency/model endpoints ilkin build müddətinə təsir edir. Cache download script-də açıq retry/timeout yoxdur; transient network failure-da deployment failed ola bilər. Retry owner tərəfindən deployment səviyyəsində, freeze dəyişikliyi olmadan edilə bilər. Transformers fallback pinned runtime dependency deyil; primary cached torch.hub path yoxlanmalıdır.

Docker engine olan ayrıca maşında reproducible smoke (mövcud laptop port/tunnel istifadə edilmir):

```sh
docker build -t retrace-ai-cloud .
docker run --rm --name retrace-ai-cloud-check -p 8538:10000 \
  -e PORT=10000 -e GAMEQA_PUBLIC_REPLAY=1 retrace-ai-cloud
curl --fail http://127.0.0.1:8538/_stcore/health
```

Exact application startup command: `python scripts/start_deployment.py` (Docker CMD). Provider secret replay üçün tələb olunmur; live üçün yalnız `OPENROUTER_API_KEY`.

## Rollback və handoff

Bu task-da cloud service olmadığı üçün cloud rollback lazım deyil. Sonradan yaradılmış ayrıca Render service-i owner suspend edə və ya həmin service-in əvvəlki verified deployment-inə rollback edə bilər; repo/Cloudflare/laptop proseslərinə toxunmaq lazım deyil. Auto deploy off qalmalıdır. Deploy edilmiş commit və config hash ayrıca qeyd edilməlidir.

Default branch merge ayrıca approval tələb edir və edilməyib. Branch/PR hazırlığı paid hosting təsdiqi əvəzi deyil. Cloud URL, actual Render build/start timing/logs, 4 GB workload memory, fresh live result və persistence hələ tamamlanmalı verification-lardır. Köhnə demo linkini switch etmək bu işin scope-unda deyil.
