# A3 review: frozen comparison on dev12

Date 2026-10-09 (Baku). This file has one section by experiment-tracker-pm. Other sections (e.g. QA visual review) are added by their owners and are not edited here.

## Scoring and reproducibility (experiment-tracker-pm)

Scope: no new inference, no tuning, no git commands were run for this section. All numbers below were recomputed from raw rows: `artifacts/ali/a3/{A,B,C}/predictions.jsonl`, `artifacts/ali/a1/{A,B,C}/predictions.jsonl` (byte-identical to `docs/ali/a1_evidence/predictions_{A,B,C}.jsonl`), the per-call dumps `artifacts/ali/a1_inputs/{a1,a3}/{B,C}/<id>/calls.jsonl`, frozen labels `docs/ali/labels_ali.csv` (sha256 prefix 524583859358b6dc, matches `artifacts/ali/a3/score.json`) and marks `docs/ali/a1_evidence/obs_review.csv`. Truth: rule D1 = bug (5), rule A1 = clean (7). Recompute script was kept outside the repo (`/tmp/etpm/an.py`, `d.py`).

Status wording (mandatory):
- dev12 is a **development diagnostic, not held-out**. The 12 pairs were used for the A1 decision (D17) and for tuning the pixel control threshold (0.782 from dev); the selection was seeded and committed before model output, but the results still must not be read as generalization.
- The 60-case eval set (`data/manifests/eval_subset_60.json`, E1/E2/E4 in `docs/EXPERIMENTS.md`) is a **historical regression set only**, not a measurement of this build.
- **No DINOv2 superiority claim.** The only measured signal in favour of DINOv2 proposals is on VLM *observation* quality: C (region crops) y+p 9/12 vs B (full frame) 4/12, scored on A1 text only (see below). It did not produce better automatic decisions.

### 1. Integrity table (A3)

| Check | A pixel | B full-frame VLM | C hybrid | Result |
|---|---|---|---|---|
| Rows | 12 | 12 | 12 | ok |
| Duplicate IDs | 0 | 0 | 0 | ok |
| Missing IDs vs `configs/ali_dev12.json` (dev12) | 0 | 0 | 0 | ok |
| Extra IDs | 0 | 0 | 0 | ok |
| Rows with `error` | 0 | 0 | 0 | ok |
| `is_mock` rows | 0 | 0 | 0 | ok, all real |
| `engine_mode` | n/a | 10 real, 2 degraded (guard contradiction, kept as REVIEW) | 12 real | disclosed |
| `config_hash` | 642b6e26f39d | 642b6e26f39d | 642b6e26f39d | same across arms |
| Row-level `cache.status` | n/a (no VLM) | 12 fresh | 12 fresh | ok |
| VLM calls in `calls.jsonl` | n/a | 24 | 56 | 80 total |
| `cache_hit` true | n/a | 0 of 24 | 0 of 56 | **all fresh** |
| Calls with `is_mock` true / `ok` false | n/a | 0 / 0 | 0 / 0 | ok |
| Row `cache.calls`/`hits` equals `calls.jsonl` counts | n/a | 12/12 consistent | 12/12 consistent | ok |

The "2 degraded" rows in B (counts from A1 QA, reproduced in A3 by identical rows): vr_59af7164 and vr_43773eb8, where an allowed verdict contradicted a change type that is never auto-allowed. They stay in the denominators.

B vs C same model, prompt and rules (per sample, 12/12 each):
- `model` = `ollama:qwen2.5vl:3b` and `prompt_version` = `v9` in all 24 VLM rows.
- `rule_ids_given` = [A1, D1] in all 24 rows (and also all 24 in A1).
- `alignment_status` equal per ID (11 identity, 1 unreliable = vr_ef9b073a, in both arms).
- B `b_input` = `aligned` 12/12 (C has no `b_input` field by design).
- Known by-design difference (found by QA in A1): the second-stage scene-audit image and prompt in C list and draw the regions already checked; B's audit sees none. Same aligned frames, not byte-identical audit image.
- Config: `configs/ali_a3_qwen.yaml` differs from `configs/ali_a1_qwen.yaml` only in `dump_tag` (a1 -> a3) and `cache_dir` (`data/cache_ali_a1` -> `data/cache_ali_a3`), which is the only reason `config_hash` differs (3a144cfcbb67 vs 642b6e26f39d).
- Code commit differs between the runs per `run_meta.json`: A1 at 0b75b8a, A3 at a5590a5. I did not inspect the source diff (no git allowed here); the identical outputs below show no change in the measured fields, but this is a caveat.

### 2. A1 vs A3 determinism (Qwen 2.5-VL 3B, temperature 0, both with a fresh cache, 0 cache hits in 80 + 80 calls)

Exact match counts, A1 row vs A3 row for the same sample id:

| Field | A pixel | B | C |
|---|---|---|---|
| `decision` | 12/12 | 12/12 | 12/12 |
| `n_proposals` | 12/12 | 12/12 | 12/12 |
| `truncation_cause` | 12/12 | 12/12 | 12/12 |
| `verdicts` list | 12/12 | 12/12 | 12/12 |
| Region id + verdict + box | 12/12 | 12/12 | 12/12 |
| Stage-1 observation text (regions + scene audit) | n/a | 12/12 | 12/12 |

- Total: 36/36 rows have the same decision, n_proposals, truncation cause, verdicts, region boxes and region verdicts. Stage-1 text identical in 24/24 VLM rows.
- Per-call dump text files (`R*_stage1/stage2`, `SCENE_audit*`, `.txt`): 80 of 80 identical between `a1_inputs/a1` and `a1_inputs/a3`; the file sets are identical.
- Full-row comparison with timing keys excluded (`started_at`, all `latency_s`, `timings.*`, `run_id`, `dump_dir`, `config_hash`): A and B 0 differing rows. C 12 rows differ in the timing keys only; a field-by-field walk shows differences exclusively in `started_at`, `config_hash`, `dump_dir`, `run_id`, `latency_s`, `regions[].latency_s`, `audit.latency_s` and `timings.*`. No semantic field differs.
- **List of every difference: none** in decision, n_proposals, truncation cause, region verdicts, boxes or stage-1 text. Only wall-clock values differ (B 37.0-49.3 s, median 41.6 s in A3; C 63.3-161.0 s, median 79.6 s in A3; A1: B 38.1-47.8 s, C 68.9-159.7 s).
- Interpretation and limit: at temperature 0 with a fresh cache, this host, this model and these 12 pairs, the pipeline reproduced exactly once. That is one repeat (n = 2 runs), not a general determinism guarantee; other hardware, Ollama versions or quantizations are not covered. Because A3 reproduces A1 exactly, A3 is a replication, not additional evidence: the effective sample stays 12 pairs.

### 3. Counts vs targets (A3 = A1 by identity; n = 12, 5 bug / 7 clean)

Engineering targets (not promised results): observations 10/12 correct, 0 bug false-PASS, clean PASS >= 4 (of 7; originally 4/6), coverage >= 6/12. Coverage = (PASS+FAIL)/12. False-PASS is always shown next to coverage.

| Arm | PASS / FAIL / REVIEW | Bug false-PASS | Coverage | Clean PASS | Obs y (strict) | Obs y+p | Targets met |
|---|---|---|---|---|---|---|---|
| A pixel | 12 / 0 / 0 | **5/5** | 12/12 | 7/7 | n/a | n/a | clean PASS, coverage only because it passes everything; false-PASS target failed |
| B full-frame VLM | 8 / 0 / 4 | **5/5** | 8/12 | 3/7 | 1/12 | 4/12 | coverage; **failed**: false-PASS, clean PASS (3 < 4), observations |
| C hybrid | 0 / 0 / 12 | 0/5 | **0/12** | 0/7 | 1/12 | 9/12 | false-PASS; **failed**: coverage, clean PASS (0 < 4), observations (strict) |

Reading: no arm meets all four targets, and the two arms with coverage (A, B) pass every bug. C avoids false-PASS only by abstaining on all 12 pairs (9 are global-change collapse on cutscenes, 3 are Unity pairs with no truncation). C produced zero FAILs, so it found no bug automatically either. Failed targets, stated plainly: 10/12 observations (both arms 1/12 strict), coverage for C (0/12), clean PASS for B (3/7) and C (0/7), false-PASS for A and B (5/5).

Uncertainty (Clopper-Pearson, two-sided 95%, n small): B and A false-PASS 5/5 has lower bound 0.48; C false-PASS 0/5 has upper bound 0.52, and C coverage 0/12 has upper bound 0.26. Differences between arms are large in kind (all vs none), but no rate is estimated precisely.

Observation marks: Ali marked 24 rows (A1) in `docs/ali/a1_evidence/obs_review.csv`: B y 1 / p 3 / n 8; C y 1 / p 8 / n 3. `artifacts/ali/a3/obs_review.csv` is an unmarked copy. Because stage-1 text is identical in A1 and A3 (12/12 per arm), the A1 marks apply to A3 rows by text identity, but they were **scored on A1 only**, by one rater (Ali), with partial credit judged by hand and a possible anchoring effect noted in `A1_diagnostic.md` (Claude's independent review disagrees on one row, vr_43773eb8 C: y not p, which would make C 2 y / 7 p). Per-case classes in `artifacts/ali/a3/score.md` show `unscored` because that file was generated without marks; `artifacts/ali/a1/score.md` is the marked version.

### 4. Sensitivity: vr_330651ed counted as clean (4 bug / 8 clean)

Per `docs/ali/labels_audit.md`, the D1 label of vr_330651ed (subtitle language change) is weakly supported. Labels file is unchanged; this is a re-count only, recomputed from A3 rows.

| Arm | Bug false-PASS | Clean PASS | Coverage |
|---|---|---|---|
| A pixel | 4/4 | 8/8 | 12/12 |
| B full-frame VLM | 4/4 | 4/8 | 8/12 |
| C hybrid | 0/4 | 0/8 | 0/12 |

vr_330651ed decisions: A PASS, B PASS, C NEEDS_REVIEW. Under this re-count B reaches clean PASS 4/8 (the target of 4 is met numerically) while still passing all 4 bugs. Conclusion unchanged: only C avoids false-PASS, with zero coverage. The 5 labels that were Claude-proposed and confirmed by Ali (3 Unity, vr_330651ed, overlay note on vr_4255ae09) remain a limitation; Unity pairs are all bugs, so source is confounded with class.

### 5. What this does and does not support

- Supported (dev12, n = 12, one model): localization on the Unity bug pairs matches Ali's boxes; the binding constraint is VLM perception (Qwen 3B described the missing barrel as "different texture and lighting"; Gemini 3.5 Flash described the removal in 2/2 on the same crop, n = 2, a reproducer not a measurement). Abstention policy is safe on this set but gives no automatic decision.
- Not supported: any statement that the hybrid improves accuracy, coverage or decisions over the simpler arms; any generalization beyond dev12; any speed-up or QA-workload claim; "fine-tuned" or "production-ready".
- Unresolved failures stay in the report: C returns REVIEW (not FAIL) on the clear Unity bug vr_4b921c5d in both A1 and A3; B and A return PASS on it.

### 6. Reproducibility

Code commit A3 a5590a5 (A1: 0b75b8a), `configs/ali_a3_qwen.yaml` (hash 642b6e26f39d), Ollama `qwen2.5vl:3b`, prompt v9, temperature 0, `dinov2_vits14`, cache namespace `data/cache_ali_a3` (fresh), dumps `artifacts/ali/a1_inputs/a3/`, labels hash prefix 524583859358b6dc, dev12 list `configs/ali_dev12.json`. Runner `scripts/ali_a1_run.py`, scorer `scripts/ali_a1_score.py`. Registry: `docs/ali/EXPERIMENT_REGISTRY.md`.

## Visual review (QA)

Owner: qa-engineer. Reviewed: `artifacts/ali/a3/{A,B,C}/predictions.jsonl` (12 rows each), `run_meta.json`, input dumps `artifacts/ali/a1_inputs/a3/{B,C}/<id>/`. No VLM call and no git command by QA. Scripts outside the repo: `/tmp/qa_scripts/recompute_a3.py` and ad-hoc `python3 -I` snippets. Truth = Ali's frozen rule column (D1 bug 5, A1 clean 7). Same 12 dev pairs used for tuning decisions: development diagnostic, not held-out. Counts agree with the scoring section above (independent recompute).

### Integrity: PASS
- 12 rows per arm, IDs equal `configs/ali_dev12.json`, no duplicates, missing or extra; no errors, no mocks (36/36 rows; all 80 dumped calls `ok`, not mock).
- B and C: same model (`ollama:qwen2.5vl:3b`), prompt `v9`, config_hash `642b6e26f39d`, rules [A1, D1], same `vlm` block in `run_meta.json`, same commit `a5590a5`; `b_input = aligned` 12/12; alignment status equal per ID (11 identity, 1 unreliable = vr_ef9b073a).
- Cache: all 24 B/C rows `fresh`, hits 0; `calls.jsonl` 80 calls, 0 `cache_hit`. New namespace `data/cache_ali_a3`.
- REVIEW rows kept: B 4, C 12 in files and denominators. Results: A 12 PASS (bug false-PASS 5/5, coverage 12/12); B 8/0/4 (false-PASS 5/5, clean PASS 3/7, coverage 8/12); C 0/0/12 (false-PASS 0/5, clean PASS 0/7, coverage 0/12). Sensitivity (330651ed clean): B 4/4 and 4/8; C 0/4 and 0/8.

### B vs C audit input (note, not a defect)
SCENE audit prompt body is identical for all 12 IDs except line 1: C lists the already-checked regions ("outlined in yellow ... R1=[...]") and its audit PNG draws them, B says "none". Same aligned frames, not a byte-identical audit image (hybrid design).

### Q1 (important): A3 == A1, so it is a determinism check, not a second sample
For B and C every decision, scene-audit text, proposal box and region verdict equals `docs/ali/a1_evidence/predictions_{B,C}.jsonl`; all 40 dumped PNGs have the same SHA-256 as `artifacts/ali/a1_inputs/a1/`. Only `config_hash` differs (3a144cfcbb67 vs 642b6e26f39d) because `dump_tag` and `cache_dir` changed (`diff configs/ali_a1_qwen.yaml configs/ali_a3_qwen.yaml`). Cite the counts once, never as two runs or as replication of accuracy. The effective sample stays 12 pairs.

### Q2 (minor): cache provenance in exports
Demo/exported ZIPs read `unknown (replay possible)` (no per-call data in `analysis.json`) although `calls.jsonl` proves fresh. Conservative and honest. For "fresh", cite `artifacts/ali/a1_inputs/a3/*/*/calls.jsonl` (80 calls, 0 hits), not the ZIP.

### Q3 (minor): B's 4 REVIEWs have mixed causes
59af7164 and 43773eb8 degraded (guard contradiction), 41bab231 scene audit uncertain, ef9b073a alignment unreliable. Say "B abstained on 4", not "errored on 4".

### Visual inspection of what the VLM saw
Evidence copies in `docs/ali/a3_evidence/` (hashes in `SHA256SUMS.txt`).
- vr_4b921c5d: `vr_4b921c5d_C_R1_vlm_input.png` shows the barrel plainly present BEFORE and absent AFTER at 680x336; crop representation is adequate. Qwen said "texture and lighting" (uncertain). `vr_4b921c5d_B_scene_audit_input.png` (1032x288): the missing barrel is a small area at lower right; B said "lighting brighter" and PASSed (clearest B forbidden-change miss).
- vr_09a066d3 (A1): `vr_09a066d3_C_R1_collapsed_vlm_input.png`, full-frame region at 680x189 is readable (blue shirt to grey jacket). C's region text says lighting (uncertain) while its audit says outfit; REVIEW comes from the global-collapse policy, not picture quality.
- vr_d07179d5: roof and TELEPHONE sign present BEFORE, absent AFTER; Qwen "replaced by a red mirror". Proposal correct (IoU 0.71 vs label).

### Preserved genuine failure / boundary example: vr_c1f47c57 (D1, pedestal removed)
- Truth (my reading of `docs/ali/a3_evidence/vr_c1f47c57_pedestal_zoom_ref_vs_cand.png`): BEFORE has a stone pedestal behind the table under the statue; AFTER the pedestal is gone and a dark slab hangs under the statue. Real forbidden change, obvious at full frame.
- Localization worked: R1 [1815,1493,2115,1608] and R2 [1812,1614,2131,1785], both source `classical` (not DINOv2), cover the slab and the wall; label bbox [1680,1490,2260,1780].
- Perception failed: `docs/ali/a3_evidence/vr_c1f47c57_C_R1_vlm_input.png` shows skull, candle and lantern in both halves plus a new dark band at the top of AFTER. Qwen R1: "rectangular object and cylindrical object with a pointed top are missing" (hallucinated removal), verdict `allowed` + `disappeared`, which the guards turned into REVIEW. `docs/ali/a3_evidence/vr_c1f47c57_C_R2_vlm_input.png`: R2 "wall more polished" (wrong; uncertain). Ali's mark for this C row is p (Claude agreed); my reading is that the only credit is for the right area/"disappeared" class, not for the object.
- Scene audit (B and C): `allowed`, A1, "different color and lighting": by itself a false PASS, and B did PASS the pair. C's REVIEW (run `20261009T121824Z-157529`, "R1: invalid or failed model response; R2: uncertain.") exists only because region-level guards caught contradictions. Not FAIL: no arm caught this bug. Final: A PASS, B PASS, C NEEDS_REVIEW.

### Observation marks (now scored) and my visual reading
`docs/ali/a1_evidence/obs_review.csv`: B y1/p3/n8 (y+p 4/12), C y1/p8/n3 (y+p 9/12); strict 10/12 not met by either arm. For the examples above the marks are 4b921c5d B n / C p, d07179d5 B n / C p, c1f47c57 B n / C p, 09a066d3 B y / C p. The C "p" marks on 4b921c5d and d07179d5 give credit for the right region/object with a wrong description (barrels "texture/lighting", booth "mirror"); the change itself (removal) was not named. Read "9/12 y+p" as partial credit, one rater, possible anchoring (noted in `A1_diagnostic.md`), not as perception being correct. Since A3 stage-1 text equals A1 text, the marks carry over by identity but were scored on A1.

### Not verified
Commit-level code diff between A1 (0b75b8a) and A3 (a5590a5) (no git); live UI replay; any generalization beyond these 12 pairs; hardware or Ollama-version variance of the determinism result.
