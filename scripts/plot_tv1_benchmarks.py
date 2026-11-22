"""plot_tv1_benchmarks.py - Vẽ KB1, KB2, KB6 từ docs/evidence/tv1/benchmark_final.csv.   [TV1]

Dùng: python3 plot_tv1_benchmarks.py <benchmark_final.csv> <thư mục ra>
Mỗi cấu hình có 3 lần lặp: cột là trung bình, chấm là từng lần đo.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(src, dtype={"fraction": str, "cores": str})


def bars(sub, key, title, xlabel, name, order=None):
    order = order or list(dict.fromkeys(sub[key]))
    plt.figure(figsize=(7, 4.5))
    for i, k in enumerate(order):
        v = sub[sub[key] == k]["seconds"]
        plt.bar(i, v.mean(), color="#6c8ebf", alpha=0.8)
        plt.scatter([i] * len(v), v, color="black", s=14, zorder=3)
    plt.xticks(range(len(order)), order)
    plt.title(title); plt.xlabel(xlabel); plt.ylabel("Thời gian (giây)")
    plt.tight_layout(); plt.savefig(out / name, dpi=150); plt.close()
    print("Da tao", name)


bars(df[df.label == "size"], "fraction", "KB1 - df.sample(): thời gian theo tỷ lệ dữ liệu", "Tỷ lệ mẫu", "kb1_size_sample.png")
bars(df[df.label == "sizedays"], "fraction", "KB1 - lọc theo ngày: thời gian theo tỷ lệ dữ liệu", "Tỷ lệ số ngày", "kb1_size_days.png")
bars(df[df.label == "cores"], "cores", "KB2 - thời gian theo số core", "Tổng số core", "kb2_cores.png", ["1", "2", "4"])
bars(df[df.label.isin(["part8", "part50", "part200"])], "label", "KB6 - thời gian theo shuffle.partitions", "spark.sql.shuffle.partitions", "kb6_partitions.png", ["part8", "part50", "part200"])
