"""Mode-specific real preflight checks on isolated files; no Spark simulation."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("preflight", ROOT / "scripts/pipeline_preflight.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.lake = self.base / "data/lake"
        (self.lake / "landing").mkdir(parents=True)
        (self.lake / "landing/synthetic.csv").write_text(",".join(module.HEADER) + "\n")
        (self.base / "jobs").mkdir()
        for job in ["00_ingest.py", "01_profiling.py", "02_cleaning.py"]:
            (self.base / "jobs" / job).touch()

    def run_preflight(self, mode):
        def mapped(value):
            text = str(value)
            if text == "/data" or text.startswith("/data/"):
                return self.base / text.lstrip("/")
            if text == "/opt/jobs":
                return self.base / "jobs"
            return Path(value)
        with patch.object(module, "Path", mapped), patch.object(sys, "argv", ["preflight", mode]), patch.dict(os.environ, DATA_DIR="/data/lake", DATA_KIND="synthetic"):
            module.preflight()

    def test_quality_does_not_require_aggregation(self):
        self.run_preflight("--quality-check")

    def test_quality_requires_profile(self):
        (self.base / "jobs/01_profiling.py").unlink()
        with self.assertRaisesRegex(ValueError, "Mounted job missing"):
            self.run_preflight("--quality-check")

    def test_quality_rejects_profile_outputs(self):
        (self.lake / "reports").mkdir()
        (self.lake / "reports/profiling_clean.json").touch()
        with self.assertRaisesRegex(ValueError, "Existing report"):
            self.run_preflight("--quality-check")

    def test_quality_requires_landing(self):
        (self.lake / "landing/synthetic.csv").unlink()
        with self.assertRaisesRegex(ValueError, "No input CSV"):
            self.run_preflight("--quality-check")

    def test_ingest_clean_ignores_unrelated_profile(self):
        (self.lake / "reports").mkdir()
        (self.lake / "reports/profiling_clean.json").touch()
        self.run_preflight("--ingest-clean")

    def test_quality_rejects_existing_raw(self):
        (self.lake / "raw").mkdir()
        (self.lake / "raw/keep.txt").touch()
        with self.assertRaisesRegex(ValueError, "Existing raw output"):
            self.run_preflight("--quality-check")

    def test_full_still_requires_aggregation(self):
        with self.assertRaisesRegex(ValueError, "03_aggregation.py"):
            self.run_preflight("--full")

    def test_full_rejects_existing_aggregation_metrics(self):
        (self.base / "jobs/03_aggregation.py").touch()
        (self.lake / "reports").mkdir()
        (self.lake / "reports/aggregation_metrics.json").touch()
        with self.assertRaisesRegex(ValueError, "Existing report: aggregation_metrics.json"):
            self.run_preflight("--full")

    def test_quality_ignores_aggregation_metrics(self):
        (self.lake / "reports").mkdir()
        (self.lake / "reports/aggregation_metrics.json").touch()
        self.run_preflight("--quality-check")


if __name__ == "__main__":
    unittest.main(verbosity=2)
