# Deployment readiness — C5

Primary path **Render Docker Web Service, ən az 4 GB RAM /2 CPU**-dur. Free 512 MB plan üçün uyğunluq təsdiqlənməyib. DINOv2 CPU-da işləyə bilər; GPU hosting məcburi deyil. 4 GB engineering headroom-dur, hosted RAM/latency ölçməsi deyil. Render GitHub Dockerfile build və environment secrets dəstəkləyir ([Docker documentation](https://render.com/docs/docker), [compute plans](https://render.com/docs/compute-plans)). C5 external service yaratmır, hosting almır və public deploy etmir.

## Frozen identity və startup

- `configs/openrouter_gemini_pilot.yaml`, merged hash **eaa371255716**.
- OpenRouter `https://openrouter.ai/api/v1`; **google/gemini-3.5-flash**, reasoning **low**, prompt **v9**.
- Secret **OPENROUTER_API_KEY** host environment-dədir, Docker build argument/Git/ZIP/log daxilində deyil. Mövcud $5 key limit və no automatic top-up dəyişmir.
- Python **3.12**, pinned direct runtime versions `requirements.txt`. CPU Torch 2.6.0 / torchvision 0.21.0 official CPU index-dən əvvəl qurulur. OpenCV headless eyni cv2 API üçün Linux GUI dependency-sini aradan qaldırır.
- Entrypoint **`python scripts/start_deployment.py`** config-i seçir, source edit etmir. `PORT` host-dan, default 8501; health **`/_stcore/health`**.

```sh
docker build -t gameqa-demo .
docker run --rm -p 8501:8501 gameqa-demo
# Live üçün shell environment secret-i keçirir, dəyəri command-da yoxdur:
docker run --rm -p 8501:8501 -e OPENROUTER_API_KEY gameqa-demo
```

`.env.example` placeholder-only-dir. Docker context `.env`, secrets.toml, Git, local caches/weights/history-ni istisna edir. Non-root `gameqa` user, writable `/app/artifacts` və `/app/references`. Default storage ephemeral-dir. History retention üçün persistent mount/backup owner tərəfindən qurulmalıdır. Boş mount-da barrel seed bərpa edilir; mövcud run overwrite edilmir. Multiple replicas/shared approvals yoxlanılmayıb.

Build public DINO source **7764ea0f912e53c92e82eb78a2a1631e92725fc8** və `dinov2_vits14_pretrain.pth` pre-cache edir. Weight SHA256 **b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9**, **88,283,115 bytes**. Source-un 156 runtime Python faylı əvvəlki local frozen cache ilə Git blob hash üzrə eynidir. Weights Git-ə daxil edilmir. CPU wheels ilə image yüzlərlə MB ola bilər; final ölçü build-də ölçülməlidir. Replay startup DINO/VLM yükləmir; model live Analyze və CI load check-də yüklənir. Hosted CPU latency/concurrency C5-də ölçülməyib.

## Portable replay

`deploy/replay/barrel` təxminən **18.7 MiB** compact package-dir: historical analysis, exact rules/input/crop PNGs, sanitized four-call captures və usage/runtime identity. `package.json` bütün fayl SHA256-larını və source ZIP identity-ni saxlayır. Duplicate aligned input/overlay startup-da bərpa olunur; current report logic export yaradır. Judgments/historical timings dəyişmir. Bərpa ZIP-i source ZIP ilə byte-identical deyil və **fresh inference deyil**.

Saved run **20261009T123704Z-8e4e19**: “Saved run replay — no new inference”, stored rules, FAIL, R1 crops, evidence download. Key olmadıqda live Analyze disabled/açıq warning; replay qalır. ZIP evidence.json, analysis.json, Markdown, rules, inputs/crops saxlayır. Local C1 dev bundle tələb olunmur; əlavə local presets clean host-da olmaya bilər. Live uploads mümkündür; frozen demos independent accuracy test deyil.

## Windows local command

```powershell
$env:OPENROUTER_API_KEY = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
[bool]$env:OPENROUTER_API_KEY
$env:PORT = '8525'
.venv\Scripts\python.exe scripts/start_deployment.py
```

Key dəyərini print etməyin. Global Python/drivers/existing caches dəyişdirilməməlidir.

## Verification və owner checklist

GitHub Actions: offline tests, diff check, Linux Docker build, keyless health/replay/export və CPU DINO load. Local Windows Docker daemon unavailable; local container build edilmədi. Exact completed checks final delivery və `FINAL_GITHUB_STATE.md`-dədir. Health 200 təkbaşına UI sübutu deyil.

1. Final PR checks/merge və default **master** SHA-nı təsdiqləyin. Repo private-dir; visibility dəyişdirilməyib. Render GitHub access-i owner verməlidir.
2. Dockerfile/default branch ilə service yaradın, ən az 4 GB /2 CPU və health path seçin. Resource creation/purchase C5 xaricindədir.
3. Host **OPENROUTER_API_KEY** secret-i və $5 limit/no auto top-up yoxlayın. Paid Analyze üçün access/budget control qərarı verin; C5 auth sistemi əlavə etmir.
4. Keyless replay, stored rules/FAIL/crops/ZIP yoxlayın. Fresh result iddiası etməyin.
5. History lazımdırsa persistent disk/backup qurun; upload privacy/retention qaydasını müəyyən edin.
6. Hosted CPU latency/RAM/cold start ölçün. Production, held-out accuracy, missing-pedestal fix və DINO contribution iddiası etməyin.

C2 hər iki arm-da 41.7% coverage; hybrid 1/5 bug false-PASS. Missing pedestal açıq failure; tuning yalnız explicit unblock ilə.
