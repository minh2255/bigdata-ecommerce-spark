# Sửa đổi hỗ trợ benchmark TV1 cần nhóm trưởng review

Phần này được giữ từ phiên thiết lập trước và tách thành commit riêng khi chuẩn bị
push nhánh TV3 ngày 19 tháng 10 năm 2026. Không thuộc sản phẩm chính được phân công
cho TV3, không thay thế trách nhiệm thực nghiệm/báo cáo của TV1 hoặc trực quan KPI TV4.
Phiên rà soát phát hành không chạy lại benchmark.

## File và lý do

| File | Thay đổi hỗ trợ | Điều cần TV1 xác nhận |
| --- | --- | --- |
| jobs/04_benchmark.py | Collect bảng nhóm ngày/loại sự kiện để materialize count và sum, thay vì chỉ count số nhóm; giữ CSV cũ và thêm JSONL cấu hình/timing | Chốt phép đo cần so sánh, giới hạn số nhóm nếu mở rộng dữ liệu và phạm vi thời gian |
| scripts/run_benchmarks.sh | Truyền DATA_DIR vào container, dùng mảng Bash có quote, set -euo pipefail và ghi nhãn lần lặp | Kiểm tra tương thích với các nhánh khác và đường dẫn dữ liệu dùng cho thực nghiệm chính thức |
| scripts/plot_tv3_checks.py | Tiện ích lịch sử vẽ kiểm thử/benchmark synthetic, yêu cầu nhãn nguồn và đủ lượt lặp | Đây không phải jobs/05_charts.py của TV4; không coi là biểu đồ KPI bàn giao |

Truy vấn benchmark tổng hợp count và sum(price) theo event_date/event_type. Nếu chỉ
gọi count() để đếm nhóm, kết quả n/revenue có thể không cần được tính trong kế hoạch.
Collect ở đây chỉ lấy bảng nhóm nhỏ (93 nhóm trong synthetic tháng 10 đã đo), không
collect toàn bộ sự kiện. JSONL ghi application ID, fraction, core limit, shuffle/AQE,
số dòng mẫu, tổng giá và thời gian chưa làm tròn để truy vết.

Tên revenue trong truy vấn mẫu là tổng price của mọi loại sự kiện, không phải doanh
thu purchase của nghiệp vụ. Bổ sung JSONL dùng tên price_sum_all_event_types để chỉ
rõ điểm này. Phạm vi thời gian action không gồm startup và khám phá schema; không
so trực tiếp với Pandas nếu phạm vi đo hoặc mẫu đầu vào khác nhau.

## Kết quả đã có và giới hạn

Hồ sơ lịch sử trong docs/tv3_setup_results.md ghi 30 ứng dụng KB1/KB2/KB6 thành công
trên synthetic, mỗi cấu hình 3 lần. CSV/JSONL/ảnh benchmark và code hỗ trợ được đối
chiếu hash trong docs/evidence/tv3/preserved_prior_work.json trước khi đóng gói; không
bị sửa hoặc chạy lại trong phiên hoàn thiện cá nhân/phát hành.

KB1 vẫn sample từ cùng bộ file, không phải bốn bộ dữ liệu vật lý độc lập. KB6 bật
AQE nên cấu hình shuffle không đồng nghĩa số partition cuối. Mẫu nhỏ và OS cache
ảnh hưởng số đo. Đây là minh chứng kiểm thử, chưa là kết quả Kaggle hay kết luận
tổng quát về Spark/Pandas. Nhóm trưởng cần review riêng commit này trước khi quyết
định tích hợp, điều chỉnh hoặc chuyển về nhánh phụ trách TV1.

## Phân biệt với gói chính TV3

Commit chính TV3 chứa cleaning, validation/preflight/pipeline, kiểm thử, tài liệu,
Word và minh chứng chọn lọc. Pipeline TV3 không gọi benchmark hay tiện ích biểu đồ
lịch sử, nên có thể review phần chính độc lập với hai file benchmark của TV1.
Nhánh chỉ được push để bàn giao; không tự merge vào main.
