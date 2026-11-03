import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

DATA_DIR = os.environ.get("DATA_DIR", "/data")

spark = SparkSession.builder.appName("create_test_data").getOrCreate()

rows = [
    ("2026-10-01 08:00:00", "view", 1, "s1", 100.0, "Electronics", "Samsung"),
    ("2026-10-01 08:10:00", "cart", 1, "s1", 100.0, "Electronics", "Samsung"),
    ("2026-10-01 08:20:00", "purchase", 1, "s1", 100.0, "Electronics", "Samsung"),
    ("2026-10-01 09:00:00", "view", 2, "s2", 200.0, "Electronics", "Apple"),
    ("2026-10-01 09:15:00", "purchase", 2, "s2", 200.0, "Electronics", "Apple"),
    ("2026-10-02 10:00:00", "view", 3, "s3", 50.0, "Accessories", "Logitech"),
    ("2026-10-02 10:10:00", "cart", 3, "s3", 50.0, "Accessories", "Logitech"),
    ("2026-10-02 11:00:00", "purchase", 3, "s3", 50.0, "Accessories", "Logitech")
]

columns = [
    "event_time", "event_type", "user_id",
    "user_session", "price", "cat_l1", "brand"
]

df = spark.createDataFrame(rows, columns)

df = (
    df.withColumn("event_time", F.to_timestamp("event_time"))
      .withColumn("event_date", F.to_date("event_time"))
      .withColumn("event_hour", F.hour("event_time"))
)

output_path = f"{DATA_DIR}/clean/events"

df.write.mode("overwrite").parquet(output_path)

print("Created test data:", output_path)
print("Number of events:", df.count())

spark.stop()
