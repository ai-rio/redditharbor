#!/usr/bin/env python3
"""
Script Analysis and Organization Tool
Analyzes all scripts to categorize them for proper organization
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


def analyze_script_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python script to determine its purpose and status"""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            'name': file_path.name,
            'path': str(file_path),
            'size': 0,
            'purpose': 'ERROR',
            'category': 'error',
            'essential': False,
            'status': 'unreadable',
            'description': f'Error reading file: {e}',
            'dependencies': [],
            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }

    # Extract key information
    name = file_path.name
    size = len(content)

    # Extract description from docstring
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    description = docstring_match.group(1).strip() if docstring_match else "No description"

    # Extract imports
    imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+(.+)$', content, re.MULTILINE)
    dependencies = []
    for imp in imports:
        parts = imp.split(',')
        for part in parts:
            dep = part.strip().split(' as ')[0]
            if dep and not dep.startswith('.'):
                dependencies.append(dep)

    # Determine category based on name and content
    category = determine_category(name, content, description)

    # Determine if essential based on category and content
    essential = determine_essential(name, category, content)

    # Determine status
    status = determine_status(content)

    return {
        'name': name,
        'path': str(file_path),
        'size': size,
        'purpose': description.split('\n')[0] if description else "No description",
        'category': category,
        'essential': essential,
        'status': status,
        'description': description,
        'dependencies': dependencies[:10],  # Limit dependencies shown
        'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
    }


def determine_category(name: str, content: str, description: str) -> str:
    """Determine script category based on name and content"""

    name_lower = name.lower()
    content_lower = content.lower()
    desc_lower = description.lower()

    # Essential core scripts
    if any(keyword in name_lower for keyword in ['batch_opportunity_scoring', 'collect_reddit_data', 'doit_runner']):
        return 'core'

    # DLT related
    if any(keyword in name_lower for keyword in ['dlt_']) or 'dlt' in content_lower:
        return 'dlt'

    # Trust layer related
    if any(keyword in name_lower for keyword in ['trust_']) or 'trust' in content_lower:
        return 'trust'

    # Testing scripts
    if any(keyword in name_lower for keyword in ['test_', 'analyze_']):
        return 'testing'

    # Analysis scripts
    if any(keyword in name_lower for keyword in ['analyze_', 'generate_reports']):
        return 'analysis'

    # Database operations
    if any(keyword in desc_lower for keyword in ['database', 'clean', 'cleanup']):
        return 'database'

    # Collection scripts
    if any(keyword in desc_lower for keyword in ['collect', 'collection', 'reddit']):
        return 'collection'

    # Workflow/pipeline scripts
    if any(keyword in name_lower for keyword in ['run_', 'workflow', 'pipeline']):
        return 'workflow'

    # One-time analysis
    if any(keyword in name_lower for keyword in ['ab_threshold', 'activity_constrained']):
        return 'analysis'

    return 'misc'


def determine_essential(name: str, category: str, content: str) -> bool:
    """Determine if script is essential for current system"""

    # Core essential scripts
    essential_scripts = {
        'batch_opportunity_scoring.py',
        'collect_reddit_data.py',
        'doit_runner.py',
        'dlt_trust_pipeline.py',
        'trust_layer_integration.py'
    }

    if name in essential_scripts:
        return True

    # Essential categories
    if category in ['core', 'trust', 'dlt']:
        return True

    # Scripts with current usage indicators
    if 'CURRENTLY ACTIVE' in content or 'MAIN ENTRY POINT' in content:
        return True

    # Recent modification (last 7 days) might indicate active usage
    return False


def determine_status(content: str) -> str:
    """Determine script status based on content indicators"""

    content_lower = content.lower()

    # Check for completion indicators
    if any(phrase in content_lower for phrase in ['complete', 'finished', 'done', 'completed']):
        if any(phrase in content_lower for phrase in ['test', 'demo', 'example']):
            return 'test_complete'
        else:
            return 'complete'

    # Check for TODO/FIXME indicators
    if any(indicator in content.upper() for indicator in ['TODO', 'FIXME', 'XXX', 'HACK']):
        return 'incomplete'

    # Check for error handling
    if 'error' in content_lower and 'except' in content_lower:
        return 'functional'

    # Check for main execution
    if 'if __name__ == "__main__"' in content:
        return 'functional'

    return 'unknown'


def analyze_all_scripts() -> List[Dict[str, Any]]:
    """Analyze all scripts in the scripts directory"""
    scripts_dir = Path(__file__).parent
    scripts = []

    for script_file in scripts_dir.glob("*.py"):
        if script_file.name != "script_analysis.py":  # Skip this analysis script
            analysis = analyze_script_file(script_file)
            scripts.append(analysis)

    return sorted(scripts, key=lambda x: (not x['essential'], x['category'], x['name']))


def generate_organization_report(scripts: List[Dict[str, Any]]) -> str:
    """Generate organization report with recommendations"""

    report = []
    report.append("# SCRIPT ORGANIZATION ANALYSIS REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Scripts: {len(scripts)}")
    report.append("")

    # Categorize scripts
    categories = {}
    for script in scripts:
        category = script['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(script)

    # Essential scripts
    essential_scripts = [s for s in scripts if s['essential']]
    report.append(f"## ESSENTIAL SCRIPTS ({len(essential_scripts)})")
    report.append("")
    report.append("These scripts are required for current system operation:")
    report.append("")

    for script in essential_scripts:
        report.append(f"### ✅ {script['name']}")
        report.append(f"**Category:** {script['category']} | **Status:** {script['status']}")
        report.append(f"**Purpose:** {script['purpose']}")
        report.append(f"**Size:** {script['size']} bytes | **Modified:** {script['last_modified'][:10]}")
        report.append("")

    # Non-essential scripts by category
    report.append("## NON-ESSENTIAL SCRIPTS")
    report.append("")

    for category, category_scripts in categories.items():
        if category in ['core', 'trust', 'dlt']:
            continue  # Already covered essential scripts

        non_essential = [s for s in category_scripts if not s['essential']]
        if non_essential:
            report.append(f"### {category.upper()} ({len(non_essential)})")
            report.append("")

            for script in non_essential:
                status_emoji = "✅" if script['status'] in ['complete', 'functional'] else "⚠️"
                report.append(f"#### {status_emoji} {script['name']}")
                report.append(f"**Purpose:** {script['purpose']}")
                report.append(f"**Status:** {script['status']} | **Size:** {script['size']} bytes")
                report.append("")

    # Recommendations
    report.append("## ORGANIZATION RECOMMENDATIONS")
    report.append("")

    # Scripts to archive
    archive_candidates = []
    for script in scripts:
        if not script['essential'] and script['status'] in ['complete', 'test_complete']:
            archive_candidates.append(script)

    if archive_candidates:
        report.append("### 📦 Scripts to Archive")
        report.append("These completed one-time scripts can be moved to archive:")
        report.append("")
        for script in archive_candidates:
            report.append(f"- `{script['name']}` - {script['purpose']}")
        report.append("")

    # Scripts to keep but organize
    keep_scripts = [s for s in scripts if not s['essential'] and s not in archive_candidates]
    if keep_scripts:
        report.append("### 🗂️ Scripts to Keep (Organize by Category)")
        report.append("These scripts should be organized into subdirectories:")
        report.append("")

        # Group by category
        keep_by_category = {}
        for script in keep_scripts:
            cat = script['category']
            if cat not in keep_by_category:
                keep_by_category[cat] = []
            keep_by_category[cat].append(script)

        for category, category_scripts in keep_by_category.items():
            report.append(f"**{category.title()}/**")
            for script in category_scripts:
                report.append(f"  - `{script['name']}`")
            report.append("")

    return "\n".join(report)


def main():
    """Main execution"""
    print("🔍 Analyzing RedditHarbor scripts...")

    scripts = analyze_all_scripts()

    # Generate and save report
    report = generate_organization_report(scripts)

    report_path = Path(__file__).parent / "script_organization_report.md"
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"📄 Analysis complete! Report saved to: {report_path}")
    print("\n" + report)

    # Print summary
    essential_count = len([s for s in scripts if s['essential']])
    total_count = len(scripts)
    archive_count = len([s for s in scripts if not s['essential'] and s['status'] in ['complete', 'test_complete']])

    print(f"\n📊 SUMMARY:")
    print(f"  - Total scripts: {total_count}")
    print(f"  - Essential scripts: {essential_count}")
    print(f"  - Candidates for archiving: {archive_count}")
    print(f"  - Scripts to organize: {total_count - essential_count - archive_count}")


if __name__ == "__main__":
    main()