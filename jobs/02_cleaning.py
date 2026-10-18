"""TV3: seven cleaning rules from BD_Project.docx; TV2 contract pending.

DATA_DIR selects an isolated Data Lake. Existing output is never overwritten.
"""
import json
import os
import time
from pathlib import Path

from pyspark import StorageLevel
from pyspark.sql import SparkSession, functions as F


def main():
    root = Path(os.environ.get("DATA_DIR", "/data"))
    output = root / "clean/events"
    report = root / "reports/cleaning_metrics.json"
    schema_report = root / "reports/cleaning_schema.json"
    if output.exists() or report.exists() or schema_report.exists():
        raise FileExistsError("Cleaning output exists; choose a new DATA_DIR to preserve it")
    spark = (SparkSession.builder.appName("02_cleaning")
             .config("spark.sql.session.timeZone", "UTC").getOrCreate())
    started = time.perf_counter()
    cached = []
    counts = {}
    stage_seconds = {}
    removed = {}

    def checkpoint(name, frame):
        stage_start = time.perf_counter()
        frame = frame.persist(StorageLevel.MEMORY_AND_DISK)
        cached.append(frame)
        counts[name] = frame.count()
        previous = list(counts)[-2] if len(counts) > 1 else None
        lost = counts[previous] - counts[name] if previous else 0
        if previous:
            removed[f"{previous}_to_{name}"] = lost
        stage_seconds[name] = round(time.perf_counter() - stage_start, 3)
        print(f"[CLEAN] {name}={counts[name]} removed={lost} "
              f"stage_seconds={stage_seconds[name]}", flush=True)
        if len(cached) > 1:
            cached[-2].unpersist()
        return frame

    try:
        raw_input = spark.read.parquet(str(root / "raw/events"))
        expected_types = {"event_time": "string", "event_type": "string",
                          "product_id": "bigint", "category_id": "bigint",
                          "category_code": "string", "brand": "string", "price": "double",
                          "user_id": "bigint", "user_session": "string"}
        actual_types = {field.name: field.dataType.simpleString() for field in raw_input.schema}
        if any(actual_types.get(key) != value for key, value in expected_types.items()):
            raise ValueError(f"Raw schema does not match the guide: {actual_types}")
        raw = checkpoint("raw", raw_input)
        df = checkpoint("after_dedup", raw.dropDuplicates())
        df = checkpoint("after_timestamp", df.withColumn(
            "event_ts", F.try_to_timestamp(
                F.regexp_replace("event_time", " UTC$", ""),
                F.lit("yyyy-MM-dd HH:mm:ss"))).filter(F.col("event_ts").isNotNull()))
        df = checkpoint("after_event_type", df.filter(
            F.col("event_type").isin("view", "cart", "purchase")))
        df = checkpoint("after_price", df.filter(
            (F.col("price") > 0) & ~F.isnan("price")
            & (F.col("price") < F.lit(float("inf")))))
        df = checkpoint("after_identity", df.filter(
            F.col("user_id").isNotNull() & F.col("user_session").isNotNull()
            & (F.length(F.trim("user_session")) > 0)))

        def unknown_if_empty(column):
            return F.when(column.isNull() | (F.length(F.trim(column)) == 0),
                          F.lit("unknown")).otherwise(F.trim(column))

        cat = F.split(F.col("category_code"), r"\.")
        clean = (df.withColumn("cat_l1", unknown_if_empty(F.get(cat, 0)))
                 .withColumn("cat_l2", unknown_if_empty(F.get(cat, 1)))
                 .withColumn("brand", unknown_if_empty(F.lower(F.col("brand"))))
                 .withColumn("event_date", F.to_date("event_ts"))
                 .withColumn("event_hour", F.hour("event_ts"))
                 .withColumn("day_of_week", F.date_format("event_ts", "E"))
                 .drop("event_time"))
        # Keep each day's rows together instead of writing one file per task/day.
        write_start = time.perf_counter()
        if counts["after_identity"]:
            (clean.repartition("event_date").write.mode("errorifexists")
             .partitionBy("event_date").parquet(str(output)))
        else:
            # No date partitions exist for zero rows. Keep one schema-bearing
            # empty Parquet file so downstream spark.read.parquet still works.
            clean.coalesce(1).write.mode("errorifexists").parquet(str(output))
        stage_seconds["write"] = round(time.perf_counter() - write_start, 3)
        reread_start = time.perf_counter()
        counts["written"] = spark.read.parquet(str(output)).count()
        stage_seconds["readback_count"] = round(time.perf_counter() - reread_start, 3)
        assert counts["written"] == counts["after_identity"], "Output row count mismatch"
        source_path = root / "reports/source.json"
        source = json.loads(source_path.read_text()) if source_path.exists() else {}
        metrics = {
            "data_dir": str(root), "timezone": "UTC", "counts": counts,
            "removed": removed, "stage_seconds": stage_seconds,
            "status": "SUCCESS_EMPTY" if not counts["written"] else "SUCCESS",
            "data_kind": os.environ.get("DATA_KIND") or source.get("data_kind", "UNKNOWN"),
            "application_id": spark.sparkContext.applicationId,
            "empty_output": counts["written"] == 0,
            "partition_columns": ["event_date"],
            "extensions_pending_tv2": ["finite price (reject NaN/Inf)",
                                       "reject whitespace-only session",
                                       "blank category/brand becomes unknown"],
            "id_rules": "user_id non-null only; no positive-ID or UUID constraint",
            "seconds": round(time.perf_counter() - started, 3),
            "rules_source": "BD_Project.docx section 5.3; TV2 contract pending",
        }
        report.parent.mkdir(parents=True, exist_ok=True)
        with schema_report.open("x", encoding="utf-8") as handle:
            json.dump(clean.schema.jsonValue(), handle, indent=2)
        with report.open("x", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2)
        print(f"[CLEAN] raw={counts['raw']} after_dedup={counts['after_dedup']} "
              f"after_filter={counts['after_identity']} time={metrics['seconds']}s", flush=True)
    finally:
        for frame in cached:
            frame.unpersist()
        spark.stop()


if __name__ == "__main__":
    main()
