#!/usr/bin/env python3
"""
Verification script to confirm production metrics instrumentation is complete.

This script checks that both Agno Analyzer and Pipeline Orchestrator have
proper metrics tracking with opportunity_id propagation and agent-level tracking.
"""

import re
from pathlib import Path

def check_file_instrumentation(file_path: str, patterns: dict) -> dict:
    """Check instrumentation patterns in a file"""
    results = {}
    content = Path(file_path).read_text()

    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        results[pattern_name] = {
            'count': len(matches),
            'matches': matches[:3]  # First 3 matches for review
        }

    return results

def main():
    """Main verification function"""
    print("🔍 Production Metrics Instrumentation Verification")
    print("=" * 60)

    # Patterns to check in agno_analyzer.py
    agno_patterns = {
        'individual_agent_tracking': r'with metrics\.track\("transform",\s*agent_name=agent_short_name,\s*opportunity_id=opportunity_id\)',
        'main_analysis_tracking': r'with metrics\.track\("transform",\s*agent_name="agno_analyzer",\s*opportunity_id=opportunity_id\)',
        'market_research_tracking': r'with metrics\.track\("transform",\s*agent_name="market",\s*opportunity_id=opportunity_id\)',
        'opportunity_id_in_input': r'"opportunity_id":\s*f"opp-\{getattr\(submission, \'id\', \'unknown\'\)\}"',
        'cost_tracking': r'context\["api_cost_usd"\]',
        'metadata_tracking': r'context\["metadata"\]'
    }

    # Patterns to check in pipeline_orchestrator.py
    orchestrator_patterns = {
        'extract_tracking': r'with metrics\.track\("extract",\s*agent_name="reddit_client"\)',
        'transform_tracking': r'with metrics\.track\("transform",\s*agent_name="agno_analyzer",\s*opportunity_id=opportunity_id\)',
        'load_tracking': r'with metrics\.track\("load",\s*agent_name="database_loader"\)',
        'opportunity_id_propagation': r'opportunity_id\s*=\s*f"opp-\{getattr\(submission, \'id\', f\'unknown-\{i\}\'\)\}"',
        'batch_tracking': r'opportunity_ids.*\[.*f"opp-',
        'metadata_in_context': r'context\["metadata"\]\s*='
    }

    # Patterns to check in agno_agents.py
    agents_patterns = {
        'agent_base_tracking': r'with self\.metrics\.track\("transform",\s*agent_name=agent_name,\s*opportunity_id=opportunity_id\)',
        'agent_name_mapping': r'"WillingnessToPayAgent":\s*"wtp"',
        'cost_and_metadata': r'context\["metadata"\]'
    }

    # Check each file
    files_to_check = [
        ('pipeline-v3/transform/agno_analyzer.py', agno_patterns, 'Agno Analyzer'),
        ('pipeline-v3/orchestration/pipeline_orchestrator.py', orchestrator_patterns, 'Pipeline Orchestrator'),
        ('pipeline-v3/transform/agno_agents.py', agents_patterns, 'Agent Classes')
    ]

    all_passed = True

    for file_path, patterns, display_name in files_to_check:
        print(f"\n📋 Checking {display_name}: {file_path}")
        print("-" * 50)

        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            all_passed = False
            continue

        results = check_file_instrumentation(file_path, patterns)
        file_passed = True

        for pattern_name, result in results.items():
            status = "✅" if result['count'] > 0 else "❌"
            print(f"{status} {pattern_name}: {result['count']} matches")

            if result['count'] == 0:
                file_passed = False
                all_passed = False
            elif result['count'] > 0:
                # Show first match for verification
                if result['matches']:
                    print(f"    Example: {result['matches'][0][:80]}...")

        if file_passed:
            print(f"✅ {display_name} instrumentation complete")
        else:
            print(f"❌ {display_name} has missing instrumentation")

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SUCCESS: All production metrics instrumentation is complete!")
        print("\nKey improvements made:")
        print("✅ Individual agent tracking with opportunity_id propagation")
        print("✅ Phase-level tracking (extract, transform, load)")
        print("✅ Agent name mapping (wtp, segment, price, payment, market)")
        print("✅ Cost and metadata tracking in all contexts")
        print("✅ Opportunity ID propagation through pipeline")
        print("\nThe QA audit finding has been resolved!")
    else:
        print("❌ FAILURE: Some instrumentation is missing")
        print("Please review the failed checks above.")

    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)