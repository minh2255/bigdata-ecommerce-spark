# Phụ lục A. Schema dữ liệu các tầng raw và clean

Phụ lục này mô tả cấu trúc dữ liệu ở từng tầng của Data Lake trong đồ án. Quy tắc biến đổi giữa các tầng nằm ở `docs/data_contract.md` (v1.0); phụ lục chỉ ghi lại **hình dạng** dữ liệu. Schema clean dưới đây lấy từ `reports/cleaning_schema.json` của lần chạy trên 3 triệu dòng đầu của `2019-Oct.csv` (`data/real_sample3m_run01`), tức là schema Spark thực sự ghi ra, không phải schema dự kiến.

Mọi thời gian theo UTC (`spark.sql.session.timeZone = UTC`).

## A.1 Tổng quan các tầng

| Tầng | Đường dẫn trong `DATA_DIR` | Định dạng | Job tạo ra | Nội dung |
| --- | --- | --- | --- | --- |
| landing | `landing/*.csv` | CSV có header | Tải từ Kaggle (hoặc `scripts/generate_data.py`) | Dữ liệu gốc, không sửa |
| raw | `raw/events/` | Parquet (snappy) | `jobs/00_ingest.py` | Giống landing, chỉ đổi định dạng và gán kiểu cố định |
| clean | `clean/events/event_date=YYYY-MM-DD/` | Parquet, phân vùng theo ngày | `jobs/02_cleaning.py` | Đã dedup, lọc dòng lỗi, chuẩn hóa, thêm cột thời gian |
| samples | `samples/frac_0.01`, `frac_0.05`, `frac_0.1` | Parquet, 1 file mỗi mẫu | `jobs/make_sample.py` | Lấy mẫu ngẫu nhiên từ clean, `seed=42`, cùng schema clean |
| reports | `reports/*.json`, `*.csv` | JSON / CSV | Các job | Số liệu ingest, cleaning, profiling |

Cây thư mục của một lần chạy (ví dụ `data/real_sample3m_run01`):

```text
real_sample3m_run01/
├── landing/
│   └── 2019-Oct_first3m.csv               383 MB
├── raw/
│   └── events/
│       ├── _SUCCESS
│       ├── part-00000-*.snappy.parquet
│       └── part-00001-*.snappy.parquet     95 MB tổng
├── clean/
│   └── events/
│       ├── _SUCCESS
│       ├── event_date=2019-10-01/
│       │   └── part-*.c000.snappy.parquet
│       ├── event_date=2019-10-02/
│       └── event_date=2019-10-03/        150 MB tổng
└── reports/
    ├── ingest_log.csv
    ├── cleaning_metrics.json
    ├── cleaning_schema.json
    ├── profiling_raw.json
    └── profiling_clean.json
```

## A.2 Schema tầng landing và raw

File CSV có header đúng 9 cột theo thứ tự dưới đây. `00_ingest.py` đọc bằng schema cố định (không dùng `inferSchema`, vì suy kiểu phải quét file 5,7 GB thêm một lần), rồi ghi nguyên sang Parquet. Vì vậy tầng raw có **cùng 9 cột, cùng kiểu** với bảng này.

| # | Cột | Kiểu Spark | Null được | Ý nghĩa | Ví dụ |
| --- | --- | --- | --- | --- | --- |
| 1 | event_time | string | có | Thời điểm sự kiện, có hậu tố ` UTC`; chưa phải timestamp | `2019-10-01 00:00:00 UTC` |
| 2 | event_type | string | có | Loại sự kiện: `view`, `cart`, `purchase` | `view` |
| 3 | product_id | bigint | có | Mã sản phẩm | `3900821` |
| 4 | category_id | bigint | có | Mã danh mục (số 19 chữ số) | `2053013552326770905` |
| 5 | category_code | string | có | Danh mục dạng cây, phân cách bằng `.` | `appliances.environment.water_heater` |
| 6 | brand | string | có | Thương hiệu | `aqua` |
| 7 | price | double | có | Giá sản phẩm (USD) | `33.20` |
| 8 | user_id | bigint | có | Mã người dùng | `554748717` |
| 9 | user_session | string | có | Mã phiên (UUID); một phiên có nhiều sự kiện | `9333dfbd-b87a-4708-9857-6336556b0fcc` |

Hai dòng đầu của `2019-Oct.csv`:

```text
event_time,event_type,product_id,category_id,category_code,brand,price,user_id,user_session
2019-10-01 00:00:00 UTC,view,44600062,2103807459595387724,,shiseido,35.79,541312140,72d76fde-8bb3-4e00-8c23-a032dfed738c
2019-10-01 00:00:00 UTC,view,3900821,2053013552326770905,appliances.environment.water_heater,aqua,33.20,554748717,9333dfbd-b87a-4708-9857-6336556b0fcc
```

Dòng đầu tiên đã thiếu `category_code` (ô rỗng giữa hai dấu phẩy). Trên toàn tháng 10, 31,8% dòng thiếu `category_code` và 14,4% thiếu `brand` (contract mục 7).

Ghi chú về kiểu:

- Mọi cột đều để null được. Ở raw, Spark không chặn null; việc kiểm tra thuộc về profiling và cleaning.
- Khi đọc CSV, ô `price` không phải số (ví dụ `nan`, `inf` viết thường) sẽ thành **null**, không thành `NaN`. Vì vậy trong `profiling_raw.json` lỗi này xuất hiện ở `price_null`.
- `category_id` dùng `bigint` vì giá trị vượt giới hạn `int` (khoảng 2,1 tỷ).

## A.3 Schema tầng clean

`clean/events` có 14 cột: bỏ `event_time`, giữ 8 cột còn lại của raw và thêm 6 cột mới. Thứ tự dưới đây là thứ tự trong `cleaning_schema.json`.

| # | Cột | Kiểu Spark | Nguồn | Bất biến sau cleaning |
| --- | --- | --- | --- | --- |
| 1 | event_type | string | giữ từ raw | Chỉ `view`, `cart`, `purchase` |
| 2 | product_id | bigint | giữ từ raw | Không kiểm tra dương hay null (chỉ ghi nhận trong profiling) |
| 3 | category_id | bigint | giữ từ raw | Như trên |
| 4 | category_code | string | giữ từ raw | Có thể null; giữ để truy lại cấp 3 trở xuống |
| 5 | brand | string | raw, trim + viết thường | Không null; thiếu/rỗng → `unknown` |
| 6 | price | double | giữ từ raw | Hữu hạn và > 0 |
| 7 | user_id | bigint | giữ từ raw | Không null |
| 8 | user_session | string | giữ từ raw | Không null, không rỗng hay toàn khoảng trắng |
| 9 | event_ts | timestamp | **mới**, parse từ `event_time` | Không null, giờ UTC |
| 10 | cat_l1 | string | **mới**, phần 1 của `category_code` | Không null; thiếu → `unknown` |
| 11 | cat_l2 | string | **mới**, phần 2 của `category_code` | Không null; thiếu → `unknown` |
| 12 | event_date | date | **mới**, ngày của `event_ts` | Cột phân vùng; nằm trong 01–31/10/2019 |
| 13 | event_hour | int | **mới**, giờ của `event_ts` | 0–23 |
| 14 | day_of_week | string | **mới**, thứ của `event_ts` | `Mon` … `Sun` (chữ, không phải số) |

Ví dụ: dòng raw thứ hai ở mục A.2 sau khi làm sạch (`category_code` có 3 cấp nên cấp 3 `water_heater` không có cột riêng, nhưng vẫn còn trong `category_code`):

| Cột | Giá trị |
| --- | --- |
| event_type | `view` |
| product_id | `3900821` |
| category_id | `2053013552326770905` |
| category_code | `appliances.environment.water_heater` |
| brand | `aqua` |
| price | `33.2` |
| user_id | `554748717` |
| user_session | `9333dfbd-b87a-4708-9857-6336556b0fcc` |
| event_ts | `2019-10-01 00:00:00` |
| cat_l1 | `appliances` |
| cat_l2 | `environment` |
| event_date | `2019-10-01` |
| event_hour | `0` |
| day_of_week | `Tue` |

Dòng raw thứ nhất (thiếu `category_code`) sẽ có `cat_l1 = cat_l2 = unknown` và `category_code = null`.

Ghi chú khi đọc tầng clean:

- **Đọc từ gốc `clean/events`**, không đọc thẳng một thư mục ngày; như vậy Spark mới nhận ra cột `event_date` từ tên thư mục. Khi đọc lại, Spark đưa cột phân vùng `event_date` xuống **cuối** schema, nên thứ tự cột lúc đọc khác thứ tự trong `cleaning_schema.json`.
- Spark khai báo mọi cột là `nullable = true`, kể cả các cột đã đảm bảo không null. Bất biến nghiệp vụ được kiểm bằng `jobs/01_profiling.py clean` (mục `invariants` trong `profiling_clean.json`), không dựa vào cờ nullable.
- `unknown` là nhãn quy ước, không phải thương hiệu hay danh mục thật. Trên 3 triệu dòng đầu, `brand = unknown` chiếm 14,5% và `cat_l1 = unknown` chiếm 31,4%.
- Clean có thể có dòng giống nhau, vì dedup chạy trên raw **trước** khi chuẩn hóa. Các job sau không `dropDuplicates` lại (contract mục 2).
- Tập rỗng hợp lệ: khi mọi dòng bị loại, `clean/events` không có thư mục ngày nhưng vẫn có một file Parquet mang schema, và `cleaning_metrics.json` có `status = SUCCESS_EMPTY`.

## A.4 Đối chiếu cột raw → clean

| Cột raw | Cột clean | Biến đổi |
| --- | --- | --- |
| event_time | event_ts, event_date, event_hour, day_of_week | Bỏ hậu tố ` UTC`, parse `yyyy-MM-dd HH:mm:ss`; dòng không parse được bị loại. Cột `event_time` bị bỏ |
| event_type | event_type | Lọc giữ 3 giá trị hợp lệ |
| product_id | product_id | Giữ nguyên |
| category_id | category_id | Giữ nguyên |
| category_code | category_code, cat_l1, cat_l2 | Giữ nguyên cột gốc; tách theo `.` lấy 2 cấp đầu, thiếu → `unknown` |
| brand | brand | Viết thường + trim; thiếu/rỗng → `unknown` |
| price | price | Lọc giữ giá hữu hạn và > 0 |
| user_id | user_id | Lọc bỏ null |
| user_session | user_session | Lọc bỏ null và rỗng/khoảng trắng |

## A.5 Các file báo cáo trong `reports/`

| File | Job ghi | Nội dung chính |
| --- | --- | --- |
| `ingest_log.csv` | `00_ingest.py` | Mỗi lần ingest một dòng: `rows`, `seconds` |
| `cleaning_metrics.json` | `02_cleaning.py` | `counts` sau từng bước (`raw`, `after_dedup`, `after_timestamp`, `after_event_type`, `after_price`, `after_identity`, `written`), `removed`, `stage_seconds`, `status` |
| `cleaning_schema.json` | `02_cleaning.py` | Schema Spark của clean (nguồn của bảng A.3) |
| `profiling_raw.json` | `01_profiling.py raw` | `rows`, `duplicate_rows`, `nulls`, `blank_strings`, thống kê `price`, `event_type_counts`, `event_time` (sai định dạng, không parse được), `brand_normalization_needed` (chữ hoa, khoảng trắng thừa), `distinct_approx` |
| `profiling_clean.json` | `01_profiling.py clean` | Các chỉ số như raw, thêm `date_range`, `event_hour_range`, `unknown_ratio` và `invariants` (job thoát mã 1 nếu một bất biến sai) |
| `generate_data_truth.json` | `scripts/generate_data.py` | Chỉ có ở dữ liệu giả: số lỗi đã cố ý chèn, dùng để đối chiếu |

Các job không ghi đè file báo cáo đã có; mỗi lần chạy dùng một `DATA_DIR` mới.
