#!/usr/bin/env bash
# (Bản tạm của TV1 theo file hướng dẫn cài đặt; TV3 sẽ hoàn thiện)
set -e
export MSYS_NO_PATHCONV=1

SUBMIT="docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --driver-memory 2g"

$SUBMIT /opt/jobs/00_ingest.py
$SUBMIT /opt/jobs/01_profiling.py raw
$SUBMIT /opt/jobs/02_cleaning.py
$SUBMIT /opt/jobs/01_profiling.py clean
$SUBMIT /opt/jobs/03_aggregation.py

echo "Pipeline xong. Xem ket qua trong data/"
