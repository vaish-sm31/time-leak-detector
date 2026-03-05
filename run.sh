#!/usr/bin/env bash
set -e

echo "Running Time Leak Detector..."

START=$(date +%s)

python -m src.ingest
python -m src.run_metrics
python -m src.run_rankings
python -m src.run_simulation
python -m src.run_feedback_loop

END=$(date +%s)
ELAPSED=$((END - START))

echo "Pipeline completed in ${ELAPSED} seconds."