#!/usr/bin/env bash
# TV3: all modes preserve outputs; logs are created on the host even on failure.
set -euo pipefail
export MSYS_NO_PATHCONV=1
REPO_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_DIR"
LOG_DIR=${PIPELINE_LOG_DIR:-"$REPO_DIR/data/reports/tv3_pipeline_logs"}
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pipeline-$(date -u +%Y%m%dT%H%M%SZ)-${BASHPID}.log"
exec > >(tee -a "$LOG_FILE") 2>&1
stage=arguments
trap 'code=$?; printf "[EXIT] stage=%s code=%s log=%s\n" "$stage" "$code" "$LOG_FILE"' EXIT
fail() { echo "[ERROR] $2"; exit "$1"; }
MODE=${1:---full}
[[ $# -le 1 ]] || fail 2 'Only one mode argument is supported'
if [[ "$MODE" == --available ]]; then
  echo '[ALIAS] --available means --ingest-clean; no profiling or aggregation is run'
  MODE=--ingest-clean
fi
case "$MODE" in --full|--ingest-clean|--clean-only) ;; *) fail 2 'Usage: run_pipeline.sh [--full|--ingest-clean|--clean-only]' ;; esac
DATA_DIR=${DATA_DIR:-/data}
DATA_KIND=${DATA_KIND:-}
SPARK_CONTAINER=${SPARK_CONTAINER:-spark-master}
SPARK_MASTER_URL=${SPARK_MASTER_URL:-spark://spark-master:7077}
SPARK_DRIVER_MEMORY=${SPARK_DRIVER_MEMORY:-2g}
[[ "$SPARK_DRIVER_MEMORY" =~ ^[1-9][0-9]*[gm]$ ]] || fail 2 'Invalid SPARK_DRIVER_MEMORY (example: 2g or 512m)'
[[ "$SPARK_MASTER_URL" =~ ^spark://[^[:space:]]+:[0-9]+$ ]] || fail 2 'Invalid SPARK_MASTER_URL'
[[ -z "$DATA_KIND" || "$DATA_KIND" == synthetic || "$DATA_KIND" == real ]] || fail 2 'DATA_KIND must be synthetic or real'
required=(02_cleaning.py)
if [[ "$MODE" != --clean-only ]]; then required=(00_ingest.py 02_cleaning.py); fi
if [[ "$MODE" == --full ]]; then required=(00_ingest.py 01_profiling.py 02_cleaning.py 03_aggregation.py); fi
stage=source-preflight
missing=0
for job in "${required[@]}"; do
  if [[ ! -f "$REPO_DIR/jobs/$job" ]]; then echo "[MISSING] $job"; missing=1; fi
done
((missing == 0)) || fail 3 'Required source missing; no Spark job started'
[[ -f "$REPO_DIR/scripts/pipeline_preflight.py" ]] || fail 3 'Missing preflight helper'
stage=docker-config
command -v docker >/dev/null || fail 4 'Docker CLI is unavailable'
# Relative host path: MSYS_NO_PATHCONV must preserve /opt and /data paths,
# but would also prevent Git Bash's /d/... host path conversion for Docker.
docker compose -f docker-compose.yml config --quiet || fail 4 'Compose config failed'
[[ "$(docker inspect --format '{{.State.Running}}' "$SPARK_CONTAINER")" == true ]] || fail 4 'Spark container is not running'
stage=data-preflight
docker exec -e DATA_DIR="$DATA_DIR" -e DATA_KIND="$DATA_KIND" "$SPARK_CONTAINER" python3 /opt/scripts/pipeline_preflight.py "$MODE" || fail 4 'Data/job preflight failed'
submit=(docker exec -e DATA_DIR="$DATA_DIR" -e DATA_KIND="$DATA_KIND" "$SPARK_CONTAINER"
        /opt/spark/bin/spark-submit --master "$SPARK_MASTER_URL" --driver-memory "$SPARK_DRIVER_MEMORY")
run_job() {
  local job=$1; shift
  stage="$job $*"
  echo "[RUN] $stage DATA_DIR=$DATA_DIR"
  local code=0
  "${submit[@]}" "/opt/jobs/$job" "$@" || code=$?
  if ((code != 0)); then echo "[SUBMIT ERROR] job=$job exit=$code"; exit "$code"; fi
}
if [[ "$MODE" != --clean-only ]]; then run_job 00_ingest.py; fi
if [[ "$MODE" == --full ]]; then run_job 01_profiling.py raw; fi
run_job 02_cleaning.py
if [[ "$MODE" == --full ]]; then
  run_job 01_profiling.py clean
  run_job 03_aggregation.py
  echo "[DONE FULL] $DATA_DIR"
else
  echo "[DONE TV3] mode=$MODE; profiling and aggregation were not run"
fi
stage=complete
