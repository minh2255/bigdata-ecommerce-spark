"""Plot completed synthetic validation/benchmarks; not TV4's missing KPI charts."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

root = Path(sys.argv[1])
out = root / "reports"
source = json.loads((out / "source.json").read_text())
if source.get("data_kind") != "SYNTHETIC_TEST_ONLY":
    raise ValueError("This plotting script requires explicitly marked synthetic test data")
metrics = json.loads((out / "cleaning_metrics.json").read_text())
names = ["raw", "after_dedup", "after_timestamp", "after_event_type", "after_price", "after_identity"]
values = [metrics["counts"][name] for name in names]
fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(["Input", "Deduplicated", "Valid time", "Valid event", "Valid price", "Valid identity"], values, color="#24748e")
ax.invert_yaxis()
for i, value in enumerate(values):
    ax.text(value, i, f"  {value:,}", va="center", fontsize=10)
ax.set_xlim(0, max(values) * 1.2)
ax.set_xlabel("Rows")
ax.set_title("TV3 cleaning checks — SYNTHETIC DATA ONLY")
fig.tight_layout()
path = out / "tv3_cleaning_synthetic.png"
if path.exists():
    raise FileExistsError(path)
fig.savefig(path, dpi=160)
plt.close(fig)

if (out / "benchmark_runs.jsonl").exists():
    frame = pd.read_json(out / "benchmark_runs.jsonl", lines=True)
    panels = [("size", "fraction", "KB1 · sampled fraction (all input files scanned)"),
              ("cores", "cores", "KB2 · executor core limit"),
              ("part", "shuffle_partitions", "KB6 · configured shuffle partitions (AQE on)")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    summary = []
    for ax, (label, column, title) in zip(axes, panels):
        selected = frame[frame.label.str.startswith(label)].copy()
        selected[column] = pd.to_numeric(selected[column])
        stats = selected.groupby(column).seconds.agg(["mean", "std", "count"])
        if stats.empty or (stats["count"] < 3).any():
            raise ValueError(f"Incomplete experiment: {label} needs >=3 repeats per configuration")
        ax.bar(stats.index.astype(str), stats["mean"], yerr=stats["std"].fillna(0), capsize=4, color="#24748e")
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Action time (seconds)")
        ax.set_xlabel(column)
        for value, row in stats.iterrows():
            summary.append({"experiment": label, "configuration": value, **row.to_dict()})
    fig.suptitle("SYNTHETIC DATA ONLY · mean ± sample SD · 3 repeats · excludes Spark startup")
    fig.tight_layout()
    path = out / "tv3_benchmarks_synthetic.png"
    if path.exists():
        raise FileExistsError(path)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    with (out / "tv3_benchmark_summary.csv").open("x", newline="") as handle:
        pd.DataFrame(summary).to_csv(handle, index=False)
if (out / "storage_benchmark.jsonl").exists():
    frame = pd.read_json(out / "storage_benchmark.jsonl", lines=True)
    stats = frame.groupby("format").seconds.agg(["mean", "std", "count"])
    if set(stats.index) != {"csv", "parquet"} or (stats["count"] != 3).any():
        raise ValueError("KB3 needs exactly three trials per format")
    sizes = json.loads((out / "storage_sizes.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    order = ["csv", "parquet"]
    axes[0].bar(order, [sizes[key] / 1024**2 for key in order], color="#24748e")
    axes[0].set_ylabel("MiB (data files only)")
    axes[0].set_title("Raw storage size")
    axes[1].bar(order, stats.loc[order, "mean"], yerr=stats.loc[order, "std"], capsize=4, color="#24748e")
    axes[1].set_ylabel("Seconds (mean ± sample SD)")
    axes[1].set_title("Read + count; 3 trials; OS cache retained")
    fig.suptitle("KB3 support measurement · SYNTHETIC DATA ONLY")
    fig.tight_layout()
    path = out / "tv3_storage_synthetic.png"
    if path.exists():
        raise FileExistsError(path)
    fig.savefig(path, dpi=160)
    plt.close(fig)
print(f"[TV3 CHARTS] {out}; SYNTHETIC DATA ONLY")
