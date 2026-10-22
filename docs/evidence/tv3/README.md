# Danh mục minh chứng TV3

Các file nhỏ trong thư mục này được chọn từ log/ảnh/JSON thật. Không chứa CSV đầu vào,
Parquet, dataset Kaggle, token hay toàn bộ thư mục data. manifest.json ghi nguồn,
mục đích, dung lượng và SHA256 của 41 file được chọn ban đầu; các bản kiểm tra cuối
như snapshot Master, kiểm tra tài liệu và hash bảo toàn được ghi riêng.
Git giữ nguyên byte của thư mục minh chứng theo .gitattributes để checkout trên
Windows/Linux không làm đổi CRLF/LF và sai hash. Khoảng trắng cuối dòng do Spark
phát ra được giữ trong log thật; chỉ file log minh chứng được miễn kiểm tra whitespace.

| Nhóm file | Nội dung và giới hạn |
| --- | --- |
| integration_summary.json | 26 bước ghi nhận của suite, gồm một suite 7 unit tests và các fixture/guard Spark thật; PASS trên máy hiện tại |
| unit_control_flow.log | 7 unit tests với mock Docker cố ý lỗi; xác nhận full order tới chỗ dừng, mã 42 và quote; không chứng minh full pipeline thành công |
| mixed_* | 14 raw → 13 dedup → 12 thời gian → 11 event → 6 giá → 3 định danh; kiểm tra giá trị/schema/UTC/guard |
| empty_* | Raw 0, clean 0; SUCCESS_EMPTY và Parquet còn schema |
| all-invalid_* | Raw 2, sau timestamp 1, sau giá 0; readback 0, không tạo ngày giả |
| valid-repeat_* | Ba sự kiện chung session, có ngày UTC khác và user_id âm; giữ đủ 3 theo luật hiện tại |
| *_pipeline_selected.log | Trích dòng RUN/INGEST/CLEAN/PREFLIGHT/DONE/EXIT từ log thật; log đầy đủ còn ở data/reports/tv3_handoff_20261018 |
| *_overwrite_guard.log | Preflight thật trả 4; runner kiểm tra hash các file clean và metrics không đổi |
| full_missing_jobs.log | Full mode thật trả 3 trước ingest vì thiếu 01_profiling.py và 03_aggregation.py |
| missing-input.log / mixed-input.log / bad-header.log | Preflight thật chặn thiếu CSV, trộn tên nguồn hoặc sai header trước ingest |
| fixture_guard_final.log | Bốn fixture vẫn khớp sau guard provenance; không ghi đè report; từ chối nguồn không gắn synthetic và tập trên 10000 dòng |
| actual_schema_rejection_summary.json / actual_spark_schema_failure.log | Job Spark thật từ chối raw.price string thay vì double, shell giữ exit 1, không tạo clean/metrics; tách với mock exit 42 |
| initial_git_bash_path_failure.log | Lượt tích hợp đầu thất bại do đường dẫn Compose Git Bash; đã sửa, không tính lượt này thành công |
| baseline_synthetic_cleaning_metrics.json | Báo cáo synthetic cũ 201995 raw → 200000 dedup → 197973 clean, tổng 32.46 s; chưa có thời gian riêng từng bước |
| baseline_historical_independent_validation.json | Đối chiếu toàn bộ giá trị synthetic đã chạy ở phiên trước, bằng bản checker cũ; checker hiện tại đã có giới hạn |
| baseline_current_distributed_validation.json | Validator Spark mới: 197973 clean, 0 vi phạm, 31 ngày, schema/UTC đúng; không phải đối chiếu từng dòng raw-to-clean |
| kb5_cleaning_steps.csv | Số liệu hỗ trợ TV2; synthetic + fixture, không phải profiling_raw/clean chính thức; thời gian trống nghĩa chưa có đo riêng |
| baseline_cleaning_synthetic.png | Biểu đồ chất lượng synthetic lịch sử; không chạy benchmark/vẽ KPI mới |
| spark_master_2_workers.png | Ảnh lịch sử Master có 2 worker ALIVE; xem snapshot JSON riêng để biết trạng thái lúc bàn giao |
| cleaning_jobs.png / cleaning_stages.png / cleaning_sql.png | Ảnh thật trong lần cleaning đầu sau đó bị dừng vì nhiều file nhỏ; KHÔNG phải bằng chứng lần đó thành công |
| master_handoff_snapshot.json | API Master tại lúc đóng gói: worker/state/core/memory; không giả lập screenshot |
| word_qa.json | Word 12 trang, Ch.2.2 3 trang/Ch.5 4 trang, chữ cỡ 12 và chữ/viền bảng đen; kiểm tra đủ 12 ảnh trang |
| preserved_prior_work.json | 37 hash code/benchmark/ảnh và Parquet baseline so với hồ sơ trước, tất cả giữ nguyên |

## Quy tắc diễn giải

Tất cả dữ liệu xử lý ở đây là SYNTHETIC TEST ONLY. Không có Kaggle thật. Một số
file baseline là lịch sử trước khi thêm metadata/guard mới, nên luôn ghi riêng
phiên bản và phạm vi. Không cộng thời gian từng giai đoạn như thể đó là các thí nghiệm
độc lập. Không suy test cùng máy thành kiểm chứng máy thành viên khác.

Đối chiếu cả hàng chỉ dành cho fixture nhỏ; script chặn trên 10000 dòng trước khi
nạp danh sách. Validator Spark cho tập lớn chỉ nhận scalar từ phép giảm phân tán.
Không tạo profiling_raw.json/profiling_clean.json hoặc KPI giả.

## Kết quả và log đầy đủ

Suite thành công: data/reports/tv3_handoff_20261018/20261018_233715_9e89b2/summary.json.
Lượt lỗi giữ lại: data/reports/tv3_handoff_20261018/20261018_233703_57a409/.
Kiểm tra baseline: data/reports/tv3_handoff_20261018/baseline_distributed_validation.log.
Word QA: data/reports/tv3_handoff_20261018/word_qa/final/.
Các vùng data bị Git bỏ qua; gói được chọn này có thể review mà không cần nộp dataset.
