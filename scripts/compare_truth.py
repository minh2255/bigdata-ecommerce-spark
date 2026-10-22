"""compare_truth.py - So số lỗi generate_data.py đã chèn với số dòng cleaning đã loại.   [TV2]

Dùng: python scripts/compare_truth.py <thư_mục_vùng_dữ_liệu>
  ví dụ: python scripts/compare_truth.py data/synthetic_tv2_test
Input : <vùng>/reports/generate_data_truth.json, <vùng>/reports/cleaning_metrics.json
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
d = (sys.argv[1] if len(sys.argv) > 1 else "data/synthetic_tv2_test").rstrip("/") + "/reports/"
t = json.load(open(d + "generate_data_truth.json"))
m = json.load(open(d + "cleaning_metrics.json"))
r, c = m["removed"], m["counts"]
price = t["price_zero"] + t["price_negative"] + t["price_nan"]
ident = t["blank_session"] + t["null_user_id"]
rows = [
    ("Tổng dòng raw", t["total_rows_written"], c["raw"], "exact"),
    ("Dòng trùng", t["duplicate_rows"], r["raw_to_after_dedup"], "exact"),
    ("event_type lạ", t["bad_event_type"], r["after_timestamp_to_after_event_type"], "near"),
    ("Giá 0/âm/NaN", price, r["after_event_type_to_after_price"], "near"),
    ("Session trống + user null", ident, r["after_price_to_after_identity"], "near"),
]
bad = 0
print(f"{'Mục':28}{'Đã chèn':>9}{'Bị loại':>9}  Kết quả")
for name, inj, rem, mode in rows:
    # "near": một dòng có thể dính nhiều lỗi nên chỉ bị tính ở bước loại đầu tiên => rem <= inj
    ok = inj == rem if mode == "exact" else rem <= inj and inj - rem <= 0.02 * inj + 20
    bad += not ok
    print(f"{name:28}{inj:>9}{rem:>9}  {'OK' if ok else 'LỆCH'}")
print(f"status={m['status']} written={c['written']}")
sys.exit(1 if bad else 0)
