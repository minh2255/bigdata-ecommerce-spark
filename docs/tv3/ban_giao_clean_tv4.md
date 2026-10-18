# Giao diện dữ liệu clean bàn giao cho TV4

## Vùng đã có dữ liệu

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

TV4 cần xác nhận: đọc được schema và counts; hiểu UTC; không xem session là khóa duy nhất; phân biệt unknown với nhãn thật; đối chiếu KPI bằng truy vấn độc lập khi job aggregation đã có. Tại thời điểm bàn giao chưa có xác nhận của TV4 và chưa chạy aggregation, nên tất cả mục này ở trạng thái chờ tích hợp.

# Bảng số liệu gửi TV2 cho KB5

Xem docs/evidence/tv3/kb5_cleaning_steps.csv: mỗi dòng có bộ dữ liệu, loại nguồn, giai đoạn, số còn lại, số bị loại và thời gian giai đoạn nếu phiên đó có ghi. Ô thời gian trống của bản cũ có nghĩa chưa được đo riêng, không phải bằng 0. Bảng gồm synthetic baseline và fixture mới; không có Kaggle. Không đặt tên hoặc coi bảng này là profiling_raw.json/profiling_clean.json chính thức. TV2 cần tạo hai báo cáo đó bằng job của mình và xác nhận các quy tắc mở rộng.
