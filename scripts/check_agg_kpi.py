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

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("DATA_DIR", "/data"))
TOL = 0.01  # sai số tuyệt đối cho tổng tiền (đã làm tròn 2 chữ số theo bảng)


def main():
    agg = {n: pd.read_parquet(ROOT / "agg" / n)
           for n in ["daily_kpi", "category_kpi", "brand_kpi", "funnel", "hourly"]}
    # Đọc từng thư mục ngày, chỉ lấy cột cần; phiên/người dùng đếm duy nhất qua hash uint64
    # để vừa bộ nhớ khi clean có hàng chục triệu dòng (đọc nguyên bảng vào pandas bị OOM).
    ev = ["view", "cart", "purchase"]
    counts = {e: 0 for e in ev}
    n_rows = n_days = 0
    revenue = 0.0
    sess_hash = {e: [] for e in ev}
    user_hash = []
    for day in sorted((ROOT / "clean/events").glob("event_date=*")):
        d = pd.read_parquet(day, columns=["event_type", "price", "user_id", "user_session"])
        n_days += 1
        n_rows += len(d)
        for e in ev:
            m = d["event_type"] == e
            counts[e] += int(m.sum())
            sess_hash[e].append(np.unique(pd.util.hash_array(d.loc[m, "user_session"].to_numpy())))
        revenue += float(d.loc[d["event_type"] == "purchase", "price"].sum())
        user_hash.append(np.unique(d["user_id"].to_numpy()))
    sess = {e: len(np.unique(np.concatenate(sess_hash[e]))) for e in ev}
    n_users = len(np.unique(np.concatenate(user_hash)))
    checks = []

    def add(name, expected, actual, tol=0.0):
        ok = abs(float(expected) - float(actual)) <= tol
        checks.append({"check": name, "expected": float(expected), "actual": float(actual), "ok": bool(ok)})

    add("daily_kpi: so ngay", n_days, len(agg["daily_kpi"]))
    for col, et in [("views", "view"), ("carts", "cart"), ("purchases", "purchase")]:
        add(f"daily_kpi: tong {col}", counts[et], agg["daily_kpi"][col].sum())
    add("daily_kpi: tong doanh thu", revenue, agg["daily_kpi"]["revenue"].sum(),
        TOL * max(1, len(agg["daily_kpi"])))
    add("category_kpi: tong so don", counts["purchase"], agg["category_kpi"]["orders"].sum())
    add("category_kpi: tong doanh thu", revenue, agg["category_kpi"]["revenue"].sum(),
        TOL * max(1, len(agg["category_kpi"])))
    add("brand_kpi: tong so don", counts["purchase"], agg["brand_kpi"]["orders"].sum())
    add("brand_kpi: tong doanh thu", revenue, agg["brand_kpi"]["revenue"].sum(),
        TOL * max(1, len(agg["brand_kpi"])))
    add("hourly: tong su kien", n_rows, agg["hourly"]["count"].sum())
    for _, row in agg["funnel"].iterrows():
        add(f"funnel: so phien {row['event_type']}", sess.get(row["event_type"], 0), row["sessions"])
    add("daily_kpi: active_users khong vuot so user duy nhat",
        0, max(0, int(agg["daily_kpi"]["active_users"].max()) - n_users))

    summary = {"data_dir": str(ROOT), "clean_rows": int(n_rows), "purchases": int(counts["purchase"]),
               "all_pass": all(c["ok"] for c in checks), "checks": checks}
    out = ROOT / "reports/kpi_check.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for c in checks:
        print(("OK   " if c["ok"] else "FAIL ") + f"{c['check']}: expected={c['expected']} actual={c['actual']}")
    print(f"all_pass={summary['all_pass']} -> {out}")
    sys.exit(0 if summary["all_pass"] else 1)


if __name__ == "__main__":
    main()
