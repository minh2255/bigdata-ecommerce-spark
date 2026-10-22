#!/usr/bin/env bash
# Chạy KB1, KB2, KB6 (phần của TV1). Mỗi cấu hình chạy REPEAT lần (mặc định 3).
# Cách dùng:  bash scripts/run_benchmarks.sh [kb1|kb2|kb6|all]
set -euo pipefail
export MSYS_NO_PATHCONV=1   # tránh Git Bash trên Windows tự đổi đường dẫn /opt/...

cd "$(dirname "${BASH_SOURCE[0]}")/.."
DATA_DIR=${DATA_DIR:-/data}
SUBMIT=(docker exec -e DATA_DIR="$DATA_DIR" spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 2g)
REPEAT=${REPEAT:-3}
WHICH=${1:-all}

kb1() {  # kích thước dữ liệu
  for f in 0.1 0.25 0.5 1.0; do
    for i in $(seq 1 "$REPEAT"); do echo "[RUN] KB1 fraction=$f repeat=$i"; "${SUBMIT[@]}" /opt/jobs/04_benchmark.py "$f" size; done
  done
}
kb2() {  # số core (--total-executor-cores phải đứng TRƯỚC tên file job)
  for c in 1 2 4; do
    for i in $(seq 1 "$REPEAT"); do echo "[RUN] KB2 cores=$c repeat=$i"; "${SUBMIT[@]}" --total-executor-cores "$c" /opt/jobs/04_benchmark.py 1.0 cores; done
  done
}
kb6() {  # số shuffle partition
  for n in 8 50 200; do
    for i in $(seq 1 "$REPEAT"); do echo "[RUN] KB6 partitions=$n repeat=$i"; "${SUBMIT[@]}" --conf "spark.sql.shuffle.partitions=$n" /opt/jobs/04_benchmark.py 1.0 "part$n"; done
  done
}

case "$WHICH" in
  kb1) kb1 ;;
  kb2) kb2 ;;
  kb6) kb6 ;;
  all) kb1; kb2; kb6 ;;
  *) echo "Dung: bash scripts/run_benchmarks.sh [kb1|kb2|kb6|all]"; exit 1 ;;
esac
echo "Xong. Xem data/reports/benchmark.csv"
