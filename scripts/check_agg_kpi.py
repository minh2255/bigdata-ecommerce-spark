"""check_agg_kpi.py - Đối chiếu các bảng agg (03_aggregation.py) với clean/events.   [TV4]

Dùng: python3 check_agg_kpi.py   (đọc DATA_DIR, cần pandas + pyarrow)
Output: $DATA_DIR/reports/kpi_check.json; thoát mã 1 nếu có chỉ số lệch.
Tính độc lập bằng pandas từ clean rồi so với từng bảng agg: tổng doanh thu, số đơn,
tổng số sự kiện theo giờ, số phiên của funnel và số dòng theo ngày.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("DATA_DIR", "/data"))
TOL = 0.01  # sai số tuyệt đối cho tổng tiền (đã làm tròn 2 chữ số theo bảng)


def main():
    clean = pd.read_parquet(ROOT / "clean/events")
    agg = {n: pd.read_parquet(ROOT / "agg" / n)
           for n in ["daily_kpi", "category_kpi", "brand_kpi", "funnel", "hourly"]}
    buy = clean[clean["event_type"] == "purchase"]
    checks = []

    def add(name, expected, actual, tol=0.0):
        ok = abs(float(expected) - float(actual)) <= tol
        checks.append({"check": name, "expected": float(expected), "actual": float(actual), "ok": bool(ok)})

    n_days = clean["event_date"].nunique()
    add("daily_kpi: so ngay", n_days, len(agg["daily_kpi"]))
    for col, et in [("views", "view"), ("carts", "cart"), ("purchases", "purchase")]:
        add(f"daily_kpi: tong {col}", (clean["event_type"] == et).sum(), agg["daily_kpi"][col].sum())
    add("daily_kpi: tong doanh thu", buy["price"].sum(), agg["daily_kpi"]["revenue"].sum(),
        TOL * max(1, len(agg["daily_kpi"])))
    add("category_kpi: tong so don", len(buy), agg["category_kpi"]["orders"].sum())
    add("category_kpi: tong doanh thu", buy["price"].sum(), agg["category_kpi"]["revenue"].sum(),
        TOL * max(1, len(agg["category_kpi"])))
    add("brand_kpi: tong so don", len(buy), agg["brand_kpi"]["orders"].sum())
    add("brand_kpi: tong doanh thu", buy["price"].sum(), agg["brand_kpi"]["revenue"].sum(),
        TOL * max(1, len(agg["brand_kpi"])))
    add("hourly: tong su kien", len(clean), agg["hourly"]["count"].sum())
    sess = clean.groupby("event_type")["user_session"].nunique()
    for _, row in agg["funnel"].iterrows():
        add(f"funnel: so phien {row['event_type']}", sess.get(row["event_type"], 0), row["sessions"])
    add("daily_kpi: active_users khong vuot so user duy nhat",
        0, max(0, int(agg["daily_kpi"]["active_users"].max()) - clean["user_id"].nunique()))

    summary = {"data_dir": str(ROOT), "clean_rows": int(len(clean)), "purchases": int(len(buy)),
               "all_pass": all(c["ok"] for c in checks), "checks": checks}
    out = ROOT / "reports/kpi_check.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for c in checks:
        print(("OK   " if c["ok"] else "FAIL ") + f"{c['check']}: expected={c['expected']} actual={c['actual']}")
    print(f"all_pass={summary['all_pass']} -> {out}")
    sys.exit(0 if summary["all_pass"] else 1)


if __name__ == "__main__":
    main()
