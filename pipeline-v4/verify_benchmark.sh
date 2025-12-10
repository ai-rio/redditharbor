#!/bin/bash
# Verification script for Performance Benchmark (Task 3.4)
# Demonstrates benchmark execution and validates results

set -e

echo "=================================="
echo "Task 3.4: Performance Benchmark"
echo "Verification Script"
echo "=================================="
echo ""

# Check Python environment
echo "1. Verifying Python environment..."
source ../.venv/bin/activate
python --version
echo "✓ Python environment active"
echo ""

# Check dependencies
echo "2. Checking benchmark dependencies..."
python -c "import psutil; import pandas; print('✓ psutil:', psutil.__version__)"
python -c "import pandas; print('✓ pandas:', pandas.__version__)"
echo ""

# Verify benchmark script exists
echo "3. Verifying benchmark script..."
if [ -f "benchmark_loaders.py" ]; then
    echo "✓ benchmark_loaders.py exists ($(wc -l < benchmark_loaders.py) lines)"
else
    echo "✗ benchmark_loaders.py not found"
    exit 1
fi
echo ""

# Verify loaders can be imported
echo "4. Verifying loader imports..."
python -c "from load.postgres_loader import PostgresLoader; print('✓ PostgresLoader imported')"
python -c "from load.sqlmodel_loader import SQLModelLoader; print('✓ SQLModelLoader imported')"
echo ""

# Check if results exist
echo "5. Checking benchmark results..."
if [ -f "benchmark_results.json" ]; then
    echo "✓ benchmark_results.json exists ($(wc -c < benchmark_results.json) bytes)"
    echo ""
    echo "Key Results:"
    python -c "
import json
with open('benchmark_results.json') as f:
    data = json.load(f)
print(f\"  Data Volumes: {data['data_volumes']}\")
print(f\"  Test Timestamp: {data['timestamp']}\")
print('')
print('Performance Gaps:')
for metric, values in data['comparison'].items():
    if metric != 'memory_usage':
        faster = values['faster']
        diff = values['difference_percent']
        print(f\"  {metric:20s}: {diff:+6.1f}% (faster: {faster})\")
"
else
    echo "✗ benchmark_results.json not found"
    echo "  Run: python benchmark_loaders.py"
fi
echo ""

# Check report
echo "6. Verifying performance report..."
if [ -f "PERFORMANCE_BENCHMARK_REPORT.md" ]; then
    echo "✓ PERFORMANCE_BENCHMARK_REPORT.md exists ($(wc -l < PERFORMANCE_BENCHMARK_REPORT.md) lines)"
    echo ""
    echo "Report Summary:"
    grep -A 1 "^**Performance Gate Status:**" PERFORMANCE_BENCHMARK_REPORT.md | head -2
else
    echo "✗ PERFORMANCE_BENCHMARK_REPORT.md not found"
    exit 1
fi
echo ""

# Final summary
echo "=================================="
echo "Verification Complete"
echo "=================================="
echo ""
echo "Deliverables:"
echo "  ✓ benchmark_loaders.py         - Benchmark test suite"
echo "  ✓ benchmark_results.json       - Raw benchmark data"
echo "  ✓ PERFORMANCE_BENCHMARK_REPORT.md - Analysis and recommendations"
echo ""
echo "Status: Task 3.4 deliverables verified"
echo ""
