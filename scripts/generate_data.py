"""generate_data.py - Sinh dữ liệu giả cùng schema với Kaggle 2019-Oct.csv.   [TV2]

Dùng để cả nhóm code/test khi chưa có dữ liệu thật. Cố ý chèn lỗi để kiểm tra
job làm sạch và profiling:
  ~1%   dòng trùng hoàn toàn            (cleaning rule 1)
  ~1%   price = 0                       (rule 4)
  ~0.2% event_type lạ ("wishlist")      (rule 3)
  ~0.2% user_session rỗng/toàn khoảng trắng (rule 4, mở rộng TV2)
  ~0.1% price = NaN                     (rule 4, mở rộng TV2)
  ~0.1% price âm                        (rule 4)
  ~0.1% user_id bỏ trống                (rule 4)
  category_code / brand rỗng ~1/6 số dòng (rule 5, 6); brand có chữ hoa ("Apple")

Dùng:  python3 generate_data.py [số_dòng=200000]
Input : không
Output: $DATA_DIR/landing/synthetic.csv   (tên có chữ "synthetic": pipeline_preflight yêu cầu)
        $DATA_DIR/reports/source.json           (data_kind = SYNTHETIC_TEST_ONLY)
        $DATA_DIR/reports/generate_data_truth.json (số lỗi đã chèn, để đối chiếu profiling)
Log   : [GEN] wrote ~N rows to ...
"""
import csv
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

DATA_DIR = os.environ.get("DATA_DIR", "/data")
n = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
out = f"{DATA_DIR}/landing/synthetic.csv"
HEADER = ["event_time", "event_type", "product_id", "category_id", "category_code",
          "brand", "price", "user_id", "user_session"]

if os.path.exists(out):
    sys.exit(f"[GEN] {out} đã tồn tại; xóa nó hoặc đặt DATA_DIR mới (không ghi đè)")
os.makedirs(os.path.dirname(out), exist_ok=True)

cats = ["electronics.smartphone", "computers.notebook", "appliances.kitchen.refrigerator",
        "apparel.shoes", "furniture.living_room.sofa", ""]
brands = ["samsung", "Apple", "xiaomi", "huawei", "lg", ""]
start = datetime(2019, 10, 1)
random.seed(42)
truth = {"requested_rows": n, "duplicate_rows": 0, "price_zero": 0, "price_negative": 0,
         "price_nan": 0, "bad_event_type": 0, "blank_session": 0, "null_user_id": 0}

rows_written = 0
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    for _ in range(n):
        ts = start + timedelta(seconds=random.randint(0, 31 * 24 * 3600 - 1))
        r = random.random()
        if r < 0.01:
            price, key = 0.0, "price_zero"
        elif r < 0.011:
            price, key = -round(random.uniform(1, 100), 2), "price_negative"
        elif r < 0.012:
            price, key = "nan", "price_nan"
        else:
            price, key = round(random.uniform(1, 2000), 2), None
        if key:
            truth[key] += 1

        etype = random.choices(["view", "cart", "purchase"], weights=[90, 7, 3])[0]
        if random.random() < 0.002:
            etype = "wishlist"
            truth["bad_event_type"] += 1

        session = str(uuid.UUID(int=random.getrandbits(128), version=4))
        if random.random() < 0.002:
            session = random.choice(["", "   "])
            truth["blank_session"] += 1

        user_id = random.randint(500000000, 600000000)
        if random.random() < 0.001:
            user_id = ""
            truth["null_user_id"] += 1

        row = [ts.strftime("%Y-%m-%d %H:%M:%S UTC"), etype,
               random.randint(1000000, 1100000),
               random.randint(2053013552226107000, 2053013552226108000),
               random.choice(cats), random.choice(brands), price, user_id, session]
        w.writerow(row)
        rows_written += 1
        if random.random() < 0.01:
            w.writerow(row)          # dòng trùng cố ý
            rows_written += 1
            truth["duplicate_rows"] += 1

truth["total_rows_written"] = rows_written
os.makedirs(f"{DATA_DIR}/reports", exist_ok=True)
source_path = f"{DATA_DIR}/reports/source.json"
if not os.path.exists(source_path):
    with open(source_path, "w") as f:
        json.dump({"data_kind": "SYNTHETIC_TEST_ONLY", "generator": "scripts/generate_data.py",
                   "seed": 42}, f, indent=2)
with open(f"{DATA_DIR}/reports/generate_data_truth.json", "w") as f:
    json.dump(truth, f, indent=2)
print(f"[GEN] wrote ~{n} rows ({rows_written} incl. duplicates) to {out}")
print(f"[GEN] injected: {json.dumps(truth)}")
