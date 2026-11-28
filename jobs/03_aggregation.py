"""03_aggregation.py - Tổng hợp KPI từ clean/events.   [TV4]

DATA_DIR chọn vùng dữ liệu. Không ghi đè: nếu agg/<bảng> hoặc reports/aggregation_metrics.json
đã tồn tại, job dừng với FileExistsError trước khi chạy Spark; dùng DATA_DIR mới để giữ kết quả cũ
(cùng quy ước với 00_ingest, 02_cleaning).

Đầu ra: agg/{daily_kpi, category_kpi, brand_kpi, funnel, hourly, conversion} và
reports/aggregation_metrics.json (số dòng clean, số dòng mỗi bảng, thời gian chạy).
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

DATA_DIR = os.environ.get("DATA_DIR", "/data")

TABLE_NAMES = ["daily_kpi", "category_kpi", "brand_kpi", "funnel", "hourly", "conversion"]
METRICS_PATH = Path(DATA_DIR) / "reports" / "aggregation_metrics.json"
existing = [str(Path(DATA_DIR) / "agg" / n) for n in TABLE_NAMES if (Path(DATA_DIR) / "agg" / n).exists()]
if METRICS_PATH.exists():
    existing.append(str(METRICS_PATH))
if existing:
    raise FileExistsError(f"Aggregation output exists: {existing}; choose a new DATA_DIR to preserve it")

started = time.perf_counter()
spark = (
    SparkSession.builder
    .appName("03_aggregation")
    .config("spark.sql.session.timeZone", "UTC")  # contract: mọi thời gian theo UTC
    .getOrCreate()
)

# 1. Đọc dữ liệu đã được TV3 làm sạch
df = spark.read.parquet(f"{DATA_DIR}/clean/events")

df.createOrReplaceTempView("events")

# 2. KPI theo ngày
daily_kpi = spark.sql("""
    SELECT
        event_date,
        SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS views,
        SUM(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS carts,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchases,
        ROUND(
            SUM(CASE WHEN event_type = 'purchase' THEN price ELSE 0 END),
            2
        ) AS revenue,
        COUNT(DISTINCT user_id) AS active_users
    FROM events
    GROUP BY event_date
""")

# 3. KPI theo danh mục sản phẩm
purchases = df.filter(F.col("event_type") == "purchase")

category_kpi = purchases.groupBy("cat_l1").agg(
    F.count("*").alias("orders"),
    F.round(F.sum("price"), 2).alias("revenue")
)

# 4. KPI theo thương hiệu
brand_kpi = purchases.groupBy("brand").agg(
    F.count("*").alias("orders"),
    F.round(F.sum("price"), 2).alias("revenue")
)

# 5. Funnel theo loại hành vi
funnel = df.groupBy("event_type").agg(
    F.countDistinct("user_session").alias("sessions")
)

# 6. Hành vi theo giờ
hourly = df.groupBy("event_hour", "event_type").count()

# 7. Lưu kết quả tổng hợp
tables = {
    "daily_kpi": daily_kpi,
    "category_kpi": category_kpi,
    "brand_kpi": brand_kpi,
    "funnel": funnel,
    "hourly": hourly
}

table_rows = {}
for name, table in tables.items():
    output_path = f"{DATA_DIR}/agg/{name}"
    table.write.mode("errorifexists").parquet(output_path)
    table_rows[name] = spark.read.parquet(output_path).count()
    print(f"Saved: {output_path} rows={table_rows[name]}")

# 8. Tỷ lệ chuyển đổi (1 dòng) tính từ bảng funnel đã ghi, tránh quét lại clean.
# Mỗi loại sự kiện đếm số phiên riêng, không phải chuyển đổi trong cùng một phiên.
sessions = {r["event_type"]: r["sessions"] for r in spark.read.parquet(f"{DATA_DIR}/agg/funnel").collect()}
n_view, n_cart, n_buy = (int(sessions.get(e, 0)) for e in ("view", "cart", "purchase"))


def ratio(num, den):
    return round(num / den, 4) if den else None


conversion = spark.createDataFrame(
    [(n_view, n_cart, n_buy, ratio(n_cart, n_view), ratio(n_buy, n_cart), ratio(n_buy, n_view))],
    "sessions_view long, sessions_cart long, sessions_purchase long, "
    "view_to_cart double, cart_to_purchase double, view_to_purchase double",
)
output_path = f"{DATA_DIR}/agg/conversion"
conversion.coalesce(1).write.mode("errorifexists").parquet(output_path)
table_rows["conversion"] = 1
print(f"Saved: {output_path} rows=1")

# 9. Minh chứng chạy job (cùng kiểu cleaning_metrics.json)
clean_rows = df.count()
metrics = {
    "utc_time": datetime.now(timezone.utc).isoformat(),
    "application_id": spark.sparkContext.applicationId,
    "data_dir": DATA_DIR,
    "clean_rows": clean_rows,
    "table_rows": table_rows,
    "shuffle_partitions": spark.conf.get("spark.sql.shuffle.partitions"),
    "timezone": spark.conf.get("spark.sql.session.timeZone"),
    "seconds_total": round(time.perf_counter() - started, 2),
    "timing_scope": "SparkSession start to metrics write; includes the extra clean count()",
}
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(METRICS_PATH, "x", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)
print(f"[AGG] clean_rows={clean_rows} seconds={metrics['seconds_total']} -> {METRICS_PATH}")

spark.stop()
