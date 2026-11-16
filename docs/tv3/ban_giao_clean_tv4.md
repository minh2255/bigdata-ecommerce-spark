# Giao diện dữ liệu clean bàn giao cho TV4

## Vùng dữ liệu thật (Kaggle tháng 10/2019)

Đường dẫn container: /data/real_oct_full/clean/events (nguồn: `docs/evidence/tv2/cleaning_metrics_merged.json`, trường data_dir; `TV2_Plan_Roadmap.md`). Vùng này **được gộp từ 8 lát ngày** (real_oct_s1..s8) do cleaning nguyên khối bị hết bộ nhớ trên máy 8 GB; không phải một lần chạy `02_cleaning.py` duy nhất. Số dòng: raw 42.448.764, clean 42.349.872, 31 thư mục event_date. Dữ liệu nằm ở máy TV2 (thư mục data không lên Git); TV4 cần xin quyền truy cập hoặc đường dẫn từ TV2. Đọc đường dẫn gốc để Spark nhận event_date từ thư mục. Mục TV4 xác nhận ở cuối tài liệu vẫn chưa thực hiện.

## Vùng synthetic đã kiểm chứng

Đường dẫn container đã kiểm chứng: /data/synthetic_tv3_20261018_optimized/clean/events. Đường dẫn Windows: D:/Desktop/BigData/data/synthetic_tv3_20261018_optimized/clean/events. Đây là dữ liệu SYNTHETIC TEST ONLY, 197973 hàng, 31 thư mục ngày; không phải kết quả Kaggle. File metrics của vùng là báo cáo bản cleaning đã kiểm chứng trước khi bổ sung metadata/thời gian chi tiết; số liệu và dữ liệu cũ được giữ nguyên. Các fixture mới minh họa giao diện metrics/schema hiện tại trong danh mục minh chứng.

## Schema đọc bằng Spark

| Cột | Kiểu Spark | Ý nghĩa hoặc quy ước |
| --- | --- | --- |
| event_type | string | view/cart/purchase |
| product_id | bigint | ID sản phẩm giữ từ raw; chưa áp luật dương hoặc non-null bổ sung |
| category_id | bigint | ID danh mục giữ từ raw; chưa áp luật dương hoặc non-null bổ sung |
| category_code | string | Chuỗi phân cấp gốc, có thể null |
| brand | string | trim + lowercase; null/rỗng thành unknown |
| price | double | Hữu hạn và > 0 theo quy tắc đang áp dụng |
| user_id | bigint | Không null; chưa áp luật dương |
| user_session | string | Không null/trắng; có thể lặp giữa nhiều sự kiện; không kiểm định UUID |
| event_ts | timestamp | Timestamp được tạo trong session UTC |
| cat_l1 | string | Cấp đầu category_code, trim; thiếu/rỗng thành unknown |
| cat_l2 | string | Cấp thứ hai, trim; thiếu/rỗng thành unknown |
| event_hour | int | Giờ UTC, 0–23 |
| day_of_week | string | Mon/Tue/Wed/Thu/Fri/Sat/Sun theo mẫu E, không phải số |
| event_date | date | Ngày UTC; cột phân vùng khi có dữ liệu |

Nullability do Spark khai báo không thay cho các bất biến nghiệp vụ. category_code, product_id, category_id có thể null theo quy tắc hiện tại; không suy rằng chúng đã được kiểm chứng đầy đủ chỉ vì job thành công. event_time bị bỏ khỏi clean. Raw dedup xét toàn bộ hàng trước chuẩn hóa; các hàng clean có thể trở nên giống nhau nếu raw chỉ khác ở phần được chuẩn hóa. Không tự dropDuplicates lần nữa ở TV4 nếu chưa chốt ý nghĩa với TV2/TV3.

## Cách đọc và điều kiện tích hợp

```python
spark.conf.set("spark.sql.session.timeZone", "UTC")
events = spark.read.parquet("/data/synthetic_tv3_20261018_optimized/clean/events")
events.printSchema()
events.orderBy("event_ts").show(5, truncate=False)
```

Đọc đường dẫn gốc của bảng để Spark phát hiện event_date từ thư mục. Nếu đọc trực tiếp một thư mục ngày, dùng option basePath trỏ về gốc khi cần giữ cột phân vùng. Khi đọc bằng Pandas/PyArrow, event_date có thể biểu diễn thành dictionary/string do partition discovery; bảng kiểu trong tài liệu này là schema Spark đã kiểm tra, không phải cam kết dtype Pandas tự động.

Đầu ra rỗng có _SUCCESS và một file Parquet chứa schema ngay ở gốc, không có thư mục ngày giả. Metrics SUCCESS_EMPTY và count=0. TV4 cần xử lý DataFrame rỗng trước khi suy KPI, không giả doanh thu 0 của một ngày không tồn tại. Với tập không rỗng, số file/ngày là đặc tính của lần chạy, không phải API mà downstream được phép phụ thuộc.

TV4 cần xác nhận: đọc được schema và counts; hiểu UTC; không xem session là khóa duy nhất; phân biệt unknown với nhãn thật; đối chiếu KPI bằng truy vấn độc lập khi job aggregation đã có. Tại thời điểm cập nhật 15/11/2026 job `03_aggregation.py` của TV4 đã có trên `origin/main` và TV2 đã chạy nó trong lần `--full` trên synthetic, nhưng chưa có xác nhận của TV4 đã đọc clean thật và đối chiếu KPI, nên tất cả mục này vẫn ở trạng thái chờ xác nhận.

# Bảng số liệu gửi TV2 cho KB5

Xem bảng số dòng từng bước trong docs/tv3_run_20261027.md và cleaning_metrics.json cùng vùng dữ liệu; các file 20261027_* trong danh mục minh chứng giữ số loại và thời gian từng bước. Baseline cũ và fixture là synthetic; số liệu Kaggle thật xem `cleaning_metrics_merged.json` và Ch.5 mục 5.8. Không đặt tên hoặc coi bảng này là profiling_raw.json/profiling_clean.json chính thức. Mode --quality-check hiện gọi job profiling chính thức của TV2 để tạo hai báo cáo. Luật theo contract v1.0. Kết quả mới, schema, đường dẫn và số liệu KB5 xem docs/tv3_run_20261027.md.

## Lượt tích hợp contract v1.0 ngày 27 tháng 10 năm 2026

Clean synthetic mới: /data/synthetic_quality_20261027_095328_f07dad/clean/events, 19.627 dòng, 31 ngày. Windows: D:/Desktop/BigData/data/synthetic_quality_20261027_095328_f07dad/clean/events. Metadata/schema và profiling raw/clean chính thức ở reports của cùng vùng, validator 0 vi phạm. KB5: raw 20.203; dedup 20.000; timestamp 20.000; event_type 19.948; price 19.675; identity/written 19.627. Xem docs/tv3_run_20261027.md để lấy application ID, lệnh và giới hạn phép đo. Số liệu Kaggle do TV2 chạy; xác nhận của TV4 chưa có.
