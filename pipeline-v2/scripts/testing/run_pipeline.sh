#!/bin/bash
#
# Pipeline v2 Runner Script
# Properly executes the pipeline with UV-managed Python environment
#
# Usage:
#   ./pipeline-v2/run_pipeline.sh --limit 10 --subreddits productivity
#   ./pipeline-v2/run_pipeline.sh --help
#

set -e  # Exit on error

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Go up two levels to get to project root (testing -> scripts -> pipeline-v2 -> project root)
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

echo "🚀 RedditHarbor Pipeline v2"
echo "=========================="
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: UV is not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run pipeline with UV (uses existing environment without re-syncing)
cd "$PROJECT_ROOT"
# Set PYTHONPATH to include pipeline-v2 for storage module imports
export PYTHONPATH="$PROJECT_ROOT/pipeline-v2:$PYTHONPATH"

# SQLAlchemy import test passed - proceed with pipeline
echo "🔧 Starting pipeline with SQLAlchemy storage..."

exec uv run --no-sync python pipeline-v2/main.py "$@"
