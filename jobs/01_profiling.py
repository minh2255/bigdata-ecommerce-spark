"""01_profiling.py - Đo chất lượng dữ liệu của một tầng.   [TV2]

Dùng: spark-submit 01_profiling.py raw    # trước cleaning, đọc $DATA_DIR/raw/events
      spark-submit 01_profiling.py clean  # sau cleaning,  đọc $DATA_DIR/clean/events
Input : $DATA_DIR/raw/events hoặc $DATA_DIR/clean/events (Parquet)
Output: $DATA_DIR/reports/profiling_{layer}.json  (không ghi đè nếu đã có)
Log   : [PROFILE] ...
Luật đối chiếu: docs/data_contract.md. Tầng clean thoát mã 1 nếu vi phạm bất biến ở mục 4.
"""
import json
import os
import sys
import time
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

EVENT_TYPES = ("view", "cart", "purchase")
UUID_RE = r"(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
TIME_RE = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC$"
RAW_STRING = ["event_time", "event_type", "category_code", "brand", "user_session"]
CLEAN_STRING = ["event_type", "category_code", "brand", "user_session", "cat_l1", "cat_l2", "day_of_week"]


def count_if(condition):
    return F.count(F.when(condition, 1))


def finite(price):
    return price.isNotNull() & ~F.isnan(price) & (price != F.lit(float("inf"))) \
        & (price != F.lit(float("-inf")))


def blank(column):
    return column.isNotNull() & (F.length(F.trim(column)) == 0)


def common_exprs(df):
    """Biểu thức đếm dùng chung cho raw và clean: null mỗi cột, giá, ID, tập phân biệt."""
    price = F.col("price")
    exprs = {"rows": F.count(F.lit(1))}
    for name in df.columns:
        exprs[f"null__{name}"] = count_if(F.col(name).isNull())
    for name in RAW_STRING if "event_time" in df.columns else CLEAN_STRING:
        exprs[f"blank__{name}"] = count_if(blank(F.col(name)))
    exprs.update({
        "price_null": count_if(price.isNull()),
        "price_le_0": count_if(price <= 0),
        "price_negative": count_if(price < 0),
        "price_zero": count_if(price == 0),
        "price_nan": count_if(F.isnan(price)),
        "price_inf": count_if(price.isin(float("inf"), float("-inf"))),
        "price_min": F.min(F.when(finite(price), price)),
        "price_max": F.max(F.when(finite(price), price)),
        "price_mean": F.avg(F.when(finite(price), price)),
        "user_id_le_0": count_if(F.col("user_id") <= 0),
        "product_id_le_0": count_if(F.col("product_id") <= 0),
        "category_id_le_0": count_if(F.col("category_id") <= 0),
        "session_not_uuid": count_if(F.col("user_session").isNotNull()
                                     & ~F.col("user_session").rlike(UUID_RE)),
        "event_type_invalid": count_if(F.col("event_type").isNotNull()
                                       & ~F.col("event_type").isin(*EVENT_TYPES)),
        "distinct_users": F.approx_count_distinct("user_id"),
        "distinct_sessions": F.approx_count_distinct("user_session"),
        "distinct_products": F.approx_count_distinct("product_id"),
    })
    return exprs


def layer_exprs(layer, df):
    exprs = common_exprs(df)
    if layer == "raw":
        ts = F.try_to_timestamp(F.regexp_replace("event_time", " UTC$", ""),
                                F.lit("yyyy-MM-dd HH:mm:ss"))
        exprs.update({
            "event_time_bad_format": count_if(F.col("event_time").isNotNull()
                                              & ~F.col("event_time").rlike(TIME_RE)),
            "event_time_unparsable": count_if(ts.isNull()),
            "ts_min": F.min(ts),
            "ts_max": F.max(ts),
            "brand_has_upper": count_if(F.col("brand") != F.lower(F.col("brand"))),
            "brand_has_outer_space": count_if(F.col("brand") != F.trim(F.col("brand"))),
        })
    else:
        exprs.update({
            "ts_min": F.min("event_ts"),
            "ts_max": F.max("event_ts"),
            "date_min": F.min("event_date"),
            "date_max": F.max("event_date"),
            "event_hour_min": F.min("event_hour"),
            "event_hour_max": F.max("event_hour"),
            "brand_unknown": count_if(F.col("brand") == "unknown"),
            "cat_l1_unknown": count_if(F.col("cat_l1") == "unknown"),
            "cat_l2_unknown": count_if(F.col("cat_l2") == "unknown"),
            "day_of_week_invalid": count_if(~F.col("day_of_week").isin(
                "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")),
        })
    return exprs


def plain(value):
    if value is None or isinstance(value, (int, bool)):
        return value
    if isinstance(value, float):
        return None if value != value else value
    return str(value)


def ratio(part, total):
    return round(part / total, 6) if total else None


def build_report(layer, df, root):
    started = time.perf_counter()
    row = df.agg(*[expr.alias(key) for key, expr in layer_exprs(layer, df).items()]).first()
    m = {key: plain(row[key]) for key in row.asDict()}
    rows = m["rows"]
    empty = rows == 0

    # Dòng trùng cả 9 cột (raw) / cả cột clean (clean: trùng còn lại sau chuẩn hóa).
    distinct_rows = df.dropDuplicates().count()
    event_type_counts = {r["event_type"]: r["count"]
                         for r in df.groupBy("event_type").count().collect()}

    report = {
        "layer": layer,
        "data_dir": str(root),
        "timezone": "UTC",
        "status": "SUCCESS_EMPTY" if empty else "SUCCESS",
        "rows": rows,
        "columns": df.columns,
        "duplicate_rows": rows - distinct_rows,
        "duplicate_ratio": ratio(rows - distinct_rows, rows),
        "nulls": {c: m[f"null__{c}"] for c in df.columns},
        "blank_strings": {k.split("__", 1)[1]: v for k, v in m.items() if k.startswith("blank__")},
        "price": {key: m[key] for key in (
            "price_null", "price_le_0", "price_negative", "price_zero", "price_nan", "price_inf",
            "price_min", "price_max", "price_mean")},
        "price_le_0_ratio": ratio(m["price_le_0"], rows),
        "event_type_counts": {str(k): v for k, v in sorted(
            event_type_counts.items(), key=lambda kv: str(kv[0]))},
        "event_type_invalid": m["event_type_invalid"],
        "ids": {key: m[key] for key in (
            "user_id_le_0", "product_id_le_0", "category_id_le_0", "session_not_uuid")},
        "distinct_approx": {"users": m["distinct_users"], "sessions": m["distinct_sessions"],
                            "products": m["distinct_products"]},
        "timestamp_min": m["ts_min"],
        "timestamp_max": m["ts_max"],
    }
    if layer == "raw":
        report["event_time"] = {"bad_format": m["event_time_bad_format"],
                                "unparsable": m["event_time_unparsable"]}
        report["brand_normalization_needed"] = {
            "has_upper": m["brand_has_upper"], "has_outer_space": m["brand_has_outer_space"]}
    else:
        report["date_range"] = {"min": m["date_min"], "max": m["date_max"]}
        report["event_hour_range"] = {"min": m["event_hour_min"], "max": m["event_hour_max"]}
        report["unknown_ratio"] = {
            "brand": ratio(m["brand_unknown"], rows),
            "cat_l1": ratio(m["cat_l1_unknown"], rows),
            "cat_l2": ratio(m["cat_l2_unknown"], rows),
            "brand_rows": m["brand_unknown"], "cat_l1_rows": m["cat_l1_unknown"],
            "cat_l2_rows": m["cat_l2_unknown"]}
        report["invariants"] = check_invariants(report, m, root)
    report["profile_seconds"] = round(time.perf_counter() - started, 3)
    return report


# Ghi chú: Spark đọc CSV với nanValue mặc định "NaN"; chuỗi "nan"/"inf" không parse được sẽ thành
# null ở raw, nên giá NaN/Inf của file CSV có thể hiện ở price_null thay vì price_nan/price_inf.


def check_invariants(report, m, root):
    """Bất biến ở mục 4 của docs/data_contract.md. Tập rỗng thì mọi bất biến đúng hiển nhiên."""
    required = ["price", "user_id", "user_session", "brand", "cat_l1", "cat_l2", "event_ts", "event_date"]
    checks = {
        "no_price_le_0": m["price_le_0"] == 0,
        "no_price_nan_or_inf": m["price_nan"] == 0 and m["price_inf"] == 0,
        "no_null_required_columns": all(report["nulls"][c] == 0 for c in required),
        "no_blank_session": m["blank__user_session"] == 0,
        "event_type_valid": m["event_type_invalid"] == 0,
        "event_hour_0_23": m["rows"] == 0 or (0 <= m["event_hour_min"] and m["event_hour_max"] <= 23),
        "day_of_week_valid": m["day_of_week_invalid"] == 0,
    }
    raw_path = root / "reports/profiling_raw.json"
    if raw_path.exists() and m["rows"]:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        # Ngày UTC nằm trong khoảng thời gian của raw; raw đã dedup nên clean không nhiều hơn raw.
        checks["date_within_raw_range"] = (
            str(m["date_min"]) >= str(raw["timestamp_min"])[:10]
            and str(m["date_max"]) <= str(raw["timestamp_max"])[:10])
        checks["rows_not_more_than_raw_distinct"] = (
            m["rows"] <= raw["rows"] - raw["duplicate_rows"])
    checks["all_pass"] = all(checks.values())
    return checks


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("raw", "clean"):
        print("Usage: 01_profiling.py raw|clean", file=sys.stderr)
        sys.exit(2)
    layer = sys.argv[1]
    root = Path(os.environ.get("DATA_DIR", "/data"))
    source = root / layer / "events"
    out = root / f"reports/profiling_{layer}.json"
    if out.exists():
        raise FileExistsError(f"{out} exists; choose a new DATA_DIR to preserve it")
    spark = (SparkSession.builder.appName(f"01_profiling_{layer}")
             .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    try:
        df = spark.read.parquet(str(source))
        report = build_report(layer, df, root)
        meta = root / "reports/source.json"
        report["data_kind"] = (os.environ.get("DATA_KIND")
                               or (json.loads(meta.read_text()).get("data_kind") if meta.exists() else None)
                               or "UNKNOWN")
        report["application_id"] = spark.sparkContext.applicationId
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        print(f"[PROFILE] layer={layer} rows={report['rows']} duplicates={report['duplicate_rows']} "
              f"price_le_0={report['price']['price_le_0']} status={report['status']} "
              f"time={report['profile_seconds']}s -> {out}", flush=True)
        failed = [k for k, v in report.get("invariants", {}).items() if v is False]
        if failed:
            print(f"[PROFILE] INVARIANT FAILED: {failed}", file=sys.stderr, flush=True)
            sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
