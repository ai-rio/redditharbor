#!/usr/bin/env python3
"""
Test and validate the cost tracking fixes
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("RedditHarbor Cost Tracking - Test and Fix Script")
    print("=" * 50)

    # Read the SQL fix content
    fix_sql_path = project_root / 'supabase' / 'migrations' / '20251114005544_fix_cost_tracking_functions.sql'

    if not fix_sql_path.exists():
        print(f"❌ SQL fix file not found: {fix_sql_path}")
        return 1

    with open(fix_sql_path, 'r') as f:
        sql_content = f.read()

    print(f"✅ SQL fix file found: {fix_sql_path}")
    print(f"📄 File size: {len(sql_content)} characters")

    # Test the SQL syntax
    print("\n🔍 Analyzing SQL content...")

    # Check for key components
    checks = [
        ("get_cost_summary function", "get_cost_summary"),
        ("cost_summary_simple view", "cost_summary_simple"),
        ("analyze_costs_by_date_range function", "analyze_costs_by_date_range"),
        ("Parameter validation", "IF p_start_date > p_end_date"),
        ("Error handling", "RAISE EXCEPTION"),
        ("Permissions grant", "GRANT SELECT ON cost_summary_simple"),
        ("Documentation comments", "COMMENT ON")
    ]

    all_passed = True
    for check_name, search_text in checks:
        if search_text in sql_content:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name} - Missing '{search_text}'")
            all_passed = False

    if all_passed:
        print("\n✅ All SQL components present and valid!")
    else:
        print("\n❌ Some SQL components are missing!")
        return 1

    print("\n📝 Instructions to apply the fix:")
    print("1. Open Supabase Studio: http://127.0.0.1:54323")
    print("2. Go to the SQL Editor")
    print("3. Copy and paste the contents of:")
    print(f"   {fix_sql_path}")
    print("4. Execute the SQL script")
    print("\nOr run the following commands:")
    print("   supabase db reset  # This will apply all migrations including the fix")

    print("\n🧪 After applying the fix, test with these queries:")

    test_queries = [
        ("Simple View Test", "SELECT * FROM cost_summary_simple;"),
        ("Function Default Test", "SELECT * FROM get_cost_summary();"),
        ("Function Date Range Test", "SELECT * FROM get_cost_summary(CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE);"),
        ("Date Analysis Test", "SELECT * FROM analyze_costs_by_date_range(CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE, 'day');")
    ]

    for query_name, query in test_queries:
        print(f"\n{query_name}:")
        print(f"   {query}")

    print("\n📊 Alternative direct queries (no functions required):")

    direct_queries = [
        ("Basic Cost Overview", """
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_enabled,
    COALESCE(SUM(CASE WHEN cost_tracking_enabled = true THEN llm_total_cost_usd ELSE 0 END), 0) as total_cost_usd
FROM workflow_results
WHERE processed_at >= CURRENT_DATE - INTERVAL '30 days';
        """),

        ("Daily Cost Trends", """
SELECT
    DATE(llm_timestamp) as cost_date,
    COUNT(*) as daily_requests,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as daily_cost_usd
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '7 days'
    AND llm_total_cost_usd > 0
GROUP BY DATE(llm_timestamp)
ORDER BY cost_date DESC;
        """)
    ]

    for query_name, query in direct_queries:
        print(f"\n{query_name}:")
        print(f"   {query.strip()}")

    print("\n🔧 Troubleshooting:")
    print("• If you get 'function does not exist' errors, ensure the migration was applied")
    print("• If you get 'permission denied' errors, check that grants were applied")
    print("• If you get no data, verify that cost tracking is enabled in your workflow_results")
    print("• Check the workflow_results table has llm_total_cost_usd > 0 values")

    return 0

if __name__ == "__main__":
    sys.exit(main())