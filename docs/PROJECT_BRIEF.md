# AI Gaming — Rule-Aware Visual Regression Prototype

**Version:** 1.0  
**Tarix:** 9 oktyabr 2026  
**Owner:** Ali / mövcud Product Owner  
**İcra komandası:** PM, Python Developer, QA Engineer, Data Engineer, DL Engineer, Documentation Engineer  
**İş pəncərəsi:** başlanğıcdan 10–12 saat  
**Gözlənilən nəticə:** lokal işləyən, real AI inference göstərən və növbəti gün insan tərəfindən davam etdirilə bilən prototype.

Bu sənəd implementation üçün əsas project brief-dir. Agent definition-ləri ayrıca `AI_Gaming_Agent_Team.md` sənədindədir. Product Owner-ın qəbul edilmiş tələbləri bu sənəddəki default texniki seçimlərdən üstündür. Implementation zamanı edilən dəyişikliklər `docs/DECISIONS.md`-də qeyd edilməlidir.

## 1. Nə qururuq?

QA və ya qrafika mühəndisi əvvəl təsdiqlənmiş oyun skrinşotunu yeni build-in skrinşotu ilə müqayisə edir. İstifadəçi hansı dəyişikliklərin icazəli, hansılarının problem olduğunu müəyyənləşdirir. Tətbiq dəyişmiş ola bilən bölgələri tapır, əvvəl/sonra kəsiklərini göstərir və hər bölgəni qaydalara görə qiymətləndirir.

**Əsas istifadəçi axını:** reference image + candidate image + change rules → dəyişiklik təklifləri → bölgə üzrə visual evidence və hökm → ümumi nəticə → istifadəçinin bug report export etməsi və ya yeni reference təsdiqləməsi.

Problem təkcə piksel fərqini tapmaq deyil. Hava, işıq və character customization dəyişə bilər, amma obyektin yoxa çıxması və ya tələb edilən elementin dəyişməsi bug ola bilər. Buna görə bölgə tapma və qaydaya əsaslanan qiymətləndirmə ayrı mərhələlərdir.

**Prototype-in əsas hipotezi:** DINOv2 patch features ilə dəyişiklik bölgələrinin təklif edilməsi, VLM-in diqqətini həmin bölgələrə yönəltməklə rule-aware comparison-a kömək edə bilər. Bu, eksperimentlə yoxlanmalıdır; üstün nəticə əvvəlcədən qəbul edilmir.

## 2. Final prototype necə görünməlidir?

Bir lokal web tətbiqi açılır. İstifadəçi ilk ekranda iki image upload sahəsi və ya hazır demo pair seçimi görür. İcazəli/icazəsiz qaydaları daxil edib **Analyze** düyməsini basır.

Nəticə ekranında aşağıdakılar görünür:

1. Reference və candidate original screenshots yanaşı.
2. Dəyişiklik təklifləri qutularla və sabit region ID-lərlə.
3. Hər region üçün reference/candidate crops.
4. Observed change, `allowed` / `forbidden` / `uncertain` hökmü, tətbiq olunan rule ID-lər və qısa visual evidence.
5. Ümumi `PASS` / `FAIL` / `NEEDS REVIEW` nəticəsi və səbəbi.
6. Hansı modelin həqiqətən işlədiyi, alignment vəziyyəti, error/truncation göstəricisi və latency.
7. **Export bug report** və **Approve as new reference** əməliyyatları.

User flow-da əsas vurğu vizual müqayisə və qərardır. Patch ölçüləri, tensor shape-lər və debug config-lər əsas ekranı doldurmamalıdır; lazım olduqda ayrıca expandable diagnostics hissəsində göstərilə bilər.

Prototype video və gameplay sessiyası tələb etmədən, hazır screenshot pair-ləri ilə demo edilə bilməlidir. CLI analysis yolu UI-dan ayrıca işləməlidir ki, QA və sonrakı development avtomatlaşdırıla bilsin.

## 3. Scope və prioritetlər

| Prioritet | Requirement |
| --- | --- |
| P0 | İki image upload və hazır demo pair seçimi |
| P0 | Editable allow/deny rules və saxlanan rule ID-lər |
| P0 | Real frozen DINOv2 feature extraction və region proposals |
| P0 | Mövcud credentials/model imkanından istifadə edən real VLM comparison |
| P0 | Before/after crops, boxes və bölgə üzrə evidence |
| P0 | Deterministic final aggregation: pass/fail/review |
| P0 | Timeout, invalid output və model unavailable üçün aydın review/error vəziyyəti |
| P0 | Lokal bug report export və reference history |
| P0 | Reproducible data manifest, mənalı testlər və human handoff |
| P1 | Kiçik held-out benchmark evaluation və classical baseline comparison |
| P1 | Cache, saved run seçimi və expandable diagnostics |
| P2 | Əlavə polish, daha çox sample, threshold experiments |

P1 benchmark smoke evaluation mümkün olduqca təhvilə daxil edilməlidir; işlədilməyibsə açıq incomplete kimi qeyd olunmalıdır. P2 heç vaxt işləyən P0 axınını və təhvil sənədini gecikdirməməlidir.

**Bu MVP-yə daxil deyil:** video, oyunu oynayan agent, Unity/Unreal plugin, fine-tuning/training, authentication, cloud deployment, microservices, external issue tracker inteqrasiyası və avtomatik reference replacement.

“Bug açmaq” bu versiyada lokal report yaratmaq deməkdir. Jira/GitHub ticket yaradılmayacaq. User reference update seçməyincə heç bir reference dəyişdirilməyəcək.

## 4. Data, paper və model linkləri

| Mənbə | Link | Nə üçün istifadə olunur? |
| --- | --- | --- |
| Benchmark project | https://asgaardlab.github.io/videogameqa-bench/ | Task izahı, nümunələr və reported scores |
| Paper — arXiv | https://arxiv.org/abs/2505.15952 | Tədqiqat və version history |
| Paper — v2 HTML | https://arxiv.org/html/2505.15952v2 | Dataset construction və methodology |
| Paper — PDF | https://arxiv.org/pdf/2505.15952 | Tam paper |
| Dataset card / viewer | https://huggingface.co/datasets/taesiri/VideoGameQA-Bench | License, schema və record preview |
| Dataset files | https://huggingface.co/datasets/taesiri/VideoGameQA-Bench/tree/main | Repository media və metadata |
| Metadata directory | https://huggingface.co/datasets/taesiri/VideoGameQA-Bench/tree/main/data | Parquet metadata |
| Metadata download | https://huggingface.co/datasets/taesiri/VideoGameQA-Bench/resolve/main/data/test-00000-of-00001.parquet?download=true | Metadata-first preparation |
| Images directory | https://huggingface.co/datasets/taesiri/VideoGameQA-Bench/tree/main/images | Seçilmiş record-ların image assets-i |
| Published artifacts | https://asgaardlab.github.io/videogameqa-bench/artifacts.html | Müəlliflərin output və qualitative results səhifəsi |
| DINOv2 official repository | https://github.com/facebookresearch/dinov2 | Model code, pretrained checkpoints və model card |

Metadata download link-i repository-nin göstərdiyi download ünvanıdır. Bu brief hazırlanarkən binary faylın download-u tamamlanmayıb; agent işləyəcəyi mühitdə bunu yoxlamalıdır. Link siyahısı dataset və weights-in artıq lokalda olduğunu bildirmir.

Benchmark üçün ayrıca code repository URL-i bu brief-də təsdiqlənməyib. “Published artifacts” səhifəsi executable benchmark code kimi təqdim edilməməlidir. Pipeline üçün öz minimal preparation/evaluation skriptlərimiz yazılacaq.

### Dataset faktları və doğru istifadə

Project visual regression task üçün **250 sample** göstərir. Paper **9 Unity scene** əsasında object removal və **70 cutscene glitch instance** təsvir edir; cutscene-lər glitch-free frames ilə cütləşdirilib. Bu 70 instance həmin regression dataset təsvirinin hissəsidir, ayrıca əlavə video scope deyil.

Dataset card **CC BY 4.0** license və full repository üçün **33.4 GB** ölçü göstərir. Bütün repository-ni yükləmək lazım deyil. Məqsəd visual-regression metadata və yalnız seçilən pair-lərin şəkilləridir.

Mənbədəki **45.2%** o4-mini üçün həmin reported visual-regression müqayisəsinin nəticəsidir. Bunu bütün bug task-larının nəticəsi, bug recall-u və ya bugünkü bütün modellər üçün yuxarı hədd kimi istifadə etməyin.

### Metadata-first preparation

1. Dataset revision/commit-i müəyyənləşdir və manifest-də saxla.
2. Kiçik Parquet metadata faylını əldə et. Files səhifəsi `data/test-00000-of-00001.parquet` göstərir.
3. Faktiki schema və task category dəyərlərini yoxla; string-ləri təxmin etmə.
4. Visual regression records-u seç. Gözlənilən 250 ilə faktiki count-u müqayisə et; fərq varsa revision və seçim logic-ini izah et.
5. Original question, ground truth və media fields-i saxla. Reference/candidate sırasını prompt/metadata və nümunə yoxlaması ilə təsdiqlə.
6. Metadata-da göstərilən media path-ləri repository tree ilə uyğunlaşdır. Preview-də `media_folder` tək `image/` formasında görünə bilər, repository isə `images/` göstərir; kör-koranə path concatenation etmə.
7. Yalnız seçilən image assets-i endir, decode et, ölçüləri və checksum-ları yoxla.
8. İlk 10–20 real pair-i komandaya tez ver; sonra uyğun olarsa subset-i tamamla.
9. Original files-i qoruyub working copies yarat; label-lər evaluation-only manifest-də qalsın.

Metadata preview-də `custom_id`, `question_categories`, `question`, `ground_truth`, `media_path`, `media_type`, `media_folder`, `media_source` sahələri görünür. Implementation faktiki faylı yoxlamalıdır; `ground_truth` string içində JSON ola bilər, onu validasiya etmədən boolean-a çevirməyin.

Image assets seçilmiş record folder-ləri üzrə görünür, buna görə selective transfer araşdırılmalıdır. Mənbə dəyişibsə və media packed archive-dadırsa, metadata filter-i selective byte transfer zəmanəti deyil. Full dataset download-a səssiz keçmə. PM-ə constraint-i bildir və daha kiçik real subset-lə davam et.

### Manifest tələbləri

Hər record üçün: stable sample ID, reference/candidate relative paths, original question/rules, dataset revision, source/group ID əgər məlumdursa, checksums, dimensions, validation status. Ground truth və split evaluation-only faylda saxlanmalıdır.

Inference input-a label ötürülməməlidir. Demo samples və development samples held-out evaluation-dan ayrılmalıdır. Eyni reference, scene və ya source sequence paylaşan samples mümkün olduqca eyni group-da saxlanmalıdır. Group bilinmirsə uydurmayın; leakage limitation-ı yazın.

Source dataset bu records-u `test` split-də yayımlayır. Prototype üçün yaradılan development/evaluation bölgüsü bizim daxili protocol-dur, dataset-in rəsmi train/test bölgüsü deyil.

`DATA_CARD.md` real count, seçmə logic-i, revision, missing files, label distribution və limitations saxlamalıdır. `THIRD_PARTY_NOTICES.md` dataset/paper attribution və istifadə olunan model/license məlumatını saxlamalıdır.

## 5. Model və inference yanaşması

### A. Input validation və alignment

- Image decode, file size, dimensions və pixel count limitləri yoxlanır.
- İki image-də original aspect ratio və resize/pad transform-ları qeyd olunur.
- Matching screenshots üçün identity alignment başlanğıc seçimidir.
- Kiçik capture drift üçün optional translation/affine alignment istifadə edilə bilər; quality diagnostics və valid-overlap mask tələb olunur.
- Fərqli kamera mövqeyi, ciddi scene mismatch və unreliable alignment review-a göndərilir.
- Alignment itən obyektin fərqini “düzəldərək” gizlətməməlidir.

### B. DINOv2 change proposals

- Default başlanğıc model: frozen **DINOv2 ViT-S/14**, official repository-dəki `dinov2_vits14`.
- Mövcud uyğun checkpoint varsa istifadə oluna bilər; model/revision və tested device/dtype qeyd edilməlidir.
- Training yoxdur. `eval()` və inference mode istifadə edilir.
- Spatial patch features çıxarılır; global CLS vector spatial heatmap əvəzi deyil.
- Reference və aligned candidate üçün eyni preprocessing tətbiq edilir.
- L2-normalized patch features arasında spatial cosine distance hesablanır: `1 - cosine_similarity`.
- Difference map threshold → bounded morphology → connected components → box merge/padding.
- Threshold, minimum region area, box padding və region cap config-dədir.
- Patch grid → resized/padded image → original reference coordinate transform-u düzgün izlənir.

Feature distance bug probability deyil. Kiçik obyekt itkisi patch resolution-da görünməyə bilər. Evidence varsa classical pixel-difference proposal-ları ilə union/fallback istifadə oluna bilər; hər proposal-ın source-u saxlanmalıdır. Bu metod DINOv2 semantic path-in yerinə səssiz keçməməlidir.

### C. VLM region judgment və scene audit

Hər seçilən region üçün VLM-ə before/after crops, full-image context, doğru image order, region location və original rules verilir. Structured response aşağıdakıları qaytarır:

- observed change;
- `allowed`, `forbidden` və ya `uncertain` verdict;
- applicable rule ID-lər;
- qısa observable visual evidence;
- model identifier və varsa error.

Schema yoxlanır. Unknown rule ID, malformed JSON, image evidence ilə dəstəklənməyən hökm və conflicting rules uncertainty yaradır. Modelin öz verdiyi confidence calibrated probability sayılmır.

Region proposals əlavə dəyişiklikləri buraxa bilər. Buna görə bütün scene pair üçün ayrıca audit edilir. Audit yeni şübhəli dəyişiklik tapırsa onu investigation/review-a daxil et; proposals boşdur deyə avtomatik pass vermə.

Provider/model seçimi hazır credentials və mühitdən asılıdır. Mövcud işləyən bir VLM adapter kifayətdir. Yeni subscription və compute alınmır. API key yoxdur deyə dummy verdict-lər real AI nəticəsi kimi göstərilmir.

### D. Final decision policy

| Vəziyyət | Final decision |
| --- | --- |
| Reliable visual evidence və applicable rule ilə forbidden change | `FAIL` |
| Bütün mərhələlər tamamlanıb, tapılan changes allowed-dur, scene audit əlavə problem tapmayıb | `PASS` |
| Identical decoded images və valid inputs | Documented deterministic shortcut ilə `PASS` mümkündür |
| Uncertain judgment, rule conflict, missing rule coverage, unreliable alignment | `NEEDS REVIEW` |
| Model unavailable, timeout, invalid response, truncated proposals və ya incomplete coverage | Reliable fail artıq yoxdursa `NEEDS REVIEW` |

Reliable forbidden change artıq sübut edilibsə, başqa komponentin problemi həmin fail-i pass-a çevirmir. Errors analysis status-da ayrıca göstərilir. `PASS` sistemin heuristic nəticəsidir; bütün mümkün bug-ların yoxluğunun sübutu deyil.

### E. Bounded execution və cache

- Default maksimum 8 region + 1 whole-scene audit.
- Request timeout default 30 saniyə; hər request üçün maksimum 2 attempt.
- End-to-end run üçün ayrıca configurable deadline olmalıdır; vaxtı bitən job review-a keçir. Region limits sürətli cavab zəmanəti deyil.
- Region cap digər şübhəli region-ları kəsirsə truncation saxlanır və pass verilmir.
- Cache key image content, rules, model/config version və preprocessing/transform məlumatına bağlıdır.
- Streamlit rerun yeni inference request-i avtomatik təkrarlamamalıdır.
- Device/dtype və model load failures görünən olmalıdır; real/model-degraded/mock modes ayrıdır.

## 6. Rule format və nümunə

Minimum hər rule-da `id`, `effect` (`allow` / `deny`) və `description` olur. User descriptions original formada saxlanır. Optional structured editing sadə qalmalıdır; ayrıca böyük policy language qurulmur.

```yaml
rules:
  - id: A1
    effect: allow
    description: Weather and lighting may change if scene objects remain present.
  - id: A2
    effect: allow
    description: Character clothing color may change; the character must remain visible.
  - id: D1
    effect: deny
    description: Existing scene objects must not disappear.
  - id: D2
    effect: deny
    description: Visible geometry or textures must not become corrupted.
```

Bu illustrative rules-dur, bütün benchmark records üçün universal ground truth policy deyil. Benchmark evaluation-da həmin record-un original question/rules-u əsas götürülür.

Eyni region üçün weather change allowed, amma obyekt itkisi forbidden ola bilər. Region yalnız “hava dəyişib” deyə bütövlükdə allowed sayılmamalıdır. Qaydalar bir-birinə ziddirsə və ya relevant change üçün qərar çıxarmaq mümkün deyilsə review seçilir.

## 7. UI və local persistence contract

### Analysis workflow

1. Upload/select pair.
2. Edit/review rules.
3. Analyze; progress və engine status göstər.
4. Inspect original images, boxes, paired crops və verdicts.
5. Export report və ya explicit reference approval.

### Bug report export

Bir local run directory-də Markdown report, JSON analysis və evidence images yaradılır. Download üçün onları ZIP etmək mümkündür. Report title, observed/expected behavior, applicable rules, sample/run ID, screenshots/crops, model/config versions və timings saxlayır.

Screenshot-lar engine/build metadata vermirsə, report build ID və repro gameplay steps uydurmamalıdır. Bu screenshot comparison report-dur; source engine-də bug reproduction ayrıca insan işi ola bilər.

### Reference update

User explicit approval action ilə candidate-i yeni reference kimi seçir. Yeni version yaradılır, əvvəlki image/version qorunur və audit event yazılır. Update benchmark source assets və ground truth-u dəyişmir. UI əvvəlki və yeni reference ID-ni göstərir.

### Artifacts

```text
artifacts/<run_id>/
  analysis.json
  rules.yaml
  report.md
  images/
  crops/
  diagnostics/
references/<reference_id>/
  versions/
  history.json
```

Unique run IDs, atomic writes və path validation tələb olunur. Credentials report və log-lara yazılmır. Diagnostic artifacts problemi araşdırmağa kömək etməli, lazımsız böyük dump yaratmamalıdır.

## 8. Ortaq interfaces və code structure

Default stack: **Python + Streamlit + PyTorch + OpenCV + Pillow + NumPy + Pydantic + pytest**, və yalnız lazım olan bir VLM client. Mövcud uyğun repo conventions qorunur. One-process app, local files, small CLI və config kifayətdir.

```text
PROJECT_BRIEF.md
README.md
app.py
src/gameqa/
  contracts.py
  pipeline.py
  storage.py
  vision/
    alignment.py
    features.py
    proposals.py
    judge.py
  data/
    prepare.py
    manifest.py
scripts/evaluate.py
configs/default.yaml
tests/
docs/
HANDOFF.md
THIRD_PARTY_NOTICES.md
```

| Contract | Semantics |
| --- | --- |
| `Rule` | Stable ID, allow/deny effect, original description |
| `PairInput` | Ordered images, rules, optional sample ID; label yoxdur |
| `AlignmentResult` | Status, candidate→reference transform, overlap mask, diagnostics |
| `RegionProposal` | ID, reference-coordinate box, distance score, proposal source |
| `RegionJudgment` | Region ID, observed change, verdict, rule IDs, evidence, model/errors |
| `AnalysisResult` | Run ID, execution status, final decision, judgments, scene audit, versions, coverage, timings, paths |

Box formatı `[x1, y1, x2, y2]`, original reference image pixel coordinates; right/bottom exclusive. Candidate üzərində original-coordinate box göstərilirsə inverse transform tətbiq edilir. Aligned crop reference box ilə kəsilir. Resize/pad və patch transforms unudulmamalıdır.

Functions kiçik və cohesive, public interfaces typed, coordinate/decision logic documented olmalıdır. Generic framework və service layers yaratmaq lazım deyil. Documentation agent readability-ni yoxlayır; hər developer öz code readability-sinə cavabdehdir.

## 9. QA, experiments və ölçmə

### Required functional checks

- Identical images.
- Removed object və small-object miss inspection.
- Allowed appearance/weather/lighting change.
- Simultaneous allowed və forbidden change.
- Small translation və unreliable alignment.
- Different dimensions, borders və correct crop coordinates.
- Empty/conflicting rules.
- Corrupt/oversized images.
- Missing DINOv2 weights, unavailable VLM, timeout, invalid JSON/rule IDs.
- Proposal truncation, stale cache və repeated UI submission.
- Report export və preserved reference history.

Deterministic failure injection üçün mocks istifadə oluna bilər. Bunlar real DINOv2/VLM smoke run-dan ayrı göstərilməlidir. Bug fix root cause-a yönəlməli və regression test-lə qorunmalıdır.

### Evaluation protocol

İlk məqsəd kiçik real held-out sample üzrə ölçülən smoke evaluation-dur. Data əlçatandırsa 250-record subset hazırlanır. Hədlər yalnız development samples-də seçilir. Demo selection unbiased benchmark nəticəsi sayılmır.

Minimum müqayisə: classical pixel baseline və real DINOv2 + VLM pipeline eyni IDs/rules üzrə. Vaxt və credentials imkan verərsə whole-image VLM-only baseline əlavə edilə bilər; bu əlavə experiment P0 delivery-ni bloklamır. İşlədilməyən method üçün nəticə yazılmır.

Report faktiki sample IDs/counts, label distribution, bug precision/recall, confusion matrix, decided-pair accuracy, review rate, decision coverage, excluded/error counts və inference timings göstərir. Reviewed cases denominator-dan səssiz çıxarılmır. Binary mapping lazımdırsa məsələn review→fail seçimi ayrıca qeyd olunur.

Pair-level labels-dən localization IoU çıxarmaq olmaz. Region metrics üçün ayrıca manual annotations tələb olunur və onların count/source-u ayrıca göstərilir. Bu prototype üçün minimum region verification vizual inspection və failure gallery-dir.

Accuracy target və paper-dən üstünlük vədi qoyulmur. Məqsəd işləyən, ölçülən və limits-i bilinən hypothesis prototype-dir.

## 10. Agent ownership və 10–12 saatlıq plan

| Role | Ownership |
| --- | --- |
| Product Owner | Product intent və qəbul edilən scope |
| PM | Milestones, file ownership, integration, decisions, final acceptance/handoff |
| Python Developer | UI, contracts, orchestration, storage, dependencies |
| DL Engineer | Alignment, features, proposals, VLM adapter/prompt |
| Data Engineer | Metadata preparation, media selection, manifest, data card |
| QA Engineer | Independent regression tests, evaluation logic, acceptance evidence |
| Documentation Engineer | README, code walkthrough, demo runbook, readability feedback |

PM contracts-u ilk saatda dondurur. Shared file-larda yalnız bir owner eyni vaxtda edit edir. İmkan varsa branches/worktrees istifadə olunur; PM ready patches-i tez-tez inteqrasiya edir. Repo instructions və istifadəçinin mövcud işi qorunur.

| Elapsed time | Milestone |
| --- | --- |
| 0–1 h | Repo/hardware/credentials yoxlaması, contracts, first data inspection |
| 1–3 h | Runnable UI + baseline proposals/crops/report, first real pairs |
| 3–6 h | Real DINOv2 + VLM integration, coordinates və error states |
| 6–8 h | Held-out smoke evaluation, failure inspection, allowed/forbidden demos |
| 8–10 h | Scope freeze, end-to-end fixes, docs, fresh-process launch |
| 10–12 h | Final verification, checkpoint, evidence və handoff |

Blokerdə agent yalnız gözləmir: typed stub ilə müstəqil hissəni işləyir. 30 dəqiqə həll olunmayan blocker PM-ə evidence və iki bounded alternative ilə bildirilir. Yeni paid provider/hardware alınmır. Runtime dayanırsa checkpoint və next action saxlanır; fasiləsiz 12 saatlıq çalışma platformanın real imkanına bağlıdır.

## 11. Fallback və completion status

| Constraint | Delivery davranışı | Status |
| --- | --- | --- |
| VLM mövcud deyil | Proposals/crops işləyir, judgments uncertain, final review | Degraded prototype; full AI incomplete |
| DINOv2 mövcud deyil | Aydın labelled classical proposals | Degraded prototype; semantic component incomplete |
| Full subset hazırlanmır | Smaller verified real subset + exact count/reason | Data/evaluation limitation |
| Real data alınmır | Clearly labelled controlled fixtures | Functional demo; benchmark evidence incomplete |
| Alignment etibarsızdır | Originals və diagnostics göstər, review | Supported error behavior |

Mock nəticəsi real inference əvəzinə istifadə edilməməlidir. Degraded prototype işlək təhvil ola bilər, amma **full AI prototype complete** sayılmır.

## 12. Definition of done — səhər nə təhvil verilir?

- [ ] Fresh process-dən documented command ilə açılan lokal app.
- [ ] Upload və hazır demo pair seçimi.
- [ ] Editable rules və doğru region/evidence displays.
- [ ] Ən az bir real DINOv2 + real VLM analysis artifact.
- [ ] Forbidden, allowed və uncertain/error üçün üç reproducible demo case; synthetic fixtures varsa labelled.
- [ ] Fail/pass/review policy və error-to-pass regression coverage.
- [ ] Lokal report export və audit/history ilə reference update.
- [ ] Actual data count/revision/attribution və leak-free manifests.
- [ ] QA commands/results; ölçülən evaluation və ya exact incomplete səbəbi.
- [ ] Tested environment/model/config versions.
- [ ] Stable git checkpoint və ya versioned delivery snapshot.
- [ ] `HANDOFF.md`, `QA_REPORT.md`, `DATA_CARD.md`, `MODEL_NOTES.md`, `CODE_WALKTHROUGH.md`, `DEMO_RUNBOOK.md`.

Proposed launch interface: `streamlit run app.py`. Proposed testing interface: `python -m pytest`. Agentlər bunları actual implementation-a uyğunlaşdırıb həqiqətən işlədikdən sonra README/HANDOFF-da verified kimi göstərməlidir. Bu brief həmin command-ların artıq test edildiyini iddia etmir.

`HANDOFF.md` Azərbaycan dilində, English technical terms ilə bunları cavablandırmalıdır:

1. Nə işləyir, nə partial, nə incomplete-dir?
2. Setup/run üçün actual verified commands hansılardır?
3. Hansı pair-lərlə demo etmək olar və gözlənilən behavior nədir?
4. Screenshot-dan verdict-ə gedən actual code path hansıdır?
5. Model/data/config dəyişmək üçün hansı files edit edilir?
6. Hansı tests/experiments həqiqətən run edilib və nəticələri nədir?
7. Ən vacib known failure necə reproduce olunur?
8. Ali növbəti gün ilk hansı üç işi etməlidir?

**Final acceptance:** bir-birindən ayrı “hazır” komponentlər deyil, end-to-end işləyən və sübutları saxlanan prototype. İnsan kodu oxuyub qərarların necə verildiyini başa düşməli və ertəsi gün development-i davam etdirə bilməlidir.
