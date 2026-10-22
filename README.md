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

**Trạng thái mã nguồn:** nhánh nền hiện chỉ có ingest và benchmark của TV1.
Nhánh TV3 bổ sung cleaning và hoàn thiện pipeline. Còn chờ TV2 bàn giao
`generate_data.py`, `01_profiling.py`, `make_sample.py`, data contract;
TV4 bàn giao `03_aggregation.py`, `pandas_baseline.py`, `05_charts.py`.
Lệnh pipeline đầy đủ sẽ báo thiếu file trước khi chạy bất kỳ job nào.
Chi tiết kiểm thử Windows và cách dùng vùng dữ liệu riêng: [docs/windows11_tv3.md](docs/windows11_tv3.md).

```bash
# 1. Khởi động cụm Spark
docker compose up -d --build
docker compose ps                     # 3 container running
# Mở http://localhost:8080 -> Alive Workers: 2, 4 cores

# 2. Dữ liệu (chọn 1)
# A. Thật: đặt 2019-Oct.csv vào data/landing/
# B. Giả (chỉ khi TV2 đã bàn giao script):
docker exec spark-master python3 /opt/scripts/generate_data.py 200000

# 3. Chạy pipeline
bash scripts/run_pipeline.sh --full
# Khi chưa đủ job, chỉ chạy phạm vi ingest + cleaning:
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
