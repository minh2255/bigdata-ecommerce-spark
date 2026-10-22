# 2.1 Big Data, Data Lake và định dạng Parquet

## 2.1.1 Big Data và mô hình 5V

Big Data là cách gọi các tập dữ liệu mà việc lưu trữ, xử lý hoặc phân tích bằng một chương trình chạy trên một máy với công cụ thông thường trở nên khó khăn hoặc không thực tế. Tính chất này thường được mô tả bằng năm chữ V. Đồ án dùng mô hình đó để đối chiếu với bộ dữ liệu *eCommerce behavior data from multi category store* (Kaggle), tháng 10/2019.

| V | Ý nghĩa | Biểu hiện trong dữ liệu của đồ án |
| --- | --- | --- |
| Volume (khối lượng) | Dung lượng và số bản ghi lớn | File `2019-Oct.csv` có 5.668.612.855 byte (khoảng 5,7 GB) và 42.448.764 dòng sự kiện |
| Velocity (tốc độ) | Dữ liệu sinh ra liên tục, cần xử lý kịp thời | Mỗi lượt xem, thêm giỏ hàng, mua hàng là một sự kiện có dấu thời gian đến từng giây; trên hệ thống thật dữ liệu đến liên tục. Đồ án xử lý theo lô (batch) nên chỉ mô phỏng đặc trưng này |
| Variety (đa dạng) | Nhiều dạng và cấu trúc dữ liệu | Dữ liệu ở dạng bán cấu trúc (CSV): có cột số, cột chuỗi, danh mục dạng cây (`electronics.smartphone`) và nhiều giá trị thiếu |
| Veracity (độ tin cậy) | Chất lượng và độ chính xác | Có dòng trùng, giá bằng 0, `user_session` rỗng, `brand` và `category_code` thiếu; đây là lý do cần bước profiling và làm sạch |
| Value (giá trị) | Giá trị rút ra được | Phễu mua hàng (view → cart → purchase), doanh thu theo ngày/giờ, thương hiệu và danh mục nổi bật |

Hai chữ V có ý nghĩa trực tiếp nhất với đồ án là Volume và Veracity. Volume giải thích vì sao cần Spark thay vì Pandas trên một máy (thực nghiệm KB4). Veracity giải thích vì sao phải có data contract và bước làm sạch trước khi tính KPI. Ngược lại, Velocity chỉ được mô phỏng chứ không được kiểm chứng: đồ án không xử lý luồng thời gian thực.

Cần phân biệt "lớn" theo nghĩa tương đối. Với một máy 8 GB RAM, file khoảng 5,7 GB không thể nạp vào bộ nhớ Pandas cùng các bước xử lý phụ, dù với một trung tâm dữ liệu thì đây chỉ là tập dữ liệu nhỏ. Đồ án chạy trên cụm Docker gồm một master và hai worker trên cùng một máy, vì vậy kết quả minh họa cách phân chia công việc chứ không chứng minh khả năng mở rộng ngang trên nhiều máy.

<!-- page -->

## 2.1.2 Data Lake và các tầng dữ liệu

Data Lake là nơi lưu trữ dữ liệu ở dạng gần với nguyên gốc, chưa cần quyết định trước cách phân tích. Khác với kho dữ liệu (data warehouse) yêu cầu dữ liệu đã được mô hình hóa trước khi ghi (schema-on-write), data lake cho phép ghi trước và áp schema khi đọc (schema-on-read). Lợi ích là giữ được dữ liệu gốc để làm lại khi luật thay đổi; rủi ro là nếu không có quy ước, kho dữ liệu dễ biến thành "đầm lầy" nơi không ai biết cột nào đáng tin.

Đồ án tổ chức data lake trên hệ thống file theo bốn tầng. Mỗi tầng ghi vào một thư mục riêng dưới `DATA_DIR`, và một lần chạy dùng `DATA_DIR` mới để không ghi đè kết quả cũ.

| Tầng | Thư mục | Nội dung | Người/Job tạo |
| --- | --- | --- | --- |
| landing | `landing/*.csv` | File CSV tải về, giữ nguyên | Tải từ Kaggle |
| raw | `raw/events` | Cùng dữ liệu đó ở dạng Parquet, schema cố định 9 cột, **không sửa nội dung** | `00_ingest.py` |
| clean | `clean/events` | Dữ liệu đã làm sạch theo data contract, phân vùng theo `event_date` | `02_cleaning.py` |
| agg | `agg/` | Bảng tổng hợp nhỏ phục vụ KPI và biểu đồ | `03_aggregation.py` |

Báo cáo chất lượng (`profiling_raw.json`, `profiling_clean.json`, `cleaning_metrics.json`) nằm ở `reports/`. Việc tách raw và clean có hai lý do. Thứ nhất, raw là bản đối chứng: mọi số liệu "trước làm sạch" của KB5 đều lấy từ đây. Thứ hai, nếu luật làm sạch thay đổi (ví dụ contract nâng từ 1.0 lên 1.1), chỉ cần chạy lại từ raw mà không phải đọc lại CSV 5,7 GB.

Quy tắc của mỗi tầng được ghi trong `docs/data_contract.md`. Điểm cần nhớ là clean **không** loại thêm dòng vì ID không dương hay `user_session` không đúng UUID, vì kiểm tra trên dữ liệu thật không thấy vi phạm nào; đồng thời các dòng thiếu `brand` hoặc `category_code` không bị loại mà được gán nhãn `unknown`, bởi chúng chiếm một phần lớn dữ liệu.

<!-- page -->

## 2.1.3 Định dạng Parquet

Parquet là định dạng lưu trữ theo cột (columnar) mã nguồn mở, được dùng rộng rãi với Spark. Ở định dạng theo dòng như CSV, các giá trị của cùng một dòng nằm cạnh nhau; ở Parquet, các giá trị của cùng một cột nằm cạnh nhau trong từng khối (row group). Bốn đặc điểm sau là lý do đồ án chọn Parquet cho raw và clean:

1. **Lưu theo cột.** Truy vấn chỉ cần vài cột (ví dụ `price` và `event_type`) thì Spark chỉ đọc các cột đó, bỏ qua phần còn lại. CSV bắt buộc đọc và tách toàn bộ dòng.
2. **Nén.** Các giá trị cùng cột có kiểu và phân bố giống nhau nên nén hiệu quả hơn; cột có ít giá trị khác nhau như `event_type` được mã hóa từ điển rất gọn. File Parquet vì vậy thường nhỏ hơn đáng kể so với CSV cùng dữ liệu.
3. **Giữ schema.** Tên cột và kiểu dữ liệu nằm trong file. Khi đọc không phải khai báo lại hay suy luận kiểu, tránh việc quét file hai lần như `inferSchema` trên CSV.
4. **Hỗ trợ phân vùng và lọc sớm.** Dữ liệu clean được chia thư mục theo `event_date=YYYY-MM-DD/`, nên truy vấn theo ngày chỉ đọc đúng thư mục cần thiết; thống kê min/max trong file giúp bỏ qua khối không liên quan.

Đổi lại, Parquet không đọc được bằng trình soạn thảo văn bản, và ghi một file Parquet tốn tài nguyên hơn ghi CSV. Với pipeline phân tích "ghi một lần, đọc nhiều lần" của đồ án, đó là đánh đổi chấp nhận được.

Thực nghiệm KB3 kiểm chứng các nhận định trên bằng số đo thật: so dung lượng thư mục `landing/` với `raw/events`, và so thời gian `count()` cùng thời gian tính tổng một cột khi đọc CSV (có schema cố định) với khi đọc Parquet, mỗi phép đo chạy ba lần. Kết quả và biểu đồ nằm ở phần KB3 của Chương 6; chương này chỉ nêu cơ sở lý thuyết và không trích số liệu khi chưa có file `kb3.csv` tương ứng.

## 2.1.4 Liên hệ với các chương sau

Chương 3 mô tả chi tiết schema và kết quả profiling dữ liệu raw. Chương 2.2 (TV3) giải thích Spark xử lý các tầng này như thế nào. Chương 6 trình bày KB3 (CSV so với Parquet) và KB5 (chất lượng trước và sau làm sạch). Phụ lục có schema raw và schema clean đầy đủ.
