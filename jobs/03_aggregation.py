
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

DATA_DIR = os.environ.get("DATA_DIR", "/data")

spark = (
    SparkSession.builder
    .appName("03_aggregation")
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

for name, table in tables.items():
    output_path = f"{DATA_DIR}/agg/{name}"
    table.write.mode("overwrite").parquet(output_path)
    print(f"Saved: {output_path}")

spark.stop()
