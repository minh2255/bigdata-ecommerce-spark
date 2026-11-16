"""Actual Spark regression checks for TV2 clean invariants used by TV3."""
import importlib.util
import sys
from pathlib import Path
from pyspark.sql import SparkSession, functions as F

spec = importlib.util.spec_from_file_location("profiling", "/opt/jobs/01_profiling.py")
profiling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiling)
spark = SparkSession.builder.appName("tv3_profile_contract_regression").config("spark.sql.session.timeZone", "UTC").getOrCreate()
try:
    root = Path(sys.argv[1])
    frame = spark.read.parquet(str(root / "contract case/clean/events"))
    report = profiling.build_report("clean", frame, root / "contract case")
    assert report["rows"] == 6 and report["duplicate_rows"] == 1, report
    assert report["invariants"]["all_pass"], report
    print("[PASS] normalized duplicates allowed; strict UTC contract fixture profiles clean", flush=True)
    corrupt = frame.withColumn("event_type", F.lit(None).cast("string")).withColumn("user_session", F.lit("\t\n"))
    report = profiling.build_report("clean", corrupt, root / "contract case")
    assert report["invariants"]["event_type_valid"] is False, report
    assert report["invariants"]["no_blank_session"] is False, report
    assert report["invariants"]["all_pass"] is False, report
    print("[PASS] null event_type and whitespace sessions fail clean invariants", flush=True)
    empty = spark.read.parquet(str(root / "empty case/clean/events"))
    report = profiling.build_report("clean", empty, root / "empty case")
    assert report["status"] == "SUCCESS_EMPTY" and report["invariants"]["all_pass"], report
    print("[PASS] schema-bearing empty output profiles successfully", flush=True)
    print("[APPLICATION] " + spark.sparkContext.applicationId, flush=True)
finally:
    spark.stop()
