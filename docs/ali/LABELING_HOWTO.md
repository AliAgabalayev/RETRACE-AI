# Label vermə təlimatı (Ali üçün)

1. `docs/ali/labeling_sheet.csv` faylını aç; ilk 6 sətir balanced-six-dir, əvvəlcə onları doldur.
2. Hər sətir üçün `contact_sheet_<id>.png` aç: sol before (reference), orta after (candidate), sağ abs-diff.
3. `visible_primary_change`: gözlə görünən əsas dəyişikliyi bir cümlə ilə yaz (model nəticəsinə baxma).
4. `valid_comparison_conditions`: iki şəkil eyni səhnədir və müqayisə etibarlıdır? (yes/no + qısa səbəb).
5. `source_scene`: oyun/səhnə ailəsi; `rule_allowed_or_forbidden`: A1 (allowed) və ya D1 (forbidden).
6. `approx_bbox_x1y1x2y2_reference_px`: reference şəklin ORİJİNAL piksel koordinatları, `x1,y1,x2,y2` (sağ/aşağı daxil deyil); ölçü `reference_size_wh` sütunundadır.
7. `uncertainty` (low/medium/high), `out_of_scope` (Y/N) və `notes` doldur; contact sheet aşağı ölçeklidir, koordinatı orijinal ölçüyə çevir.
8. Pair label-ə baxıb konkret obyekt dəyişikliyini təxmin etmə; yalnız gördüyünü yaz.
9. Bitirəndən sonra faylı `docs/ali/labels_ali.csv` kimi saxla və A1-dən əvvəl commit et (freeze).
