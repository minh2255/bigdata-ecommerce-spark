# Chương 1. Giới thiệu

## 1.1 Bối cảnh và bài toán

Các sàn thương mại điện tử ghi lại từng lượt xem sản phẩm, thêm vào giỏ và mua hàng của người dùng. Một tháng dữ liệu của một sàn
(bộ *eCommerce behavior data from multi category store* trên Kaggle, file `2019-Oct.csv`) đã gồm 42.448.764 dòng và khoảng 5,67 GB CSV.
Dữ liệu này có dòng trùng, giá không hợp lệ, thiếu `category_code` và `brand`, nên không thể dùng ngay cho phân tích kinh doanh.

Đề tài: **làm sạch, chuẩn hóa và tổng hợp dữ liệu hành vi khách hàng thương mại điện tử quy mô lớn bằng Apache Spark**. Nhóm phụ trách giai đoạn
Storage → Processing: nhận CSV đã nằm trong vùng lưu trữ và trả về dữ liệu sạch (`clean/events`, Parquet phân vùng theo ngày) cùng các bảng KPI (`agg/*`)
để nhóm Analytics hoặc Presentation dùng tiếp.

## 1.2 Vì sao cần Big Data

Đề yêu cầu chỉ ra ít nhất hai đặc trưng; báo cáo dùng ba lập luận, mỗi lập luận có số liệu ở các chương sau:

- **Volume.** 42,4 triệu dòng, 5,67 GB CSV. Đọc và `sum(price)` trên CSV mất khoảng 56 giây trong khi Parquet mất khoảng 3 giây (Ch.6, KB3). Với bộ dữ liệu 7 tháng, khối lượng tăng nhiều lần.
- **Veracity.** Dòng trùng hoàn toàn, giá không dương (68.673 dòng), thiếu category/brand; sau làm sạch còn 42.349.872 dòng (Ch.3, Ch.6 KB5).
- **Nhu cầu xử lý phân tán.** Một truy vấn tổng hợp chạy song song trên hai worker; đi từ 1 lên 2 core giảm thời gian rõ rệt (KB2). Khi dữ liệu đủ lớn Spark vượt Pandas
  trên một máy (KB4: điểm giao giữa 5% và 10% dữ liệu), và cleaning nguyên khối trên máy 8 GB hết bộ nhớ nên phải chia theo ngày (Ch.5).

## 1.3 Mục tiêu và phạm vi

Mục tiêu: (1) xây pipeline `landing → raw → clean → agg` chạy được, không ghi đè và tái lập được; (2) làm sạch theo data contract v1.0 và chứng minh bằng profiling trước/sau;
(3) tổng hợp năm bảng KPI và đối chiếu độc lập với clean; (4) đo sáu thực nghiệm (KB1–KB6) trên dữ liệu thật; (5) rút bài học và giới hạn.

Phạm vi: một tháng dữ liệu (tháng 10/2019), cụm Spark giả lập 1 master + 2 worker bằng Docker trên một máy Windows 11. Ngoài phạm vi: ingestion theo thời gian thực
(Kafka), dashboard, lưu trữ phân tán (HDFS/S3) và chạy nhiều máy.

## 1.4 Cấu trúc báo cáo

Ch.2 trình bày nền tảng (Big Data, Data Lake, Parquet, Spark); Ch.3 mô tả dữ liệu và yêu cầu làm sạch; Ch.4 thiết kế hệ thống; Ch.5 triển khai cleaning và pipeline;
Ch.6 sáu thực nghiệm KB1–KB6; Ch.7 kết quả KPI và demo; Ch.8 thảo luận và bài học; Ch.9 kết luận. Phụ lục: schema, hướng dẫn chạy trên Windows, phân công và ghi chú dùng AI.

## 1.5 Phân công

| Thành viên | Phần việc chính |
|---|---|
| TV1 (nhóm trưởng) | Hạ tầng Docker/Spark, ingest, benchmark KB1/KB2/KB6, Ch.4 |
| TV2 | Data contract, profiling, samples, KB3/KB5, Ch.2.1, Ch.3 |
| TV3 | Cleaning, pipeline, kiểm thử, Ch.2.2, Ch.5 |
| TV4 | Aggregation, đối chiếu KPI, KB4, biểu đồ, Tóm tắt, Ch.1, Ch.7, Ch.9, ghép báo cáo |

Tỷ lệ đóng góp và họ tên/MSSV do nhóm điền ở phần phụ lục phân công.
