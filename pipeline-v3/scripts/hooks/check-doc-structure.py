#!/usr/bin/env python3
"""
Claude Code Hook: Documentation Structure Validator
Enforces proper documentation organization in docs/ directory.

Usage: uv run check-doc-structure.py [--docs-path PATH]
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Define required docs/ directory structure
DOCS_STRUCTURE = {
    'README.md': 'required',
    'api/': 'directory',
    'architecture/': 'directory',
    'components/': 'directory',
    'contributing/': 'directory',
    'guides/': 'directory',
    'implementation/': 'directory',
    'assets/': 'directory',
    'agno-integration/': 'directory',
    'technical-debt/': 'directory',
    'testing/': 'directory'
}

# Documentation file naming rules
NAMING_RULES = {
    'kebab_case': True,  # All files should use kebab-case
    'exceptions': ['README.md', 'CHANGELOG.md', 'LICENSE']  # These can use different naming
}

def check_docs_structure(docs_path: str = 'docs') -> dict:
    """Check if docs/ directory follows proper organization."""
    docs_dir = Path(docs_path)

    if not docs_dir.exists():
        return {
            'valid': False,
            'errors': [f'Docs directory {docs_path} does not exist'],
            'warnings': [],
            'structure': {}
        }

    errors = []
    warnings = []
    structure = {}

    # Check required files and directories
    for item, expected_type in DOCS_STRUCTURE.items():
        item_path = docs_dir / item

        if expected_type == 'required':
            if not item_path.exists():
                errors.append(f'Missing required file: {item}')
            else:
                structure[item] = '✅ exists'

        elif expected_type == 'directory':
            if not item_path.exists() or not item_path.is_dir():
                warnings.append(f'Missing recommended directory: {item}/')
            else:
                structure[item] = '✅ directory exists'

    # Check for orphan files in docs root
    allowed_root_files = {'README.md'}
    for item in docs_dir.iterdir():
        if item.is_file() and item.name not in allowed_root_files:
            warnings.append(f'Orphan file in docs root: {item.name} (should be in a subdirectory)')

    # Check file naming conventions
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            file_path = Path(root) / file

            # Skip exceptions
            if file in NAMING_RULES['exceptions']:
                continue

            # Check kebab-case naming
            if NAMING_RULES.get('kebab_case', False):
                expected_name = file.lower().replace('_', '-').replace(' ', '-')
                if file != expected_name:
                    rel_path = file_path.relative_to(docs_dir)
                    warnings.append(f'File naming violation: {rel_path} should be {expected_name}')

    # Check for empty directories
    for root, dirs, files in os.walk(docs_dir):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            if not any(dir_path.iterdir()):
                rel_path = dir_path.relative_to(docs_dir)
                warnings.append(f'Empty directory: docs/{rel_path}')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'structure': structure
    }

def check_doc_file_content(file_path: str) -> dict:
    """Check if a documentation file follows content standards."""
    path = Path(file_path)

    if not path.exists() or not path.suffix == '.md':
        return {'valid': True, 'issues': []}

    issues = []

    try:
        content = path.read_text(encoding='utf-8')

        # Check for proper markdown structure
        if not content.strip():
            issues.append('File is empty')
            return {'valid': False, 'issues': issues}

        lines = content.split('\n')

        # Check for title
        has_title = any(line.strip().startswith('# ') for line in lines)
        if not has_title and path.name != 'README.md':
            issues.append('Missing document title (should start with # Title)')

        # Check for proper document structure
        if len(content.split('\n\n')) < 2:
            issues.append('Document should have multiple paragraphs for better structure')

    except Exception as e:
        issues.append(f'Error reading file: {str(e)}')

    return {
        'valid': len(issues) == 0,
        'issues': issues
    }

def main():
    parser = argparse.ArgumentParser(description='Check documentation structure')
    parser.add_argument('--docs-path', default='docs', help='Path to docs directory')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--check-content', action='store_true', help='Check file content quality')

    args = parser.parse_args()

    # Check docs structure
    structure_result = check_docs_structure(args.docs_path)

    # Optionally check content quality
    content_issues = []
    if args.check_content:
        docs_dir = Path(args.docs_path)
        for file_path in docs_dir.rglob('*.md'):
            content_result = check_doc_file_content(file_path)
            if not content_result['valid']:
                content_issues.extend([
                    f"{file_path.relative_to(docs_dir)}: {issue}"
                    for issue in content_result['issues']
                ])

    # Combine results
    result = {
        'structure': structure_result,
        'content': {
            'valid': len(content_issues) == 0,
            'issues': content_issues
        },
        'overall_valid': structure_result['valid'] and len(content_issues) == 0
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("📚 DOCUMENTATION STRUCTURE CHECK")
        print("=" * 40)

        # Structure results
        if structure_result['errors']:
            print("\n🚫 ERRORS:")
            for error in structure_result['errors']:
                print(f"  ❌ {error}")

        if structure_result['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in structure_result['warnings']:
                print(f"  ⚠️  {warning}")

        # Content results
        if args.check_content:
            if content_issues:
                print("\n📝 CONTENT ISSUES:")
                for issue in content_issues:
                    print(f"  📄 {issue}")

        # Summary
        if result['overall_valid']:
            print("\n✅ Documentation structure is properly organized")
        else:
            print("\n❌ Documentation structure needs improvements")

        print(f"\nStructure: {'✅ Valid' if structure_result['valid'] else '❌ Invalid'}")
        if args.check_content:
            print(f"Content: {'✅ Valid' if len(content_issues) == 0 else '❌ Issues found'}")

    sys.exit(0 if result['overall_valid'] else 1)

if __name__ == '__main__':
    main()
