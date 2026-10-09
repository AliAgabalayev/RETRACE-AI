# Ali local UI self-test — 2026-10-09 17:46 Bakı

**Current status17:46:** Ali `.env` key-ini yenilədi; auth-only check **HTTP200/authenticated=true** verdi. Köhnə managed Streamlit process dayandırıldı, yeni process aşağıdakı `env -u` launch ilə başladı. Local UI health **HTTP200/ok**-dır. Key dəyəri göstərilməyib; generation/VLM call edilməyib. Əvvəlki401 aşağıda historical diagnostic kimi saxlanılır.

Ali ayrıca göstəriş verdi: stopped local processes-dən sonra latest merged integration kodunu gətir, UI-ı OpenRouter ilə aç və özünün test edə bilməsi üçün addımları göstər. Bu **local self-test**-dir; Celalın final recording üçün ayrıca UI-ready SHA gate-i saxlanılır.

## İcra edilmiş yoxlamalar

- Main checkout `feat/hackathon-demo-integration`, latest fetched origin ilə eyni **`79a0ef740196cbaa0639579386c6c591d2bfd8ca`**. Presentation/docs ayrıca `docs/ali-final-pitch` branch-də qorundu; source dəyişdirilmədi.
- `GAMEQA_CONFIG=configs/openrouter_gemini_pilot.yaml`: config hash **`eaa371255716`**, OpenAI-compatible adapter enum `openai`, endpoint `https://openrouter.ai/api/v1`, exact model `google/gemini-3.5-flash`, low.
- Streamlit **http://localhost:8501**, foreground managed terminal process. Sandbox socket bind PermissionError verdi; eyni launch authorized host process-də açıldı.
- `GET /_stcore/health` → **HTTP200 / ok**.
- AppTest opening-only → **0 exceptions**; title Rule-aware visual regression; Pair source Upload two images, VLM engine Real(config). Analyze klik edilmədi; model call yoxdur.
- Initial local key env presence yoxlandı, dəyər göstərilmədi. Auth-only `GET https://openrouter.ai/api/v1/auth/key` → HTTP401 idi; process environment və `.env` fərqli key saxlayırdı və ilkin hər ikisi401 verdi. Ali `.env` update-dən sonra **dotenv auth200** oldu. Global environment dəyişdirilmədi; yalnız yeni app child process-dən köhnə env key çıxarıldı ki, native dotenv loader yeni dəyəri götürsün.
- C2 saved-run directories bu host-a transfer olunmayıb; canonical run namespace-də saved runs siyahısının boş olması bu mərhələdə expected-dir.

Launch:

```bash
env -u OPENROUTER_API_KEY GAMEQA_CONFIG=configs/openrouter_gemini_pilot.yaml .venv/bin/streamlit run app.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true \
  --browser.gatherUsageStats false
```

Bu launch `.env`/key update-dən sonra fresh process ilə yerinə yetirildi; cached Judge/proses environment-də köhnə key qalmır. Əgər əvvəlki error run açıqdırsa, browser yeni session ilə açılır; eyni page-in rerun/Analyze memoization-u köhnə nəticəni göstərməsin. Root model generation etməyib.

## Ali necə yoxlayır?

1. http://localhost:8501 aç; **VLM engine = Real(config)** saxla.
2. İlk smoke: Pair source **Demo pair** → **synthetic fixture | object_removed**. Rules hazır gəlir. Bu synthetic-dir; benchmark nəticəsi kimi göstərilmir. Valid key-dən sonra **Analyze** bas; bir job bitməmiş ikinci job başlatma.
3. Decision yanında observed change, R1 before/after crops, rule IDs və validation/errors yoxla. **Diagnostics → versions** içində `vlm_model` OpenRouter/Gemini3.5, prompt v9, config hash eaa371255716 olmalıdır. Enum `openai` OpenAI model demək deyil; compatible adapter-dir.
4. Real barrel üçün **Upload two images**: `data/work/vr_4b921c5d/reference.png` və `candidate.png`. Rules editor-a exact A1/allow və D1/deny descriptions köçür: `artifacts/20261009T112802Z-c4530d/rules.yaml`. Default illustrative A1/A2/D1/D2 rules həmin dev comparison-un exact rules-u deyil.
5. Qwen həmin real pair-də REVIEW verdi; C2 Gemini saved result `20261009T123704Z-8e4e19` FAIL R1/SCENE(D1)-dir. Bu tarixi comparison-dur; Ali host-da yeni run eyni cavaba zəmanət vermir. Canlı müddəti ayrıca qeyd et.
6. **Export ZIP** endir; `report.md`, `analysis.json`, `evidence.json`, `rules.yaml`, images/crops aç. Stored model/config və final qərar eyni olmalıdır.
7. Known failure: `data/work/vr_c1f47c57/` missing pedestal. C2 B/C PASS verib; bug false-PASS1/5 **coverage5/12 ilə birlikdə**. Bu example model limitini göstərir, test gözləntisini PASS uğuruna çevirmir.

OpenRouter gateway/provider yoludur; model burada Gemini3.5 Flash-dır. Pipeline/proposals/policy Qwen baseline ilə frozen saxlanılıb. Görünən fərq modelin təsvir/verdict keyfiyyətidir: barrel Qwen REVIEW/Gemini C2 FAIL; booth C2 C FAIL/B REVIEW; pedestal yenə yanlış PASS. DINOv2 advantage və ümumi safety iddiası yoxdur.

## Presentation files main switch-dən sonra

Tracked slides docs branch-də saxlanılır. Main integration UI dəyişməsin deyə local copies git-ignored `artifacts/ali/presentation/{pitch,slides}/` altındadır. Motion `artifacts/ali/motion/ali_evidence_motion_DRAFT_110s.mp4`-dır: 110s silent draft, final recording deyil. Final recording yalnız C4 UI-ready SHA + final bundle/download verification-dən sonra.
