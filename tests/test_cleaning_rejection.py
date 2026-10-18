"""Actual Spark failure propagation test using an invalid raw schema.

Creates only a new synthetic rejection fixture, not a substitute job.
"""
import json
import os
import subprocess
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
run_id = uuid.uuid4().hex[:10]
data_dir = "/data/tv3 rejected schema " + run_id
evidence = ROOT / "data/reports/tv3_handoff_20261018" / ("schema_rejection_" + run_id)
evidence.mkdir(parents=True, exist_ok=False)
fixture_code = '''import json,sys
from pathlib import Path
import pyarrow as pa,pyarrow.parquet as pq
r=Path(sys.argv[1])
(r/"raw/events").mkdir(parents=True,exist_ok=False)
(r/"reports").mkdir()
pq.write_table(pa.table({"event_time":["2019-10-01 00:00:00 UTC"],"event_type":["view"],"product_id":[1],"category_id":[2],"category_code":["electronics.phone"],"brand":["a"],"price":["10.5"],"user_id":[3],"user_session":["session"]}),r/"raw/events/part-invalid-schema.parquet")
(r/"reports/source.json").write_text(json.dumps({"data_kind":"SYNTHETIC_TEST_ONLY","fixture":"price deliberately string rather than double"}))
'''
subprocess.run(["docker", "exec", "spark-master", "python3", "-c", fixture_code, data_dir], check=True)
log = evidence / "actual_spark_schema_failure.log"
with log.open("w", encoding="utf-8") as handle:
    result = subprocess.run(["C:/Program Files/Git/bin/bash.exe", "scripts/run_pipeline.sh", "--clean-only"],
                            cwd=ROOT, env=dict(os.environ, DATA_DIR=data_dir, DATA_KIND="synthetic"),
                            stdout=handle, stderr=subprocess.STDOUT, timeout=120)
text = log.read_text(encoding="utf-8", errors="replace")
assert result.returncode == 1, (result.returncode, text[-5000:])
assert "Raw schema does not match the guide" in text
assert "[SUBMIT ERROR] job=02_cleaning.py exit=1" in text
assert "[DONE TV3]" not in text
local = ROOT / "data" / data_dir.removeprefix("/data/")
assert not (local / "clean/events").exists()
assert not (local / "reports/cleaning_metrics.json").exists()
summary = {"status": "PASS", "scope": "real Spark submit failure, not mock",
           "expected_exit": 1, "actual_exit": result.returncode,
           "reason": "raw price has string type instead of double", "data_dir": data_dir,
           "clean_output_created": False, "pipeline_stopped": True,
           "log": str(log.relative_to(ROOT))}
(evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("PASS: actual Spark schema rejection propagates exit 1; no clean output; " + str(evidence))
