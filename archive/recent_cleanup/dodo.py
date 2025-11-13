#!/usr/bin/env python3
"""
RedditHarbor Task Management with doit

This file defines all RedditHarbor tasks for doit automation.
Tasks are organized in logical groups and include proper dependency tracking.

Usage:
    doit list                    # Show all available tasks
    doit                          # Run default pipeline
    doit collect_reddit_data     # Run specific task
    doit run_full_pipeline       # Run complete pipeline
"""

import os
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules for task definitions
try:
    from config.settings import (
        SUPABASE_URL, SUPABASE_KEY,
        ENABLE_PII_ANONYMIZATION,
        ERROR_LOG_DIR
    )
    from core.setup import check_dependencies
except ImportError as e:
    print(f"Warning: Could not import project modules: {e}")
    print("Make sure you're in the project root and dependencies are installed")

# Configuration constants
SCRIPTS_DIR = "scripts"
DATA_DIR = "data"
REPORTS_DIR = "reports"
LOGS_DIR = "error_log"
VENV_PYTHON = str(project_root / ".venv" / "bin" / "python")

# Ensure directories exist
for dir_path in [DATA_DIR, REPORTS_DIR, LOGS_DIR]:
    Path(dir_path).mkdir(exist_ok=True)

# ==============================================================================
# CORE PIPELINE TASKS
# ==============================================================================

def task_collect_reddit_data():
    """
    Task 1: Collect Reddit data and store in database
    """
    return {
        'doc': 'Collect Reddit posts and comments using PRAW API',
        'actions': [f'{VENV_PYTHON} {SCRIPTS_DIR}/collect_reddit_data.py'],
        'file_dep': [
            f'{SCRIPTS_DIR}/collect_reddit_data.py',
            'core/collection.py',
            'config/settings.py',
            'pyproject.toml'
        ],
        'targets': [
            f'{LOGS_DIR}/collection_log.txt'  # Log file indicates completion
        ],
        'uptodate': [True],  # Always run for fresh data
    }

def task_analyze_opportunities():
    """
    Task 2: Analyze collected data for opportunities using AI
    """
    return {
        'doc': 'Analyze Reddit data for business opportunities using AI',
        'actions': [f'{VENV_PYTHON} {SCRIPTS_DIR}/analyze_opportunities.py'],
        'file_dep': [
            f'{SCRIPTS_DIR}/analyze_opportunities.py',
            'agent_tools/opportunity_analyzer_agent.py',
            'agent_tools/llm_profiler.py',
            'config/settings.py'
        ],
        'task_dep': ['collect_reddit_data'],  # Wait for data collection
        'targets': [
            f'{LOGS_DIR}/analysis_log.txt'
        ],
    }

def task_generate_reports():
    """
    Task 3: Generate final reports from analyzed opportunities
    """
    return {
        'doc': 'Generate professional reports from opportunity analysis',
        'actions': [f'{VENV_PYTHON} {SCRIPTS_DIR}/generate_reports.py'],
        'file_dep': [
            f'{SCRIPTS_DIR}/generate_reports.py',
            'config/settings.py'
        ],
        'task_dep': ['analyze_opportunities'],  # Wait for analysis
        'targets': [
            'reports/',
            f'{LOGS_DIR}/reports_log.txt'
        ],
    }

def task_run_full_pipeline():
    """
    Complete pipeline orchestrator - runs all tasks in sequence
    """
    return {
        'doc': 'Run complete RedditHarbor pipeline: collect → analyze → report',
        'actions': [f'python3 {SCRIPTS_DIR}/run_pipeline.py'],
        'file_dep': [
            f'{SCRIPTS_DIR}/run_pipeline.py',
            f'{SCRIPTS_DIR}/collect_reddit_data.py',
            f'{SCRIPTS_DIR}/analyze_opportunities.py',
            f'{SCRIPTS_DIR}/generate_reports.py',
            'config/settings.py'
        ],
        'task_dep': [
            'collect_reddit_data',
            'analyze_opportunities',
            'generate_reports'
        ],
        'verbosity': 2,  # Show detailed output
    }

# ==============================================================================
# UTILITY TASKS
# ==============================================================================

def task_clean_database():
    """
    Clean database slate for fresh start
    """
    return {
        'doc': 'Clean all data from database for fresh pipeline run',
        'actions': [f'python3 {SCRIPTS_DIR}/clean_database_slate.py'],
        'file_dep': [
            f'{SCRIPTS_DIR}/clean_database_slate.py',
            'config/settings.py'
        ],
        'uptodate': [True],  # Always allow running
    }

def task_check_environment():
    """
    Verify environment and dependencies
    """
    def check_env():
        """Check environment variables and dependencies"""
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            print("Please check your .env file")
            return False

        # Check dependencies
        try:
            check_dependencies()
            print("✅ All dependencies available")
            return True
        except Exception as e:
            print(f"❌ Dependency check failed: {e}")
            return False

    return {
        'doc': 'Verify environment variables and dependencies',
        'actions': [check_env],
        'uptodate': [True],  # Always check
        'verbosity': 2,
    }

def task_start_services():
    """
    Start required services (Supabase)
    """
    return {
        'doc': 'Start Supabase services locally',
        'actions': ['supabase start'],
        'uptodate': [True],  # Always check
        'verbosity': 2,
    }

# ==============================================================================
# DEVELOPMENT TASKS
# ==============================================================================

def task_run_tests():
    """
    Run test suite
    """
    return {
        'doc': 'Run pytest test suite',
        'actions': [f'{VENV_PYTHON} -m pytest tests/ -v'],
        'file_dep': [
            'tests/',
            'core/',
            'config/'
        ],
        'verbosity': 2,
    }

def task_lint_code():
    """
    Run linting and formatting
    """
    return {
        'doc': 'Run ruff linting and formatting',
        'actions': [
            f'{VENV_PYTHON} -m ruff check .',
            f'{VENV_PYTHON} -m ruff format .'
        ],
        'file_dep': [
            'core/',
            'scripts/',
            'tests/',
            'config/',
            'ruff.toml'
        ],
        'verbosity': 2,
    }

def task_run_dashboard():
    """
    Start Marimo dashboard
    """
    return {
        'doc': 'Start Marimo dashboard for data visualization',
        'actions': ['marimo edit marimo_notebooks/opportunity_dashboard_fixed.py'],
        'file_dep': [
            'marimo_notebooks/opportunity_dashboard_fixed.py'
        ],
        'uptodate': [True],  # Always can start
        'verbosity': 2,
    }

# ==============================================================================
# BATCH PROCESSING TASKS
# ==============================================================================

def task_test_batch_scoring():
    """Test batch opportunity scoring on small dataset"""
    return {
        'doc': 'Test batch opportunity scoring with small dataset',
        'actions': ['SCORE_THRESHOLD=25.0 python3 scripts/batch_opportunity_scoring.py'],
        'file_dep': [
            'scripts/batch_opportunity_scoring.py',
            'agent_tools/opportunity_analyzer_agent.py',
            'agent_tools/llm_profiler.py'
        ],
        'uptodate': [True],
        'verbosity': 2,
    }

def task_full_scale_collection():
    """
    Run full-scale Reddit data collection
    """
    return {
        'doc': 'Run full-scale Reddit data collection with DLT',
        'actions': ['python3 scripts/full_scale_collection.py'],
        'file_dep': [
            'scripts/full_scale_collection.py',
            'core/dlt_reddit_source.py',
            'core/activity_validation.py',
            'config/dlt_settings.py'
        ],
        'targets': [
            f'{LOGS_DIR}/dlt_collection_log.txt'
        ],
        'uptodate': [True],
        'verbosity': 2,
    }

# ==============================================================================
# QUALITY ASSURANCE TASKS
# ==============================================================================

def task_qa_function_distribution():
    """
    Run QA check for function count distribution bias
    """
    return {
        'doc': 'QA: Check function count distribution for bias detection',
        'actions': ['python3 scripts/qa_function_count_distribution.py'],
        'file_dep': [
            'scripts/qa_function_count_distribution.py'
        ],
        'uptodate': [True],
        'verbosity': 2,
    }

def task_e2e_test():
    """
    Run end-to-end pipeline test
    """
    return {
        'doc': 'Run end-to-end pipeline test with small batch',
        'actions': ['python3 scripts/e2e_test_small_batch.py'],
        'file_dep': [
            'scripts/e2e_test_small_batch.py',
            'core/',
            'agent_tools/',
            'config/'
        ],
        'uptodate': [True],
        'verbosity': 2,
    }

# ==============================================================================
# DEFAULT TASKS
# ==============================================================================

# Define default task when running `doit` without arguments
DEFAULT_TASKS = [
    'check_environment',
    'run_full_pipeline'
]

def task_default():
    """
    Default task - runs complete pipeline
    """
    return {
        'doc': 'Default task: run complete RedditHarbor pipeline',
        'actions': [],
        'task_dep': DEFAULT_TASKS,
        'verbosity': 2,
    }

# ==============================================================================
# TASK GROUPS
# ==============================================================================

# You can run task groups like: doit collect
def task_collect():
    """Collection tasks group"""
    return {
        'doc': 'Run all data collection tasks',
        'actions': [],
        'task_dep': ['collect_reddit_data', 'full_scale_collection'],
    }

def task_analysis():
    """Analysis tasks group"""
    return {
        'doc': 'Run all analysis tasks',
        'actions': [],
        'task_dep': ['analyze_opportunities', 'test_batch_scoring'],
    }

def task_reports():
    """Reports tasks group"""
    return {
        'doc': 'Run all reporting tasks',
        'actions': [],
        'task_dep': ['generate_reports'],
    }

def task_qa():
    """Quality assurance tasks group"""
    return {
        'doc': 'Run all QA tasks',
        'actions': [],
        'task_dep': ['qa_function_distribution', 'e2e_test'],
    }

def task_dev():
    """Development tasks group"""
    return {
        'doc': 'Run all development tasks (lint, test)',
        'actions': [],
        'task_dep': ['lint_code', 'run_tests'],
    }

# ==============================================================================
# CLEANUP TASKS
# ==============================================================================

def task_cleanup():
    """
    Clean generated files and logs
    """
    def clean_files():
        import shutil
        import glob

        # Clean log files
        for pattern in ['error_log/*.txt', 'error_log/*.log']:
            for file_path in glob.glob(pattern):
                try:
                    os.remove(file_path)
                    print(f"Removed: {file_path}")
                except FileNotFoundError:
                    pass

        # Clean data directory (keep structure)
        if Path(DATA_DIR).exists():
            for item in Path(DATA_DIR).glob('*'):
                if item.is_file():
                    item.unlink()
                    print(f"Removed: {item}")

        # Clean reports directory
        if Path(REPORTS_DIR).exists():
            shutil.rmtree(REPORTS_DIR)
            Path(REPORTS_DIR).mkdir(exist_ok=True)
            print(f"Cleaned: {REPORTS_DIR}/")

        print("✅ Cleanup completed")

    return {
        'doc': 'Clean generated files, logs, and temporary data',
        'actions': [clean_files],
        'uptodate': [True],
        'verbosity': 2,
    }

if __name__ == '__main__':
    # Allow running this file directly: python dodo.py
    import subprocess
    subprocess.run([sys.executable, '-m', 'doit'] + sys.argv[1:])