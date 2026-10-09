# C2 final runtime evidence — source və verification gate

Tarix: **2026-10-09, Asia/Baku**. Owner: independent QA. İlkin 17:18 check-də yalnız reported summary var idi; **17:23 update** exact reconciled SHA-dan raw records-u yoxlayır. C2 inference işlədilmədi, VLM call sayı **0**.

**Status: C2 committed raw numbers locally recomputed / actual ZIP bytes və recording pending.** Git-workflow-master exact integration SHA **`79a0ef740196cbaa0639579386c6c591d2bfd8ca`**-nı `/tmp/ali-c2-79a0ef7.ROajGB/checkout`-da detached checkout kimi təsdiqlədi. QA `docs/c2_openrouter/` rows/calls/stages/identity/ZIP-verification records-u həmin tree-dən oxudu. Compact result: [C2_RECOMPUTED.json](C2_RECOMPUTED.json). **Ayrıca Celal UI-ready SHA gələnədək recording blocked qalır**; code SHA bu gate-i açmır. Lokal C1/C2 ZIP bytes yoxdur; C1 üçün `docs/CELAL_C1_DEMO_GATE.md` Celal host-undakı yoxlamanı sənədləşdirir.

## Mənbələr və status

| Evidence | Faktiki mənbə | Bu session-da status |
|---|---|---|
| Qwen A1 baseline | `docs/ali/a1_evidence/predictions_A.jsonl`, `predictions_B.jsonl`, `predictions_C.jsonl`; frozen `labels_ali.csv`; `configs/ali_dev12.json` | **Locally verified**: 12 unique ID per arm, exact dev12/label set, aşağıdakı counts |
| Qwen A3 | `artifacts/ali/a3/{A,B,C}/predictions.jsonl`, A1/A3 `calls.jsonl` dumps | **Locally verified**: 36/36 decision və observation eyni; hər run-da 80 fresh call, 0 hit, 0 mock. Determinism check, yeni sample deyil |
| Qwen demo exports | `artifacts/ali/demo_zips/`-də üç ZIP | **Locally verified**: CRC, required files, 18/18 evidence hashes, decisions və exclusive crop dimensions. Hamısı REVIEW; Gemini FAIL ZIP-i deyil |
| C1 selected barrel FAIL | `docs/CELAL_C1_DEMO_GATE.md`; run `20261009T115633Z-83936b`, config hash `6cfbba559386` | **Celal-documented verification**: 4 live calls, CLI 25.4442 s, UI saved-run replay/download. Bu host-da archive/capture müstəqil yoxlanmayıb |
| C2 OpenRouter dev12 | Exact `79a0ef7` tree: `docs/c2_openrouter/{B,C}_predictions.jsonl`, calls/stages/identity files | **Locally recomputed raw records**: below counts, pairwise differences, call/cache/cost sums və model/config identity |
| C2 C exports | Exact tree-də `zip-verification.json`, `docs/C3_FREEZE_VERIFICATION.json` | **Celal-documented archive checks**, locally verified record correspondence; actual ZIP CRC/member hashes bu host-da pending |

## Lokal verified Qwen baseline

| Arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Clean PASS |
|---|---|---|---|---|
| A pixel | 12 / 0 / 0 | 5/5 | 12/12 | 7/7 |
| B full-frame Qwen | 8 / 0 / 4 | 5/5 | 8/12 | 3/7 |
| C hybrid Qwen | 0 / 0 / 12 | 0/5 | 0/12 | 0/7 |

C 0/5 false-PASS **0/12 coverage** ilə birlikdə oxunur: bütün pairs REVIEW-dur. C-də 9/12 global-change collapse var. Observation marks bir rater-in manual partial-credit nəticəsidir: B y+p **4/12**, C y+p **9/12**; strict y hər ikisində **1/12**.

Frozen dev labels A1 başlayandan sonra finalized olub; 5 bug label-dən 4-ü Claude-proposed corrections, Ali tərəfindən confirmed-dir. `vr_330651ed` yalnız subtitle language dəyişir və öz cutscene rules-u text rule daşımır; ambiguous sensitivity-də onu clean sayanda false-PASS A **4/4**, B **4/4**, C **0/4**, coverage müvafiq olaraq **12/12**, **8/12**, **0/12** qalır. Bu development diagnostic-dir, held-out accuracy deyil.

## C2 — committed raw-dan independently recomputed

| Verified arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Bug FAIL | Clean PASS | Clean false-FAIL |
|---|---|---|---|---|---|---|
| B full-frame Gemini 3.5 Flash via OpenRouter | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 2/5 | 0/7 | 2/7 |
| C hybrid Gemini 3.5 Flash via OpenRouter | 1 / 4 / 7 | 1/5 | 5/12 (41.7%) | 3/5 | 0/7 | 1/7 |

Hər arm-da 12 unique ID dev12 selection və frozen label set-i ilə exact match; 5 bug / 7 clean, no row-level provider error, no mock. B/C config identity blocks yalnız output/cache namespaces-də fərqlənir; hash **C `eaa371255716`**, **B `2dfeb64cd673`**. Exact returned/requested model bütün 80 calls-da **`google/gemini-3.5-flash`**, OpenRouter endpoint, reasoning_effort configured low, prompt v9. Low-effort response echo-si yoxdur; reasoning tokens calibration/guarantee kimi oxunmur.

Aggregate counts eynidir, **10/12 per-pair decision eynidir**: booth `vr_d07179d5` **C FAIL / B REVIEW**, clean `vr_ef9b073a` **C REVIEW / B FAIL**. **4 FAIL = 4 detected bug deyil**: C-də 3 bug FAIL + 1 frozen-clean false-FAIL; B-də 2 bug FAIL + 2 frozen-clean false-FAIL. Qwen hybrid 0/12-dən C2 5/12-yə coverage artır, amma 1/5 bug false-PASS və clean PASS0/7 qalır; **DINOv2-hybrid advantage demonstrated deyil**.

**Əsas failure:** pedestal `vr_c1f47c57` hər iki arm-da **PASS**; C run **`20261009T124621Z-0b0c2b`**. C region observations shadow/lighting, scene “No differences observed”. Barrel hər iki arm-da **FAIL**; C run **`20261009T123704Z-8e4e19`**, reason R1(D1), SCENE(D1). Booth C FAIL run **`20261009T124304Z-580c0b`** roof/sign disappearance-u təsvir edir; B REVIEW. Outfit C REVIEW run **`20261009T123947Z-584a66`**. Bunlar selected development examples-dir.

Calls-dan Decimal sum **$0.2871945** provider-reported cost, unknown costs0: **C56calls/$0.1934625**, **B24calls/$0.0937320**. 80 unique generation ID, **HTTP20080/80**, call/stage cache_hits0, all80 stage attempts1 → **0 retries**. `calls.jsonl.attempt` global ordinal1…80-dir, retry count deyil. Native exported evidence cache status unknown qalır; freshness burada external call/stage records-dan verified-dir. Invoice, full request/image captures və label-input audit bu host-da yoxlanmayıb. Orchestration median C39.99005s, B19.7196s; C1 CLI25.4442s ayrıca selected run-dır.

C-də 9/12 global-change collapse; 7 REVIEW-in hamısı truncated-dir. C-də 5 rows semantic rule/response guard errors daşıyır: `vr_4255ae09`, `vr_d07179d5`, `vr_fec26436`, `vr_ef9b073a`, `vr_43773eb8`. Bunlar HTTP failure deyil və reliable FAIL-in prioritetini pozmur. B row errors0. Subtitle clean sensitivity bug false-PASS hər iki arm **1/4**, coverage **5/12**; clean false-FAIL C1/8, B2/8. `vr_43773eb8` frozen A1 olsa da actual subtitle absence scope conflict-i Celal doc-da qeyd olunub; frozen scoring dəyişdirilmir.

Historical inference SHA **`c917532ac3161a0886f626985c53307eb2d477d8`**, implementation freeze SHA **`bdd93fb534e8c0e9b574e60d383bc8b14dd03bf3`**, delivery SHA **`79a0ef740196cbaa0639579386c6c591d2bfd8ca`** ayrı saxlanır. Config file LF SHA256 `2e781b544b6d177f7955218babb51103dde684b9a70eb164a1dab0249d26274f`; eyni contents CRLF representation hash `d18ff48f9690d2f8a8643f151deb2890cca08df9c98ae057f9cc5eec3a539210` Celal freeze doc-la exact match — Windows line endings, semantic config fərqi deyil.

## Pinned tests, archive və recording gates

Exact delivery SHA cwd + pinned `PYTHONPATH` ilə full suite:

`PYTHONPATH=/tmp/ali-c2-79a0ef7.ROajGB/checkout/src /home/aliagabalayev/Desktop/Workspace/neuroscience-hackhaton/.venv/bin/python -m pytest -q`

→ **194 passed, 6 skipped in 5.14s**, exit0, no real-model calls. Ali initial docs checkpoint **193 passed /6 skipped** və Celal historical **186 passed /6 deselected** ayrıca evidence-dir.

C2 `zip-verification.json` 12 C run ID/decision-i raw rows-la uyğun gəlir; Celal **80 member hash checks** və CRC pass sənədləşdirib. C3 JSON 12 unchanged archive SHA256 verir. **Actual ZIP bytes bu tree-də yoxdur**, ona görə QA onların CRC/hashlərini locally recomputed kimi yazmır. B helper native AnalysisResult ZIP yaratmır; B ZIP claim yoxdur. C2 current actual browser/download yoxlaması əvvəl edilməyib.

**Recording gate: ayrıca Celal UI-ready SHA tələb olunur**, sonra həmin checkpoint-dən fresh Streamlit launch, actual UI-exported ZIP/hash/decision check. Code/raw verification bu gate-i əvəz etmir. Final video/slides, second-device və authorized human submission confirmation pending-dir. Internal deadline **19:30** dəyişmir.
