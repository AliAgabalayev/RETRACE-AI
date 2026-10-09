# Celal — first runtime gate handoff

**Gate: PARTIAL. Useful visual judgment: BLOCKED.** Environment və real DINOv2 işləyir; real pair → actual CLI/UI → conservative REVIEW → report ZIP yolu icra olundu. VLM image calls meaningful response vermədi. Bu nəticə working hybrid perception və ya QA accuracy claim-i deyil.

## Vaxt və Git

- Actual start: **2026-10-09 14:43:01 Asia/Baku**; 15:15 cutoff-a 31m59s qalırdı. 45 dəqiqəlik pəncərə əvəzinə daha erkən 15:15 cutoff tətbiq edildi.
- Diagnostic freeze: **15:09:39**; həmin vaxt cutoff-a 5m21s qalırdı. Bundan sonra yalnız handoff/Git/owned-process cleanup; yeni model experiment/install yoxdur.
- Worktree: `C:\Users\celal\OneDrive\Belgeler\ChatGPT\Hackaton\neuroscience-runtime-eval`.
- Branch: `feat/hackathon-runtime-eval`.
- BASE_SHA və executed application HEAD: `b7aa8b8a2155cdbe2f71f9598fd25c3f50ed5683`.
- Runtime observer checkpoint / HEAD bu handoff yazılarkən: **`6bda35db392170e6480d1ca3740ac8b74865b6a5`**. Sonrakı docs-only delivery commit application code-u dəyişmir; final SHA `git rev-parse HEAD` və ignored `artifacts/runtime-gate-20261009/final-git-state.json` ilə qeyd olunur.
- Read-only `git ls-remote origin HEAD` 15:09-da həmin b7aa8b8 full SHA-nı qaytardı. Fetch/reset/clean/master edit edilməyib.
- Ali ilə BASE_SHA/bundle sorğusu verildi, cavab gəlmədi: **shared-base agreement UNCONFIRMED**. Remote `feat/hackathon-vision-evidence` həmin ilkin check-də görünmədi; bu, Ali-nin lokal işinin olmadığını sübut etmir.
- Audit report orijinal `neuroscience-hackhaton` checkout-da untracked olaraq qorunur. Onu və əvvəlki caches/reference history-ni dəyişmədim.

## Environment — verified

Windows / PowerShell; Anaconda Python **3.12.3**. Dedicated `.venv` **system-site-packages** ilə mövcud Torch-u reuse edir. Yeni package writes yalnız `.venv`-dədir; global Conda/driver/CUDA dəyişməyib.

Versions: OpenCV distribution **4.12.0.88** (`cv2.__version__ == 4.12.0`); NumPy **2.0.2**; Torch **2.6.0+cu124**; torchvision **0.21.0+cu124**; Pillow **10.4.0**; Streamlit **1.61.1**; pytest **8.3.4**; Pydantic **2.8.2**; httpx **0.27.0**; PyYAML **6.0.1**. `import cv2, torch, gameqa.pipeline` uğurludur, CUDA available=True. cv2 `.venv/Lib/site-packages`-də, Torch Anaconda-dadır.

Start resource check: RTX 4060 Laptop **8188 MiB**, **6921 MiB free VRAM**; available RAM təxminən **2.22 GiB**; C: free **124,557,529,088 bytes**. RAM məhduddur. Anaconda psutil `disk_usage('.')` ayrıca SystemError verdi; disk free PowerShell ilə ölçüldü, app defect kimi sayılmadı.

Existing Ollama service **11434** toxunulmadan saxlanıldı; yalnız text-only `qwen3:8b-q4_K_M` var idi. Provider environment key **presence** check-ləri false idi; heç key value oxunub/log-lanmayıb. Yeni service **11435**, project-local `models/ollama`, Ollama **0.40.1** istifadə etdi. `qwen2.5vl:3b` təxminən 3.2 GB download oldu; backend əlavə compat GGUF migration artifacts yaratdı. Model weights/data/caches commit edilmir.

Initial downloaded model tag ID **fb90415cde1e** idi. Runtime compat migration-dan sonrakı observed manifest digest **`79d4979787523c92629bc043c0584a5132d6758e40b429586203a6b1094cb6f8`**; `ollama-tags.json`/`ollama-show.json` saxlanıb. Capabilities `completion`, `vision` göstərir; image batches service log-da encoded/decoded oldu, amma coherent output yoxdur. Model adı/capability list təkbaşına working inference sübutu deyil.

Frozen DINOv2 ViT-S/14 CUDA cold load **39.0394s** (download daxil). Source `facebookresearch/dinov2` torch.hub **mutable main**, weights `https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth` (~84.2 MiB). Actual SHA256 **`b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`**. Custom TORCH_HOME səbəbilə native version field `weights_sha256=unknown` dedi; external source-identity evidence actual hash-i saxlayır. Ali-nin feature code-u dəyişdirilməyib.

## Exact setup/start commands

Bu commands worktree root-dan PowerShell-dədir. Working env artıq yaradılıb; mövcud `.venv`-i təkrar recreate etməyin.

```powershell
python -m venv --system-site-packages .venv
.\.venv\Scripts\python.exe -m pip install --no-deps opencv-python==4.12.0.88
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TORCH_HOME = (Join-Path (Get-Location) 'models\torch')
```

Separate terminal, project-local Ollama service (original 11434-dən ayrıdır):

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = (Join-Path (Get-Location) 'models\ollama')
$env:OLLAMA_KEEP_ALIVE = '10m'
ollama serve
# Başqa terminalda, eyni OLLAMA_HOST:
ollama pull qwen2.5vl:3b
```

Model artıq downloaded-dir; yenidən pull lazım deyil. CLI/UI config-lər ignored `artifacts/runtime-gate-20261009/{cli,ui}.yaml`-dadır. Default config ilə müqayisədə yalnız VLM base_url və isolated artifacts/cache/reference paths dəyişir; prompts, thresholds, policy və scoring dəyişmir. Config hashes: CLI **b45912efc951**, UI **2d320955df23**. Hər iki cache namespace əvvəl yeni/boş idi.

Executed actual CLI (observer original `gameqa.cli.main` və `httpx.post`-u delegate edir; response substitution yoxdur):

```powershell
.\.venv\Scripts\python.exe scripts/runtime_gate_capture.py `
  --evidence-dir artifacts/runtime-gate-20261009/capture-cli -- `
  analyze --config artifacts/runtime-gate-20261009/cli.yaml `
  --reference artifacts/runtime-gate-20261009/inputs/vr_562bb641/reference.png `
  --candidate artifacts/runtime-gate-20261009/inputs/vr_562bb641/candidate.png `
  --rules artifacts/runtime-gate-20261009/inputs/vr_562bb641/rules.yaml `
  --sample-id vr_562bb641 --json
```

Reproducer üçün evidence directory-ni **yeni adla** verin və yeni empty cache/output config yaradın; helper existing capture directory-ni overwrite etmir. Existing evidence/caches silinməsin.

Executed UI start:

```powershell
$env:GAMEQA_CONFIG = 'artifacts/runtime-gate-20261009/ui.yaml'
.\.venv\Scripts\python.exe -m streamlit run app.py `
  --server.address 127.0.0.1 --server.port 8522 --server.headless true `
  --browser.gatherUsageStats false
```

## Inputs və provenance

Fallback olaraq yalnız **iki dev pair üçün 4 JPEG** tələb edildi; whole dataset/metadata parquet download edilmədi. Manifest/splits/labels regenerate edilmədi. Pinned dataset revision `2afbfdcc9cb84318845f348c023bb2e92b942e29`; URL formatı existing `prepare.py` ilə eynidir. Inference-ə yalnız images + manifest rules verildi, eval label verilmədi.

Tam bərpa olunmuş **`vr_562bb641`**, Youtube-Cutscene, 1207×718:

- Reference raw SHA: `fb63b98b2ed12da728bbcd908eee637dc88c047499b3b314c5cafe0518304f90`.
- Candidate raw SHA: `ea4f1194c0438b0a0ff06cd44947006beea8be1c98966d2e89b8487ab4669d61`.
- PNG SHA-lar: reference `86fa5576424d9c9cea29a0209ce79ed1deb0c1b47207fc9c6b88d9a22fa2803f`; candidate `9db614710c66a68f0df0cac705a7c9e6414c6725cb717243b0000485610ec0a4`.
- Both raw hashes committed manifest ilə match oldu; provenance JSON source URLs/revision/size saxlayır. Benchmark dev label “bug” selection üçün istifadə olunub; **independent human bug verification yoxdur**. Ali-nin selected/human-verified pair-i hələ alınmayıb.
- İkinci `vr_59af7164` clean dev pair-in yalnız reference-i bərpa oldu; candidate download DNS `getaddrinfo failed (11001)` ilə dayandı. Allowed/ambiguous real runs **EXECUTED deyil**.

## Actual run evidence

Artifact root: `artifacts/runtime-gate-20261009/` (bütün paths bu worktree-dədir).

| Yol | Nəticə |
| --- | --- |
| CLI run `20261009T105610Z-e59fa4` | NEEDS_REVIEW; engine_mode native `real`, execution_status native `complete`; bu flags valid visual output demək deyil |
| CLI wall / pipeline | **124.5174s** / **46.7498s**; cold warmup ayrıca **73.0271s**, provider-reported load ~59.11s |
| DINO features / proposals | Features **0.6048s**, 1 full-frame proposal `[0,0,1207,718]`, `truncated=True`; alignment unreliable |
| CLI VLM | 1 text warmup + **4 image HTTP calls** (2 stage-1 retries region, 2 scene); image replies empty/invalid, stage 2-yə çatmadı; valid observation/rule judgment yoxdur |
| CLI cache | Yeni boş namespace; observer calls actual network calls idi, disk-cache responses istifadə edilmədi. Model internal prefix reuse ayrıca anlayışdır |
| UI run `20261009T110111Z-9aeda9` | Actual browser upload, exact two rules editing, Analyze, boxes/crops və error inspection; NEEDS_REVIEW; pipeline **3.2956s**, failed warm requests, successful inference latency deyil |
| Input/rules identity | CLI və UI normalized PNG hashes original selected PNG-lərlə match; UI rules manifest/CLI rules ilə exact match |
| Plain browser Rerun | Eyni run ID və analysis hash/mtime qaldı; model expiry dəyişmədi (`rerun-verification.json`). Yeni run/inference əlaməti yoxdur |
| ZIP | CLI **5,760,271 bytes / 32 entries**, UI **4,430,524 bytes**; both archives open, `testzip() is None`; expected input/rules/crops/analysis/Markdown mövcuddur |

CLI ZIP: `runs-cli/20261009T105610Z-e59fa4.zip`; əlavə olaraq provider-capture exact composed PNG-ləri, prompts/schemas, raw HTTP response bodies, config, package/model/source identity və input provenance daxil edildi. Structured verdict/errors `analysis.json`-dadır. UI ZIP: `runs-ui/20261009T110111Z-9aeda9.zip`. Final checks/hashes/member lists `zip-verification.json`-dadır.

Browser **Export ZIP** click edildi, lakin automation download event-i timeout verdi: **browser download completion UNVERIFIED**. Server-generated archive integrity yuxarıda verified-dir; bunlar ayrı checks-dir. `ui-review.jpg` actual result screenshot-dur. Approval/history bu gate-də run edilməyib; references path isolated olsa da REVIEW-i approve etmək lazım deyildi.

## Tests — yeni execution, historical nəticə deyil

```powershell
.\.venv\Scripts\python.exe -m pytest -m 'not real_model' -q -ra `
  -p no:cacheprovider --basetemp "$env:TEMP\gameqa-runtime-gate-pytest-unsandboxed"
```

- İlkin sandbox run: **57 failed, 117 passed, 6 deselected, 0 skipped, 13.42s, exit 1**. Failures əsasən atomic `os.replace` WinError 5; AppTest də bu storage restriction-dan təsirləndi. Log qorunub.
- Eyni suite ayrı authorized unsandboxed temporary storage-də: **174 passed, 6 deselected, 0 skipped, 12.70s, exit 0**. App source/test dəyişdirilmədən keçdi. İlk failures gizlədilmir və app fix claim-i yoxdur.
- Real-model marker-li **6 test deselected** idi; passing kimi sayılmır. Bu suite model accuracy ölçmür. Historical 168/60-pair rəqəmləri bu gate-in nəticəsi deyil.
- Helper `--help` və actual delegation run yoxlanıb. `git diff --check` uğurludur. Global package install/upgrade edilməyib.

## Concrete blocker → Ali handoff

Existing `vision/judge.py`-ın Ollama requests-i schema `format` ilə service 11435-ə gedir. Capture `call-02-request.json` və `call-02-message-0-image-0.png` exact reproducer-dir; JSON-da image placeholders PNG bytes ilə base64-ə çevriləndə original request bərpa olunur.

Ollama **0.40.1**, llama-server build **631109b34**, image batches decode olunduqdan sonra server log-da:

```text
got exception: Unexpected empty grammar stack after accepting piece: @ (31)
```

Client HTTP **200**, `model=""`, `message.content=""`, `done=false` aldı; bu success deyil. Raw captures saxlanıb. Same exact prompt/image/options ilə `format="json"` diagnostic də boş response verdi. Yalnız `format`-ı çıxaran diagnostic **HTTP 500: prediction aborted, token repeat limit reached** verdi. Buna görə “schema → JSON mode” dəyişməsi verified fix deyil. Bu diagnostics perception quality score deyil. Log excerpt `ollama-observed-excerpt.txt` tool session-dən transkripsiyadır, full persisted server log deyil.

**Bir next action:** Ali-nin verified image-capable original runtime/provider-ında captured exact image + request reproducer-i işlətmək, onun işləyən Ollama version/config/adapter identity-sini qaytarmaq. Ali owns `vision/` provider/crop/prompts/report code; bu faylları dəyişmədim. Coherent stage-1 output alındıqdan sonra eyni dev pair ilə yeni namespace-də engineering gate təkrarlansın. Forced PASS, truncation guard removal, threshold/prompt tuning və training edilməsin.

## Files changed / service lifecycle

- `scripts/runtime_gate_capture.py`: local Ollama calls üçün observer; original CLI/provider/policy delegate edilir, headers/environment credentials log-lanmır; exact PNG və response evidence saxlanır.
- `docs/CELAL_HANDOFF.md`: bu handoff.
- Application/config/tests/manifests/instructions və Ali-owned vision/report files unchanged.
- `.venv`, `models/`, runtime inputs/configs/logs/caches/runs/ZIP/screenshot ignored local outputs-dur; stage/commit/push edilmir.
- Owned test services: localhost **8522** (Streamlit) və **11435** (project-local Ollama). Final cleanup vəziyyəti `final-git-state.json`-da qeyd edilir; original 11434 service toxunulmur. Restart commands yuxarıdadır.
- Browser download və independent human annotation pending; useful VLM/hybrid perception **BLOCKED**. Dependency-clean UI + DINO + truthful REVIEW/ZIP yalnız partial engineering progress-dir.

Bu bounded task burada dayanır. Yeni diagnostic/intervention roadmap-ı gözlənilir.
