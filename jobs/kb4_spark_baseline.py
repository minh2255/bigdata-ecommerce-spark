"""kb4_spark_baseline.py - Phía Spark của KB4 (Pandas so với Spark).   [TV4]

Dùng: spark-submit kb4_spark_baseline.py <tỷ lệ> [số lần lặp]
Input : $DATA_DIR/samples/frac_<tỷ lệ>   (cùng mẫu mà jobs/pandas_baseline.py đọc)
Output: thêm dòng vào $DATA_DIR/reports/kb4_benchmark.csv (engine, fraction, run, seconds)

Cùng phép đo với pandas_baseline.py: đọc Parquet + groupby(event_date, event_type) + count/sum,
kết quả được thu về driver (collect) để Spark thực sự chạy hết các phép tổng hợp.
Thời gian không gồm khởi động SparkSession; mỗi lần lặp đọc lại Parquet từ đĩa.
"""
import csv
import os
import sys
import time
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))


def main():
    if len(sys.argv) < 2:
        print("Cach dung: kb4_spark_baseline.py 0.01 [so_lan_lap]", file=sys.stderr)
        sys.exit(2)
    fraction = float(sys.argv[1])
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    path = DATA_DIR / "samples" / f"frac_{fraction}"
    if not path.exists():
        print(f"Khong tim thay du lieu mau: {path}", file=sys.stderr)
        sys.exit(1)

    spark = (SparkSession.builder.appName(f"kb4_spark_{fraction}")
             .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    report = DATA_DIR / "reports" / "kb4_benchmark.csv"
    report.parent.mkdir(parents=True, exist_ok=True)
    is_new = not report.exists()
    with open(report, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["engine", "fraction", "run", "seconds"])
        for run in range(1, repeats + 1):
            start = time.perf_counter()
            df = spark.read.parquet(str(path))
            result = (df.groupBy("event_date", "event_type")
                      .agg(F.count("*").alias("event_count"), F.sum("price").alias("total_price"))
                      .collect())
            seconds = round(time.perf_counter() - start, 4)
            print(f"[SPARK] fraction={fraction} run={run} groups={len(result)} seconds={seconds}")
            writer.writerow(["spark", fraction, run, seconds])
    spark.stop()


if __name__ == "__main__":
    main()
