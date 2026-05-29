#!/bin/bash
# run_benchmark.sh — Run flm bench for a single model and save results.
#
# Usage:
#   bash run_benchmark.sh <model_tag>
#   bash run_benchmark.sh llama3.2:1b
#
# Note: Run one model at a time. Concurrent FLM processes exhaust NPU memory.
# For 4B+ models, use bench_serve.py instead (flm bench OOMs at 32k context).

set -euo pipefail

MODEL="${1:?Usage: run_benchmark.sh <model_tag>}"
RESULTS_DIR="$(dirname "$0")/../results"
mkdir -p "$RESULTS_DIR"

echo "=== Pulling $MODEL ==="
flm pull "$MODEL"

echo ""
echo "=== Dropping OS cache before benchmark ==="
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null || true

echo ""
echo "=== Benchmarking $MODEL ==="
cd "$RESULTS_DIR"
flm bench "$MODEL" 2>&1

echo ""
echo "=== Done: $MODEL ==="
echo "Results saved to $RESULTS_DIR"
