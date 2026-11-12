# Đối chiếu số liệu báo cáo TV2 sau sửa — 12/11/2026

Phạm vi: `docs/tv2/ch02_1_bigdata.md`, `ch03_du_lieu.md`, `ch06_kb3_kb5.md`, `phu_luc_schema.md`, `ch08_bai_hoc_ai.md`. Đây là lượt xử lý các phát hiện trong `audit_5b_review_20261111.md` và kiểm tra lại bản hiện tại; giữ nguyên audit cũ để tra lịch sử. Không chạy lại Spark, không sửa dữ liệu hoặc báo cáo JSON/CSV nguồn.

| Nhóm phát hiện | Cách xử lý và nguồn |
| --- | --- |
| Thời gian cleaning | Dùng nguyên `cleaning_metrics_merged.json:cleaning_seconds_total = 2552.5` giây ở Ch.3, Ch.6, Ch.8; bỏ quy đổi phút làm tròn thêm. |
| Benchmark KB3 | Bảng ba lần chạy, mean, dung lượng và speedup lấy nguyên `kb3.csv`; ingest `173.46` giây lấy từ `ingest_log.csv`. Giữ hệ số nguồn, không tính lại từ mean đã làm tròn. |
| Cấu hình KB3 | Đối chiếu `kb3_env.json`: executor/driver `2g`, 8 CPU, `mem_total_gb_in_container = 4.8`; code KB3 chia theo lũy thừa hai nên ghi GiB. Không gán cấu hình này cho lần OOM hoặc demo. |
| Profiling và cleaning | Ch.3/Ch.6 giữ số đếm raw/clean, các bước lọc và hiệu số. Tổng giảm 98.892; giá không dương raw 68.673 nhưng bước lọc giá loại 68.670 do dedup trước đó. Các tổng từng bước khớp tổng 8 lát. |
| Tỷ lệ | Bỏ phần trăm tự làm tròn; giữ số đếm hoặc tỷ lệ thập phân đã có trong profiling nguồn. Phụ lục dùng `unknown_ratio` toàn tháng và tập thử. |
| Bảng chéo thiếu nguồn | Bỏ các số 68.523 view/150 cart giá 0, hai session đều cart và 36.242 danh mục sâu 3 cấp khỏi báo cáo. Chưa xác minh các chi tiết này; không tạo nguồn thay thế hoặc khẳng định chúng sai. |
| Suy luận theo event_type/doanh thu | Giữ mức giảm view/cart/purchase qua toàn bộ cleaning. Bỏ định lượng trùng riêng từng loại và kết luận nguyên nhân giảm purchase hoặc ảnh hưởng doanh thu khi chưa có bảng chéo/tổng tiền nguồn. |
| Số lần OOM/mã lỗi | Chỉ dẫn ghi chú OOM của metrics gộp; bỏ số lần lỗi, mã lỗi và RAM executor của lần lỗi do thiếu log lịch sử tương ứng. |
| Dung lượng phụ lục | Giữ byte nguyên snapshot: landing 400957999, raw 98256658, clean 155044118; bỏ MiB quy đổi thêm. Đã đối chiếu lại kích thước file hiện có, loại dotfiles; nói rõ tổng cây thư mục. |
| Ví dụ và schema phụ lục | Đối chiếu snapshot `audit_5b_sources_20261111.json`: hai dòng CSV, ví dụ raw/clean, schema 9/14 cột và 31 ngày toàn tháng. Giữ ví dụ số/UUID; thu hẹp phát biểu parse `nan` theo quan sát M1, không khái quát mọi cách viết Infinity. |
| Bất biến | JSON clean toàn tháng có 7 bất biến và all_pass=true; duplicate_rows được báo riêng. Kiểm tra ngày so với raw trong code chỉ thêm khi có profiling raw cùng DATA_DIR. Không gọi 0 dòng trùng sau chuẩn hóa là ràng buộc chung. |
| Tập thử và synthetic | Tập thử dùng `audit_5b_sample3m/`; so mốc ngày, counts và tỷ lệ. M1 dùng `m1_20261110_231427/`; compare_truth có hai đối chiếu exact và ba near, không mô tả cả năm là bằng tuyệt đối. |
| Diễn giải | Ch.2.1 giới hạn nhận định Pandas theo bằng chứng TV2; Ch.3 phân biệt số sự kiện với phễu theo phiên. Ch.8 ghi đúng vai trò AI và chưa thay việc sinh viên tự kiểm tra. |

`verify.ps1` kiểm tra các bảng KB3/KB5 với nguồn, tổng 8 lát, bất biến, byte thư mục, tỷ lệ và dữ liệu profiling bản evidence so với bản trong data. JSON được so theo nội dung sau parse vì định dạng/xuống dòng có thể khác; không khẳng định hash file gốc giống nhau. Kết quả và SHA256 của năm Markdown cuối nằm trong `checks.json`. Chạy lại từ PowerShell bằng `& docs/evidence/tv2/report_numbers_recheck_20261112/verify.ps1`; lệnh chỉ cập nhật `checks.json` của lượt kiểm tra này.

Các đối chiếu tự động kiểm tra những nhóm số đã chỉ định; bảng trên ghi phần rà soát theo ngữ cảnh. Những chi tiết thiếu nguồn được loại khỏi kết luận, không được coi là kết quả đã xác minh. Các số hiệu chương, phiên bản, tham số code và ví dụ không phải chỉ số thực nghiệm. Kịch bản demo có số nói làm tròn để trình bày; checklist/bản nháp bàn giao và roadmap cũ không thuộc năm chương đã chốt này.

Việc sinh viên đọc lại, điền khai báo theo thực tế, chụp ảnh, diễn tập, tự ôn và TV1/TV4 review/nhận bàn giao vẫn cần xác nhận riêng.
