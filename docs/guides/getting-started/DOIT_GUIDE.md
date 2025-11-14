# RedditHarbor Task Management with doit

This guide explains how to use doit for RedditHarbor task management and automation.

## Installation

doit is already installed in your `.venv` environment. No additional setup required.

## Quick Start

```bash
# List all available tasks
python3 scripts/doit_runner.py list

# Run default pipeline (collect → analyze → report)
python3 scripts/doit_runner.py

# Run specific task
python3 scripts/doit_runner.py collect_reddit_data

# Run complete pipeline
python3 scripts/doit_runner.py run_full_pipeline
```

## Available Tasks

### Core Pipeline Tasks
- `collect_reddit_data` - Collect Reddit posts and comments
- `analyze_opportunities` - Analyze data for business opportunities
- `generate_reports` - Generate professional reports
- `run_full_pipeline` - Run complete pipeline

### Utility Tasks
- `check_environment` - Verify environment setup
- `clean_database` - Clean database for fresh start
- `start_services` - Start Supabase services
- `cleanup` - Clean generated files and logs

### Development Tasks
- `run_tests` - Run pytest test suite
- `lint_code` - Run ruff linting and formatting
- `run_dashboard` - Start Marimo dashboard

### Quality Assurance
- `qa_function_distribution` - Check for function count bias
- `e2e_test` - Run end-to-end pipeline test
- `full_scale_collection` - Run full-scale data collection

### Task Groups
- `collect` - Run all collection tasks
- `analysis` - Run all analysis tasks
- `reports` - Run all reporting tasks
- `qa` - Run all QA tasks
- `dev` - Run all development tasks

## Advanced Usage

### Dependency Management
doit automatically manages dependencies between tasks. For example:
```bash
# This will automatically run: collect_reddit_data → analyze_opportunities → generate_reports
python3 scripts/doit_runner.py run_full_pipeline
```

### Incremental Builds
doit caches results and only runs tasks when inputs change:
```bash
# Second run will be instant if nothing changed
python3 scripts/doit_runner.py collect_reddit_data
```

### Task Selection
You can run specific tasks or groups:
```bash
# Run specific task
python3 scripts/doit_runner.py collect_reddit_data

# Run task group
python3 scripts/doit_runner.py collect

# Run multiple tasks
python3 scripts/doit_runner.py collect_reddit_data analyze_opportunities
```

### File Dependencies
doit tracks file dependencies and only re-runs tasks when files change:
```bash
# Will only run if config/settings.py or scripts/collect_reddit_data.py changed
python3 scripts/doit_runner.py collect_reddit_data
```

## Common Workflows

### 1. Development Workflow
```bash
# 1. Check environment
python3 scripts/doit_runner.py check_environment

# 2. Run tests and linting
python3 scripts/doit_runner.py dev

# 3. Run pipeline
python3 scripts/doit_runner.py run_full_pipeline
```

### 2. Clean Pipeline Run
```bash
# 1. Clean everything
python3 scripts/doit_runner.py cleanup
python3 scripts/doit_runner.py clean_database

# 2. Run fresh pipeline
python3 scripts/doit_runner.py run_full_pipeline
```

### 3. Quality Assurance
```bash
# 1. Run QA checks
python3 scripts/doit_runner.py qa

# 2. Run tests
python3 scripts/doit_runner.py run_tests

# 3. Verify with E2E test
python3 scripts/doit_runner.py e2e_test
```

### 4. Data Collection
```bash
# 1. Small batch collection
python3 scripts/doit_runner.py collect_reddit_data

# 2. Full-scale collection
python3 scripts/doit_runner.py full_scale_collection
```

## Custom Tasks

To add custom tasks, edit `dodo.py`:

```python
def task_my_custom_task():
    """Custom task description"""
    return {
        'doc': 'Task description',
        'actions': ['echo "Running custom task"'],
        'file_dep': ['dependency_file.py'],
        'targets': ['output_file.txt'],
        'task_dep': ['other_task'],  # Dependencies on other tasks
    }
```

## Environment Integration

The doit runner automatically:
- Uses the `.venv` virtual environment
- Sets correct PYTHONPATH
- Changes to project root directory
- Handles environment variables

## Troubleshooting

### Module Import Errors
If you see import errors, ensure you're in the project root and dependencies are installed:
```bash
uv sync  # Install dependencies
python3 scripts/doit_runner.py check_environment
```

### Task Not Found
List all available tasks:
```bash
python3 scripts/doit_runner.py list
```

### Virtual Environment Issues
Ensure the `.venv` directory exists and is activated:
```bash
# Recreate venv if needed
rm -rf .venv
uv venv
uv sync
```

## Integration with UV

doit works seamlessly with UV:
- Uses `.venv/bin/python` for execution
- Respects `uv.lock` dependency lock file
- Integrates with UV's fast dependency management

## Performance Features

### Parallel Execution
doit can run tasks in parallel:
```bash
doit -n 4  # Run with 4 parallel processes
```

### Task Caching
doit automatically caches results and skips unchanged tasks, making repeated runs fast.

### File Watching
For development, you can use doit's auto-reload feature:
```bash
doit auto  # Automatically re-run tasks when files change
```

## Configuration

The task configuration is in `dodo.py`:
- **Actions**: Commands or Python functions to execute
- **Dependencies**: Files or tasks that must complete first
- **Targets**: Output files created by the task
- **Uptodate**: Conditions to skip task execution

## Migration from Manual Execution

Replace manual script execution:

| Before | After |
|--------|-------|
| `python scripts/collect_reddit_data.py` | `python3 scripts/doit_runner.py collect_reddit_data` |
| `python scripts/analyze_opportunities.py` | `python3 scripts/doit_runner.py analyze_opportunities` |
| `python scripts/run_pipeline.py` | `python3 scripts/doit_runner.py run_full_pipeline` |

## Benefits

1. **Dependency Management**: Automatic dependency resolution
2. **Incremental Builds**: Only runs what needs to run
3. **Task Organization**: Clean, documented task structure
4. **Error Handling**: Better error reporting and recovery
5. **Parallel Execution**: Can run multiple tasks simultaneously
6. **Integration**: Seamless UV and Python integration
7. **Professional**: Industry-standard task automation

For more information, see the [doit documentation](https://pydoit.org/).