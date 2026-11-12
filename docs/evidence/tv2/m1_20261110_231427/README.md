# M1 — Synthetic full pipeline, 10/11/2026

Commit được chạy: `bab9f3149a605b16d354b8c6098f8825a26ef46a` trên `main`.
`jobs/03_aggregation.py` của TV4 đã có; không còn bị chặn bởi thiếu source.

## Lần chạy

- DATA_DIR mới: `/data/synthetic_tv2_m1_20261110_231427`.
- Hai worker được kiểm tra ALIVE trước khi chạy và sau compare_truth.
- Cấu hình container: executor memory `2g`, executor cores `1`, shuffle partitions `800`.
- Driver memory của lần submit: `1g`; không sửa cấu hình cụm.
- `run_pipeline.sh --full` hoàn tất, `[EXIT] stage=complete code=0`.
- Cả `daily_kpi`, `category_kpi`, `brand_kpi`, `funnel`, `hourly` có `_SUCCESS`.
  Đây là xác nhận ghi output thành công, chưa phải kiểm toán nội dung KPI của TV4.

Lệnh PowerShell đã dùng để tạo dữ liệu và gọi pipeline (các biến runName đã được thay bằng giá trị thực):

```powershell
$env:DATA_DIR = '/data/synthetic_tv2_m1_20261110_231427'
$env:DATA_KIND = 'synthetic'
$env:SPARK_DRIVER_MEMORY = '1g'
$env:PIPELINE_LOG_DIR = 'data/synthetic_tv2_m1_20261110_231427/pipeline_logs'
docker exec -e "DATA_DIR=$env:DATA_DIR" spark-master python3 /opt/scripts/generate_data.py 200000
& 'C:\Program Files\Git\bin\bash.exe' scripts/run_pipeline.sh --full
docker exec spark-master python3 /opt/scripts/compare_truth.py /data/synthetic_tv2_m1_20261110_231427
```

**Không chạy lại các lệnh sinh dữ liệu/pipeline với DATA_DIR này.** Chọn tên mới và xác nhận chưa tồn tại cho mỗi lần chạy tiếp theo.

## Kết quả từ JSON/CSV

| Chỉ số | Giá trị | Nguồn |
|---|---:|---|
| Raw rows | 202032 | profiling_raw.json |
| Raw duplicate_rows | 2032 | profiling_raw.json |
| Raw duplicate_ratio | 0.010058 | profiling_raw.json |
| Raw price_le_0 | 2309 | profiling_raw.json |
| Raw price_le_0_ratio | 0.011429 | profiling_raw.json |
| Raw price_null | 220 | profiling_raw.json |
| Clean rows | 196492 | profiling_clean.json |
| Clean duplicate_rows | 0 | profiling_clean.json |
| Clean price_le_0 | 0 | profiling_clean.json |
| Clean invariants.all_pass | true | profiling_clean.json |
| Ingest seconds | 20.79 | ingest_log.csv |
| Raw profiling seconds | 22.415 | profiling_raw.json |
| Cleaning seconds | 177.855 | cleaning_metrics.json |
| Clean profiling seconds | 83.339 | profiling_clean.json |

Các tỷ lệ là giá trị nguyên bản trong JSON, không phải phần trăm.
Giá `nan` do generator ghi có thể được CSV reader chuyển thành null; raw `price_nan=0`
không có nghĩa là generator không chèn NaN. Dòng lỗi cũng có thể được nhân bản.

`compare_truth.py` chạy trong container, exit code 0:

| Mục | Đã chèn | Đối chiếu cleaning | Kết quả |
|---|---:|---:|---|
| Tổng dòng raw | 202032 | 202032 | OK, exact |
| Dòng trùng | 2032 | 2032 | OK, exact |
| Event type lạ | 424 | 424 | OK, near |
| Giá 0/âm/NaN | 2508 | 2498 | OK, near |
| Session trống + user null | 595 | 586 | OK, near |

Các giá trị trên lấy từ `generate_data_truth.json` và `cleaning_metrics.json`.
Kiểm tra near dùng đúng ngưỡng trong script: removed <= injected và
injected - removed <= 0.02 * injected + 20, vì lỗi có thể giao nhau.

## Bằng chứng và trạng thái review

Các JSON/CSV trong thư mục này được sao chép từ `DATA_DIR/reports`; đã kiểm tra SHA256
khớp từng file. `pipeline_summary.log` trích các dòng preflight, stage, kết quả và exit từ log gốc.
`run_summary.json` lưu commit, cấu hình và kiểm tra marker output.
Log đầy đủ nằm ở `data/synthetic_tv2_m1_20261110_231427/pipeline_logs/pipeline-20261110T161432Z-1429.log`.

Không sửa source hoặc dữ liệu cũ; không commit/push/mở PR trong lượt này.
Mục chạy full đã đạt; M1 vẫn chờ người dùng gửi tin và TV1 review.
