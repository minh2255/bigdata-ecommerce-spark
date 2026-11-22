# Tóm tắt

Báo cáo trình bày một pipeline Apache Spark làm sạch, chuẩn hóa và tổng hợp dữ liệu hành vi khách hàng thương mại điện tử: bộ Kaggle
*eCommerce behavior data from multi category store*, tháng 10/2019, 42.448.764 dòng (5,67 GB CSV). Pipeline gồm bốn tầng `landing → raw → clean → agg`
lưu bằng Parquet, chạy trên cụm Docker 1 master + 2 worker và mỗi lần chạy dùng một vùng `DATA_DIR` riêng, không ghi đè.

Cleaning theo data contract v1.0 giữ lại 42.349.872 dòng (loại 98.892 dòng). Máy 8 GB không cleaning nguyên khối được nên dữ liệu được chia thành 8 lát ngày; kết quả gộp
khớp số liệu ban đầu. Từ tầng clean, năm bảng KPI (ngày, danh mục, thương hiệu, phễu, giờ) được tính trong 1 phút 21 giây và đối chiếu độc lập: 14/14 kiểm tra đạt.
Trong tháng, tổng doanh thu là 229,9 triệu trên 742.773 đơn; ngành điện tử chiếm 76,7% doanh thu, Apple chiếm 48,4%, và tỷ lệ chuyển đổi theo phiên (purchase/view) khoảng 6,8%.

Sáu thực nghiệm cho thấy: Parquet nhỏ hơn CSV khoảng 3,87 lần về dung lượng và đọc nhanh hơn khoảng 17,7 lần (KB3); thêm core giúp đến 2 core rồi bão hòa trên một máy (KB2);
phân vùng theo ngày giúp truy vấn theo ngày chỉ tăng 1,7 lần khi dữ liệu tăng 11,9 lần (KB1); 50 và 200 shuffle partition cho kết quả gần nhau (KB6); Pandas nhanh hơn Spark ở mẫu 1% nhưng
Spark nhanh hơn ở 10% (KB4). Các kết luận chỉ áp dụng cho một máy, mỗi cấu hình đo 3 lần, và chưa suy ra được cho cụm nhiều máy.

**Từ khóa:** Apache Spark, Parquet, Data Lake, làm sạch dữ liệu, KPI, thương mại điện tử.
