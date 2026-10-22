# Data contract – eCommerce behavior data (TV2)

Tài liệu này là **luật chung** cho cả nhóm: TV2 định nghĩa dữ liệu hợp lệ, TV3 cài đặt trong
`jobs/02_cleaning.py`, TV4 dựa vào để tính KPI. Phiên bản 1.0 – chốt các câu hỏi TV3 đã nêu
trong `docs/tv3_handoff.md` (mục "Contract chính thức").

- Nguồn: Kaggle *eCommerce behavior data from multi category store*, file `2019-Oct.csv`
  (≈ 5,7 GB, > 40 triệu dòng).
- Mỗi dòng là một sự kiện của người dùng trên sàn thương mại điện tử.
- Quy ước thời gian: **mọi thời gian theo UTC** (`spark.sql.session.timeZone = UTC`).

## 1. Schema tầng raw (`landing/*.csv` → `raw/events`)

CSV có header, đúng thứ tự cột dưới đây (`pipeline_preflight.py` kiểm tra).

| Cột | Kiểu Spark | Ý nghĩa | Ghi chú |
| --- | --- | --- | --- |
| event_time | string | Thời điểm sự kiện, dạng `2019-10-01 00:00:00 UTC` | Có hậu tố ` UTC`; chưa là timestamp |
| event_type | string | `view` / `cart` / `purchase` | |
| product_id | bigint | Mã sản phẩm | |
| category_id | bigint | Mã danh mục | |
| category_code | string | Danh mục dạng cây, ví dụ `electronics.smartphone` | Nhiều dòng null |
| brand | string | Thương hiệu | Có thể null; có thể lẫn chữ hoa |
| price | double | Giá sản phẩm | |
| user_id | bigint | Mã người dùng | |
| user_session | string | Mã phiên truy cập (UUID) | Một phiên có nhiều sự kiện |

Raw giữ nguyên dữ liệu gốc, **không sửa gì** (chỉ đổi định dạng CSV → Parquet).

## 2. Quy tắc làm sạch (raw → clean)

Áp dụng theo đúng thứ tự. Cột "Xử lý" là hành động khi vi phạm.

| # | Quy tắc hợp lệ | Xử lý khi vi phạm | Lý do |
| --- | --- | --- | --- |
| 1 | Không có hai dòng raw giống hệt nhau ở **cả 9 cột** | Giữ 1 bản, bỏ phần trùng | Dòng lặp làm sai số đếm và doanh thu. Dedup xét trên dòng raw, **trước** khi chuẩn hóa |
| 2 | `event_time` đúng dạng `yyyy-MM-dd HH:mm:ss UTC` | Bỏ dòng (không parse được → null) | Không tính toán theo thời gian được |
| 3 | `event_type` ∈ {`view`, `cart`, `purchase`} | Bỏ dòng | Loại giá trị lạ |
| 4a | `price` hữu hạn và `price > 0` (loại NaN, ±Infinity, 0, âm) | Bỏ dòng | Vô nghĩa cho doanh thu |
| 4b | `user_id` khác null | Bỏ dòng | Không phân tích được theo người dùng |
| 4c | `user_session` khác null và không rỗng/toàn khoảng trắng | Bỏ dòng | Không phân tích được theo phiên |
| 5 | `category_code` tách theo dấu `.` thành `cat_l1`, `cat_l2` | Thiếu/rỗng → `"unknown"`; **không bỏ dòng** | Giữ doanh thu của sản phẩm không có danh mục |
| 6 | `brand` được trim + viết thường | null/rỗng → `"unknown"`; **không bỏ dòng** | Gộp `Samsung` và `samsung` |
| 7 | Thêm cột `event_ts`, `event_date`, `event_hour`, `day_of_week` | — | Phục vụ KPI và phân vùng |

### Những điều contract **cố ý không bắt buộc**

| Nội dung | Quyết định | Cách theo dõi |
| --- | --- | --- |
| `product_id`, `category_id`, `user_id` phải dương | **Không loại** dòng | Chỉ đếm số vi phạm trong `profiling_*.json` |
| `user_session` phải đúng định dạng UUID | **Không loại** dòng | Chỉ đếm trong profiling |
| `product_id`, `category_id` khác null | **Không loại** dòng | Đếm null trong profiling |
| `category_code` null | Bình thường (tỷ lệ thật sẽ lấy từ `profiling_raw.json`) | Tỷ lệ `unknown` ở cột `cat_l1` |

Lý do: loại thêm dòng theo các điều này chưa có bằng chứng về lỗi thật và sẽ làm đổi tổng
doanh thu/phễu. Nếu profiling dữ liệu thật cho thấy có vi phạm đáng kể, nhóm quyết định lại
và nâng contract lên phiên bản 1.1.

### Hệ quả cần nhớ

- **Dedup trước chuẩn hóa:** sau bước 5–6 vẫn có thể xuất hiện các dòng clean giống nhau
  (ví dụ chỉ khác `Samsung` / `samsung`). Đây là hành vi đúng của contract; **TV4 không
  `dropDuplicates` lần nữa**.
- **`user_session` không phải khóa duy nhất:** một phiên có nhiều sự kiện.
- **`unknown` là nhãn quy ước**, không phải thương hiệu/danh mục thật; KPI theo brand/danh mục
  nên báo riêng hoặc loại `unknown` khi xếp hạng.
- **Tập rỗng hợp lệ:** nếu mọi dòng bị loại, `clean/events` rỗng nhưng vẫn có schema
  (`SUCCESS_EMPTY`); các job sau phải xử lý được.

## 3. Schema tầng clean (`clean/events`, phân vùng `event_date`)

| Cột | Kiểu Spark | Ý nghĩa / bất biến |
| --- | --- | --- |
| event_type | string | `view` / `cart` / `purchase` |
| product_id | bigint | Giữ từ raw |
| category_id | bigint | Giữ từ raw |
| category_code | string | Giữ từ raw, có thể null |
| brand | string | trim + lowercase; không bao giờ null (`unknown`) |
| price | double | Hữu hạn và > 0 |
| user_id | bigint | Không null |
| user_session | string | Không null, không rỗng |
| event_ts | timestamp | Giờ UTC; thay cho `event_time` (cột này bị bỏ) |
| cat_l1 | string | Danh mục cấp 1; không null (`unknown`) |
| cat_l2 | string | Danh mục cấp 2; không null (`unknown`) |
| event_hour | int | 0–23 (UTC) |
| day_of_week | string | `Mon` … `Sun` (không phải số) |
| event_date | date | Ngày UTC; **cột phân vùng** (thư mục `event_date=YYYY-MM-DD/`) |

Khi đọc: dùng đường dẫn gốc `clean/events` để Spark nhận ra cột `event_date`.

## 4. Các bất biến để kiểm chứng (profiling trên tầng clean)

`jobs/01_profiling.py clean` phải cho kết quả:

1. Số dòng trùng hoàn toàn của raw đã bị loại (so với `profiling_raw.json`).
2. `price_le_0` = 0, `price_nan_or_inf` = 0.
3. Không có null ở `user_id`, `user_session`, `brand`, `cat_l1`, `cat_l2`, `event_ts`, `event_date`.
4. `event_type` chỉ gồm 3 giá trị hợp lệ.
5. `0 ≤ event_hour ≤ 23`; `event_date` nằm trong khoảng ngày của dữ liệu nguồn
   (1–31/10/2019 với `2019-Oct.csv`).

## 5. Dữ liệu giả để test

`scripts/generate_data.py` sinh `landing/synthetic.csv` cùng schema raw, cố ý chèn lỗi và ghi
số lượng thực tế vào `reports/generate_data_truth.json` để đối chiếu với profiling:

| Lỗi chèn | Tỷ lệ | Quy tắc kiểm tra |
| --- | --- | --- |
| Dòng trùng | ≈ 1% | 1 |
| `price = 0` | ≈ 1% | 4a |
| `price` âm | ≈ 0,1% | 4a |
| `price = NaN` | ≈ 0,1% | 4a |
| `event_type = wishlist` | ≈ 0,2% | 3 |
| `user_session` rỗng/khoảng trắng | ≈ 0,2% | 4c |
| `user_id` trống | ≈ 0,1% | 4b |
| `brand` / `category_code` rỗng, brand lẫn chữ hoa (`Apple`) | ≈ 1/6 | 5, 6 |

Vùng dữ liệu giả phải để trong `DATA_DIR` riêng, tên file có chữ `synthetic`
(pipeline từ chối trộn với dữ liệu Kaggle thật).

## 7. Kiểm chứng luật trên dữ liệu Kaggle thật (22/10/2026)

Quét toàn bộ `2019-Oct.csv` (42.448.764 dòng) để xem luật có hợp lý không. Các số dưới đây
là số trên **raw**, chưa qua cleaning; `profiling_raw.json` sẽ thay thế khi có.

| Hiện tượng | Số dòng | Quy tắc | Nhận xét |
| --- | --- | --- | --- |
| Dòng trùng cả 9 cột | 30.220 (0,07%) | 1 | Có thật, cần dedup |
| `price = 0` | 68.673 (0,16%) | 4a | 68.523 `view` + 150 `cart`, **không có `purchase`** nên loại không làm lệch doanh thu |
| `price` < 0, NaN, Inf | 0 | 4a | Chưa thấy ở dữ liệu thật; luật vẫn giữ để chặn dữ liệu bẩn |
| `user_session` rỗng | 2 | 4c | Có thật (2 dòng `cart`), loại là đúng |
| `user_id` null / ≤ 0 | 0 | 4b | Không cần luật ID dương |
| `user_session` không phải UUID | 0 | — | Không cần luật UUID |
| `product_id`, `category_id` null | 0 | — | Không cần loại |
| `category_code` null | 13.515.609 (31,8%) | 5 | Rất lớn, **phải** thành `unknown`, không được loại dòng |
| `brand` null | 6.113.008 (14,4%) | 6 | Như trên |
| `brand` có chữ hoa / khoảng trắng thừa | 0 | 6 | Dữ liệu gốc đã chữ thường; lowercase+trim chỉ là phòng ngừa |
| `event_time` sai định dạng | 0 | 2 | Khoảng 2019-10-01 00:00:00 đến 2019-10-31 23:59:59 |
| `event_type` | view 40.779.399; cart 926.516; purchase 742.849 | 3 | Chỉ có 3 giá trị hợp lệ |
| `category_code` sâu 3 cấp | 36.242 (0,09%) | 5 | Cấp 3 bị bỏ vì clean chỉ giữ `cat_l1`, `cat_l2`; `category_code` gốc vẫn còn trong clean |

**Kết luận:** 7 quy tắc + 3 mở rộng của v1.0 phù hợp, không cần đổi `02_cleaning.py`.
Dự kiến clean ≈ 42.448.764 − 30.220 (trùng) − ~68.673 (giá 0) − 2 (session rỗng) ≈ 42,35 triệu
dòng (có thể lệch nhỏ vì các lỗi giao nhau); con số chính thức lấy từ `cleaning_metrics.json`.

## 6. Lịch sử phiên bản

| Phiên bản | Nội dung |
| --- | --- |
| 1.0 | Chốt 7 quy tắc + 3 mở rộng (price hữu hạn, session không trắng, blank → unknown); ID dương/UUID chỉ ghi nhận |
| 1.0 (bổ sung) | Thêm mục 7: kiểm chứng luật trên dữ liệu thật, không đổi luật |
