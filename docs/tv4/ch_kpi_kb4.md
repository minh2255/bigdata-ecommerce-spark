# TV4 – Tổng hợp KPI, đối chiếu và KB4 (Pandas so với Spark)

> Số liệu dưới đây chạy trên **dữ liệu Kaggle thật** (tháng 10, 42.349.872 dòng clean, 31 ngày) trong vùng
> `DATA_DIR=/data/real_oct_full` (không đưa lên Git), ngày 22/11/2026, cụm Docker Compose 1 master + 2 worker
> (mỗi worker 2 core, 2 GB). Bản chạy synthetic trước đó chỉ dùng để thử pipeline, không dùng làm kết quả báo cáo.

## 1. Đầu vào và bảng tổng hợp

`jobs/03_aggregation.py` đọc `clean/events` và ghi 5 bảng vào `agg/`: `daily_kpi` (views, carts, purchases, revenue,
active_users theo `event_date`), `category_kpi`, `brand_kpi`, `funnel` (số phiên khác nhau theo `event_type`) và
`hourly` (số sự kiện theo giờ và loại). Doanh thu và số đơn chỉ tính từ `purchase`. Giá trị `unknown` trong
brand/danh mục là nhãn hợp lệ theo contract v1.0 nên xuất hiện như một nhóm riêng. Thời gian là UTC; `user_session`
không phải khóa duy nhất (xem [bàn giao clean](../tv3/ban_giao_clean_tv4.md)).

## 2. Đối chiếu KPI với clean

`scripts/check_agg_kpi_spark.py` tính lại bằng Spark từ `clean/events` (dữ liệu thật quá lớn cho pandas) rồi so từng
bảng agg. Kết quả [`kpi_check.json`](../evidence/tv4/kpi_check.json): **13/13 kiểm tra đạt, `all_pass=true`**.

| Chỉ số | Giá trị (clean = agg) |
|---|---|
| Tổng dòng clean / tổng sự kiện (`hourly`) | 42.349.872 |
| Số ngày (`daily_kpi`) | 31 |
| view / cart / purchase (`daily_kpi`) | 40.708.807 / 898.292 / 742.773 |
| Doanh thu (purchase) | 229.933.212,63 |
| Số phiên funnel view / cart / purchase | 9.237.562 / 573.019 / 629.560 |

Các số trên khớp với `profiling_clean` của TV2, nên số của TV4 nhất quán với phần làm sạch.

## 3. Tỷ lệ chuyển đổi và lưu ý về funnel

`05_charts.py` ghi [`conversion_rate.json`](../evidence/tv4/conversion_rate.json):

| Tỷ lệ | Giá trị |
|---|---|
| view → cart | 6,2% (573.019 / 9.237.562) |
| view → purchase | **6,8%** (629.560 / 9.237.562) |
| cart → purchase | 109,87% (không hợp lệ, xem dưới) |

Bảng `funnel` đếm số phiên khác nhau **riêng cho từng loại sự kiện**, không phải phễu trong cùng một phiên. Số phiên có
`purchase` (629.560) lớn hơn số phiên có `cart` (573.019) vì nhiều phiên mua hàng không ghi nhận sự kiện `cart`, nên
tỷ lệ cart → purchase vượt 100% và **không dùng được làm kết luận**. Báo cáo chỉ trích tỷ lệ view → purchase (≈6,8%)
và nói rõ cách đếm này. Muốn có phễu đúng nghĩa phải đếm theo cùng `user_session` (chưa làm).

## 4. KB4 – Pandas so với Spark

Cùng phép đo ở hai phía: đọc `samples/frac_<tỷ lệ>` (tạo bằng `jobs/make_sample.py`, seed 42), `groupby(event_date,
event_type)` tính count và sum(price), 3 lần lặp. Pandas: `jobs/pandas_baseline.py`; Spark:
`jobs/kb4_spark_baseline.py`. Dữ liệu thô: [`kb4_benchmark.csv`](../evidence/tv4/kb4_benchmark.csv) (18 dòng).

| Tỷ lệ mẫu | Số dòng (xấp xỉ) | Pandas TB (s) | Spark TB 3 lần (s) | Spark lần 1 (s) | Spark lần 2–3 TB (s) |
|---|---|---|---|---|---|
| 0,01 | 424 nghìn | 0,59 | 3,53 | 8,25 | 1,17 |
| 0,05 | 2,1 triệu | 1,85 | 3,79 | 9,12 | 1,12 |
| 0,10 | 4,2 triệu | 4,08 | 3,84 | 9,01 | 1,25 |

**Diễn giải đúng phạm vi:**
- Pandas tăng gần tuyến tính theo kích thước (0,59 → 1,85 → 4,08 s), còn Spark gần như phẳng.
- Lần chạy đầu của Spark chậm (8–9 s) vì khởi tạo JVM, executor và đọc Parquet lần đầu (cold start).
- Tính cả cold start, Spark chậm hơn Pandas ở mẫu 0,01 và 0,05 và chỉ ngang ở mẫu 0,1 (3,84 so với 4,08 s).
  Tính các lần đã khởi động, Spark nhanh hơn Pandas từ mẫu 0,05 (1,12 so với 1,85 s) và khoảng 3,3 lần ở mẫu 0,1.
  Điểm hòa vốn nằm quanh 2–4 triệu dòng.
- Pandas chưa hết RAM ở mẫu 0,1. Việc Pandas không mở rộng lên toàn bộ 42 triệu dòng là suy luận từ xu hướng
  tuyến tính và bộ nhớ, **chưa đo trực tiếp**.
- Hạn chế: chạy trên một máy, 3 lần lặp mỗi mẫu, chưa tách riêng thời gian khởi động khỏi thời gian xử lý.

## 5. Biểu đồ

[`daily_revenue.png`](../evidence/tv4/daily_revenue.png), [`category_revenue.png`](../evidence/tv4/category_revenue.png),
[`funnel.png`](../evidence/tv4/funnel.png), [`hourly_activity.png`](../evidence/tv4/hourly_activity.png),
[`brand_revenue.png`](../evidence/tv4/brand_revenue.png), [`pandas_vs_spark.png`](../evidence/tv4/pandas_vs_spark.png),
sinh bởi `jobs/05_charts.py`. Biểu đồ KB1/KB2/KB3/KB5/KB6 sinh bởi `jobs/06_benchmark_charts.py` từ số liệu của TV1 và TV2.

## 6. Thay đổi code

- `jobs/pandas_baseline.py`: đọc `samples/frac_*`, nhận số lần lặp, ghi `kb4_benchmark.csv`.
- `jobs/kb4_spark_baseline.py` (mới): phía Spark của KB4, cùng cột `engine,fraction,run,seconds`.
- `jobs/05_charts.py`: đọc `kb4_benchmark.csv`; thêm biểu đồ hourly, top thương hiệu và `conversion_rate.json`.
- `jobs/06_benchmark_charts.py` (mới): biểu đồ KB1/2/3/5/6.
- `scripts/check_agg_kpi.py` (pandas, cho dữ liệu nhỏ) và `scripts/check_agg_kpi_spark.py` (Spark, cho dữ liệu thật).

## 7. Cách chạy lại

```bash
export DATA_DIR=/data/<vung_moi>   # cần clean/events; 03 dùng mode overwrite nên dùng vùng mới
spark-submit /opt/jobs/03_aggregation.py
spark-submit /opt/scripts/check_agg_kpi_spark.py
spark-submit /opt/jobs/make_sample.py 0.01 0.05 0.1
for f in 0.01 0.05 0.1; do python3 /opt/jobs/pandas_baseline.py $f 3; spark-submit /opt/jobs/kb4_spark_baseline.py $f 3; done
python3 /opt/jobs/05_charts.py
```

## 8. Chưa làm / hạn chế

- TV4 chưa xác nhận bàn giao clean trong `docs/tv3/ban_giao_clean_tv4.md` (cần tick sau khi nhóm đồng ý).
- Chưa có ảnh Spark UI cho job aggregation và chưa tập demo.
- `03_aggregation.py` ghi `overwrite`, khác quy ước "không ghi đè" của các job khác; chưa sửa.
- Phễu chưa tính theo cùng phiên (xem mục 3).