
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
AGG_DIR = DATA_DIR / "agg"
REPORT_DIR = DATA_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(REPORT_DIR / filename, dpi=150)
    plt.close()
    print(f"Da tao: {filename}")


# 1. Bieu do doanh thu theo ngay
daily = pd.read_parquet(AGG_DIR / "daily_kpi")
daily = daily.sort_values("event_date")

plt.figure(figsize=(10, 5))
plt.plot(
    daily["event_date"].astype(str),
    daily["revenue"],
    marker="o"
)
plt.title("Daily Revenue")
plt.xlabel("Date")
plt.ylabel("Revenue")
plt.xticks(rotation=45)
save_chart("daily_revenue.png")


# 2. Bieu do doanh thu theo danh muc
category = pd.read_parquet(AGG_DIR / "category_kpi")
category = category.sort_values("revenue", ascending=False).head(10)

plt.figure(figsize=(10, 5))
plt.bar(category["cat_l1"].astype(str), category["revenue"])
plt.title("Top Categories by Revenue")
plt.xlabel("Category")
plt.ylabel("Revenue")
plt.xticks(rotation=45)
save_chart("category_revenue.png")


# 3. Bieu do so phien theo loai hanh vi
funnel = pd.read_parquet(AGG_DIR / "funnel")
order = ["view", "cart", "purchase"]

funnel = (
    funnel.set_index("event_type")
    .reindex(order, fill_value=0)
    .reset_index()
)

plt.figure(figsize=(8, 5))
plt.bar(funnel["event_type"], funnel["sessions"])
plt.title("Sessions by Event Type")
plt.xlabel("Event Type")
plt.ylabel("Distinct Sessions")
save_chart("funnel.png")


# 4. Bieu do benchmark Pandas va Spark
benchmark_path = REPORT_DIR / "benchmark.csv"

if benchmark_path.exists():
    benchmark = pd.read_csv(benchmark_path)

    if not benchmark.empty:
        benchmark["seconds"] = pd.to_numeric(
            benchmark["seconds"], errors="coerce"
        )

        summary = (
            benchmark.dropna(subset=["seconds"])
            .groupby(["engine", "fraction"], as_index=False)["seconds"]
            .mean()
        )

        summary["fraction"] = summary["fraction"].astype(str)

        plt.figure(figsize=(9, 5))

        for engine, group in summary.groupby("engine"):
            plt.plot(
                group["fraction"],
                group["seconds"],
                marker="o",
                label=engine
            )

        plt.title("Pandas vs Spark Benchmark")
        plt.xlabel("Data Fraction")
        plt.ylabel("Average Execution Time (seconds)")
        plt.legend()
        save_chart("pandas_vs_spark.png")

print("Hoan thanh tao bieu do!")
