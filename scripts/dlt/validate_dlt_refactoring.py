#!/usr/bin/env python3
"""
DLT Primary Key Refactoring Validation Script

This script validates that all hard-coded primary key strings have been
successfully replaced with centralized constants across the codebase.

Usage:
    python scripts/validate_dlt_refactoring.py
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Hard-coded primary key patterns to detect
HARD_CODED_PATTERNS = [
    r'primary_key\s*=\s*["\']submission_id["\']',
    r'primary_key\s*=\s*["\']opportunity_id["\']',
    r'primary_key\s*=\s*["\']comment_id["\']',
    r'primary_key\s*=\s*["\']display_name["\']',
    r'primary_key\s*=\s*["\']id["\']',
]

# Expected import patterns for constants
EXPECTED_IMPORTS = [
    r'from\s+core\.dlt\s+import\s+.*PK_',
    r'from\s+core\.dlt\.constants\s+import\s+.*PK_',
]

# Files that should use DLT constants
TARGET_FILES = [
    "core/dlt_app_opportunities.py",
    "core/dlt_collection.py",
    "core/dlt_cost_tracking.py",
    "core/dlt_reddit_source.py",
    "scripts/dlt/dlt_opportunity_pipeline.py",
    "scripts/dlt/dlt_trust_pipeline.py",
]


def find_python_files(project_root: Path) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []
    for file_path in project_root.rglob("*.py"):
        # Skip .venv and other ignore directories
        if ".venv" in file_path.parts:
            continue
        if "__pycache__" in file_path.parts:
            continue
        if ".git" in file_path.parts:
            continue
        # Skip archived files as they are not part of active codebase
        if "archive" in file_path.parts:
            continue

        python_files.append(file_path)
    return python_files


def check_hardcoded_patterns(file_path: Path) -> List[Tuple[int, str]]:
    """Check file for hard-coded primary key patterns."""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [(0, f"Error reading file: {e}")]

    for line_num, line in enumerate(lines, 1):
        for pattern in HARD_CODED_PATTERNS:
            if re.search(pattern, line):
                issues.append((line_num, line.strip()))

    return issues


def check_expected_imports(file_path: Path) -> bool:
    """Check if file has expected DLT imports."""
    if file_path.name not in [Path(f).name for f in TARGET_FILES]:
        return True  # Not a target file, skip import check

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False

    for pattern in EXPECTED_IMPORTS:
        if re.search(pattern, content):
            return True

    return False


def analyze_ast_for_primary_keys(file_path: Path) -> Dict[str, List[int]]:
    """Analyze AST for primary key usage in function calls and decorators."""
    usage = {
        "primary_key_usage": [],
        "dlt_decorators": [],
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            # Check function calls with primary_key argument
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "primary_key":
                        usage["primary_key_usage"].append(node.lineno)

            # Check DLT decorators
            if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                if node.func.id in ['resource', 'source']:
                    usage["dlt_decorators"].append(node.lineno)

            # Check attribute access like dlt.resource
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr'):
                if node.func.attr in ['resource', 'source']:
                    usage["dlt_decorators"].append(node.lineno)

    except Exception:
        pass  # AST parsing failed, skip

    return usage


def validate_constants_module() -> bool:
    """Validate that the constants module is working correctly."""
    try:
        sys.path.insert(0, str(Path.cwd()))
        from core.dlt import PK_SUBMISSION_ID, PK_OPPORTUNITY_ID, validate_primary_key

        # Test basic functionality
        assert PK_SUBMISSION_ID == "submission_id"
        assert PK_OPPORTUNITY_ID == "opportunity_id"
        assert validate_primary_key(PK_SUBMISSION_ID) == True

        return True
    except Exception as e:
        print(f"❌ Constants module validation failed: {e}")
        return False


def main():
    """Main validation function."""
    project_root = Path.cwd()
    print("🔍 DLT Primary Key Refactoring Validation")
    print("=" * 60)

    # Validate constants module first
    print("\n📋 Validating Constants Module...")
    if not validate_constants_module():
        print("❌ Constants module validation failed!")
        return 1

    print("✅ Constants module working correctly")

    # Find all Python files
    python_files = find_python_files(project_root)
    print(f"\n📁 Found {len(python_files)} Python files")

    # Check for hard-coded patterns
    print("\n🔍 Checking for Hard-coded Primary Key Patterns...")
    total_issues = 0
    files_with_issues = 0

    for file_path in python_files:
        # Skip the constants module itself and test files
        if "constants.py" in str(file_path) or "test_" in file_path.name:
            continue

        issues = check_hardcoded_patterns(file_path)
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            print(f"\n❌ {file_path.relative_to(project_root)}:")
            for line_num, line in issues:
                print(f"   Line {line_num}: {line}")

    if total_issues == 0:
        print("✅ No hard-coded primary key patterns found!")
    else:
        print(f"\n❌ Found {total_issues} hard-coded patterns in {files_with_issues} files")

    # Check target files for expected imports
    print("\n📦 Checking Target Files for Expected Imports...")
    missing_imports = []

    for target_file in TARGET_FILES:
        file_path = project_root / target_file
        if not file_path.exists():
            print(f"⚠️  {target_file} not found")
            continue

        if not check_expected_imports(file_path):
            missing_imports.append(target_file)

    if missing_imports:
        print("❌ Files missing expected DLT imports:")
        for file_path in missing_imports:
            print(f"   {file_path}")
    else:
        print("✅ All target files have expected imports!")

    # Analyze target files with AST
    print("\n🌳 Analyzing Target Files with AST...")
    for target_file in TARGET_FILES:
        file_path = project_root / target_file
        if not file_path.exists():
            continue

        usage = analyze_ast_for_primary_keys(file_path)
        if usage["primary_key_usage"]:
            print(f"📊 {target_file}: {len(usage['primary_key_usage'])} primary_key usages")
        if usage["dlt_decorators"]:
            print(f"🎨 {target_file}: {len(usage['dlt_decorators'])} DLT decorators")

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    if total_issues == 0 and not missing_imports:
        print("✅ REFACTORING VALIDATION PASSED!")
        print("   - No hard-coded primary key patterns found")
        print("   - All target files have expected imports")
        print("   - Constants module working correctly")
        print("\n🎉 DLT Merge Disposition Dependencies issue has been resolved!")
        return 0
    else:
        print("❌ REFACTORING VALIDATION FAILED!")
        if total_issues > 0:
            print(f"   - Found {total_issues} hard-coded patterns")
        if missing_imports:
            print(f"   - {len(missing_imports)} files missing expected imports")
        print("\nPlease address the issues above before completing the refactoring.")
        return 1


if __name__ == "__main__":
    sys.exit(main())