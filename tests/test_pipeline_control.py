"""Unit tests of shell control flow with a deliberately failing mock Docker.

No Spark result is simulated or reported as integration success. Mock sources
exist only in an ignored unit sandbox, never in the project's jobs directory.
"""
import os
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "data/reports/tv3_handoff_20261018/unit sandbox" / uuid.uuid4().hex[:8]
BASH = "C:/Program Files/Git/bin/bash.exe"


class PipelineControlTests(unittest.TestCase):
    def run_case(self, name, mode, missing=None, **extra):
        repo = SANDBOX / name / "repo with spaces"
        (repo / "scripts").mkdir(parents=True, exist_ok=False)
        (repo / "jobs").mkdir()
        bindir = repo / "mock bin"
        bindir.mkdir()
        shutil.copyfile(ROOT / "scripts/run_pipeline.sh", repo / "scripts/run_pipeline.sh")
        (repo / "scripts/pipeline_preflight.py").write_text("# unit sandbox only\n")
        for job in ["00_ingest.py", "01_profiling.py", "02_cleaning.py", "03_aggregation.py"]:
            if job != missing:
                (repo / "jobs" / job).write_text("# MOCK CONTROL-FLOW TEST ONLY; not executable Spark code\n")
        (repo / "docker-compose.yml").write_text("# mock config\n")
        trace = repo / "trace.txt"
        docker = bindir / "docker"
        docker.write_text('''#!/usr/bin/env bash
printf '<%s>' "$@" >> "$TRACE_FILE"; printf '\\n' >> "$TRACE_FILE"
if [[ "$1" == compose ]]; then exit "${MOCK_CONFIG_EXIT:-0}"; fi
if [[ "$1" == inspect ]]; then echo true; exit 0; fi
if [[ "$*" == *pipeline_preflight.py* ]]; then exit "${MOCK_PREFLIGHT_EXIT:-0}"; fi
if [[ "$*" == *"${MOCK_FAIL_JOB:-00_ingest.py}"* ]]; then exit 42; fi
exit 0
''', encoding="utf-8", newline="\n")
        env = dict(os.environ, TRACE_FILE=str(trace), DATA_DIR="/data/unit lake with spaces",
                   DATA_KIND="synthetic", PIPELINE_LOG_DIR=str(repo / "logs with spaces"))
        env.update(extra)
        # Git Bash needs POSIX PATH for the mock executable ahead of native Docker.
        posix_bin = "/" + str(bindir).replace("\\", "/").replace(":", "", 1)
        env["PATH"] = str(bindir) + os.pathsep + env["PATH"]
        command = 'export PATH="' + posix_bin + ':$PATH"; bash scripts/run_pipeline.sh ' + mode
        result = subprocess.run([BASH, "-c", command], cwd=repo, env=env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        logs = list((repo / "logs with spaces").glob("*.log"))
        self.assertEqual(len(logs), 1)
        self.assertIn(f"code={result.returncode}", logs[0].read_text(encoding="utf-8"))
        return result, trace.read_text() if trace.exists() else ""

    def test_missing_job_stops_before_docker(self):
        result, trace = self.run_case("missing", "--full", missing="01_profiling.py")
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertEqual(trace, "")

    def test_invalid_memory(self):
        result, trace = self.run_case("bad-memory", "--ingest-clean", SPARK_DRIVER_MEMORY="bad")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(trace, "")

    def test_bad_compose_config(self):
        result, trace = self.run_case("bad-config", "--ingest-clean", MOCK_CONFIG_EXIT="19")
        self.assertEqual(result.returncode, 4, result.stdout)
        self.assertNotIn("spark-submit", trace)

    def test_data_preflight_failure(self):
        result, trace = self.run_case("bad-input", "--ingest-clean", MOCK_PREFLIGHT_EXIT="4")
        self.assertEqual(result.returncode, 4, result.stdout)
        self.assertNotIn("spark-submit", trace)

    def test_submit_error_is_preserved_with_spaces(self):
        result, trace = self.run_case("submit-error", "--ingest-clean")
        self.assertEqual(result.returncode, 42, result.stdout)
        self.assertIn("<DATA_DIR=/data/unit lake with spaces>", trace)
        self.assertIn("/opt/jobs/00_ingest.py", trace)
        self.assertNotIn("/opt/jobs/02_cleaning.py", trace)

    def test_full_order_stops_at_cleaning(self):
        result, trace = self.run_case("full-order", "--full", MOCK_FAIL_JOB="02_cleaning.py")
        self.assertEqual(result.returncode, 42, result.stdout)
        self.assertLess(trace.index("/opt/jobs/00_ingest.py"), trace.index("/opt/jobs/01_profiling.py"))
        self.assertLess(trace.index("/opt/jobs/01_profiling.py"), trace.index("/opt/jobs/02_cleaning.py"))
        self.assertIn("</opt/jobs/01_profiling.py><raw>", trace)
        self.assertNotIn("</opt/jobs/01_profiling.py><clean>", trace)
        self.assertNotIn("/opt/jobs/03_aggregation.py", trace)

    def test_clean_only_does_not_require_other_sources(self):
        result, trace = self.run_case("clean-only", "--clean-only", missing="01_profiling.py", MOCK_FAIL_JOB="02_cleaning.py")
        self.assertEqual(result.returncode, 42, result.stdout)
        self.assertNotIn("/opt/jobs/00_ingest.py", trace)
        self.assertIn("/opt/jobs/02_cleaning.py", trace)


if __name__ == "__main__":
    unittest.main(verbosity=2)
