"""TV3 validation using distributed reductions; returns only scalar results.

Not a replacement for TV2 profiling. No full collect or toPandas is used.
"""
import json
import os
from pathlib import Path

from pyspark.sql import SparkSession, functions as F


def main():
    root = Path(os.environ.get("DATA_DIR", "/data"))
    report = root / "reports/cleaning_validation_spark.json"
    if report.exists():
        raise FileExistsError(report)
    metrics = json.loads((root / "reports/cleaning_metrics.json").read_text())
    spark = (SparkSession.builder.appName("tv3_validate_cleaning")
             .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    try:
        frame = spark.read.parquet(str(root / "clean/events"))
        types = dict(frame.dtypes)
        expected = {"event_type": "string", "product_id": "bigint", "category_id": "bigint",
                    "category_code": "string", "brand": "string", "price": "double",
                    "user_id": "bigint", "user_session": "string", "event_ts": "timestamp",
                    "cat_l1": "string", "cat_l2": "string", "event_hour": "int",
                    "day_of_week": "string", "event_date": "date"}
        assert all(types.get(key) == value for key, value in expected.items()), types
        valid = (F.col("event_ts").isNotNull() & F.col("event_type").isin("view", "cart", "purchase")
                 & F.col("price").isNotNull() & (F.col("price") > 0)
                 & ~F.isnan("price") & (F.col("price") < F.lit(float("inf")))
                 & F.col("user_id").isNotNull() & F.col("user_session").isNotNull()
                 & (F.length(F.trim("user_session")) > 0)
                 & F.col("event_date").eqNullSafe(F.to_date("event_ts"))
                 & F.col("event_hour").eqNullSafe(F.hour("event_ts"))
                 & F.col("day_of_week").eqNullSafe(F.date_format("event_ts", "E")))
        for column in ["brand", "cat_l1", "cat_l2"]:
            valid = valid & F.col(column).isNotNull() & (F.length(F.trim(column)) > 0)
        valid = valid & F.col("brand").eqNullSafe(F.lower(F.trim("brand")))
        result = frame.agg(F.count("*").alias("rows"),
                           F.coalesce(F.sum(F.when(~F.coalesce(valid, F.lit(False)), 1).otherwise(0)), F.lit(0)).alias("invalid_rows"),
                           F.countDistinct("event_date").alias("dates")).first().asDict()
        raw_rows = spark.read.parquet(str(root / "raw/events")).count()
        assert result["invalid_rows"] == 0, result
        assert raw_rows == metrics["counts"]["raw"]
        assert result["rows"] == metrics["counts"]["written"] == metrics["counts"]["after_identity"]
        values = list(metrics["counts"].values())
        assert all(left >= right for left, right in zip(values, values[1:]))
        report_data = {"status": "PASS", "scope": "distributed constraints/count/schema; not full raw-to-clean value equivalence",
                       "data_kind": metrics.get("data_kind", "SYNTHETIC_TEST_ONLY" if "synthetic" in str(root) else "UNKNOWN"),
                       "result": result, "raw_rows": raw_rows, "schema": types,
                       "timezone": spark.conf.get("spark.sql.session.timeZone"),
                       "application_id": spark.sparkContext.applicationId}
        with report.open("x", encoding="utf-8") as handle:
            json.dump(report_data, handle, indent=2)
        print("[TV3 VALIDATION] " + json.dumps(report_data), flush=True)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
