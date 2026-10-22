"""kb3_csv_vs_parquet.py - KB3: so CSV (landing) với Parquet (raw) về dung lượng và thời gian đọc.   [TV2]

Input : $DATA_DIR/landing/*.csv và $DATA_DIR/raw/events (đã có sau 00_ingest.py)
Output: $DATA_DIR/reports/kb3.csv       (từng lần đo + dòng mean; không ghi đè)
        $DATA_DIR/reports/kb3_env.json  (cấu hình máy/cụm lúc đo)
Mỗi phép đo chạy 3 lần (tham số REPEATS), CSV đọc với schema cố định như 00_ingest.py.
Phép đo: count() toàn bộ; sum(price) — chỉ cần 1 cột, để thấy lợi ích lưu theo cột của Parquet.
Lưu ý: lần đọc sau có thể hưởng cache của hệ điều hành; ghi rõ khi báo cáo.
"""
import csv
import glob
import json
import os
import platform
import time
from pathlib import Path

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

REPEATS = int(os.environ.get("REPEATS", "3"))
SCHEMA = StructType([
    StructField("event_time", StringType()), StructField("event_type", StringType()),
    StructField("product_id", LongType()), StructField("category_id", LongType()),
    StructField("category_code", StringType()), StructField("brand", StringType()),
    StructField("price", DoubleType()), StructField("user_id", LongType()),
    StructField("user_session", StringType()),
])


def size_bytes(path):
    path = Path(path)
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.name.startswith("."))


def mem_total_gb():
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal"):
                return round(int(line.split()[1]) / 1024 / 1024, 2)
    except OSError:
        pass
    return None


def main():
    root = Path(os.environ.get("DATA_DIR", "/data"))
    out, env_out = root / "reports/kb3.csv", root / "reports/kb3_env.json"
    if out.exists() or env_out.exists():
        raise FileExistsError("KB3 output exists; choose a new DATA_DIR to preserve it")
    csv_files = sorted(glob.glob(str(root / "landing/*.csv")))
    parquet_dir = root / "raw/events"
    spark = (SparkSession.builder.appName("kb3_csv_vs_parquet")
             .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    try:
        readers = {
            "csv": lambda: spark.read.csv(csv_files, header=True, schema=SCHEMA),
            "parquet": lambda: spark.read.parquet(str(parquet_dir)),
        }
        tests = {"count": lambda df: df.count(),
                 "sum_price": lambda df: df.agg(F.sum("price")).first()[0]}
        rows = [["metric", "format", "run", "value", "unit"]]
        sizes = {"csv": sum(size_bytes(f) for f in csv_files), "parquet": size_bytes(parquet_dir)}
        for fmt, size in sizes.items():
            rows.append(["size", fmt, "-", size, "bytes"])
        rows.append(["size_ratio", "csv/parquet", "-", round(sizes["csv"] / sizes["parquet"], 3), "x"])
        # Xen kẽ định dạng giữa các lần để lần đọc nào cũng ở điều kiện tương tự.
        times = {(t, fmt): [] for t in tests for fmt in readers}
        for run in range(1, REPEATS + 1):
            for test, fn in tests.items():
                for fmt, reader in readers.items():
                    started = time.perf_counter()
                    value = fn(reader())
                    seconds = round(time.perf_counter() - started, 3)
                    times[(test, fmt)].append(seconds)
                    rows.append([f"{test}_seconds", fmt, run, seconds, "s"])
                    print(f"[KB3] {test} {fmt} run={run} seconds={seconds} value={value}", flush=True)
        for (test, fmt), values in times.items():
            rows.append([f"{test}_seconds", fmt, "mean", round(sum(values) / len(values), 3), "s"])
        for test in tests:
            c, p = sum(times[(test, "csv")]), sum(times[(test, "parquet")])
            rows.append([f"{test}_speedup", "csv/parquet", "mean", round(c / p, 3), "x"])
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(rows)
        env = {
            "data_dir": str(root), "repeats": REPEATS, "csv_files": csv_files,
            "cpu_count_in_container": os.cpu_count(), "mem_total_gb_in_container": mem_total_gb(),
            "platform": platform.platform(), "spark_version": spark.version,
            "default_parallelism": spark.sparkContext.defaultParallelism,
            "executor_memory": spark.conf.get("spark.executor.memory", "default"),
            "driver_memory": spark.conf.get("spark.driver.memory", "default"),
            "master": spark.sparkContext.master, "application_id": spark.sparkContext.applicationId,
            "note": "Cụm Docker: 1 master + 2 worker; số core/RAM worker lấy từ docker-compose.yml",
        }
        with env_out.open("x", encoding="utf-8") as handle:
            json.dump(env, handle, indent=2, ensure_ascii=False)
        print(f"[KB3] size csv={sizes['csv']} parquet={sizes['parquet']} -> {out}", flush=True)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
