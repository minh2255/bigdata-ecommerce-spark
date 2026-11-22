# Chương 9. Kết luận

Đồ án đã xây dựng và chạy hoàn chỉnh pipeline Spark `landing → raw → clean → agg` trên dữ liệu Kaggle tháng 10/2019. Các kết quả chính:

- **Làm sạch.** 42.448.764 dòng raw được làm sạch theo data contract v1.0 còn 42.349.872 dòng (loại 98.892 dòng). Máy 8 GB buộc chia thành 8 lát ngày; kết quả gộp khớp từng lát và tổng, và TV3 đã tự chạy lại ngày 22/11/2026 với cùng số liệu.
- **KPI.** Năm bảng agg được tạo trong 1 phút 21 giây và đối chiếu độc lập với clean: 14/14 kiểm tra đạt. Doanh thu tháng 229,9 triệu trên 742.773 đơn; điện tử chiếm 76,7% doanh thu, Apple 48,4%;
  tỷ lệ chuyển đổi theo phiên khoảng 6,8%.
- **Thực nghiệm.** KB3: Parquet nhỏ hơn CSV khoảng 3,87 lần và đọc nhanh hơn khoảng 17,7 lần. KB1: lọc theo ngày giúp thời gian tăng 1,7× khi dữ liệu tăng 11,9×. KB2: thêm core giúp đến 2 core rồi bão hòa trên một máy.
  KB6: 50 và 200 partition gần như bằng nhau. KB4: Pandas nhanh hơn Spark ở 1% mẫu (0,72 so với 2,45 s), Spark nhanh hơn ở 10% (3,03 so với 4,42 s), điểm giao giữa 5% và 10%.
  KB5: bảng số dòng loại ở từng bước giải thích toàn bộ mức giảm.
- **Quy trình.** Mỗi job từ chối ghi đè (ingest, cleaning, aggregation, make_sample), nên mỗi lần chạy dùng `DATA_DIR` riêng, giữ được kết quả cũ và so sánh được các lần chạy.

**Hạn chế.** Dữ liệu một tháng của một sàn; cụm giả lập trên một máy nên không đánh giá được độ trễ mạng hay chịu lỗi nhiều nút; mỗi cấu hình đo 3 lần, chưa kiểm định thống kê;
KB4 chưa đo ở 100% dữ liệu; chưa có ảnh Spark UI cho `03_aggregation.py`; chưa chạy tái lập trên máy thành viên khác. Phễu KPI đếm phiên theo từng loại sự kiện nên chỉ là ước lượng.

**Hướng phát triển.** Thêm tháng 11/2019 và đo lại KB4 ở 100%; chạy trên cụm nhiều máy với lưu trữ phân tán (HDFS hoặc object storage); thay `Parquet` cục bộ bằng bảng có quản lý phiên bản;
tạo phễu theo phiên lồng nhau; đưa bảng `agg/*` vào công cụ dashboard (Power BI, Superset) cho nhóm Analytics.

Pipeline đáp ứng yêu cầu của giai đoạn Storage → Processing: dữ liệu sạch và các bảng KPI sẵn sàng cho giai đoạn Analytics tiếp theo, với đầy đủ minh chứng và giới hạn được ghi rõ.
