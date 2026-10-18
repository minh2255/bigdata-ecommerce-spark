"""Container-side checks for TV3's pipeline; no data is modified here."""
import csv
import json
import os
import sys
from pathlib import Path


HEADER = ["event_time", "event_type", "product_id", "category_id", "category_code",
          "brand", "price", "user_id", "user_session"]


def preflight():
    mode = sys.argv[1]
    root = Path(os.environ["DATA_DIR"])
    if not root.is_absolute() or not root.resolve().is_relative_to(Path("/data").resolve()):
        raise ValueError("DATA_DIR must be an absolute directory inside /data")
    required = (["02_cleaning.py"] if mode == "--clean-only" else
                ["00_ingest.py", "02_cleaning.py"] if mode == "--ingest-clean" else
                ["00_ingest.py", "01_profiling.py", "02_cleaning.py", "03_aggregation.py"])
    for name in required:
        if not (Path("/opt/jobs") / name).is_file():
            raise ValueError(f"Mounted job missing: {name}")
    source_path = root / "reports/source.json"
    source = json.loads(source_path.read_text()) if source_path.exists() else {}
    kinds = {"SYNTHETIC_TEST_ONLY": "synthetic", "synthetic": "synthetic", "real": "real"}
    declared = os.environ.get("DATA_KIND", "")
    if declared and declared not in {"synthetic", "real"}:
        raise ValueError("DATA_KIND must be synthetic or real")
    source_kind = kinds.get(source.get("data_kind"))
    if source_kind and declared and source_kind != declared:
        raise ValueError("DATA_KIND conflicts with existing source.json")
    kind = declared or source_kind
    if mode == "--clean-only":
        if not list((root / "raw/events").rglob("*.parquet")):
            raise ValueError("No raw/events Parquet input; clean-only does not run ingest")
    else:
        files = list((root / "landing").glob("*.csv"))
        if not files:
            raise ValueError("No input CSV in landing")
        synthetic = ["synthetic" in path.name.lower() for path in files]
        if any(synthetic) and not all(synthetic):
            raise ValueError("Mixed synthetic/real filenames; use separate DATA_DIR")
        if all(synthetic):
            if kind == "real":
                raise ValueError("Synthetic filename conflicts with DATA_KIND=real")
            kind = "synthetic"
        elif kind != "real":
            raise ValueError("Unknown CSV provenance: explicitly set DATA_KIND=real for verified real CSV")
        for path in files:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                if next(csv.reader(handle), None) != HEADER:
                    raise ValueError(f"CSV header/order differs from the guide: {path.name}")
    if not kind:
        raise ValueError("Raw provenance unknown; provide source.json or explicit DATA_KIND")
    layers = ["clean"] if mode == "--clean-only" else ["raw", "clean", "agg"]
    for layer in layers:
        path = root / layer
        if path.exists() and any(item.name != ".gitkeep" for item in path.iterdir()):
            raise ValueError(f"Existing {layer} output: choose a new DATA_DIR")
    reports = ["cleaning_metrics.json", "cleaning_schema.json"]
    if mode != "--clean-only":
        reports += ["ingest_log.csv", "profiling_raw.json", "profiling_clean.json"]
    for name in reports:
        if (root / "reports" / name).exists():
            raise ValueError(f"Existing report: {name}; choose a new DATA_DIR")
    print(f"[PREFLIGHT] mode={mode} root={root} data_kind={kind}; inputs/config/output guards PASS")


if __name__ == "__main__":
    try:
        preflight()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"[PREFLIGHT ERROR] {error}", file=sys.stderr)
        sys.exit(4)
