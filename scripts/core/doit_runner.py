#!/usr/bin/env python3
"""
RedditHarbor doit runner with automatic .venv activation

This script ensures doit runs with the correct virtual environment
activated and provides convenient task execution.

Usage:
    python scripts/doit_runner.py                    # Run default task
    python scripts/doit_runner.py list              # List all tasks
    python scripts/doit_runner.py collect_data      # Run specific task
    python scripts/doit_runner.py run_full_pipeline # Run complete pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

# Get project root (parent of scripts directory)
PROJECT_ROOT = Path(__file__).parent.parent
VENV_PATH = PROJECT_ROOT / ".venv"

def ensure_venv():
    """Ensure we're running with the correct virtual environment"""

    # Check if .venv exists
    if not VENV_PATH.exists():
        print("❌ Virtual environment not found at:", VENV_PATH)
        print("Run: uv venv to create virtual environment")
        return False

    # Check if we're already in the venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Already in virtual environment")
        return True

    # Check for UV and activate .venv
    uv_venv_python = VENV_PATH / "bin" / "python"
    if uv_venv_python.exists():
        print("✅ Using UV virtual environment")
        # Update sys.path to use venv python
        sys.executable = str(uv_venv_python)
        return True

    print("⚠️  Could not verify virtual environment setup")
    return True  # Continue anyway

def run_doit(args):
    """Run doit with proper environment"""

    # Ensure we're in project root
    os.chdir(PROJECT_ROOT)

    # Build doit command - use venv python directly if available
    venv_python = VENV_PATH / "bin" / "python"
    if venv_python.exists():
        cmd = [str(venv_python), '-m', 'doit'] + args
    else:
        cmd = [sys.executable, '-m', 'doit'] + args

    # Set environment variables
    env = os.environ.copy()

    # Add project root to PYTHONPATH
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{PROJECT_ROOT}:{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = str(PROJECT_ROOT)

    print(f"🚀 Running: {' '.join(cmd)}")
    print(f"📁 Working directory: {PROJECT_ROOT}")

    try:
        result = subprocess.run(cmd, env=env, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code: {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ doit not found. Install with: uv add --optional orchestration")
        return 1

def main():
    """Main entry point"""

    # Handle help flag
    if len(sys.argv) == 1 or sys.argv[1] in ['--help', '-h', 'help']:
        print("""
RedditHarbor Task Manager (doit)

Usage:
    python scripts/doit_runner.py [command] [options]

Available commands:
    (no args)              Run default pipeline (collect → analyze → report)
    list                    List all available tasks
    collect_reddit_data    Collect Reddit data
    analyze_opportunities   Analyze opportunities with AI
    generate_reports        Generate final reports
    run_full_pipeline       Run complete pipeline
    clean_database          Clean database slate
    check_environment       Verify environment setup
    run_tests              Run test suite
    lint_code              Run linting and formatting
    run_dashboard          Start Marimo dashboard
    clean                   Clean generated files
    qa                     Run QA tests
    dev                    Run development tasks (lint + test)

Task groups:
    collect                Run all collection tasks
    analysis               Run all analysis tasks
    reports                Run all reporting tasks
    qa                     Run all QA tasks
    dev                    Run all development tasks

Examples:
    python scripts/doit_runner.py list
    python scripts/doit_runner.py run_full_pipeline
    python scripts/doit_runner.py clean && python scripts/doit_runner.py run_full_pipeline

For more options: python scripts/doit_runner.py --help doit
        """)
        return 0

    # Special case for doit help
    if sys.argv[1] in ['--help-doit', 'help-doit']:
        return run_doit(sys.argv[2:] or ['--help'])

    # Ensure virtual environment
    if not ensure_venv():
        return 1

    # Run doit with provided arguments
    return run_doit(sys.argv[1:])

if __name__ == '__main__':
    sys.exit(main())