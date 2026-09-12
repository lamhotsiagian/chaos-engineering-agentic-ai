#!/usr/bin/env bash
set -e

# Use python3 from active environment or fallback
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "================================================================="
echo "⚡ EXECUTING ALL 15 AGENTIC AI CHAOS EXPERIMENTS SEQUENTIALLY ⚡"
echo "================================================================="

for ch in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15; do
    echo ""
    echo "-----------------------------------------------------------------"
    echo "▶️ Running Chapter ${ch} Chaos Experiment..."
    echo "-----------------------------------------------------------------"
    $PYTHON_BIN experiments/chapter${ch}/experiment.py
done

echo ""
echo "================================================================="
echo "✅ ALL 15 CHAOS EXPERIMENTS COMPLETED SUCCESSFULLY!"
echo "================================================================="
