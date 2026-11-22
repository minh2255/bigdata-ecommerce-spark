# Làm sạch, chuẩn hóa và tổng hợp dữ liệu hành vi khách hàng TMĐT bằng Apache Spark

Đồ án học phần Nhập môn Dữ liệu lớn. Pipeline: `landing/ → raw/ → clean/ → agg/` (Storage → Processing).

- **Dữ liệu:** Kaggle *eCommerce behavior data from multi category store*, file `2019-Oct.csv` (~5,67 GB, 42.448.764 dòng).
  Không đưa file dữ liệu lên Git (`data/` bị `.gitignore`).
- **Công nghệ:** Apache Spark 3.5.9 (PySpark, Spark SQL), Parquet, Docker Compose (1 master + 2 worker).

## Tài liệu theo thành viên

| Thành viên | Phần việc | Tài liệu |
|---|---|---|
| TV1 (nhóm trưởng) | Hạ tầng, ingest, benchmark KB1/KB2/KB6, Ch.4, Ch.6 | [Ch.4 Thiết kế hệ thống](docs/tv1/ch04_thiet_ke_he_thong.md), [Ch.6 KB1/KB2/KB6](docs/tv1/ch06_kb1_kb2_kb6.md), [minh chứng](docs/evidence/tv1/) |
| TV2 | Data contract, profiling, samples, KB3/KB5, Ch.2.1, Ch.3 | [Data contract v1.0](docs/data_contract.md), [Ch.3](docs/tv2/ch03_du_lieu.md), [Ch.6 KB3/KB5](docs/tv2/ch06_kb3_kb5.md), [bàn giao M4](docs/tv2/m4_handoff.md) |
| TV3 | Cleaning, pipeline, kiểm thử, Ch.2.2, Ch.5 | [Gói bàn giao TV3](docs/tv3_handoff.md), [Ch.5](docs/tv3/ch05_trien_khai.md), [phụ lục chạy Windows](docs/tv3/phu_luc_chay_windows.md), [demo 3 phút](docs/tv3/demo_3_phut.md) |
| TV4 | Aggregation, đối chiếu KPI, KB4, biểu đồ, Tóm tắt, Ch.1, Ch.7, Ch.9, ghép báo cáo | [KB4](docs/tv4/ch_kpi_kb4.md), [Ch.7](docs/tv4/ch07_ket_qua_demo.md), [Ch.1](docs/tv4/ch01_gioi_thieu.md), [Ch.8 TV1+TV4](docs/tv4/ch08_bai_hoc_tv1_tv4.md), [Ch.9](docs/tv4/ch09_ket_luan.md), [minh chứng thật](docs/evidence/tv4/real/), [báo cáo ghép (PDF)](docs/tv4/BaoCao_DoAn_BigData.pdf) |

## Cấu trúc

```
Dockerfile, docker-compose.yml   # cụm Spark 1 master + 2 worker
jobs/        # code Spark: 00_ingest, 01_profiling, 02_cleaning, 03_aggregation, 04_benchmark, 05_charts,
             #   make_sample, slice_raw_by_day, pandas_baseline, kb3_*, kb4_*, validate_cleaning
scripts/     # run_pipeline.sh, run_benchmarks.sh, generate_data.py, kiểm tra (check_*, compare_truth, preflight)
tests/       # kiểm thử pipeline, preflight, profiling, cleaning
docs/        # data contract, báo cáo từng chương theo thành viên (tv1..tv4), minh chứng (evidence/)
data/        # Data Lake (không lên Git): landing, raw, clean, agg, samples, reports
```

Sơ đồ kiến trúc và luồng dữ liệu: [Ch.4](docs/tv1/ch04_thiet_ke_he_thong.md) (nguồn draw.io ở `docs/tv1/diagrams/`).

## Trạng thái (cập nhật 22/11/2026)

- Đã merge vào `main`: hạ tầng và ingest, contract + profiling, cleaning + pipeline, aggregation + KB4 (PR #1–#10).
- Dữ liệu Kaggle thật: cleaning chạy ở máy TV2 theo 8 lát ngày (raw 42.448.764 → clean 42.349.872 dòng, 2552.5 giây;
  [`cleaning_metrics_merged.json`](docs/evidence/tv2/cleaning_metrics_merged.json)); KB1/KB2/KB6 chạy 18/11/2026 trên cùng tầng clean.
- `--full` đã chạy exit 0 trên synthetic. Máy RAM 8 GB không cleaning nguyên khối được, xem
  [phụ lục Windows](docs/tv3/phu_luc_chay_windows.md) và Ch.5 mục 5.9.
- KPI (`agg/`) và KB4 đã chạy trên **dữ liệu Kaggle thật** ngày 22/11/2026 (42.349.872 dòng clean): 14/14 kiểm tra KPI đạt, KB4 ở mẫu 1%/5%/10% ([Ch.7](docs/tv4/ch07_ket_qua_demo.md), [KB4](docs/tv4/ch_kpi_kb4.md)). `03_aggregation.py` nay từ chối ghi đè như các job khác.
- Báo cáo ghép: `python docs/tv4/build_report.py` rồi `powershell -File docs/tv4/export_pdf.ps1` (cần Microsoft Word); đầu ra `docs/tv4/BaoCao_DoAn_BigData.docx/.pdf`.
- Còn chờ: chạy tái lập trên máy thành viên khác, ảnh Spark UI (kể cả `03_aggregation.py`), tập demo, KB4 ở 100% dữ liệu, điền họ tên/MSSV/tỷ lệ đóng góp vào báo cáo.

## Chạy nhanh

Master UI ở http://localhost:8080 (máy TV1 đổi sang 9090 do trùng cổng).

```bash
# 1. Khởi động cụm Spark
docker compose up -d --build
docker compose ps                     # 3 container running; Alive Workers: 2

# 2. Dữ liệu (chọn 1)
# A. Thật: đặt 2019-Oct.csv vào landing của một DATA_DIR riêng (máy 8 GB: cleaning theo lát, xem phụ lục)
# B. Giả: đặt DATA_DIR mới và DATA_KIND=synthetic, rồi sinh dữ liệu:
docker exec spark-master python3 /opt/scripts/generate_data.py 200000

# 3. Chạy pipeline (mỗi lần dùng DATA_DIR mới; pipeline từ chối ghi đè)
bash scripts/run_pipeline.sh --quality-check   # ingest → profiling raw → cleaning → profiling clean
bash scripts/run_pipeline.sh --full            # thêm aggregation
bash scripts/run_pipeline.sh --ingest-clean    # chỉ ingest + cleaning; --clean-only: chỉ cleaning từ raw

# 4. Thực nghiệm (cần clean/events)
bash scripts/run_benchmarks.sh all             # KB1, KB2, KB6
# KB4: make_sample.py → pandas_baseline.py + kb4_spark_baseline.py → 05_charts.py (lệnh trong docs/tv4/ch_kpi_kb4.md)

# 5. Tắt cụm
docker compose down
```

Windows: dùng Git Bash để chạy `bash scripts/...`. Trong PowerShell:
`& 'C:/Program Files/Git/bin/bash.exe' scripts/run_pipeline.sh --ingest-clean`.
Không dùng `C:/Windows/system32/bash.exe` khi máy chỉ có distro Docker Desktop.
Đặt `DATA_DIR` tới vùng mới trong `/data`, ví dụ `$env:DATA_DIR='/data/real_run_01'` (và `DATA_KIND=real` hoặc `synthetic`).

Mã thoát của `run_pipeline.sh`: 2 tham số sai, 3 thiếu file job, 4 lỗi môi trường/dữ liệu/đầu ra đã tồn tại; mã khác là mã lỗi của `spark-submit`.
Chi tiết kiểm thử và lỗi thường gặp trên Windows: [docs/windows11_tv3.md](docs/windows11_tv3.md).

Kiểm thử không cần cụm Spark (mock, preflight):

```bash
python -m unittest tests.test_pipeline_control tests.test_preflight
```

## Quy tắc làm việc nhóm

Mỗi người một branch, tạo Pull Request, TV1 review rồi merge vào `main`. Không commit thư mục `data/`.
