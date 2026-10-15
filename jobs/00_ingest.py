"""00_ingest.py - Đưa CSV từ landing/ vào tầng raw/ (Parquet).   [TV1]

Input : $DATA_DIR/landing/*.csv
Output: $DATA_DIR/raw/events (Parquet)
Log   : [INGEST] rows=... time=...s  (+ ghi thêm reports/ingest_log.csv)
"""
import os
import csv
import time
from pyspark.sql import SparkSession
from pyspark.sql.types import (StructType, StructField, StringType,
                               LongType, DoubleType)

DATA_DIR = os.environ.get("DATA_DIR", "/data")

# Schema cố định (không dùng inferSchema vì phải quét file 2 lần, rất chậm với 5 GB)
schema = StructType([
    StructField("event_time", StringType()),
    StructField("event_type", StringType()),
    StructField("product_id", LongType()),
    StructField("category_id", LongType()),
    StructField("category_code", StringType()),
    StructField("brand", StringType()),
    StructField("price", DoubleType()),
    StructField("user_id", LongType()),
    StructField("user_session", StringType()),
])

spark = SparkSession.builder.appName("00_ingest").getOrCreate()

# --- Bước 1: đọc CSV + ghi Parquet (thời gian ingest) ---
start = time.perf_counter()

df = spark.read.csv(f"{DATA_DIR}/landing/*.csv", header=True, schema=schema)
df.write.mode("overwrite").parquet(f"{DATA_DIR}/raw/events")

elapsed = time.perf_counter() - start

# --- Bước 2: đếm lại số dòng từ Parquet vừa ghi (không tính vào thời gian ingest) ---
n = spark.read.parquet(f"{DATA_DIR}/raw/events").count()

print(f"[INGEST] rows={n} time={elapsed:.1f}s")

# Ghi log ra file để đưa vào báo cáo
os.makedirs(f"{DATA_DIR}/reports", exist_ok=True)
log_path = f"{DATA_DIR}/reports/ingest_log.csv"
is_new = not os.path.exists(log_path)
with open(log_path, "a", newline="") as f:
    w = csv.writer(f)
    if is_new:
        w.writerow(["rows", "seconds"])
    w.writerow([n, round(elapsed, 2)])

spark.stop()
