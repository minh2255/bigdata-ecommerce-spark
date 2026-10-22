"""Independent integration check with PyArrow (no Spark transformations).

python3 /opt/scripts/check_cleaning.py fixture /data/<new-fixture-lake>
python3 /opt/scripts/check_cleaning.py verify /data/<completed-lake>
This is bounded TV3 fixture validation (maximum 10000 raw/output rows).
Use jobs/validate_cleaning.py for large datasets. This is not TV2 profiling.
"""
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

import pyarrow.parquet as pq


def fixture(root, kind="mixed"):
    base = dict(event_time="2019-10-01 23:45:00 UTC", event_type="purchase",
                product_id=1, category_id=2, category_code="electronics.smartphone",
                brand=" Apple ", price=10.5, user_id=3, user_session="session-good")
    rows = [base, base.copy(),
            dict(base, user_session="session-blank", category_code="", brand=" "),
            dict(base, user_session="session-short", category_code="apparel", brand=None)]
    for col, value in [("event_time", "bad-time"), ("event_type", "remove"),
                       ("price", 0), ("price", -1), ("price", None),
                       ("price", "NaN"), ("price", "Infinity"),
                       ("user_id", None), ("user_session", None), ("user_session", " ")]:
        rows.append(dict(base, **{col: value}))
    if kind == "empty":
        rows = []
    elif kind == "all-invalid":
        rows = [dict(base, price=0), dict(base, event_time="bad-time")]
    elif kind == "valid-repeat":
        rows = [base, dict(base, event_type="view"),
                dict(base, event_time="2019-10-02 00:15:00 UTC", user_id=-3)]
    elif kind != "mixed":
        raise ValueError(kind)
    (root / "landing").mkdir(parents=True, exist_ok=True)
    with (root / "landing/synthetic_fixture.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(base))
        writer.writeheader()
        writer.writerows(rows)
    (root / "reports").mkdir(exist_ok=True)
    with (root / "reports/source.json").open("x", encoding="utf-8") as handle:
        json.dump({"data_kind": "SYNTHETIC_TEST_ONLY", "fixture": kind,
                   "real_kaggle_data": False}, handle, indent=2)
    print(f"[FIXTURE] kind={kind} input_rows={len(rows)}")


def verify(root):
    source_file = root / "reports/source.json"
    source = json.loads(source_file.read_text()) if source_file.exists() else {}
    if source.get("data_kind") not in {"SYNTHETIC_TEST_ONLY", "synthetic"}:
        raise ValueError("Fixture verifier requires explicit synthetic provenance; use validate_cleaning.py for real data")
    for layer in ("raw", "clean"):
        total = sum(pq.ParquetFile(path).metadata.num_rows
                    for path in (root / layer / "events").rglob("*.parquet"))
        if total > 10000:
            raise ValueError("Fixture verifier is bounded to 10000 rows; use validate_cleaning.py")
    raw = pq.read_table(root / "raw/events").to_pylist()
    counts = {"raw": len(raw)}
    def canonical(row):
        return tuple((key, "__NaN__" if isinstance(value, float) and math.isnan(value) else value)
                     for key, value in sorted(row.items()))
    dedup = list({canonical(r): r for r in raw}.values())
    counts["after_dedup"] = len(dedup)
    valid_time = []
    for row in dedup:
        try:
            ts = datetime.strptime(row["event_time"], "%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError):
            continue
        valid_time.append((row, ts))
    counts["after_timestamp"] = len(valid_time)
    valid_type = [(r, t) for r, t in valid_time if r["event_type"] in {"view", "cart", "purchase"}]
    counts["after_event_type"] = len(valid_type)
    valid_price = [(r, t) for r, t in valid_type
                   if r["price"] is not None and math.isfinite(r["price"]) and r["price"] > 0]
    counts["after_price"] = len(valid_price)
    valid = [(r, t) for r, t in valid_price
             if r["user_id"] is not None and r["user_session"] and r["user_session"].strip()]
    counts["after_identity"] = len(valid)
    actual_table = pq.read_table(root / "clean/events")
    actual = actual_table.to_pylist()
    counts["written"] = len(actual)
    metrics = json.loads((root / "reports/cleaning_metrics.json").read_text())
    assert metrics["counts"] == counts, (metrics["counts"], counts)
    expected = []
    def unknown(value):
        return value.strip() if value and value.strip() else "unknown"
    for row, ts in valid:
        cats = (row["category_code"] or "").split(".")
        expected.append({
            **{k: v for k, v in row.items() if k != "event_time"},
            "brand": unknown((row["brand"] or "").lower()),
            "cat_l1": unknown(cats[0]), "cat_l2": unknown(cats[1] if len(cats) > 1 else None),
            "event_ts": ts, "event_date": ts.strftime("%Y-%m-%d"),
            "event_hour": ts.hour, "day_of_week": ts.strftime("%a"),
        })
    for row in actual:
        row["event_date"] = str(row["event_date"])
    assert Counter(map(canonical, actual)) == Counter(map(canonical, expected)), "Output value/multiplicity mismatch"
    dates = sorted(p.name for p in (root / "clean/events").glob("event_date=*"))
    assert len(dates) == len({t.date() for _, t in valid})
    report = {"status": "PASS", "data_kind": "SYNTHETIC_TEST_ONLY", "counts": counts,
              "date_partitions": len(dates), "parquet_files": len(list((root / "clean/events").rglob("*.parquet"))),
              "schema": str(actual_table.schema),
              "checks": ["all output values vs independent Python rules", "per-stage counts",
                         "UTC derived columns", "date partitions", "invalid prices and identities"]}
    with (root / "reports/tv3_validation.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if sys.argv[1] == "fixture":
        fixture(Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "mixed")
    else:
        {"verify": verify}[sys.argv[1]](Path(sys.argv[2]))
