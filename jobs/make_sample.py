"""make_sample.py - Cắt mẫu từ tầng clean để so sánh Pandas với Spark (KB4).   [TV2]

Dùng: spark-submit make_sample.py 0.01 [0.05 0.1 ...]   (mỗi tham số là một tỷ lệ trong (0, 1])
Input : $DATA_DIR/clean/events
Output: $DATA_DIR/samples/frac_<tỷ lệ>   (1 file Parquet, seed=42; tên thư mục như 0.01, 0.05, 0.1)
        $DATA_DIR/reports/samples_log.csv (tỷ lệ, số dòng clean, số dòng mẫu, thời gian)
Log   : [SAMPLE] fraction=... rows=...
Không ghi đè mẫu đã có: dùng DATA_DIR mới hoặc xóa thư mục mẫu có chủ đích.
"""
import csv
import os
import sys
import time
from pathlib import Path

from pyspark.sql import SparkSession


def main():
    try:
        fractions = [float(arg) for arg in sys.argv[1:]]
    except ValueError:
        fractions = []
    if not fractions or any(not 0 < f <= 1 for f in fractions):
        print("Usage: make_sample.py <fraction in (0,1]> [...]", file=sys.stderr)
        sys.exit(2)
    root = Path(os.environ.get("DATA_DIR", "/data"))
    targets = {f: root / f"samples/frac_{f}" for f in fractions}
    existing = [str(path) for path in targets.values() if path.exists()]
    if existing:
        raise FileExistsError(f"Sample exists: {existing}; choose a new DATA_DIR to preserve it")
    spark = (SparkSession.builder.appName("make_sample")
             .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    try:
        clean = spark.read.parquet(str(root / "clean/events"))
        clean_rows = clean.count()
        log_path = root / "reports/samples_log.csv"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not log_path.exists()
        for fraction, target in targets.items():
            started = time.perf_counter()
            # event_date là cột thường trong mẫu (không partitionBy) để pandas đọc 1 file duy nhất.
            clean.sample(fraction=fraction, seed=42).coalesce(1).write.mode("errorifexists").parquet(str(target))
            rows = spark.read.parquet(str(target)).count()
            seconds = round(time.perf_counter() - started, 2)
            print(f"[SAMPLE] fraction={fraction} rows={rows} clean_rows={clean_rows} "
                  f"ratio={rows / clean_rows if clean_rows else 0:.4f} time={seconds}s -> {target}", flush=True)
            with log_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                if is_new:
                    writer.writerow(["fraction", "clean_rows", "sample_rows", "seconds"])
                    is_new = False
                writer.writerow([fraction, clean_rows, rows, seconds])
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
