"""Run only TV3 regression/edge cases on the existing Docker cluster.

No image build, no benchmark, no profiling/aggregation substitutes.
Every execution gets a new ignored Data Lake and evidence directory.
"""
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASH = "C:/Program Files/Git/bin/bash.exe"
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
EVIDENCE = ROOT / "data/reports/tv3_handoff_20261018" / RUN_ID
EVIDENCE.mkdir(parents=True, exist_ok=False)
DATA_BASE = "/data/tv3 handoff " + RUN_ID
RESULTS = []


def run(label, command, env=None, expected=0):
    path = EVIDENCE / (label + ".log")
    with path.open("w", encoding="utf-8") as handle:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=handle,
                                stderr=subprocess.STDOUT, text=True, timeout=300)
    if result.returncode != expected:
        print(path.read_text(encoding="utf-8", errors="replace")[-6000:], flush=True)
        raise AssertionError(f"{label}: exit {result.returncode}, expected {expected}; {path}")
    RESULTS.append({"test": label, "exit": result.returncode, "expected": expected,
                    "status": "PASS", "log": str(path.relative_to(ROOT))})
    print(f"[PASS] {label} exit={result.returncode}", flush=True)


def submit(root, job):
    return ["docker", "exec", "-e", "DATA_DIR=" + root, "-e", "DATA_KIND=synthetic",
            "spark-master", "/opt/spark/bin/spark-submit", "--master", "spark://spark-master:7077",
            "--driver-memory", "2g", "/opt/jobs/" + job]


def main():
    previous_bench = ROOT / "data/synthetic_tv3_20261018_optimized/reports/benchmark.csv"
    bench_hash = hashlib.sha256(previous_bench.read_bytes()).hexdigest() if previous_bench.exists() else None
    run("unit_control_flow", [sys.executable, "tests/test_pipeline_control.py"])
    run("full_missing_jobs", [BASH, "scripts/run_pipeline.sh", "--full"], expected=3)
    for case in ["mixed", "empty", "all-invalid", "valid-repeat"]:
        root = DATA_BASE + "/" + case + " case"
        run(case + "_fixture", ["docker", "exec", "spark-master", "python3",
                                "/opt/scripts/check_cleaning.py", "fixture", root, case])
        env = dict(os.environ, DATA_DIR=root, DATA_KIND="synthetic")
        if case == "valid-repeat":
            run(case + "_ingest", submit(root, "00_ingest.py"))
            mode = "--clean-only"
        else:
            mode = "--ingest-clean"
        run(case + "_pipeline", [BASH, "scripts/run_pipeline.sh", mode], env=env)
        run(case + "_independent_values", ["docker", "exec", "spark-master", "python3",
                                           "/opt/scripts/check_cleaning.py", "verify", root])
        run(case + "_distributed_schema_constraints", submit(root, "validate_cleaning.py"))
        local = ROOT / "data" / Path(root.removeprefix("/data/"))
        metrics = json.loads((local / "reports/cleaning_metrics.json").read_text())
        expected_rows = {"mixed": 3, "empty": 0, "all-invalid": 0, "valid-repeat": 3}[case]
        assert metrics["counts"]["written"] == expected_rows, metrics
        if expected_rows == 0:
            assert metrics["status"] == "SUCCESS_EMPTY"
        protected = [p for p in (local / "clean/events").rglob("*") if p.is_file()]
        hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        metrics_hash = hashlib.sha256((local / "reports/cleaning_metrics.json").read_bytes()).hexdigest()
        run(case + "_overwrite_guard", [BASH, "scripts/run_pipeline.sh", "--clean-only"], env=env, expected=4)
        assert hashes == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
        assert metrics_hash == hashlib.sha256((local / "reports/cleaning_metrics.json").read_bytes()).hexdigest()

    for case in ["missing-input", "mixed-input", "bad-header"]:
        root = DATA_BASE + "/" + case
        local = ROOT / "data" / Path(root.removeprefix("/data/"))
        (local / "landing").mkdir(parents=True, exist_ok=False)
        if case == "mixed-input":
            for name in ["synthetic.csv", "2019-Oct.csv"]:
                (local / "landing" / name).write_text("event_time\n")
        elif case == "bad-header":
            (local / "landing/synthetic.csv").write_text("wrong_header\n")
        run(case, [BASH, "scripts/run_pipeline.sh", "--ingest-clean"],
            env=dict(os.environ, DATA_DIR=root, DATA_KIND="synthetic"), expected=4)
        assert not (local / "raw/events").exists()
    if bench_hash:
        assert hashlib.sha256(previous_bench.read_bytes()).hexdigest() == bench_hash
    summary = {"status": "PASS", "run_id": RUN_ID, "data_base": DATA_BASE,
               "benchmark_unchanged_sha256": bench_hash,
               "tests": RESULTS, "test_host": "same Windows machine as initial setup",
               "other_member_machine_tested": False,
               "submit_error_scope": "unit mock failure only; no fake production jobs"}
    (EVIDENCE / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("[SUMMARY] " + str(EVIDENCE / "summary.json"), flush=True)


if __name__ == "__main__":
    main()
