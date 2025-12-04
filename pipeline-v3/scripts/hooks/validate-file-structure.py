#!/usr/bin/env python3
"""
Claude Code Hook: File Structure Validator
Prevents creation of unnecessary files at project root and enforces documentation organization.

Usage: uv run validate-file-structure.py [--tool-name TOOL] [--file-paths PATHS]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Set

# Define allowed root files for pipeline-v3
ALLOWED_ROOT_FILES = {
    'README.md',
    '__init__.py',
    'main.py',
    'pyproject.toml',
    'requirements.txt',
    'uv.lock',
    '.env',
    '.env.example',
    '.gitignore',
    'CLAUDE.md',
    'ai-rulez.yaml',
    'lint.sh',
    'pytest.ini',
    'ruff.toml'
}

# Define proper directories for file types (ELT Architecture)
DIRECTORY_RULES = {
    # Documentation
    '.md': 'docs/',

    # Python files following ETL architecture
    '.py': {
        'main.py': 'root',  # Allow at root
        '__init__.py': 'root',  # Allow at root
        'default': {
            # ETL pipeline stages
            'extract': ['extract_', 'reddit_', 'scraper', 'collector', 'fetcher'],
            'transform': ['transform_', 'process_', 'convert_', 'map_', 'filter_'],
            'load': ['load_', 'save_', 'store_', 'write_', 'export_', 'import_'],
            # Core business logic
            'core': ['core', 'shared', 'common'],
            # Data structures
            'models': ['model', 'schema', 'entity', 'dto'],
            # Configuration
            'config': ['config', 'settings', 'env'],
            # External services
            'services': ['service', 'client', 'api', 'external'],
            # Utilities
            'utils': ['util', 'helper', 'tool'],
            # Testing
            'tests': ['test_', 'mock_', 'fixture'],
            'default_location': 'core/'  # Fallback for unmatched files
        }
    },

    # Configuration and data files
    '.json': {
        'qa_audit_results.json': 'root',
        'test_report_*.json': 'root',
        'pytest.ini': 'root',
        'default': 'config/'
    },

    '.yaml': 'config/',
    '.yml': 'config/',

    # Scripts
    '.sh': 'scripts/',

    # SQL files
    '.sql': 'scripts/database/',

    # Log files
    '.log': 'error_log/',
}

def get_file_destination(file_path: str) -> str:
    """Determine where a file should be located based on ELT architecture."""
    path = Path(file_path)
    filename = path.name
    suffix = path.suffix

    # Check if file is in docs/ already
    if 'docs/' in file_path:
        return 'docs/'  # Already in correct location

    # Check documentation files
    if suffix == '.md' and filename != 'README.md':
        return 'docs/'

    # Check Python files with intelligent ETL-based placement
    if suffix == '.py':
        if filename in ['main.py', '__init__.py']:
            return 'root'  # Allowed at root

        # Check ELT-specific naming patterns
        py_rules = DIRECTORY_RULES['.py']['default']
        filename_lower = filename.lower()

        for directory, patterns in py_rules.items():
            if directory == 'default_location':
                continue

            for pattern in patterns:
                if filename_lower.startswith(pattern):
                    return f"{directory}/"

        # If no pattern matches, use default location
        return py_rules.get('default_location', 'core/')

    # Check JSON files
    if suffix == '.json':
        if filename in ['qa_audit_results.json', 'pytest.ini'] or filename.startswith('test_report_'):
            return 'root'  # Allow specific report files at root
        return 'config/'

    # Check other file types
    for ext, destination in DIRECTORY_RULES.items():
        if suffix == ext:
            if isinstance(destination, dict):
                if filename in destination:
                    return destination[filename]
                return destination.get('default', 'config/')
            return destination

    return 'root'  # Default to root if no rule matches

def validate_file_creation(file_paths: List[str], tool_name: str = None) -> dict:
    """Validate file creation/operation against organization rules."""
    violations = []
    warnings = []

    for file_path in file_paths:
        path = Path(file_path)

        # Skip directories and non-existent paths
        if not path.exists() and tool_name not in ['Write', 'Edit']:
            continue

        # Check if file is at project root
        if '/' not in file_path or file_path.count('/') == 0:
            filename = path.name

            # Check if root file is allowed
            if filename not in ALLOWED_ROOT_FILES:
                proper_location = get_file_destination(file_path)
                if proper_location != 'root':
                    violations.append({
                        'file': file_path,
                        'issue': f'File "{filename}" not allowed at project root',
                        'suggestion': f'Move to {proper_location}{filename}',
                        'severity': 'error'
                    })
                else:
                    warnings.append({
                        'file': file_path,
                        'issue': f'Consider if "{filename}" is necessary at project root',
                        'suggestion': 'Follow project organization standards',
                        'severity': 'warning'
                    })

        # Check documentation organization
        if file_path.endswith('.md') and file_path != 'README.md':
            if not file_path.startswith('docs/'):
                violations.append({
                    'file': file_path,
                    'issue': 'Markdown files must be in docs/ directory',
                    'suggestion': f'Move to docs/{path.name}',
                    'severity': 'error'
                })

            # Check for kebab-case in documentation
            if file_path != path.name.lower().replace('_', '-').replace(' ', '-'):
                warnings.append({
                    'file': file_path,
                    'issue': 'Documentation files should use kebab-case naming',
                    'suggestion': f'Rename to {path.name.lower().replace("_", "-").replace(" ", "-")}',
                    'severity': 'warning'
                })

    return {
        'violations': violations,
        'warnings': warnings,
        'allowed': len(violations) == 0
    }

def main():
    parser = argparse.ArgumentParser(description='Validate file structure organization')
    parser.add_argument('--tool-name', help='Tool name being used')
    parser.add_argument('--file-paths', nargs='*', help='File paths being operated on')
    parser.add_argument('--json', action='store_true', help='Output JSON format')

    args = parser.parse_args()

    # Get file paths from args or environment
    file_paths = args.file_paths or os.environ.get('CLAUDE_FILE_PATHS', '').split()
    tool_name = args.tool_name or os.environ.get('CLAUDE_TOOL_NAME', '')

    # Validate file structure
    result = validate_file_creation(file_paths, tool_name)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Print human-readable output
        if result['violations']:
            print("🚫 FILE ORGANIZATION VIOLATIONS:")
            for violation in result['violations']:
                print(f"  ❌ {violation['issue']}")
                print(f"     💡 Suggestion: {violation['suggestion']}")
                print(f"     File: {violation['file']}")
                print()

        if result['warnings']:
            print("⚠️  ORGANIZATION WARNINGS:")
            for warning in result['warnings']:
                print(f"  ⚠️  {warning['issue']}")
                print(f"     💡 Suggestion: {warning['suggestion']}")
                print(f"     File: {warning['file']}")
                print()

        if not result['violations'] and not result['warnings']:
            print("✅ File structure validation passed")

    # Exit with error code if violations exist
    sys.exit(0 if result['allowed'] else 1)

if __name__ == '__main__':
    main()