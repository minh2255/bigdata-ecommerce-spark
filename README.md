# Làm sạch, chuẩn hóa và tổng hợp dữ liệu hành vi khách hàng TMĐT bằng Apache Spark

Đồ án học phần Nhập môn Dữ liệu lớn. Pipeline: `landing/ → raw/ → clean/ → agg/` (Storage → Processing).

**Gói cá nhân TV3 hiện tại:** [bàn giao, checklist, báo cáo, kiểm thử và demo](docs/tv3_handoff.md).
Mode cá nhân: `--ingest-clean` (ingest + cleaning), `--clean-only` (chỉ cleaning từ raw).
`--available` là alias của `--ingest-clean`; không chạy profiling/aggregation.
Mỗi lần gọi script tự lưu log; dùng DATA_DIR mới và DATA_KIND đúng nguồn để giữ dữ liệu cũ.

- Dữ liệu: Kaggle *eCommerce behavior data from multi category store* (file `2019-Oct.csv`, ~5 GB).
  Không đưa file dữ liệu lên Git.
- Công nghệ: Apache Spark 3.5 (PySpark, Spark SQL), Parquet, Docker Compose.

## Cấu trúc
```
Dockerfile, docker-compose.yml   # cụm Spark 1 master + 2 worker
jobs/        # code Spark (00_ingest ... 05_charts)
scripts/     # generate_data.py, run_pipeline.sh, run_benchmarks.sh
docs/        # sơ đồ kiến trúc, data contract
data/        # Data Lake (không lên Git): landing, raw, clean, agg, samples, reports
```

## Chạy nhanh (Lưu ý: Master UI ở http://localhost:8080 (máy TV1 đổi sang 9090 do trùng cổng).)

**Trạng thái 15/11/2026:** `origin/main` đã có contract v1.0, generator, `01_profiling.py`,
`03_aggregation.py` (TV4), `make_sample.py` và `slice_raw_by_day.py`. Nhánh TV3 đã rebase lên `origin/main` `014777a`
(16/11/2026) nên có đủ các file này; `--full` trên nhánh này chưa được TV3 chạy thử. TV2 đã chạy `--full` thành công trên synthetic
(`docs/evidence/tv2/m1_20261110_231427/`) và chạy cleaning trên Kaggle thật: raw 42.448.764 → clean
42.349.872 dòng, 2552.5 giây (`docs/evidence/tv2/cleaning_metrics_merged.json`).
Dùng `--quality-check` cho ingest → profiling raw → cleaning → profiling clean.
Kết quả synthetic và lệnh Windows: [biên bản TV3](docs/tv3_run_20261027.md).
**Máy RAM 8 GB:** cleaning nguyên khối 42,4 triệu dòng bị hết bộ nhớ executor, TV2 phải chia 8 lát theo ngày
bằng `jobs/slice_raw_by_day.py`, chạy `02_cleaning.py` từng lát rồi gộp; xem
[phụ lục chạy Windows](docs/tv3/phu_luc_chay_windows.md) và Ch.5 mục 5.9 ([ch05](docs/tv3/ch05_trien_khai.md)).
Chưa có xác nhận của TV4 nhận bàn giao clean, ảnh Spark UI lúc cleaning thật và chạy tái lập trên máy khác.
Chi tiết kiểm thử Windows và cách dùng vùng dữ liệu riêng: [docs/windows11_tv3.md](docs/windows11_tv3.md).

```bash
# 1. Khởi động cụm Spark
docker compose up -d --build
docker compose ps                     # 3 container running
# Mở http://localhost:8080 -> Alive Workers: 2, 4 cores

# 2. Dữ liệu (chọn 1)
# A. Thật: đặt 2019-Oct.csv vào landing của DATA_DIR riêng (máy 8 GB: cleaning theo lát)
# B. Giả: đặt DATA_DIR mới và DATA_KIND=synthetic trước khi sinh dữ liệu:
docker exec spark-master python3 /opt/scripts/generate_data.py 200000

# 3. Chạy pipeline
bash scripts/run_pipeline.sh --quality-check
# --full cần jobs/03_aggregation.py của TV4 (có trên origin/main).
# Khi chỉ cần, chỉ chạy phạm vi ingest + cleaning:
# bash scripts/run_pipeline.sh --ingest-clean

# 4. Thực nghiệm KB1, KB2, KB6 (cần data/clean/events)
bash scripts/run_benchmarks.sh all

# 5. Tắt cụm
docker compose down
```
Windows: dùng Git Bash để chạy `bash scripts/...`. Lỗi thường gặp: xem file Hướng dẫn cài đặt, mục 10.
Trong PowerShell, dùng `& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --ingest-clean`.
Không dùng `C:/Windows/system32/bash.exe` khi máy chỉ có distro Docker Desktop.
Pipeline từ chối chạy lại vào vùng đã có đầu ra. Đặt `DATA_DIR` trỏ tới một vùng mới
trong `/data` để giữ nguyên dữ liệu cũ, ví dụ `$env:DATA_DIR='/data/real_run_01'` trong PowerShell.

## Quy tắc làm việc nhóm
Mỗi người một branch, tạo Pull Request, TV1 review rồi merge vào `main`. Không commit thư mục `data/`.
