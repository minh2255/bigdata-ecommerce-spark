"""04_benchmark.py - Đo thời gian 1 truy vấn tổng hợp chuẩn.   [TV1]

Cách dùng:  04_benchmark.py <fraction> <label>
  fraction : tỷ lệ dữ liệu dùng (0.1, 0.25, 0.5, 1.0 ...), mặc định 1.0
  label    : nhãn thực nghiệm (size, cores, part8, part50, part200, vs_pandas ...)

Mỗi lần chạy ghi thêm 1 dòng vào $DATA_DIR/reports/benchmark.csv:
  label, fraction, cores, seconds
"""
import os
import sys
import time
import csv
import json
from datetime import datetime, timezone
from pyspark.sql import SparkSession, functions as F

DATA_DIR = os.environ.get("DATA_DIR", "/data")
fraction = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
label = sys.argv[2] if len(sys.argv) > 2 else "spark"

spark = SparkSession.builder.appName(f"04_benchmark_{label}_{fraction}").getOrCreate()

# spark.cores.max chính là giá trị của --total-executor-cores (nếu không đặt -> "all")
cores = spark.conf.get("spark.cores.max", "all")
shuffle_parts = spark.conf.get("spark.sql.shuffle.partitions")

df = spark.read.parquet(f"{DATA_DIR}/clean/events")
if fraction < 1.0:
    df = df.sample(fraction=fraction, seed=42)

start = time.perf_counter()
query = (df.groupBy("event_date", "event_type")
            .agg(F.count("*").alias("n"), F.sum("price").alias("revenue"))
         )
# Only date/type groups are collected (at most 93 for October).
# count() can prune n/revenue; collect() forces both aggregates to execute.
result = query.collect()
groups = len(result)
elapsed = time.perf_counter() - start

os.makedirs(f"{DATA_DIR}/reports", exist_ok=True)
path = f"{DATA_DIR}/reports/benchmark.csv"
is_new = not os.path.exists(path)
with open(path, "a", newline="") as f:
    w = csv.writer(f)
    if is_new:
        w.writerow(["label", "fraction", "cores", "seconds"])
    w.writerow([label, fraction, cores, round(elapsed, 2)])

with open(f"{DATA_DIR}/reports/benchmark_runs.jsonl", "a") as f:
    f.write(json.dumps({
        "utc_time": datetime.now(timezone.utc).isoformat(),
        "application_id": spark.sparkContext.applicationId,
        "data_dir": DATA_DIR, "label": label, "fraction": fraction,
        "cores": cores, "shuffle_partitions": shuffle_parts,
        "aqe_enabled": spark.conf.get("spark.sql.adaptive.enabled"),
        "groups": groups, "sample_rows": sum(r["n"] for r in result),
        "price_sum_all_event_types": sum(r["revenue"] for r in result),
        "seconds": elapsed, "method": "read_sample_groupby_count_sum_collect",
        "timing_scope": "action only; excludes Spark startup and schema discovery",
    }) + "\n")

print(f"[BENCH] label={label} fraction={fraction} cores={cores} "
      f"shuffle_partitions={shuffle_parts} groups={groups} seconds={elapsed:.2f}")
spark.stop()
