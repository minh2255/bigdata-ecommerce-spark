# Chương 8 (phần TV1 và TV4). Bài học từ hạ tầng, benchmark và KPI

## 8.A Bài học từ hạ tầng và benchmark (TV1)

**Số đo đầu tiên thường là ngoại lệ.** Ở KB1 (`sample` 10%), lần đầu 83,46 s so với 44,32 và 52,56 s ở hai lần sau; ở KB2 (1 core) lần đầu 72,42 s so với 47,14 và 45,20 s. Một lần chạy
đơn lẻ có thể sai lệch rất nhiều, nên mỗi cấu hình phải chạy ít nhất 3 lần và báo cả trung vị. Nguyên nhân (cache hệ điều hành lạnh) mới là giả thuyết, chưa kiểm chứng.

**Kết quả "phẳng" cần được giải thích, không khoe.** `df.sample()` cho thời gian gần như không đổi khi dữ liệu tăng 4 lần vì vẫn đọc gần toàn bộ file Parquet; chỉ khi lọc theo ngày (tận dụng
phân vùng `event_date`) thời gian mới tăng theo dữ liệu (1,7× khi dữ liệu tăng 11,9×). Cách cắt mẫu quyết định thí nghiệm đo cái gì.

**Thêm core không luôn nhanh hơn.** 1 → 2 core nhanh hơn 1,28–1,52×, nhưng 2 → 4 không cải thiện, vì bốn core cùng dùng một ổ đĩa và RAM của một máy. Cụm giả lập trên một máy không thay cho cụm thật.

**Tham số mặc định đã khá tốt với truy vấn nhỏ.** 50 và 200 shuffle partition cho cùng kết quả; AQE gộp partition khi chạy nên con số cấu hình không phải số partition thực tế.

**Tài nguyên quyết định thiết kế.** Máy 8 GB buộc phải chia cleaning thành 8 lát ngày; Docker cấp khoảng 7,6 GiB nên mỗi worker chỉ 2 GB. Cấu hình hạ tầng phải ghi cùng kết quả đo.

**Hạn chế.** Chỉ 3 lần mỗi cấu hình; hai sơ đồ draw.io chưa được xuất thành ảnh; chưa chụp đủ ảnh Spark UI. Phần này do TV4 tổng hợp từ Ch.4 và Ch.6 của TV1, cần TV1 đọc lại và xác nhận.

## 8.B Bài học từ KPI và KB4 (TV4)

**Đối chiếu độc lập phát hiện lỗi mà "job chạy xong" không phát hiện.** Job `03_aggregation.py` thành công không chứng minh KPI đúng. Việc tính lại bằng pandas từ clean cho 14/14 khớp
(tổng sự kiện 42.349.872, doanh thu 229.933.212,63, 742.773 đơn). Chính script kiểm tra lại cho thấy một giới hạn khác: nó bị hệ điều hành kết thúc (exit 137) khi đọc nguyên 42 triệu dòng vào pandas,
và chỉ chạy được sau khi đọc từng ngày với cột cần thiết. Đây là ví dụ nhỏ cho chính lập luận Volume của đề.

**Một con số trên synthetic không thay cho dữ liệu thật.** Bản KB4 đầu chạy trên 20.000 dòng cho kết quả Pandas nhanh hơn Spark hơn 15 lần ở mọi tỷ lệ; trên dữ liệu thật, Pandas chỉ nhanh hơn ở 1% và
Spark nhanh hơn từ 10% (và có thể từ 5% nếu bỏ lần chạy đầu). Kết luận về điểm giao chỉ có nghĩa khi đo đúng quy mô.

**Sự nhất quán của quy ước.** `03_aggregation.py` ghi `overwrite` trong khi các job khác từ chối ghi đè; đã sửa để cả chuỗi pipeline có chung một quy tắc: muốn chạy lại phải dùng `DATA_DIR` mới.
Nhờ vậy kết quả cũ không bị mất và các lần chạy so sánh được.

**Đọc KPI cần đọc giới hạn của định nghĩa.** Phễu đếm phiên riêng theo từng loại sự kiện nên số phiên mua (629.560) lớn hơn số phiên có cart (573.019); nhãn `unknown` chiếm 23,3% số đơn theo danh mục;
giờ là UTC. Tỷ lệ chuyển đổi 6,8% chỉ là ước lượng gần đúng. Số cart tăng gấp 2–3 lần ở một số giai đoạn trong tháng mà dữ liệu không cho biết nguyên nhân.

**Hạn chế còn lại.** KB4 mới đo ở 1–10% (3 lần mỗi cấu hình), chưa đo ở 100% và chưa thử Pandas hết RAM; cụm Spark và Pandas cùng chạy trên một máy; chưa có ảnh Spark UI của `03_aggregation.py`.

## 8.C Tổng hợp thảo luận chung

Ba thông điệp chung xuất hiện ở cả bốn phần của nhóm:

1. **Chạy xong chưa phải đã đúng.** TV3 yêu cầu đọc lại dữ liệu, đối chiếu số dòng và schema; TV2 đối chiếu số lỗi theo thứ tự làm sạch để không cộng lặp; TV4 tính lại KPI độc lập. Mỗi tầng cần một phép kiểm tra không dùng lại chính code của nó.
2. **Giới hạn tài nguyên là một phần của kết quả.** Máy 8 GB buộc chia lát ngày (TV2, TV3); cụm một máy làm KB2 bão hòa ở 2 core (TV1); Pandas và Spark tranh chấp cùng máy (TV4). Cấu hình phải được báo cáo cùng số đo.
3. **Phân biệt số đo, giả thuyết và suy luận.** Hai bản profiling cho biết hiệu số tổng nhưng chưa tách theo bước (TV2); nguyên nhân bão hòa core hay số cart tăng mới là giả thuyết (TV1, TV4). Báo cáo ghi rõ chỗ nào đã đo và chỗ nào chưa.

Hạn chế chung: dữ liệu một tháng của một sàn, cụm giả lập trên một máy, mỗi cấu hình đo 3 lần, chưa chạy tái lập trên máy khác và chưa có ảnh Spark UI cho một số bước. Hướng mở rộng:
đo KB4 ở 100% dữ liệu; thêm tháng 11/2019; đo trên cụm nhiều máy hoặc lưu trữ phân tán; thay phễu đếm riêng bằng phễu theo phiên lồng nhau.

## 8.D Ghi chú sử dụng AI (TV4)

Claude Code hỗ trợ TV4: chạy `03_aggregation.py`, `make_sample.py` và KB4 trong Docker, sửa `03_aggregation.py` và `check_agg_kpi.py`, vẽ lại biểu đồ, soạn nháp Tóm tắt, Ch.1, Ch.6 (KB4), Ch.7, Ch.8 (phần TV1 và TV4), Ch.9
và viết script ghép báo cáo. Số liệu được lấy từ các file Parquet, CSV, JSON do lần chạy sinh ra và đối chiếu lại trong chương. Phần Ch.8 của TV1 là nháp tổng hợp từ tài liệu của TV1, cần TV1 xác nhận.
Các thành viên vẫn phải tự đọc lại mã nguồn, báo cáo và giải thích được toàn bộ pipeline trước buổi bảo vệ; họ tên, MSSV, tỷ lệ đóng góp do nhóm điền.
