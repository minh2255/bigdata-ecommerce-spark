# Chương 6 (phần TV2). Thực nghiệm KB3 và KB5

> Bản nháp. Số liệu KB3 và KB5 đã đủ, lấy từ `kb3.csv`, `profiling_raw.json`, `profiling_clean.json` (toàn tháng) và `cleaning_metrics_merged.json` trong `docs/evidence/tv2/`.

## 6.1 KB3 – CSV và Parquet

**Mục tiêu.** Kiểm chứng hai lợi ích của Parquet đã nêu ở mục 2.1.3: nén tốt hơn và đọc nhanh hơn, đặc biệt khi chỉ cần một cột.

**Cách đo.** Cùng một tập dữ liệu gốc `2019-Oct.csv` (42.448.764 dòng): bản CSV ở tầng landing và bản Parquet ở tầng raw do `00_ingest.py` tạo (ingest mất 173.46 giây, theo `ingest_log.csv`). Job `jobs/kb3_csv_vs_parquet.py` đọc CSV với schema cố định (giống ingest, không `inferSchema`) và đo hai phép:

- `count()` toàn bộ;
- `sum(price)`, chỉ cần một cột trong 9 cột.

Mỗi phép đo chạy 3 lần trên cùng cụm Docker (1 master, 2 worker; executor và driver `2g`; container thấy 8 CPU và 4.8 GiB RAM; Spark 3.5.9), lấy trung bình. Trường `mem_total_gb_in_container` được code tính theo GiB. Đây là cấu hình lần đo KB3. Số liệu thô: `docs/evidence/tv2/kb3.csv`; cấu hình: `docs/evidence/tv2/kb3_env.json`. Các số đo dưới đây giữ nguyên độ chính xác của nguồn, dùng dấu chấm thập phân.

**Kết quả.**

Bảng 6.1. Dung lượng

| Định dạng | Dung lượng | Tỷ lệ |
| --- | --- | --- |
| CSV (landing) | 5.668.612.855 byte | 3.869× |
| Parquet snappy (raw) | 1.465.175.946 byte | 1× (mốc so sánh) |

Bảng 6.2. Thời gian đọc (giây)

| Phép đo | Định dạng | Lần 1 | Lần 2 | Lần 3 | Trung bình |
| --- | --- | --- | --- | --- | --- |
| `count()` | CSV | 43.997 | 35.764 | 39.287 | **39.683** |
| `count()` | Parquet | 3.073 | 1.922 | 1.745 | **2.247** |
| `sum(price)` | CSV | 52.468 | 52.016 | 64.514 | **56.333** |
| `sum(price)` | Parquet | 3.322 | 2.977 | 3.24 | **3.18** |

Theo các dòng `count_speedup` và `sum_price_speedup` trong CSV, hệ số tăng tốc lần lượt là **17.663×** và **17.717×**. Giữ nguyên hệ số nguồn, không tính lại từ các mean đã làm tròn.

**Nhận xét.**

1. **Dung lượng.** Tỷ lệ dung lượng CSV/Parquet là 3.869 theo nguồn. Lưu theo cột và nén snappy giúp giảm dung lượng; phép đo này không tách riêng mức đóng góp của từng cơ chế mã hóa.
2. **`count()` nhanh hơn.** Parquet lưu sẵn số dòng trong phần chân file (footer) của mỗi row group, nên `count()` gần như không phải đọc dữ liệu. CSV phải đọc và tách mọi dòng.
3. **`sum(price)` cho thấy lợi ích đọc chọn cột.** Mean CSV tăng từ 39.683 lên 56.333 giây; Parquet tăng từ 2.247 lên 3.18 giây. Parquet có thể đọc riêng cột `price`; với CSV vẫn phải duyệt văn bản đầu vào. Không quy toàn bộ chênh lệch thời gian cho một cơ chế khi chưa có phép đo tách riêng.

**Hạn chế cần nói rõ.**

- Lần `count()` đầu của CSV (43.997 giây) chậm hơn hai lần sau; bộ nhớ đệm có thể ảnh hưởng. Chưa đo riêng đọc nguội và đọc ấm nên không định lượng ảnh hưởng này.
- `count()` trên Parquet có thể dùng metadata, nên hệ số 17.663× của phép này không đại diện cho mọi truy vấn. `sum(price)` phản ánh tốt hơn trường hợp thực sự đọc giá trị cột.
- Chỉ đo trên một máy chạy cụm 2 worker; không suy ra được khả năng mở rộng trên nhiều máy.

## 6.2 KB5 – Chất lượng dữ liệu trước và sau làm sạch

**Mục tiêu.** Cho thấy bằng số liệu rằng bước làm sạch loại đúng những dòng contract quy định và dữ liệu clean thỏa các bất biến.

**Cách làm.** Chạy `01_profiling.py raw` trên tầng raw và `01_profiling.py clean` trên tầng clean, so hai file JSON; đối chiếu với log `[CLEAN]` của TV3 (raw → dedup → lọc).

**Phương pháp chạy.** Theo ghi chú trong `cleaning_metrics_merged.json`, cleaning toàn bộ 42.448.764 dòng trong một lần gặp lỗi hết bộ nhớ executor; nguồn này không xác nhận số lần thử hay mã lỗi. Nhóm chia raw thành 8 lát theo ngày và chạy nguyên `02_cleaning.py` cho từng lát, rồi gộp. Các lát bao phủ toàn tháng, không chồng lấn; dòng trùng có cùng `event_time` nên luôn nằm trong cùng một lát, bảo toàn dedup. Số liệu từng lát: `docs/evidence/tv2/slices/`.

Bảng 6.3. Số dòng qua các bước cleaning (tổng 8 lát)

| Bước | Số dòng | Loại ở bước này |
| --- | --- | --- |
| raw | 42.448.764 | – |
| sau dedup | 42.418.544 | 30.220 (dòng trùng) |
| sau lọc `event_time` | 42.418.544 | 0 |
| sau lọc `event_type` | 42.418.544 | 0 |
| sau lọc giá > 0 | 42.349.874 | 68.670 |
| sau lọc định danh | 42.349.872 | 2 (session rỗng) |
| **clean (ghi ra)** | **42.349.872** | **tổng 98.892** |

Tổng thời gian cleaning 8 lát: **2552.5 giây**, lấy nguyên trường `cleaning_seconds_total` trong `cleaning_metrics_merged.json`.

Bảng 6.4. So `profiling_raw` với `profiling_clean`

| Chỉ số | Raw | Clean |
| --- | --- | --- |
| Số dòng | 42.448.764 | 42.349.872 |
| Dòng trùng | 30.220 | 0 |
| Giá ≤ 0 | 68.673 | 0 |
| `user_session` thiếu (null) | 2 | 0 |
| `brand` null / `unknown` | 6.113.008 | 6.043.456 (`unknown_ratio.brand = 0.142703`) |
| `category_code` null / `cat_l1 = unknown` | 13.515.609 | 13.475.214 (`unknown_ratio.cat_l1 = 0.318188`) |
| `view` | 40.779.399 | 40.708.807 |
| `cart` | 926.516 | 898.292 |
| `purchase` | 742.849 | 742.773 |
| Người dùng / phiên / sản phẩm (xấp xỉ) | 3.308.390 / 8.857.215 / 164.402 | 3.308.390 / 8.857.215 / 164.402 |
| Khoảng thời gian | 01/10 00:00:00 – 31/10 23:59:59 | như raw |
| Bất biến của clean | – | đạt cả 7 (`all_pass = true`) |

(Cả hai cột lấy từ `profiling_raw.json` và `profiling_clean.json` chạy trên toàn tháng; số raw trùng khớp lần quét ở mục 3.2. Số người dùng, phiên, sản phẩm là ước lượng `approx_count_distinct`.)

**Giải thích.**

1. Profiling clean ghi nhận 0 dòng trùng, 0 giá ≤ 0 và 0 session null/trắng; cả 7 bất biến đều đạt. Số bị loại cần đối chiếu theo thứ tự cleaning vì các lỗi ở raw có thể giao nhau.
2. Thiếu `brand` hoặc `category_code` không phải điều kiện loại dòng. `brand` và các cột `cat_l1`, `cat_l2` được gán `unknown`; `category_code` gốc vẫn có thể null. Tổng giảm 98.892 dòng là do dedup và các bước lọc.
3. **Lưu ý của TV3:** dedup chạy trên dòng raw, *trước* chuẩn hóa. Các dòng khác nhau ở raw vẫn có thể giống nhau sau chuẩn hóa; contract không yêu cầu dedup lại. Với dữ liệu thật, profiling raw ghi 0 dòng brand có chữ hoa và 0 dòng có khoảng trắng ngoài; kết quả clean thực đo có 0 dòng trùng.
4. **Mức giảm theo loại sự kiện.** Lấy hiệu `event_type_counts` raw và clean: `view` giảm 70.592 dòng, `cart` giảm 28.224, `purchase` giảm 76 (tổng 98.892). Đây là mức giảm qua toàn bộ cleaning, không phải số trùng riêng của từng loại sự kiện. Chưa có bảng chéo nguồn trước/sau dedup để tách các nguyên nhân; cũng chưa có tổng doanh thu trước/sau trong bộ nguồn này để định lượng ảnh hưởng đến doanh thu.
5. Số dòng giá ≤ 0 bị loại (68.670) nhỏ hơn số đếm ở raw (68.673) đúng 3 dòng, vì 3 dòng đó là bản trùng đã bị loại ở bước dedup.

**Minh chứng:** `docs/evidence/tv2/` (kb3.csv, kb3_env.json, cleaning_metrics_merged.json, slices/*, `profiling_raw.json`, `profiling_clean.json`).
