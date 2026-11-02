"""slice_raw_by_day.py - Tách raw/events thành các lát theo ngày để cleaning vừa bộ nhớ.   [TV2]

Input : $SRC_DIR/raw/events
Output: $OUT_PREFIX<k>/raw/events cho từng lát k
Dòng trùng cùng event_time nên luôn nằm trong một lát: dedup từng lát cho kết quả như dedup cả tháng.
Dùng: SRC_DIR=/data/real_oct_run01 OUT_PREFIX=/data/real_oct_s python3 slice_raw_by_day.py 1-4 5-8 ...
"""
import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession, functions as F

src = os.environ["SRC_DIR"]
prefix = os.environ["OUT_PREFIX"]
spark = (SparkSession.builder.appName("slice_raw_by_day")
         .config("spark.sql.session.timeZone", "UTC").getOrCreate())
raw = spark.read.parquet(f"{src}/raw/events")
day = F.substring("event_time", 1, 10)
for k, rng in enumerate(sys.argv[1:], start=1):
    lo, hi = (int(x) for x in rng.split("-"))
    out = f"{prefix}{k}/raw/events"
    if list(Path(out).rglob("*.parquet")):
        print(f"[SLICE] {k} days {rng} exists, skipped")
        continue
    part = raw.filter((day >= f"2019-10-{lo:02d}") & (day <= f"2019-10-{hi:02d}"))
    part.write.mode("errorifexists").parquet(out)
    print(f"[SLICE] {k} days {rng} rows={spark.read.parquet(out).count()}")
spark.stop()
