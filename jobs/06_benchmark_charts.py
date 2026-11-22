"""06_benchmark_charts.py - Ve bieu do thuc nghiem KB1, KB2, KB3, KB5, KB6.   [TV4]

Dung: python3 06_benchmark_charts.py
Input (trong $DATA_DIR/reports/, file nao thieu thi bo qua bieu do do):
  benchmark.csv      (TV1: label,fraction,cores,seconds)  -> KB1, KB2, KB6
  kb3.csv            (TV2: metric,format,run,value,unit)  -> KB3
  kb5_chart_data.csv (TV2: chart,metric,layer,value,...)  -> KB5
Output: $DATA_DIR/reports/kb1_size.png, kb2_cores.png, kb6_partitions.png,
        kb3_csv_vs_parquet.png, kb5_cleaning_steps.png
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(REPORT_DIR / filename, dpi=150)
    plt.close()
    print(f"Da tao: {filename}")


def add_labels(bars, fmt="{:.1f}"):
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 fmt.format(bar.get_height()), ha="center", va="bottom")


# ---------- KB1, KB2, KB6 tu benchmark.csv cua TV1 ----------
bench_path = REPORT_DIR / "benchmark.csv"
if bench_path.exists():
    bench = pd.read_csv(bench_path, dtype={"cores": str})
    bench["seconds"] = pd.to_numeric(bench["seconds"], errors="coerce")
    bench = bench.dropna(subset=["seconds"])

    # KB1: thoi gian theo ty le du lieu
    kb1 = bench[bench["label"] == "size"].groupby("fraction")["seconds"].mean().sort_index()
    if not kb1.empty:
        plt.figure(figsize=(7, 5))
        bars = plt.bar([f"{int(round(f * 100))}%" for f in kb1.index], kb1.values)
        add_labels(bars)
        plt.title("KB1: Execution time by data size")
        plt.xlabel("Data fraction")
        plt.ylabel("Average time (seconds)")
        save_chart("kb1_size.png")

    # KB2: thoi gian theo so core
    kb2 = bench[(bench["label"] == "cores") & (bench["fraction"] == 1.0)]
    kb2 = kb2.groupby("cores")["seconds"].mean()
    kb2 = kb2.reindex(sorted(kb2.index, key=lambda c: int(c)))
    if not kb2.empty:
        plt.figure(figsize=(7, 5))
        bars = plt.bar(kb2.index.astype(str), kb2.values)
        add_labels(bars)
        plt.title("KB2: Execution time by number of cores (100% data)")
        plt.xlabel("Total executor cores")
        plt.ylabel("Average time (seconds)")
        save_chart("kb2_cores.png")

    # KB6: thoi gian theo so shuffle partition (nhan part8, part50, part200)
    part = bench[bench["label"].str.startswith("part")]
    part = part.groupby("label")["seconds"].mean()
    part = part.reindex(sorted(part.index, key=lambda s: int(s.replace("part", ""))))
    if not part.empty:
        plt.figure(figsize=(7, 5))
        bars = plt.bar([s.replace("part", "") for s in part.index], part.values)
        add_labels(bars)
        plt.title("KB6: Execution time by shuffle partitions (100% data)")
        plt.xlabel("spark.sql.shuffle.partitions")
        plt.ylabel("Average time (seconds)")
        save_chart("kb6_partitions.png")
else:
    print(f"Bo qua KB1, KB2, KB6: khong co {bench_path}")


# ---------- KB3 tu kb3.csv cua TV2 ----------
kb3_path = REPORT_DIR / "kb3.csv"
if kb3_path.exists():
    kb3 = pd.read_csv(kb3_path, dtype=str)
    kb3["value"] = pd.to_numeric(kb3["value"], errors="coerce")

    def pick(metric, fmt, run):
        row = kb3[(kb3["metric"] == metric) & (kb3["format"] == fmt) & (kb3["run"] == run)]
        return float(row["value"].iloc[0]) if not row.empty else None

    size_csv, size_pq = pick("size", "csv", "-"), pick("size", "parquet", "-")
    count_csv, count_pq = pick("count_seconds", "csv", "mean"), pick("count_seconds", "parquet", "mean")
    sum_csv, sum_pq = pick("sum_price_seconds", "csv", "mean"), pick("sum_price_seconds", "parquet", "mean")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    if size_csv and size_pq:
        bars = axes[0].bar(["CSV", "Parquet"], [size_csv / 1e9, size_pq / 1e9])
        for bar in bars:
            axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f"{bar.get_height():.2f}", ha="center", va="bottom")
        axes[0].set_title("File size")
        axes[0].set_ylabel("GB")
    if None not in (count_csv, count_pq, sum_csv, sum_pq):
        width = 0.35
        x = range(2)
        b1 = axes[1].bar([i - width / 2 for i in x], [count_csv, sum_csv], width, label="CSV")
        b2 = axes[1].bar([i + width / 2 for i in x], [count_pq, sum_pq], width, label="Parquet")
        for bar in list(b1) + list(b2):
            axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f"{bar.get_height():.1f}", ha="center", va="bottom")
        axes[1].set_xticks(list(x))
        axes[1].set_xticklabels(["count()", "sum(price)"])
        axes[1].set_title("Read time (mean of runs)")
        axes[1].set_ylabel("Seconds")
        axes[1].legend()
    fig.suptitle("KB3: CSV vs Parquet")
    save_chart("kb3_csv_vs_parquet.png")
else:
    print(f"Bo qua KB3: khong co {kb3_path}")


# ---------- KB5 tu kb5_chart_data.csv cua TV2: so dong bi loai o tung buoc ----------
kb5_path = REPORT_DIR / "kb5_chart_data.csv"
if kb5_path.exists():
    kb5 = pd.read_csv(kb5_path)
    steps = kb5[kb5["chart"] == "cleaning_stages"].set_index("metric")["value"]
    order = ["raw", "after_dedup", "after_timestamp", "after_event_type",
             "after_price", "after_identity"]
    order = [s for s in order if s in steps.index]
    if len(order) >= 2:
        removed = [float(steps[order[i - 1]] - steps[order[i]]) for i in range(1, len(order))]
        labels = [s.replace("after_", "") for s in order[1:]]
        plt.figure(figsize=(9, 5))
        bars = plt.bar(labels, removed)
        add_labels(bars, "{:,.0f}")
        plt.title("KB5: Rows removed at each cleaning step")
        plt.xlabel("Cleaning step")
        plt.ylabel("Rows removed")
        save_chart("kb5_cleaning_steps.png")
else:
    print(f"Bo qua KB5: khong co {kb5_path}")

print("Hoan thanh ve bieu do thuc nghiem!")