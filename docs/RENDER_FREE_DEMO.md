# RETRACE-AI — 24 saatlıq Render Free replay

11 oktyabr 2026. İlkin status: **PARTIAL — Free container hazırlanıb; hosted nəticə aşağıda yenilənəcək.** Bu sənəd müvəqqəti $0 replay üçün əvvəlki 4 GB deployment planını əvəz edir. Full live application üçün əvvəlki resource assessment qüvvədədir.

## Məqsəd və qorunan sərhəd

`feat/cloud-deployment`, mövcud draft PR #10. Başlanğıc SHA `fac04203646911a43e521a79e7ea7705c369121c`; application/frozen code base `538e1b149cb75ae691888ecf23a4277fa792ad73`. Default branch-ə merge edilmir. Mövcud Cloudflare URL, port 8525 serveri və tunnel dayandırılmır, dəyişmir və submission linki switch edilmir.

Seçilən yol **Option A: mövcud Streamlit UI, replay-only Docker image**. `Dockerfile.replay` yalnız UI/import üçün lazım olan eyni pinned dependencies-i qurur; Torch, torchvision, Hugging Face və DINO weights daxil etmir. `scripts/start_free_replay.py` public replay flag-ini məcburi seçir və provider key-ləri child process-ə ötürmür. Host yanlışlıqla live flag qoysa da Analyze açılmır. Mövcud `Dockerfile`, `app.py`, historical observations, rules, model config, policy və evidence dəyişmir.

Saxlanılan funksiyalar: Reference/Candidate, stored rules, historical barrel **FAIL**, observed changes, region crops və evidence ZIP. Label açıqdır: “Recorded model run — replay, no new inference.” Live upload/analyze, DINO loading, paid VLM, yeni reference approval/history, digər pair-lərin analizi yoxdur. Bunlar replay rejiminin açıq məhdudiyyətləridir.

## Render konfiqurasiyası

- Ayrı service adı: `retrace-ai-free-replay`.
- Repository: `https://github.com/AliAgabalayev/RETRACE-AI`; branch `feat/cloud-deployment`.
- Runtime Docker; Dockerfile `./Dockerfile.replay`; build context repository root.
- Plan **Free, $0 compute, 512 MB RAM, shared CPU**, one instance; Frankfurt.
- Health `/_stcore/health`; auto deploy **Off**; heç bir disk/database/worker/paid add-on yoxdur.
- Start command image-dən: **`python scripts/start_free_replay.py`**. Render `PORT` verir; default 10000.
- Environment: `GAMEQA_PUBLIC_REPLAY=1`; config/path defaults image-dədir. **API secret tələb olunmur və əlavə edilməməlidir.** `GAMEQA_PUBLIC_STATIC` qoyulmur.

Render Free 15 dəqiqə inactivity-dən sonra sleep edir; yeni request zamanı provider təxminən bir dəqiqə wake-up deyir. Local timing bunu hosted cold-start zəmanətinə çevirmir. Ephemeral filesystem restart/redeploy/sleep zamanı dəyişiklikləri itirir; immutable replay/ZIP image daxilində olduğu üçün yenidən əlçatandır. Persistent history yoxdur. [Official Free limitations](https://render.com/docs/free).

$0 compute bütün account usage-larının sınırsız/pulsuz olması demək deyil: bandwidth və build minutes limitləri var. **Payment method/top-up əlavə etməyin**, paid plan/overage almayın; included quota bitərsə suspension qəbul edilir. ZIP hər download-da təxminən 19.5 MB outbound data-dır. Bu service default submission linkini əvəz etmir.

## Verification və evidence

Historical run `20261009T123704Z-8e4e19`, sample `vr_4b921c5d`: missing barrel, validated region və scene forbidden/D1, **FAIL**. Replay həmin nəticəni göstərir, təkrar AI qərarı çıxarmır. Config identity `eaa371255716`, recorded OpenRouter / google/gemini-3.5-flash / low / prompt v9 olaraq qalır; bu free service-də model çağırılmır.

Canonical reconstructed portable export: `deploy/replay/barrel-replay.zip`, 19,478,122 bytes; SHA256 `7399de171e5c1514a057a466e4b3bc0535a24e2b2a56bee0a1d418a6c1942e9b`. Original inputs/crops/observations qorunub; reconstructed report/index açıq qeyd edilir, original run ZIP unavailable.

- Lokal smoke: `scripts/verify_free_replay.py`; 4 UI render, 20 original asset hash, ZIP CRC/evidence decision yoxlandı; **Torch import və VLM calls: 0**. Model imports və pipeline execution assertion ilə bloklanıb. 10.643 s bütün headless smoke/ZIP/rerun müddətidir, server startup deyil.
- CI `free-replay` Docker image-i həqiqətən Torch-suz build edir; 512 MiB hard cgroup və swap limit, 1 CPU altında headless UI/rerun/ZIP, peak RSS, dynamic port/health və container restart yoxlamalarını icra edir. Hosted ölçülərdən fərqlidir; nəticə delivery zamanı qeyd olunur.
- Lokal Docker daemon yoxdur; lokal container build claim yoxdur. Mövcud venv yalnız offline yoxlamalar üçün reuse olunur, global installation/model download edilməyib.
- İlkin focused test command deployment tests-i UI tests-dən əvvəl işlətdikdə inherited config səbəbi ilə 6 failed /20 passed oldu; clean process/order ilə repeat nəticəsi delivery-də saxlanılır. Application bu testlərə uyğunlaşdırılmayıb.

## Owner manual deployment / authentication fallback

Render access olmadıqda burada dayanılır; parol/key chat-a göndərilməməlidir. Login-dən sonra:

1. **New → Web Service → Public Git Repository**, yuxarıdakı URL-ni seçin; OAuth permission expansion tələb olunmur.
2. Branch `feat/cloud-deployment`, Language Docker, Name ayrıca `retrace-ai-free-replay`, Region Frankfurt.
3. **Instance type Free ($0)**, Dockerfile Path `Dockerfile.replay`, Docker context `.`; health `/_stcore/health`; Auto deploy Off. API key, disk, database və paid extras əlavə etməyin.
4. Deploy-dən əvvəl formda Free seçildiyini təsdiqləyin. Billing/card tələb olunarsa bu task çərçivəsində əlavə etməyin və dayanıb owner-ə bildirin.
5. Yeni `*.onrender.com` URL və deploy SHA/logs-u saxlayın. Public URL-də replay label, FAIL, rules, images/crops və download yoxlayın. ZIP hash yuxarıdakına uyğun olmalıdır. Fresh AI nəticəsi iddiası etməyin.

## 24 saatdan sonra silmək

Deployment başlanğıc UTC vaxtını qeyd edib 24 saat sonrasını owner üçün deadline götürün; burada automatic deletion yaradılmır. Render Dashboard → **yalnız `retrace-ai-free-replay` service** → Settings → Delete Web Service, service adını təsdiqləyin. Başqa service, repo branch/PR və Cloudflare tunnel silinmir. Repo-da branch/PR evidence olaraq qala bilər. Müvəqqəti URL bundan sonra işləməyəcək; köhnə submission linki dəyişməz qalır.

## Məhsul iddiaları

Bu recorded demonstration-dır, canlı AI və production-ready QA deyil. C2 12 dev pair-dir; 41.7% decision coverage və missing-pedestal false-PASS limitation dəyişməyib. Free hosting model accuracy ölçmür. Yeni public URL, actual hosted plan/logs/limits və cold-start yoxlanana qədər deployment SUCCESS sayılmır.
