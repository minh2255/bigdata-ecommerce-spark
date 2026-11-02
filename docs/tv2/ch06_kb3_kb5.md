# Chương 6 (phần TV2). Thực nghiệm KB3 và KB5

> Bản nháp. Số liệu KB3 và KB5 đã đủ, lấy từ `kb3.csv`, `profiling_raw.json`, `profiling_clean.json` (toàn tháng) và `cleaning_metrics_merged.json` trong `docs/evidence/tv2/`.

## 6.1 KB3 – CSV và Parquet

**Mục tiêu.** Kiểm chứng hai lợi ích của Parquet đã nêu ở mục 2.1.3: nén tốt hơn và đọc nhanh hơn, đặc biệt khi chỉ cần một cột.

**Cách đo.** Cùng một tập dữ liệu gốc `2019-Oct.csv` (42.448.764 dòng): bản CSV ở tầng landing và bản Parquet ở tầng raw do `00_ingest.py` tạo (ingest mất 173,5 giây). Job `jobs/kb3_csv_vs_parquet.py` đọc CSV với schema cố định (giống ingest, không `inferSchema`) và đo hai phép:

- `count()` toàn bộ;
- `sum(price)`, chỉ cần một cột trong 9 cột.

Mỗi phép đo chạy 3 lần trên cùng cụm Docker (1 master, 2 worker, executor 2 GB, container 8 CPU và 4,8 GB RAM, Spark 3.5.9), lấy trung bình. Số liệu thô: `docs/evidence/tv2/kb3.csv`; cấu hình: `docs/evidence/tv2/kb3_env.json`.

**Kết quả.**

Bảng 6.1. Dung lượng

| Định dạng | Dung lượng | Tỷ lệ |
| --- | --- | --- |
| CSV (landing) | 5.668.612.855 byte (5,28 GiB) | 3,87× |
| Parquet snappy (raw) | 1.465.175.946 byte (1,36 GiB) | 1× |

Bảng 6.2. Thời gian đọc (giây)

| Phép đo | Định dạng | Lần 1 | Lần 2 | Lần 3 | Trung bình |
| --- | --- | --- | --- | --- | --- |
| `count()` | CSV | 44,0 | 35,8 | 39,3 | **39,7** |
| `count()` | Parquet | 3,1 | 1,9 | 1,7 | **2,2** |
| `sum(price)` | CSV | 52,5 | 52,0 | 64,5 | **56,3** |
| `sum(price)` | Parquet | 3,3 | 3,0 | 3,2 | **3,2** |

Parquet nhanh hơn CSV khoảng 17,7 lần ở cả hai phép đo.

**Nhận xét.**

1. **Dung lượng.** Parquet nhỏ hơn 3,87 lần nhờ lưu theo cột (các giá trị cùng kiểu đứng cạnh nhau nên nén tốt hơn), dùng từ điển cho cột lặp nhiều (`event_type`, `brand`) và lưu số dưới dạng nhị phân thay vì chữ số.
2. **`count()` nhanh hơn.** Parquet lưu sẵn số dòng trong phần chân file (footer) của mỗi row group, nên `count()` gần như không phải đọc dữ liệu. CSV phải đọc và tách mọi dòng.
3. **`sum(price)` cho thấy lợi ích đọc chọn cột.** Với CSV, thời gian tăng từ 39,7 lên 56,3 giây vì ngoài đếm còn phải chuyển chuỗi thành số; việc đọc cả 9 cột không tránh được. Với Parquet, chỉ đọc cột `price` nên thời gian chỉ tăng nhẹ (2,2 → 3,2 giây).

**Hạn chế cần nói rõ.**

- Lần chạy đầu của CSV (44,0 giây) chậm hơn hai lần sau; lần sau có thể hưởng bộ nhớ đệm của hệ điều hành. Vì vậy trung bình 3 lần hơi thiên về CSV nhanh hơn thực tế khi đọc nguội.
- `count()` trên Parquet gần như chỉ đọc metadata, nên tỷ lệ 17,7× của phép này không phải tốc độ xử lý dữ liệu thật. `sum(price)` phản ánh tốt hơn lợi ích khi thực sự đọc dữ liệu.
- Chỉ đo trên một máy chạy cụm 2 worker; không suy ra được khả năng mở rộng trên nhiều máy.

## 6.2 KB5 – Chất lượng dữ liệu trước và sau làm sạch

**Mục tiêu.** Cho thấy bằng số liệu rằng bước làm sạch loại đúng những dòng contract quy định và dữ liệu clean thỏa các bất biến.

**Cách làm.** Chạy `01_profiling.py raw` trên tầng raw và `01_profiling.py clean` trên tầng clean, so hai file JSON; đối chiếu với log `[CLEAN]` của TV3 (raw → dedup → lọc).

**Phương pháp chạy.** Cleaning toàn bộ 42,4 triệu dòng trong một lần làm executor 2 GB hết bộ nhớ (hai lần thử, mã lỗi 52). Nhóm chia raw thành 8 lát theo ngày và chạy nguyên `02_cleaning.py` cho từng lát, rồi gộp. Cách này không đổi kết quả dedup vì dòng trùng có cùng `event_time`, tức luôn nằm trong cùng một lát. Số liệu từng lát: `docs/evidence/tv2/slices/`.

Bảng 6.3. Số dòng qua các bước cleaning (tổng 8 lát)

| Bước | Số dòng | Loại ở bước này |
| --- | --- | --- |
| raw | 42.448.764 | – |
| sau dedup | 42.418.544 | 30.220 (dòng trùng) |
| sau lọc `event_time` | 42.418.544 | 0 |
| sau lọc `event_type` | 42.418.544 | 0 |
| sau lọc giá > 0 | 42.349.874 | 68.670 |
| sau lọc định danh | 42.349.872 | 2 (session rỗng) |
| **clean (ghi ra)** | **42.349.872** | **tổng 98.892 (0,23%)** |

Tổng thời gian cleaning 8 lát: 2.552,5 giây (≈ 42,5 phút).

Bảng 6.4. So `profiling_raw` với `profiling_clean`

| Chỉ số | Raw | Clean |
| --- | --- | --- |
| Số dòng | 42.448.764 | 42.349.872 |
| Dòng trùng | 30.220 | 0 |
| Giá ≤ 0 | 68.673 | 0 |
| `user_session` thiếu (null) | 2 | 0 |
| `brand` null / `unknown` | 6.113.008 (14,40%) | 6.043.456 (14,27%) |
| `category_code` null / `cat_l1 = unknown` | 13.515.609 (31,84%) | 13.475.214 (31,82%) |
| `view` | 40.779.399 | 40.708.807 |
| `cart` | 926.516 | 898.292 |
| `purchase` | 742.849 | 742.773 |
| Người dùng / phiên / sản phẩm (xấp xỉ) | 3.308.390 / 8.857.215 / 164.402 | 3.308.390 / 8.857.215 / 164.402 |
| Khoảng thời gian | 01/10 00:00:00 – 31/10 23:59:59 | như raw |
| Bất biến của clean | – | đạt cả 7 (`all_pass = true`) |

(Cả hai cột lấy từ `profiling_raw.json` và `profiling_clean.json` chạy trên toàn tháng; số raw trùng khớp lần quét ở mục 3.2. Số người dùng, phiên, sản phẩm là ước lượng `approx_count_distinct`.)

**Giải thích.**

1. Mọi lỗi định nghĩa trong contract (trùng, giá ≤ 0, session rỗng) đều về 0 ở clean; số dòng bị loại ở từng bước khớp số lỗi đếm được ở raw.
2. `brand` và `category_code` thiếu không làm mất dòng: chúng được gán `unknown`, nên số dòng clean chỉ giảm 0,23% dù gần một phần ba dòng thiếu danh mục.
3. **Lưu ý của TV3:** dedup chạy trên dòng raw, *trước* khi chuẩn hóa `brand`. Hai dòng chỉ khác chữ hoa/thường của `brand` không bị coi là trùng ở raw nhưng có thể giống nhau sau chuẩn hóa. Với dữ liệu thật, `brand` đã là chữ thường (0 dòng cần chuẩn hóa), nên hiện tượng này không xảy ra; contract vẫn giữ quy tắc phòng ngừa.
4. **Dòng bị loại tập trung ở loại sự kiện nào.** `view` giảm 70.592 dòng, `cart` giảm 28.224, `purchase` giảm 76 (tổng 98.892). Giá bằng 0 chỉ có ở `view` (68.523) và `cart` (150), nên 76 dòng `purchase` bị loại đều là dòng trùng và doanh thu không bị ảnh hưởng. Đáng chú ý là `cart` mất ít nhất 28.074 dòng trùng (3,0% số `cart`), trong khi `view` chỉ mất khoảng 2.000 dòng trùng (0,005%): dòng trùng chủ yếu là sự kiện thêm giỏ hàng bị ghi lặp. Đây là suy luận từ hiệu số, chưa kiểm tra trực tiếp từng dòng.
5. Số dòng giá ≤ 0 bị loại (68.670) nhỏ hơn số đếm ở raw (68.673) đúng 3 dòng, vì 3 dòng đó là bản trùng đã bị loại ở bước dedup.

**Minh chứng:** `docs/evidence/tv2/` (kb3.csv, kb3_env.json, cleaning_metrics_merged.json, slices/*, `profiling_raw.json`, `profiling_clean.json`).
