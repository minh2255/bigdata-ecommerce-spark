"""Actual TV2-TV3 Spark quality integration; unique lake and complete logs."""
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
LAKE = "/data/synthetic_quality_" + RUN_ID
EVIDENCE = ROOT / "data/reports/tv3_quality" / RUN_ID
EVIDENCE.mkdir(parents=True, exist_ok=False)
ENV = dict(os.environ, DATA_DIR=LAKE, DATA_KIND="synthetic")
STEPS = []


def run(label, command):
    started = time.perf_counter()
    log = EVIDENCE / (label + ".log")
    with log.open("x", encoding="utf-8") as handle:
        result = subprocess.run(command, cwd=ROOT, env=ENV, stdout=handle,
                                stderr=subprocess.STDOUT, timeout=600)
    step = dict(label=label, command=command, exit=result.returncode,
                seconds=round(time.perf_counter()-started, 3), log=str(log.relative_to(ROOT)))
    STEPS.append(step)
    (EVIDENCE / "steps.json").write_text(json.dumps(STEPS, indent=2), encoding="utf-8")
    if result.returncode:
        print(log.read_text(encoding="utf-8", errors="replace")[-7000:], flush=True)
        raise RuntimeError(f"{label} failed: exit={result.returncode}; {log}")
    print(f"[PASS] {label} seconds={step['seconds']}", flush=True)


def main():
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    run("generate", ["docker", "exec", "-e", "DATA_DIR=" + LAKE, "spark-master", "python3", "/opt/scripts/generate_data.py", str(rows)])
    run("quality_pipeline", ["C:/Program Files/Git/bin/bash.exe", "scripts/run_pipeline.sh", "--quality-check"])
    run("compare_truth", ["docker", "exec", "spark-master", "python3", "/opt/scripts/compare_truth.py", LAKE])
    run("validator", ["docker", "exec", "-e", "DATA_DIR=" + LAKE, "-e", "DATA_KIND=synthetic", "spark-master",
                      "/opt/spark/bin/spark-submit", "--master", "spark://spark-master:7077", "--driver-memory", "2g", "/opt/jobs/validate_cleaning.py"])
    local = ROOT / "data" / LAKE.removeprefix("/data/")
    reports = {name: json.loads((local / "reports" / (name + ".json")).read_text(encoding="utf-8"))
               for name in ["cleaning_metrics", "profiling_raw", "profiling_clean", "cleaning_validation_spark"]}
    m = reports["cleaning_metrics"]
    counts = list(m["counts"].values())
    assert all(a >= b for a,b in zip(counts, counts[1:]))
    assert m["counts"]["written"] == m["counts"]["after_identity"] == reports["profiling_clean"]["rows"]
    assert reports["profiling_raw"]["rows"] == m["counts"]["raw"]
    assert reports["profiling_clean"]["invariants"]["all_pass"] is True
    assert reports["cleaning_validation_spark"]["status"] == "PASS"
    summary = dict(status="PASS", data_dir=LAKE, local_data_dir=str(local), evidence=str(EVIDENCE),
                   source="scripts/generate_data.py seed=42; synthetic, not Kaggle", requested_rows=rows,
                   counts=m["counts"], application_ids={name:r["application_id"] for name,r in reports.items()},
                   cleaning_seconds=m["seconds"], steps=STEPS, other_machine_tested=False,
                   spark_config=dict(master="spark://spark-master:7077", driver_memory="2g", workers=2, worker_cores=2, worker_memory="2g"),
                   truth_limits="raw/dedup exact; other removals near: 2% injected + 20; not row equivalence")
    (EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("[SUMMARY] " + str(EVIDENCE / "summary.json"), flush=True)


if __name__ == "__main__":
    main()
