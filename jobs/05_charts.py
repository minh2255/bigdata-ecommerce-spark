
import json
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
benchmark_path = REPORT_DIR / "kb4_benchmark.csv"

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


# 5. Bieu do hoat dong theo gio (bang hourly)
hourly = pd.read_parquet(AGG_DIR / "hourly")
hourly_pivot = (
    hourly.pivot_table(index="event_hour", columns="event_type",
                       values="count", aggfunc="sum", fill_value=0)
    .sort_index()
)

plt.figure(figsize=(10, 5))
for event_type in ["view", "cart", "purchase"]:
    if event_type in hourly_pivot.columns:
        plt.plot(hourly_pivot.index, hourly_pivot[event_type],
                 marker="o", label=event_type)
plt.title("Events by Hour (UTC)")
plt.xlabel("Hour of day (UTC)")
plt.ylabel("Number of events")
plt.xticks(range(0, 24))
plt.legend()
save_chart("hourly_activity.png")


# 6. Bieu do top thuong hieu theo doanh thu (bang brand_kpi)
brand = pd.read_parquet(AGG_DIR / "brand_kpi")
top_brand = brand.sort_values("revenue", ascending=False).head(10)
top_brand = top_brand.iloc[::-1]  # dao thu tu de thuong hieu lon nhat nam tren cung

plt.figure(figsize=(10, 6))
plt.barh(top_brand["brand"].astype(str), top_brand["revenue"])
plt.title("Top 10 Brands by Revenue")
plt.xlabel("Revenue")
plt.ylabel("Brand")
save_chart("brand_revenue.png")


# 7. Ty le chuyen doi tu bang funnel (so phien theo tung loai su kien)
sessions = funnel.set_index("event_type")["sessions"]
n_view = float(sessions.get("view", 0))
n_cart = float(sessions.get("cart", 0))
n_purchase = float(sessions.get("purchase", 0))

conversion = {
    "sessions_view": int(n_view),
    "sessions_cart": int(n_cart),
    "sessions_purchase": int(n_purchase),
    "view_to_cart": round(n_cart / n_view, 4) if n_view else None,
    "cart_to_purchase": round(n_purchase / n_cart, 4) if n_cart else None,
    "view_to_purchase": round(n_purchase / n_view, 4) if n_view else None,
    "note": "Moi loai su kien dem so phien rieng; khong phai chuyen doi trong cung mot phien",
}
with open(REPORT_DIR / "conversion_rate.json", "w", encoding="utf-8") as f:
    json.dump(conversion, f, indent=2, ensure_ascii=False)
print("Ty le chuyen doi:", conversion)

print("Hoan thanh tao bieu do!")
