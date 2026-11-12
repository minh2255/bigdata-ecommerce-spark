# Chương 8 (phần TV2). Bài học và ghi chú sử dụng AI

## 8.1. Chia công việc theo giới hạn bộ nhớ

Theo ghi chú trong [cleaning_metrics_merged.json](../evidence/tv2/cleaning_metrics_merged.json), cleaning toàn bộ 42.448.764 dòng trên máy RAM 8 GB gặp lỗi hết bộ nhớ executor (OOM). Nhóm chia dữ liệu raw thành 8 lát theo ngày, chạy cùng logic cleaning cho từng lát rồi gộp kết quả. Trường `cleaning_seconds_total` ghi tổng thời gian **2552.5 giây**, thu được 42.349.872 dòng clean.

Cách chia này bảo toàn kết quả dedup vì các dòng raw trùng hoàn toàn có cùng `event_time`, nên luôn nằm trong cùng một lát. Các khoảng ngày bao phủ toàn bộ nguồn và không chồng lấn. Bài học là chia khối lượng xử lý phù hợp với tài nguyên, đồng thời đối chiếu tổng số dòng đầu vào và đầu ra của các lát để kiểm tra kết quả gộp.

## 8.2. Kiểm tra NaN và null sau khi đọc CSV

Trong lần chạy dữ liệu giả M1, [generator](../evidence/tv2/m1_20261110_231427/generate_data_truth.json) chèn 218 giá lỗi bằng chuỗi `nan`. Sau khi ingest đọc CSV với schema cố định, [profiling raw](../evidence/tv2/m1_20261110_231427/profiling_raw.json) ghi nhận 220 giá null và 0 giá NaN. Chuỗi `nan` đã thành null khi đọc; số null còn bao gồm các bản trùng.

Vì vậy, kiểm tra chất lượng phải dựa trên giá trị sau khi parse và theo dõi riêng null, NaN, vô hạn, giá không dương. Chỉ nhìn bộ đếm NaN bằng 0 sẽ bỏ sót lỗi giá. Sau cleaning, cả bốn bộ đếm này đều về 0 trong [profiling clean M1](../evidence/tv2/m1_20261110_231427/profiling_clean.json).

## 8.3. Đếm lỗi theo thứ tự làm sạch

Một dòng có thể đồng thời vi phạm nhiều quy tắc. Trên dữ liệu toàn tháng, [profiling raw](../evidence/tv2/profiling_raw.json) đếm được 68.673 dòng có giá không dương, nhưng bước lọc giá chỉ loại 68.670 dòng vì 3 dòng đã bị loại ở bước dedup trước đó.

Do đó, số lỗi ở raw mô tả chất lượng đầu vào; hiệu số trước và sau từng bước cho biết số dòng thực sự bị loại tại bước đó. Đối chiếu theo thứ tự giúp giải thích được toàn bộ mức giảm từ 42.448.764 dòng raw xuống 42.349.872 dòng clean, tránh cộng lặp các nhóm lỗi giao nhau.

## 8.4. Kiểm chứng giả thuyết về dòng trùng ở cart

Hai bản profiling toàn tháng cho thấy số sự kiện `cart` giảm từ 926.516 xuống 898.292 dòng, tức giảm 28.224 dòng qua toàn bộ cleaning. Hiệu số này cho biết mức giảm tổng cộng, chưa tách được số dòng bị loại do dedup và do từng quy tắc lọc.

Giả thuyết dòng trùng tập trung ở cart cần phép đếm trực tiếp theo `event_type` trước và ngay sau dedup; bộ evidence hiện chưa có bảng chéo này. Bài học là phân biệt kết quả đo trực tiếp với suy luận, đồng thời xác định phép kiểm tra cụ thể cần có để xác nhận suy luận đó.

## 8.5. Dùng contract để thống nhất giữa các thành viên

[Data contract](../data_contract.md) giúp TV2, TV3 và TV4 thống nhất cách profiling, cleaning và tính KPI: dedup trên raw trước chuẩn hóa, dùng thời gian UTC, giữ giá hữu hạn dương và xử lý dữ liệu thiếu bằng nhãn `unknown`. Nhờ cùng quy ước, số liệu kiểm tra của TV2 có thể đối chiếu với các bước làm sạch của TV3 và được TV4 dùng khi tổng hợp.

Một chi tiết cần thống nhất là `category_code` gốc vẫn có thể null trong clean, còn `cat_l1`, `cat_l2` được gán `unknown`. Contract làm rõ ý nghĩa từng trường, giúp ba thành viên dùng cùng cách hiểu khi viết code, đặt nhãn biểu đồ và giải thích kết quả.

## 8.6. Ghi chú sử dụng AI

Nhóm sử dụng **Claude Code** để lập roadmap và review; **ChatGPT/Codex** để hỗ trợ viết code, chạy kiểm chứng và soạn nháp báo cáo. Số liệu thực nghiệm được lấy từ JSON, CSV và log của các lần chạy; các công cụ AI hỗ trợ xử lý và diễn giải những nguồn này.

Các phần đã được kiểm chứng trong quá trình thực hiện, với sự hỗ trợ của ChatGPT/Codex, gồm: đối chiếu roadmap với mã nguồn và bằng chứng trong repo; chạy pipeline synthetic `--full` và kiểm tra kết quả profiling raw/clean; đối chiếu lỗi do generator chèn với cleaning bằng `compare_truth.py`; kiểm tra số dòng samples qua pandas, metadata Parquet và CSV; đối chiếu số liệu KB3/KB5 với JSON/CSV nguồn. Bản rà soát `docs/evidence/tv2/audit_5b_review_20261111.md` ghi các phát hiện ở bản nháp cũ. Lượt sửa ngày 12/11/2026 đã chuẩn hóa số liệu trong Ch.2.1, Ch.3, Ch.6, phụ lục schema và Ch.8 theo nguồn; bỏ các chi tiết thiếu bảng chéo nguồn và giới hạn các kết luận suy ra từ hiệu số. Bằng chứng đối chiếu sau sửa nằm trong `docs/evidence/tv2/report_numbers_recheck_20261112/`; đây là kiểm tra tài liệu với nguồn đã lưu, không phải lần chạy Spark mới. Sinh viên vẫn cần tự đọc lại mã nguồn, báo cáo và nguồn tương ứng, đồng thời tự diễn tập demo và ôn phần giải thích pipeline trước khi bảo vệ.
