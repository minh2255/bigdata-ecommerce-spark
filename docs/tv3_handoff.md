# Gói bàn giao cá nhân TV3

Phần cá nhân có thể làm độc lập đã được hoàn thiện trong repo hiện tại: cleaning,
script điều phối, kiểm thử, nội dung báo cáo, hướng dẫn, minh chứng và kịch bản demo.
Contract TV2 v1.0 và profiling đã merge; mode --quality-check tích hợp TV2–TV3.
Cập nhật 15/11/2026: TV2 đã chạy cleaning trên Kaggle thật theo 8 lát ngày (raw 42.448.764 → clean 42.349.872, 2552.5 giây;
nguồn `docs/evidence/tv2/cleaning_metrics_merged.json`) và `03_aggregation.py` của TV4 đã có trên `origin/main`.
Chưa có xác nhận TV4 nhận bàn giao, ảnh Spark UI lúc cleaning thật hoặc chạy trên máy thành viên khác.
Kết quả hiện tại, lệnh và minh chứng: [biên bản 27/10/2026](tv3_run_20261027.md).

Nhánh hiện tại: `codex/tv3-contract-quality`, tạo từ `origin/main` `1249075`.
Fetch GitHub ngày 27/10/2026 xác nhận PR #1 và #2 đã merge, TV4 chưa có aggregation.
Workspace trước khi sửa sạch; không có AGENTS.md trong checkout. Không commit,
push, PR hoặc merge trong phiên này. Không chạy lại benchmark.

Các mục kết quả 18–19/10 bên dưới là lịch sử; biên bản mới có số liệu lần chạy hiện tại.

## Phạm vi các commit bàn giao

| Nhóm | File và sản phẩm | Trách nhiệm review |
| --- | --- | --- |
| Sản phẩm chính TV3 | Cleaning, pipeline/preflight, validator, fixture/tests, Ch.2.2/5, phụ lục/Word, demo, giao diện clean và minh chứng chọn lọc | Review theo contract TV2 v1.0, giao diện với TV4 và kiểm thử tái lập |
| Hỗ trợ benchmark TV1, commit riêng | jobs/04_benchmark.py, scripts/run_benchmarks.sh và tiện ích lịch sử scripts/plot_tv3_checks.py | Nhóm trưởng/TV1 review riêng, không tính là phần chính TV3 |

Xem [bản giải thích hỗ trợ benchmark TV1](tv1_benchmark_review.md) để biết lý do,
phạm vi phép đo và các điểm cần chốt trước tích hợp. Lịch sử kết quả được giữ nguyên;
phiên phát hành chỉ rà soát và kiểm tra nhẹ, không chạy lại benchmark/Spark pipeline.

## Checklist từ phân công

| Yêu cầu TV3 | Trạng thái | Kết quả hoặc điều kiện còn chờ |
| --- | --- | --- |
| Bảy nhóm quy tắc cleaning | Đã kiểm chứng | UTC, dedup raw, event, giá/định danh, brand/category, cột dẫn xuất, Parquet |
| Log số dòng/số loại/thời gian | Đã hoàn thiện và kiểm chứng | stdout + cleaning_metrics.json; stage_seconds; cleaning_schema.json |
| Ghi dữ liệu và đọc lại | Đã kiểm chứng | Nonempty giữ repartition theo ngày; zero rows có schema và SUCCESS_EMPTY |
| Pipeline cá nhân | Đã kiểm chứng | ingest-clean, clean-only; log tự tạo; DATA_DIR có khoảng trắng |
| Full pipeline | Đã chạy ở TV2 trên synthetic; nhánh này chưa cập nhật | TV2 chạy `--full` exit 0 (`docs/evidence/tv2/m1_20261110_231427/run_summary.json`); nhánh TV3 tạo từ `1249075` chưa có `03_aggregation.py` nên `--full` ở đây vẫn exit 3 đến khi cập nhật từ `origin/main` |
| Kiểm thử độc lập | Đã kiểm chứng | Fixture bị chặn trên 10000 dòng; so toàn bộ hàng và multiplicity, không coi session là khóa |
| Kiểm tra tập lớn | Đã kiểm chứng trên synthetic | Validator Spark: 197973 dòng, 0 vi phạm, schema và UTC đúng; chỉ trả scalar |
| Rỗng/toàn bộ bị loại | Đã kiểm chứng | Hai trường hợp khác nhau đều đọc lại 0 với schema đúng |
| Guard/lỗi submit/config | Đã kiểm chứng theo phạm vi | Preflight thật, 7 unit tests mock lỗi và một job Spark thật bị từ chối schema; không fake job sản phẩm |
| Chương 2.2 khoảng 3 trang | Đã viết | Markdown, nguồn Spark 3.5.9; Word trang 1–3 sau render |
| Chương 5 khoảng 4 trang | Đã viết | Markdown; Word trang 4–7 sau render |
| Phụ lục và đóng góp Chương 8 | Đã viết | Lệnh Windows, input/output, lỗi, bài học/hạn chế và AI |
| Demo khoảng 3 phút | Đã chuẩn bị | Kịch bản, lệnh, Q&A; người dùng cần tự tập và trình bày |
| Bàn giao TV4 và hỗ trợ KB5 | Đã chuẩn bị, TV4 chưa xác nhận | Schema/UTC, đường dẫn clean thật `/data/real_oct_full/clean/events` (gộp 8 lát); profiling chính thức do TV2 tạo |
| Cleaning Kaggle | Đã chạy bởi TV2, theo 8 lát | 42.448.764 → 42.349.872 dòng, 31 thư mục event_date, `all_pass=true` từng lát; TV3 chưa chạy lại trên máy mình. Fixture guard 12 byte không được tính |
| Contract chính thức | Đã có v1.0 từ PR #2 | NaN/Inf, session trắng, blank→unknown; không áp ID dương/UUID; `02_cleaning.py` giữ nguyên logic |
| Chạy máy thành viên khác | Chưa thực hiện | Checklist để trống; không dùng test cùng máy để xác nhận thay |

## Các tài liệu sẵn sàng ghép báo cáo

- [Chương 2.2](tv3/ch02_2_spark.md): Spark/PySpark/SQL, driver/executor, lazy evaluation, shuffle/partition.
- [Chương 5](tv3/ch05_trien_khai.md): môi trường, cleaning, dữ liệu rỗng, pipeline và giới hạn tích hợp.
- [Phụ lục chạy Windows](tv3/phu_luc_chay_windows.md): lệnh PowerShell/Git Bash, kiểm tra, exit code và tiếp tục với Kaggle.
- [Chương 8 và ghi chú AI](tv3/ch08_bai_hoc_ai.md): nội dung hoàn chỉnh cùng trách nhiệm cần người thực hiện xác nhận.
- [Bản Word TV3](tv3/TV3_BaoCao.docx): chữ/bảng đen, Times New Roman 12 pt thống nhất; bản Markdown là nguồn dễ review.
- [Nguồn chính thức](tv3/nguon_chinh_thuc.md), [demo và Q&A](tv3/demo_3_phut.md), [schema bàn giao TV4/KB5](tv3/ban_giao_clean_tv4.md), [checklist máy khác](tv3/checklist_tai_lap.md).

## Những sửa đổi code trong phiên cá nhân

`jobs/02_cleaning.py` giữ đường ghi nonempty đã đạt, bổ sung empty schema-bearing Parquet,
kiểm tra schema raw, số loại/thời gian từng bước, application ID và metadata contract v1.0.
`scripts/run_pipeline.sh` có mode quality-check cùng các mode cũ, kiểm tra host/mount/config/input,
log host riêng mỗi lần, giữ mã lỗi submit và không ghi đè đầu ra. Helper
`scripts/pipeline_preflight.py` kiểm tra provenance/header/path/đầu ra.

`scripts/check_cleaning.py` giới hạn fixture và so cả hàng bằng multiset thay vì
dùng session làm khóa. `jobs/validate_cleaning.py` dùng phép giảm phân tán cho tập lớn,
không collect/toPandas toàn bộ. `tests/test_pipeline_control.py` kiểm tra điều khiển
shell bằng mock lỗi; `tests/run_tv3_integration.py` chạy bốn fixture mới trên cụm thật.
`tests/test_cleaning_rejection.py` bổ sung kiểm tra job Spark thật từ chối price sai kiểu,
pipeline trả 1 và không tạo clean; không phải lỗi submit mô phỏng.
Không thêm job profiling/aggregation giả vào jobs.

## Phân biệt sửa đổi benchmark TV1 đã có

Giữ nguyên `jobs/04_benchmark.py` và `scripts/run_benchmarks.sh` từ phiên trước.
Lý do sửa đã có: `.count()` số nhóm có thể làm phép count/sum trong agg bị prune;
collect bảng nhóm nhỏ buộc materialize tổng hợp, JSONL ghi cấu hình/timing, script
truyền DATA_DIR. Đây là thay đổi hỗ trợ TV1 cần họ review, không tính thành sản phẩm
chính TV3. Không sửa tiếp, không xóa, không chạy lại. Các biểu đồ/KB3 hỗ trợ phiên cũ
cũng được giữ làm lịch sử, không tiếp tục thực nghiệm hay làm phần TV4.
Các file hỗ trợ và giải thích được gom vào commit riêng để nhóm trưởng review;
commit chính TV3 không phụ thuộc benchmark để chạy cleaning/pipeline.

## Kiểm chứng thực tế và minh chứng

Xem [danh mục minh chứng](evidence/tv3/README.md). Phiên tích hợp thành công
`20261018_233715_9e89b2` chạy bốn fixture mới, đường dẫn dữ liệu có khoảng trắng,
đối chiếu giá trị và validation Spark; thử ghi lại bị chặn, hash dữ liệu/metrics giữ nguyên.
Bảy unit tests dùng sandbox có tên repo chứa khoảng trắng; submit failure trong unit
test là mock exit 42 và không mô phỏng full success. Kiểm tra bổ sung
`schema_rejection_4c07ecbfac` submit job cleaning thật với raw.price sai kiểu:
job từ chối schema, pipeline truyền nguyên exit 1, không có clean/metrics mới.
Full mode thật hiện exit 3 vì thiếu job. Mã 4 dùng cho preflight/config/input/đầu ra.

Lần tích hợp đầu của phiên này gặp lỗi Compose hiểu sai đường dẫn Git Bash
`/d/...` khi MSYS_NO_PATHCONV bật. Đã sửa dùng đường dẫn config tương đối sau cd repo;
giữ log lượt lỗi `20261018_233703_57a409`, không tính lượt đó thành công.
Baseline synthetic cũ vẫn có 201995 raw → 200000 dedup → 197973 clean, 31 ngày.
Validator Spark mới đọc baseline đúng schema/UTC, 0 dòng vi phạm. Các benchmark cũ
không thay đổi hash và không chạy lại.

## Công việc còn phụ thuộc và lệnh tiếp theo

TV2 đã bàn giao contract/profiling và chạy cleaning/profiling trên Kaggle thật; aggregation của TV4 đã có trên `origin/main`.
TV4 cần xác nhận nhận schema/UTC và đối chiếu KPI trên clean thật. Người dùng cần tự tập demo,
điền thông tin cá nhân/phân công đóng góp, chụp ảnh minh chứng và nhờ người khác thực hiện checklist.

Dữ liệu thật đã ở `data/real_oct_run01/landing/2019-Oct.csv` trên máy TV2 (theo `TV2_Plan_Roadmap.md`).
Chỉ khi chạy lại trên máy khác mới cần đặt CSV vào landing của một DATA_DIR mới và kiểm tra header/dung lượng/tài nguyên
theo phụ lục. Máy 8 GB không chạy nguyên khối được; dùng cách chia lát trong phụ lục. Máy đủ RAM, trong PowerShell:

```powershell
Set-Location D:/Desktop/BigData
$env:DATA_DIR='/data/real_oct_run01'
$env:DATA_KIND='real'
& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --quality-check
```

Nếu vùng đã có đầu ra, dùng DATA_DIR mới và chuẩn bị landing tương ứng, không ghi đè.
Không yêu cầu mật khẩu/token trong chat. Dữ liệu/kết quả do TV3 tự chạy trong gói này là
synthetic hoặc fixture; clean Kaggle thật do TV2 tạo (máy TV2), chưa được TV3 chạy lại hay TV4 xác nhận. Cụm giữ chạy; khi người dùng không dùng
nữa, `docker compose down` giữ dữ liệu mount.
