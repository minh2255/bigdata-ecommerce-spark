# Làm sạch, chuẩn hóa và tổng hợp dữ liệu hành vi khách hàng TMĐT bằng Apache Spark

Đồ án học phần Nhập môn Dữ liệu lớn. Pipeline: `landing/ → raw/ → clean/ → agg/` (Storage → Processing).

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

## Chạy nhanh
```bash
# 1. Khởi động cụm Spark
docker compose up -d --build
docker compose ps                     # 3 container running
# Mở http://localhost:8080 -> Alive Workers: 2, 4 cores

# 2. Dữ liệu (chọn 1)
# A. Thật: đặt 2019-Oct.csv vào data/landing/
# B. Giả:
docker exec spark-master python3 /opt/scripts/generate_data.py 200000

# 3. Chạy pipeline
bash scripts/run_pipeline.sh

# 4. Thực nghiệm KB1, KB2, KB6 (cần data/clean/events)
bash scripts/run_benchmarks.sh all

# 5. Tắt cụm
docker compose down
```
Windows: dùng Git Bash để chạy `bash scripts/...`. Lỗi thường gặp: xem file Hướng dẫn cài đặt, mục 10.

## Quy tắc làm việc nhóm
Mỗi người một branch, tạo Pull Request, TV1 review rồi merge vào `main`. Không commit thư mục `data/`.
