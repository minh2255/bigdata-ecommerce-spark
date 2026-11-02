import os
import sys
import csv
import time
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))


def run_pandas(fraction):
    sample_path = (
    DATA_DIR / "samples" / "test_full"
    if fraction == 1.0
    else DATA_DIR / "samples" / f"frac_{fraction}"
)

    if not sample_path.exists():
        print(f"Khong tim thay du lieu mau: {sample_path}")
        return

    # Doc du lieu Parquet
    start = time.perf_counter()
    df = pd.read_parquet(sample_path)

    # Tong hop so luong su kien va tong gia
    result = (
        df.groupby(["event_date", "event_type"])
        .agg(
            event_count=("event_type", "size"),
            total_price=("price", "sum")
        )
        .reset_index()
    )

    seconds = round(time.perf_counter() - start, 4)

    print(f"[PANDAS] fraction={fraction}")
    print(f"So dong dau vao: {len(df)}")
    print(f"So nhom ket qua: {len(result)}")
    print(f"Thoi gian: {seconds} giay")

    # Ghi ket qua benchmark
    report_dir = DATA_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "benchmark.csv"

    is_new = not report_file.exists()

    with open(report_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if is_new:
            writer.writerow(
                ["engine", "fraction", "run", "seconds"]
            )

        writer.writerow(
            ["pandas", fraction, 1, seconds]
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cach dung: python pandas_baseline.py 0.01")
        sys.exit(1)

    run_pandas(float(sys.argv[1]))
