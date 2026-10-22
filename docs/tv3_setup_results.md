# Kết quả thiết lập và kiểm thử TV3 ngày 18 tháng 10 năm 2026

Đây là hồ sơ thiết lập/benchmark đã có. Phiên hoàn thiện phần cá nhân tiếp theo
không chạy lại các benchmark; xem [gói bàn giao TV3 hiện tại](tv3_handoff.md) cho code,
kiểm thử điều kiện biên, Chương 2.2/5, phụ lục, demo và phần còn phụ thuộc.

Môi trường Spark trên Windows 11 đã chạy với hai worker. Ingest và cleaning
đã chạy thành công trên dữ liệu giả; pipeline toàn nhóm còn chờ mã nguồn TV2/TV4.
Mọi số liệu trong tài liệu này là **SYNTHETIC TEST ONLY**, không phải kết quả Kaggle.

## Repo và nguồn hướng dẫn

Thư mục `D:/Desktop/BigData`, nhánh `tv3/windows11-spark-setup`, nền `main`
tại `a86d31e796d7aeb7983a1d04b0b2cb9759ef3735`. Thư mục ban đầu trống.
Đã đọc [hướng dẫn cài đặt](D:/Desktop/BD_CaiDat.docx),
[hướng dẫn đồ án](D:/Desktop/BD_Project.docx) và [phân công](D:/Desktop/BD_PhanCong.docx).
File BD_CaiDat là hướng dẫn cài đặt được yêu cầu dưới tên 3_Huong_dan_cai_dat.docx.
Không commit, push hoặc merge. Không ghi đè dữ liệu cũ.

## Các bước đã xác nhận

| Bước | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Docker, Compose | PASS | Docker 29.8.2, Compose v5.6.0; version logs |
| WSL | PASS | docker-desktop chạy WSL2; kernel microsoft-standard-WSL2 |
| hello-world | PASS | hello_world.txt có Hello from Docker |
| Build | PASS | bigdata-spark:3.5.9; image_id.txt và python_dependencies.txt |
| Cụm Spark | PASS | 1 master, 2 worker ALIVE; tổng 4 core / 4096 MiB |
| Mount dùng chung | PASS | master và cả hai worker thấy cùng CSV ở /data |
| Ingest | PASS | 201995 dòng raw, ingest 7.4 giây (không tính count lại) |
| Cleaning | PASS | 197973 dòng; 31 phân vùng ngày, 31 file Parquet; 32.46 giây |
| Đối chiếu độc lập | PASS | Python/PyArrow so toàn bộ giá trị với quy tắc độc lập |
| Fixture lỗi | PASS | 14 dòng vào, 3 dòng hợp lệ ra |
| Chống ghi đè | PASS | Lần chạy lại bị chặn trước ingest; hash metrics giữ nguyên |
| Thiếu job / input / trộn tên file | PASS | Preflight chặn trước submit; logs guard_* |
| Python, Bash, Compose | PASS | py_compile, bash -n, compose config, git diff --check |
| KB1/KB2/KB6 | PASS | 30 ứng dụng thành công, 3 lượt mỗi cấu hình |
| KB3 hỗ trợ | PASS | 3 lượt mỗi định dạng, mỗi lượt đếm đúng 201995 dòng |
| Biểu đồ | PASS | 3 PNG có nhãn synthetic, đã mở kiểm tra hình |
| Profiling và KPI | CHƯA CHẠY | Thiếu job tương ứng; full mode thoát 3 trước ingest |

## Log chất lượng dữ liệu giả

| Giai đoạn | Số dòng | Số loại ở bước này |
| --- | ---: | ---: |
| Raw | 201995 | — |
| Sau bỏ trùng | 200000 | 1995 |
| Sau thời gian | 200000 | 0 |
| Sau loại sự kiện | 200000 | 0 |
| Sau giá | 197973 | 2027 |
| Sau ID và session | 197973 | 0 |
| Đọc lại Parquet | 197973 | 0 |

Generator trong tài liệu tạo 200000 bản ghi và chèn 1995 bản sao; vì vậy số dòng
CSV thực tế lớn hơn tham số 200000. Fixture riêng có số dòng từng bước
14 → 13 → 12 → 11 → 6 → 3; kiểm tra cả NaN/Inf, session trắng, thời gian lỗi,
brand trim/lower/unknown, cat_l1/cat_l2, UTC và phân vùng ngày.

Lần thử đầu tại `data/synthetic_tv3_20261018` tạo 6200 file nhỏ (200 task × 31 ngày),
chậm ở bước commit trên Windows bind mount. Đã chủ động dừng driver bằng SIGTERM,
exit 143; giữ lại dữ liệu/log và **không** tính lần này là pipeline thành công.
Sau khi repartition theo event_date, đã chạy lại pipeline từ đầu ở vùng mới
`data/synthetic_tv3_20261018_optimized`, dùng đúng CSV có cùng hash. Có _SUCCESS,
validation PASS và chỉ 31 file Parquet. Không suy ra mức speedup từ lần cũ chưa hoàn tất.

## Thực nghiệm

KB1/KB2/KB6 đã hoàn tất 30 ứng dụng, exit 0: 10 cấu hình × 3 lần.
CSV và JSONL có đúng 30 dòng kết quả, 30 application ID khác nhau.
Mỗi lượt 100% dữ liệu có đúng 197973 dòng và 93 nhóm.

| Kịch bản | Cấu hình | Trung bình giây | Độ lệch chuẩn mẫu | Số lần |
| --- | --- | ---: | ---: | ---: |
| KB1 | fraction 0.1 | 4.237 | 0.202 | 3 |
| KB1 | fraction 0.25 | 3.932 | 0.103 | 3 |
| KB1 | fraction 0.5 | 3.997 | 0.007 | 3 |
| KB1 | fraction 1.0 | 4.158 | 0.117 | 3 |
| KB2 | 1 core | 11.177 | 0.205 | 3 |
| KB2 | 2 core | 5.407 | 0.200 | 3 |
| KB2 | 4 core | 4.244 | 0.262 | 3 |
| KB6 | 8 shuffle partition | 4.293 | 0.121 | 3 |
| KB6 | 50 shuffle partition | 4.859 | 1.015 | 3 |
| KB6 | 200 shuffle partition | 4.251 | 0.031 | 3 |

Các giá trị lấy từ JSONL chưa làm tròn; benchmark.csv giữ 2 chữ số theo format TV1.
KB2 cho speedup khoảng 2.63 lần từ 1 lên 4 core trên mẫu giả này. Master JSON
trong lượt 1 core xác nhận ứng dụng chỉ được cấp 1 core, hai worker vẫn ALIVE.
KB1 không cho xu hướng tăng tuyến tính: sampling vẫn quét cùng bộ file và
dữ liệu quá nhỏ. KB6 bật AQE; không kết luận 200 partition là tối ưu chung.
Số đo action không gồm startup/schema discovery; OS cache không được làm lạnh.

KB3 được đo bổ sung bằng script kiểm thử riêng, lưu trong thư mục minh chứng,
không bổ sung thay job của TV2. Phạm vi: tạo DataFrame đọc với schema cố định
(CSV), hoặc đọc Parquet, rồi count; không tính startup/lấy schema ban đầu.
Đổi thứ tự CSV/Parquet giữa các lượt; không cache Spark, vẫn giữ OS cache.
Count có thể dùng metadata/column pruning; đây không phải phép đo đọc đầy đủ
mọi cột hay truy vấn tổng hợp nghiệp vụ.
Dung lượng chỉ tính file dữ liệu: CSV 27685503 byte; raw Parquet 12568019 byte,
tương đương CSV/Parquet khoảng 2.20 lần.

| KB3 | Trung bình giây | Độ lệch chuẩn mẫu | Số lượt |
| --- | ---: | ---: | ---: |
| CSV read + count | 1.655 | 0.828 | 3 |
| Parquet read + count | 1.799 | 0.749 | 3 |

Ở mẫu giả này chưa thấy Parquet đọc + count nhanh hơn; các khoảng biến động
chồng lấn lớn và lần đọc đầu tiên trong ứng dụng chịu chi phí khởi tạo.
Không sửa số đo theo kỳ vọng. Cần dữ liệu thật lớn hơn, nhiều lượt hơn và kiểm soát
cache/thứ tự đọc nếu muốn kết luận về tốc độ định dạng.

Ba hình trong vùng reports đã được mở và kiểm tra: tv3_cleaning_synthetic.png,
tv3_benchmarks_synthetic.png, tv3_storage_synthetic.png. File benchmark_validation.json
xác nhận 30 lượt, storage_validation.json xác nhận 6 phép đo count thành công.
Mọi biểu đồ ghi SYNTHETIC DATA ONLY.

## Thay đổi mã nguồn

TV3: thêm `jobs/02_cleaning.py`, sửa `scripts/run_pipeline.sh`, thêm kiểm thử độc lập
và script biểu đồ kiểm thử. Bổ sung tài liệu Windows/README và `.dockerignore`.
Sửa tối thiểu benchmark TV1 để force count+sum thật bằng collect bảng nhóm nhỏ,
ghi JSONL cấu hình/timing và truyền DATA_DIR xuyên suốt script thực nghiệm.
Dockerfile và docker-compose.yml giữ nguyên vì đã build/chạy đúng.

## Phần còn lại theo thành viên

| Thành viên | Còn chờ |
| --- | --- |
| TV2 | scripts/generate_data.py, jobs/01_profiling.py, jobs/make_sample.py, data contract |
| TV4 | jobs/03_aggregation.py, jobs/pandas_baseline.py, jobs/05_charts.py |
| TV2 + TV3 | KB5 chính thức với profiling_raw.json/profiling_clean.json; xác nhận quy tắc mở rộng của cleaning |
| TV2 | Bàn giao phép đo KB3 tái lập được và chạy trên dữ liệu thật với phạm vi đo thống nhất |
| TV4 | KPI, đối chiếu tổng doanh thu/số đơn và KB4 Pandas/Spark |
| TV3 | Chạy clean trên dữ liệu thật khi có; viết Ch.2.2, Ch.5 và phụ lục khi cần |

Không có các bảng agg hoặc biểu đồ KPI chính thức. Biểu đồ kiểm thử TV3 không
được coi là sản phẩm bàn giao của TV4. Chưa có dữ liệu Kaggle, chưa có kết quả
thực nghiệm dữ liệu thật.

## Người dùng cần làm khi chuyển sang dữ liệu thật

Đăng nhập [Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store),
tải và giải nén `2019-Oct.csv` vào
`D:/Desktop/BigData/data/real_oct_run01/landing/2019-Oct.csv`.
Chọn một vùng mới nếu tên đó đã có dữ liệu. Giữ nguyên các vùng synthetic.
Không cần cài thêm hay khởi động lại Windows cho lượt kiểm thử đã chạy.
Xem [lệnh PowerShell và cách tái lập](windows11_tv3.md).

## Vị trí minh chứng

`data/reports/tv3_setup_20261018/`: phiên bản, resource, master JSON, ảnh Master/Jobs/Stages/SQL,
pipeline_optimized.log, pipeline_fixture.log, validation logs, guard logs và session_manifest.json.
`data/synthetic_tv3_20261018_optimized/reports/`: source.json, ingest_log.csv,
cleaning_metrics.json, tv3_validation.json và kết quả benchmark.
`data/fixture_tv3_20261018/reports/`: cleaning_metrics.json và tv3_validation.json của fixture.
Các vùng này bị Git bỏ qua. Cụm được giữ chạy để người dùng mở UI;
khi không dùng, `docker compose down` giữ nguyên dữ liệu bind mount.

Ghi chú AI: Codex đọc ba tài liệu, thiết lập môi trường, hỗ trợ code TV3/sửa benchmark,
chạy các kiểm thử và lưu minh chứng. Các phần cần nhóm tự hiểu và xác nhận gồm
data contract, quy tắc chuẩn hóa, diễn giải benchmark và kết quả trên dữ liệu thật.
