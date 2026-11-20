# TV4 – Tổng hợp KPI, đối chiếu và KB4 (Pandas so với Spark)

> **SYNTHETIC TEST ONLY.** Mọi số liệu dưới đây lấy từ bản sao clean của lần chạy synthetic
> `synthetic_tv3_full_20261116_120201` (19.627 dòng clean, 31 ngày), chạy ngày 20/11/2026 trong vùng
> `DATA_DIR=/data/synthetic_tv4_20261120` (không đưa lên Git). Máy này không có dữ liệu Kaggle thật
> (42.349.872 dòng clean nằm trên máy TV2), nên **chưa có KPI hay KB4 trên dữ liệu thật**.

## 1. Đầu vào và bảng tổng hợp

`jobs/03_aggregation.py` đọc `clean/events` và ghi 5 bảng vào `agg/`: `daily_kpi` (31 dòng: views, carts,
purchases, revenue, active_users theo `event_date`), `category_kpi` (6 danh mục), `brand_kpi` (6 thương hiệu),
`funnel` (số phiên khác nhau theo `event_type`) và `hourly` (số sự kiện theo giờ và loại).
Doanh thu và số đơn chỉ tính từ `purchase`. Giá trị `unknown` trong brand/danh mục là nhãn hợp lệ theo contract
v1.0 nên xuất hiện như một nhóm riêng (trên synthetic, `unknown` là nhóm đứng đầu về doanh thu thương hiệu).
Thời gian là UTC; `user_session` không phải khóa duy nhất (xem [bàn giao clean](../tv3/ban_giao_clean_tv4.md)).

## 2. Đối chiếu KPI với clean

`scripts/check_agg_kpi.py` tính lại bằng pandas từ `clean/events` rồi so từng bảng agg. Kết quả
[`kpi_check.json`](../evidence/tv4/kpi_check.json): **14/14 kiểm tra đạt, `all_pass=true`**.

| Chỉ số | Từ clean | Từ agg |
|---|---|---|
| Tổng sự kiện (`hourly`) | 19.627 | 19.627 |
| view / cart / purchase (`daily_kpi`) | 17.705 / 1.342 / 580 | 17.705 / 1.342 / 580 |
| Số đơn (`category_kpi`, `brand_kpi`) | 580 | 580 |
| Doanh thu (3 bảng) | 592.819,22 | 592.819,22 (sai lệch dấu phẩy động ~1e-9) |
| Số phiên funnel view / cart / purchase | 17.705 / 1.342 / 580 | giống nhau |

Trên synthetic số phiên funnel trùng đúng số sự kiện từng loại (mỗi phiên chỉ có một sự kiện); dữ liệu thật hcó nhiều sự kiện mỗi phiên nên hai số sẽ khác nhau.
Funnel hiện đếm phiên theo từng loại riêng lẻ, không phải chuyển đổi view→cart→purchase trong cùng phiên.

## 3. KB4 – Pandas so với Spark

Cùng phép đo ở hai phía: đọc `samples/frac_<tỷ lệ>` (tạo bằng `jobs/make_sample.py`, seed 42), `groupby(event_date,
event_type)` tính count và sum(price), 3 lần lặp. Pandas: `jobs/pandas_baseline.py`; Spark (cụm 1 master + 2 worker):
`jobs/kb4_spark_baseline.py`. Dữ liệu thô: [`kb4_benchmark.csv`](../evidence/tv4/kb4_benchmark.csv).

| Tỷ lệ mẫu | Số dòng | Pandas TB (s) | Spark TB (s) |
|---|---|---|---|
| 0,01 | 232 | 0,118 | 2,79 |
| 0,05 | 1.002 | 0,114 | 2,73 |
| 0,10 | 1.989 | 0,119 | 2,71 |
| 1,00 | 19.627 | 0,151 | 2,43 |

**Diễn giải đúng phạm vi:** trên tập chỉ ~20 nghìn dòng, Pandas nhanh hơn Spark hơn 15 lần vì Spark mất chi phí
lên lịch job và shuffle cố định (lần chạy đầu ~5 s, sau đó ~1–2 s). Kết quả này **không chứng minh** điểm giao nhau
nơi Spark vượt Pandas; muốn kết luận về khả năng mở rộng phải chạy lại cùng lệnh trên samples của dữ liệu Kaggle
(424 nghìn, 2,1 triệu, 4,2 triệu dòng, TV2 đã tạo). Số lần lặp ít (3) và chưa loại lần khởi động nóng.

## 4. Biểu đồ

[`daily_revenue.png`](../evidence/tv4/daily_revenue.png), [`category_revenue.png`](../evidence/tv4/category_revenue.png),
[`funnel.png`](../evidence/tv4/funnel.png), [`pandas_vs_spark.png`](../evidence/tv4/pandas_vs_spark.png), sinh bởi `jobs/05_charts.py`.

## 5. Thay đổi code trong phiên này

- `jobs/pandas_baseline.py`: đọc `samples/frac_1.0` (trước đây tìm `test_full` không tồn tại), nhận số lần lặp,
  ghi `kb4_benchmark.csv`.
- `jobs/kb4_spark_baseline.py` (mới): phía Spark của KB4, cùng cột `engine,fraction,run,seconds`.
- `jobs/05_charts.py`: đọc `kb4_benchmark.csv`. Trước đó cùng đọc `benchmark.csv` của `04_benchmark.py` có cột
  `label,...,cores,...` khác cột Pandas, nên biểu đồ KB4 sẽ lỗi hoặc trộn số liệu.
- `scripts/check_agg_kpi.py` (mới): đối chiếu agg với clean.

## 6. Cách chạy lại

```bash
export DATA_DIR=/data/<vung_moi>   # cần clean/events; script không ghi đè agg ở 03 (mode overwrite) nên dùng vùng mới
spark-submit /opt/jobs/03_aggregation.py
python3 /opt/scripts/check_agg_kpi.py
spark-submit /opt/jobs/make_sample.py 0.01 0.05 0.1 1.0
for f in 0.01 0.05 0.1 1.0; do python3 /opt/jobs/pandas_baseline.py $f 3; spark-submit /opt/jobs/kb4_spark_baseline.py $f 3; done
python3 /opt/jobs/05_charts.py
```

## 7. Chưa làm / hạn chế

- Chưa chạy trên dữ liệu Kaggle thật (cần máy của TV2 hoặc chép `real_oct_full`).
- TV4 thật chưa xác nhận nhận bàn giao clean; tài liệu này không thay xác nhận đó.
- Chưa có ảnh Spark UI và chưa tập demo.
- `03_aggregation.py` ghi `overwrite`, khác quy ước "không ghi đè" của các job khác; chưa sửa vì ngoài phạm vi phiên này.
