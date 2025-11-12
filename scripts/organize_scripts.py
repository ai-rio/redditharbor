#!/usr/bin/env python3
"""
Script Organization Tool
Implements the organization recommendations from script_analysis.py
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def create_directory_structure():
    """Create organized directory structure"""

    base_dir = Path(__file__).parent

    # Create subdirectories
    subdirs = [
        'core',           # Essential core scripts
        'dlt',            # DLT pipeline scripts
        'trust',          # Trust layer scripts
        'analysis',       # Analysis scripts
        'collection',     # Collection scripts
        'database',       # Database operation scripts
        'testing',        # Testing scripts
        'archive',        # Archive for obsolete scripts
    ]

    created_dirs = []
    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(exist_ok=True)
        created_dirs.append(dir_path)

    return created_dirs


def get_organization_plan() -> Dict[str, List[str]]:
    """Get the organization plan based on analysis results"""

    return {
        # Scripts to archive (completed one-time scripts)
        'archive': [
            'cleanup_empty_opportunities.py',
            'run_pipeline.py'
        ],

        # Scripts to organize by category
        'core': [
            'batch_opportunity_scoring.py',
            'collect_reddit_data.py',
            'doit_runner.py'
        ],

        'dlt': [
            'ab_threshold_testing.py',
            'activity_constrained_analysis.py',
            'advanced_niche_collection.py',
            'dlt_cli.py',
            'dlt_opportunity_pipeline.py',
            'dlt_trust_pipeline.py',
            'run_full_workflow.py',
            'test_full_pipeline_workflow.py',
            'test_trust_validation_real.py'
        ],

        'trust': [
            'trust_layer_integration.py',
            'add_trust_layer_columns.py'
        ],

        'analysis': [
            'generate_reports.py'
        ],

        'collection': [
            '__init__.py'
        ],

        'database': [
            'clean_database_slate.py'
        ],

        'testing': [
            'analyze_duplicates.py',
            'analyze_opportunities.py'
        ],

        # Keep in root (special cases)
        'root': [
            'script_analysis.py',
            'organize_scripts.py'
        ]
    }


def move_script(script_name: str, target_dir: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """Move a script to target directory"""

    base_dir = Path(__file__).parent
    source_path = base_dir / script_name
    target_path = target_dir / script_name

    if not source_path.exists():
        return False, f"Source file not found: {script_name}"

    if dry_run:
        return True, f"Would move: {script_name} -> {target_dir.name}/"

    try:
        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)

        # Move the file
        shutil.move(str(source_path), str(target_path))
        return True, f"Moved: {script_name} -> {target_dir.name}/"

    except Exception as e:
        return False, f"Error moving {script_name}: {e}"


def create_subdirectory_readmes():
    """Create README files for each subdirectory"""

    base_dir = Path(__file__).parent

    readmes = {
        'core': """# Core Scripts

These scripts are essential for RedditHarbor operation and should not be moved or modified without careful consideration.

## Scripts

- **batch_opportunity_scoring.py** - Main AI opportunity analysis script
- **collect_reddit_data.py** - Reddit data collection script
- **doit_runner.py** - Main task runner with environment management

## Usage

Core scripts can be run directly or through the doit system.
""",

        'dlt': """# DLT Pipeline Scripts

These scripts implement the DLT (Data Load Tool) powered data collection and processing pipelines.

## Scripts

- **dlt_trust_pipeline.py** - Main DLT + Trust Layer pipeline (recommended)
- **dlt_opportunity_pipeline.py** - DLT + AI opportunity pipeline
- **dlt_cli.py** - DLT command-line interface
- **run_full_workflow.py** - Complete workflow orchestrator

## Usage

Use `dlt_trust_pipeline.py` for the most complete end-to-end processing.
""",

        'trust': """# Trust Layer Scripts

These scripts implement the comprehensive trust validation system for opportunity credibility assessment.

## Scripts

- **trust_layer_integration.py** - Apply trust validation to existing opportunities
- **add_trust_layer_columns.py** - Database schema migration for trust layer

## Usage

Run `trust_layer_integration.py` to add trust indicators to existing opportunities.
""",

        'analysis': """# Analysis Scripts

These scripts perform various types of data analysis and reporting.

## Scripts

- **generate_reports.py** - Generate system reports and analytics

## Usage

Use analysis scripts for insights into system performance and data quality.
""",

        'collection': """# Collection Scripts

These scripts handle data collection from Reddit and other sources.

## Scripts

- **__init__.py** - Scripts package initialization

## Usage

Collection functionality is primarily handled by core and DLT scripts.
""",

        'database': """# Database Scripts

These scripts perform database maintenance and cleanup operations.

## Scripts

- **clean_database_slate.py** - Clear all data while preserving structure

## Usage

Use with caution! Database scripts perform destructive operations.
""",

        'testing': """# Testing Scripts

These scripts are used for testing and validation purposes.

## Scripts

- **analyze_duplicates.py** - Duplicate detection and analysis
- **analyze_opportunities.py** - Opportunity data analysis

## Usage

Testing scripts help validate data quality and system functionality.
""",

        'archive': """# Archive Scripts

These scripts are no longer actively used but are preserved for reference.

## Purpose

This directory contains completed one-time scripts and deprecated functionality that may be useful for reference or future reactivation.

## Usage

Archived scripts should not be run directly unless specifically needed for historical reference.
"""
    }

    created_files = []
    for dirname, content in readmes.items():
        dir_path = base_dir / dirname
        readme_path = dir_path / 'README.md'

        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(readme_path)
        except Exception as e:
            print(f"Error creating README for {dirname}: {e}")

    return created_files


def create_main_readme():
    """Create main README for scripts directory"""

    base_dir = Path(__file__).parent
    readme_path = base_dir / 'README.md'

    content = f"""# RedditHarbor Scripts

This directory contains all RedditHarbor scripts organized by function and purpose.

## 🚀 Quick Start

### Main Pipeline (Recommended)
```bash
# Run the complete DLT + Trust Layer pipeline
python dlt/dlt_trust_pipeline.py --subreddits personalfinance investing --limit 10
```

### Core Operations
```bash
# Collect Reddit data
python core/collect_reddit_data.py

# Analyze opportunities with AI
python core/batch_opportunity_scoring.py

# Apply trust validation
python trust/trust_layer_integration.py
```

## 📁 Directory Structure

### Essential Scripts (DO NOT MOVE)
- **`core/`** - Essential system scripts
- **`dlt/`** - DLT pipeline scripts
- **`trust/`** - Trust validation scripts

### Support Scripts
- **`analysis/`** - Data analysis and reporting
- **`testing/`** - Testing and validation
- **`database/`** - Database maintenance
- **`collection/`** - Data collection utilities

### Archive
- **`archive/`** - Deprecated or one-time scripts

## 📋 Script Categories

| Category | Purpose | Scripts |
|----------|---------|---------|
| **Core** | Essential system operation | 3 scripts |
| **DLT** | Data pipeline processing | 9 scripts |
| **Trust** | Credibility validation | 2 scripts |
| **Analysis** | Data analysis | 1 script |
| **Testing** | Validation | 2 scripts |
| **Database** | Maintenance | 1 script |
| **Archive** | Deprecated | 2 scripts |

## 🎯 Recommended Workflows

### 1. Complete Pipeline (New Data)
```bash
python dlt/dlt_trust_pipeline.py
```

### 2. Trust Validation Only (Existing Data)
```bash
python trust/trust_layer_integration.py
```

### 3. Analysis and Reporting
```bash
python analysis/generate_reports.py
```

### 4. Testing
```bash
python testing/analyze_opportunities.py
python dlt/test_trust_validation_real.py
```

## ⚙️ Configuration

Most scripts use configuration from `config/settings.py`:
- `DLT_MIN_ACTIVITY_SCORE`: Activity validation threshold (25.0)
- `DEFAULT_SUBREDDITS`: Target subreddits for collection
- Reddit API credentials in `.env` file

## 🔧 Environment Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Ensure dependencies are installed
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your Reddit API credentials
```

## 📊 System Status

Last organized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

- **Total Scripts**: 21
- **Essential Scripts**: 14
- **Support Scripts**: 5
- **Archived Scripts**: 2

## 🚨 Important Notes

1. **Core scripts should never be moved** - they are integrated into the system
2. **DLT scripts require proper setup** - ensure Supabase is running locally
3. **Trust layer requires Reddit API** - valid credentials needed
4. **Archive scripts are deprecated** - use only for reference

## 📚 Documentation

For more detailed information:
- See individual subdirectory README files
- Check `docs/guides/` for comprehensive guides
- Review `config/settings.py` for configuration options

---

*This README was generated by the script organization tool on {datetime.now().strftime('%Y-%m-%d')}*
"""

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return readme_path
    except Exception as e:
        print(f"Error creating main README: {e}")
        return None


def main():
    """Main execution"""
    print("🗂️  Organizing RedditHarbor scripts...")

    dry_run = False  # Set to True for testing, False for actual execution

    # Create directory structure
    print("\n📁 Creating directory structure...")
    created_dirs = create_directory_structure()
    for dir_path in created_dirs:
        print(f"  ✅ {dir_path.name}/")

    # Get organization plan
    organization_plan = get_organization_plan()

    # Move scripts
    print(f"\n📦 Moving scripts ({'DRY RUN' if dry_run else 'LIVE EXECUTION'})...")
    total_moved = 0

    for category, scripts in organization_plan.items():
        if category == 'root':
            continue  # Skip root scripts

        target_dir = Path(__file__).parent / category

        for script in scripts:
            success, message = move_script(script, target_dir, dry_run)
            if success:
                print(f"  {message}")
                total_moved += 1
            else:
                print(f"  ❌ {message}")

    # Create README files
    print("\n📄 Creating README files...")
    created_readmes = create_subdirectory_readmes()
    for readme_path in created_readmes:
        print(f"  ✅ {readme_path.name}")

    # Create main README
    main_readme = create_main_readme()
    if main_readme:
        print(f"  ✅ {main_readme.name}")

    # Summary
    print(f"\n🎉 Script organization complete!")
    print(f"📊 Total scripts moved: {total_moved}")
    print(f"📁 Directories created: {len(created_dirs)}")
    print(f"📄 README files created: {len(created_readmes) + 1}")

    if dry_run:
        print(f"\n⚠️  This was a DRY RUN. No files were actually moved.")
        print(f"💡 To execute, change `dry_run = False` in the script and run again.")
    else:
        print(f"\n✅ All scripts have been organized successfully!")
        print(f"📖 See {Path(__file__).parent / 'README.md'} for usage guide.")


if __name__ == "__main__":
    main()