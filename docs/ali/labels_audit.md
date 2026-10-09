# Post-freeze label audit (dev12)

Date 2026-10-09 ~16:00 Baku, after the freeze (e844aab, 15:38:44) and after A1 outputs were seen. `docs/ali/labels_ali.csv` is **not modified**; findings are recorded here and their effect on A1 is stated as a sensitivity check. Reviewer: Ali with Claude, re-checking every contact sheet; vr_c1f47c57 checked at full resolution (`a1_evidence/vr_c1f47c57_pedestal_zoom.png`).

| sample | frozen rule | audit finding | rule change? |
|---|---|---|---|
| 10 pairs (a981c1d3, 41bab231, 09a066d3, 59af7164, 4255ae09, ef9b073a, 43773eb8, 4b921c5d, d07179d5) | as frozen | confirmed | no |
| vr_c1f47c57 | D1 | Description was wrong: the **stone pedestal under the statue is missing** (statue floats on a thin slab), not a small object on the table. Bbox [1680,1490,2260,1780] covers it. Uncertainty should be low. | no (D1 stands, stronger) |
| vr_fec26436 | D1 | Candidate frame is tilted/zoomed (black wedge top-left); "same perspective" overstated. Background replaced (fire, different street). | no |
| vr_330651ed | D1 | Only the subtitle language changed (plus slight pose). This pair's own D1 list (cutscene rules) does not include text changes; D1 is weakly supported → **ambiguous**. Originally a Claude draft confirmed by Ali. | possible: D1 → ambiguous/A1 |

## Sensitivity of A1 (if vr_330651ed counted as clean: 4 bug / 8 clean)
| Arm | bug false-PASS | clean PASS | coverage |
|---|---|---|---|
| A pixel | 4/4 | 8/8 | 12/12 |
| B full-frame VLM | 4/4 | 4/8 | 8/12 |
| C hybrid | 0/4 | 0/8 | 0/12 |
Conclusions unchanged: only C avoids false PASS; C gives no automatic decision. vr_330651ed remains the designated ambiguous demo case.
