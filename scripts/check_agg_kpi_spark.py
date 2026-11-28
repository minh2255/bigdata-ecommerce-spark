"""check_agg_kpi_spark.py - Doi chieu cac bang agg voi clean/events bang Spark (cho du lieu lon).   [TV4]

Dung: spark-submit check_agg_kpi_spark.py   (doc DATA_DIR)
Output: $DATA_DIR/reports/kpi_check.json; thoat ma 1 neu co chi so lech.
Khac check_agg_kpi.py (pandas): ban nay tinh lai bang Spark tu clean nen khong
can nap ca 42 trieu dong vao bo nho mot may. Cach tinh khac 03_aggregation.py
(dung DataFrame API mot lan quet, khong dung Spark SQL).
"""
import json
import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(os.environ.get("DATA_DIR", "/data"))
TOL = 0.01  # sai so tuyet doi cho tong tien (moi nhom da lam tron 2 chu so)

spark = (SparkSession.builder.appName("check_agg_kpi")
         .config("spark.sql.session.timeZone", "UTC").getOrCreate())

clean = spark.read.parquet(str(ROOT / "clean/events"))
agg = {name: spark.read.parquet(str(ROOT / "agg" / name)).toPandas()
       for name in ["daily_kpi", "category_kpi", "brand_kpi", "funnel", "hourly"]}

# Gia tri mong doi: tinh lai tu clean (mot lan quet cho cac tong, mot lan cho so phien)
is_view = F.col("event_type") == "view"
is_cart = F.col("event_type") == "cart"
is_buy = F.col("event_type") == "purchase"
exp = clean.agg(
    F.count("*").alias("rows"),
    F.sum(F.when(is_view, 1).otherwise(0)).alias("views"),
    F.sum(F.when(is_cart, 1).otherwise(0)).alias("carts"),
    F.sum(F.when(is_buy, 1).otherwise(0)).alias("purchases"),
    F.sum(F.when(is_buy, F.col("price")).otherwise(0.0)).alias("revenue"),
    F.countDistinct("event_date").alias("days"),
    F.countDistinct("user_id").alias("users"),
).first().asDict()
sessions = {row["event_type"]: row["n"] for row in
            clean.groupBy("event_type").agg(F.countDistinct("user_session").alias("n")).collect()}

checks = []


def add(name, expected, actual, tol=0.0):
    ok = abs(float(expected) - float(actual)) <= tol
    checks.append({"check": name, "expected": float(expected), "actual": float(actual), "ok": bool(ok)})


daily, category, brand = agg["daily_kpi"], agg["category_kpi"], agg["brand_kpi"]
add("daily_kpi: so ngay", exp["days"], len(daily))
add("daily_kpi: tong views", exp["views"], daily["views"].sum())
add("daily_kpi: tong carts", exp["carts"], daily["carts"].sum())
add("daily_kpi: tong purchases", exp["purchases"], daily["purchases"].sum())
add("daily_kpi: tong doanh thu", exp["revenue"], daily["revenue"].sum(), TOL * max(1, len(daily)))
add("category_kpi: tong so don", exp["purchases"], category["orders"].sum())
add("category_kpi: tong doanh thu", exp["revenue"], category["revenue"].sum(), TOL * max(1, len(category)))
add("brand_kpi: tong so don", exp["purchases"], brand["orders"].sum())
add("brand_kpi: tong doanh thu", exp["revenue"], brand["revenue"].sum(), TOL * max(1, len(brand)))
add("hourly: tong su kien", exp["rows"], agg["hourly"]["count"].sum())
for _, row in agg["funnel"].iterrows():
    add(f"funnel: so phien {row['event_type']}", sessions.get(row["event_type"], 0), row["sessions"])
add("daily_kpi: active_users khong vuot so user duy nhat",
    0, max(0, int(daily["active_users"].max()) - int(exp["users"])))
# Bang conversion chi co tu ban 03_aggregation.py moi; vung agg cu khong co thi bo qua
conv_path = ROOT / "agg/conversion"
if conv_path.exists():
    conv = spark.read.parquet(str(conv_path)).first().asDict()
    v, c, p = (sessions.get(e, 0) for e in ("view", "cart", "purchase"))
    add("conversion: view_to_cart", round(c / v, 4) if v else 0, conv["view_to_cart"] or 0, 1e-4)
    add("conversion: cart_to_purchase", round(p / c, 4) if c else 0, conv["cart_to_purchase"] or 0, 1e-4)
    add("conversion: view_to_purchase", round(p / v, 4) if v else 0, conv["view_to_purchase"] or 0, 1e-4)

summary = {"data_dir": str(ROOT), "clean_rows": int(exp["rows"]), "purchases": int(exp["purchases"]),
           "all_pass": all(c["ok"] for c in checks), "checks": checks}
out = ROOT / "reports/kpi_check.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
for c in checks:
    print(("OK   " if c["ok"] else "FAIL ") + f"{c['check']}: expected={c['expected']} actual={c['actual']}", flush=True)
print(f"all_pass={summary['all_pass']} -> {out}", flush=True)
spark.stop()
sys.exit(0 if summary["all_pass"] else 1)
sys.exit(0 if summary["all_pass"] else 1)