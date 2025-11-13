#!/usr/bin/env python3
"""
Investigate trust indicator schema and data distribution.
Checks where DLT is writing trust data and compares schemas.
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json

def main():
    """Investigate trust indicator tables and schemas."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("=" * 80)
    print("TRUST INDICATOR SCHEMA INVESTIGATION")
    print("=" * 80)

    # 1. Check if app_opportunities_trust table exists and has data
    print("\n1. CHECKING app_opportunities_trust TABLE")
    print("-" * 80)

    try:
        result = supabase.table('app_opportunities_trust').select('*', count='exact').limit(0).execute()
        print(f"✓ Table 'app_opportunities_trust' exists")
        print(f"  Row count: {result.count}")
    except Exception as e:
        print(f"✗ Error accessing app_opportunities_trust: {e}")
        print("  This table may not exist or may be in a different schema")

    # 2. Sample data with trust indicators
    print("\n2. SAMPLE DATA FROM app_opportunities_trust")
    print("-" * 80)

    try:
        result = supabase.table('app_opportunities_trust').select('*').limit(5).execute()
        print(f"  Rows retrieved: {len(result.data)}")

        if result.data:
            # Show column names
            columns = result.data[0].keys()
            print(f"\n  Columns ({len(columns)}):")
            for col in sorted(columns):
                print(f"    - {col}")

            # Identify trust-related columns
            trust_columns = [col for col in columns if 'trust' in col.lower() or 'activity' in col.lower() or 'confidence' in col.lower()]
            print(f"\n  Trust-related columns ({len(trust_columns)}):")
            for col in trust_columns:
                print(f"    - {col}")

            # Sample trust values
            print(f"\n  Sample trust indicator values (first 3 rows):")
            for i, row in enumerate(result.data[:3], 1):
                print(f"\n  Row {i} - submission_id: {row.get('submission_id', 'N/A')[:50]}")
                print(f"    title: {row.get('title', 'N/A')[:60]}...")
                for col in trust_columns:
                    value = row.get(col)
                    print(f"    {col}: {value}")
        else:
            print("  ✗ No data found in app_opportunities_trust")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    # 3. Check trust indicator NULL values
    print("\n3. TRUST INDICATOR DATA QUALITY CHECK")
    print("-" * 80)

    try:
        result = supabase.table('app_opportunities_trust').select(
            'submission_id, trust_score, trust_badge, activity_score, trust_level'
        ).limit(100).execute()

        if result.data:
            total = len(result.data)
            null_trust_score = sum(1 for r in result.data if r.get('trust_score') is None)
            null_trust_badge = sum(1 for r in result.data if r.get('trust_badge') is None)
            null_activity_score = sum(1 for r in result.data if r.get('activity_score') is None)
            null_trust_level = sum(1 for r in result.data if r.get('trust_level') is None)

            print(f"  Sample size: {total} rows")
            print(f"\n  NULL value analysis:")
            print(f"    trust_score:    {null_trust_score}/{total} ({null_trust_score/total*100:.1f}% NULL)")
            print(f"    trust_badge:    {null_trust_badge}/{total} ({null_trust_badge/total*100:.1f}% NULL)")
            print(f"    activity_score: {null_activity_score}/{total} ({null_activity_score/total*100:.1f}% NULL)")
            print(f"    trust_level:    {null_trust_level}/{total} ({null_trust_level/total*100:.1f}% NULL)")

            # Show distribution of non-NULL values
            if null_trust_score < total:
                print(f"\n  Trust score distribution (non-NULL):")
                trust_scores = [r['trust_score'] for r in result.data if r.get('trust_score') is not None]
                if trust_scores:
                    print(f"    Min: {min(trust_scores):.1f}")
                    print(f"    Max: {max(trust_scores):.1f}")
                    print(f"    Avg: {sum(trust_scores)/len(trust_scores):.1f}")

            if null_trust_badge < total:
                print(f"\n  Trust badge distribution (non-NULL):")
                badges = {}
                for r in result.data:
                    badge = r.get('trust_badge')
                    if badge:
                        badges[badge] = badges.get(badge, 0) + 1
                for badge, count in sorted(badges.items(), key=lambda x: x[1], reverse=True):
                    print(f"    {badge}: {count} ({count/total*100:.1f}%)")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    # 4. Check DLT state tables to understand schema
    print("\n4. DLT PIPELINE STATE")
    print("-" * 80)

    for table_name in ['_dlt_loads', '_dlt_version']:
        try:
            result = supabase.table(table_name).select('*').limit(5).execute()
            print(f"\n  Table: {table_name}")
            print(f"    Rows: {len(result.data)}")
            if result.data:
                print(f"    Sample record:")
                # Show first record, truncated
                sample = result.data[0]
                for key, value in sample.items():
                    value_str = str(value)[:100]
                    print(f"      {key}: {value_str}")
        except Exception as e:
            print(f"\n  Table: {table_name}")
            print(f"    ✗ Not accessible: {e}")

    # 5. Check if there are multiple tables with similar names
    print("\n5. SEARCHING FOR SIMILAR TABLE NAMES")
    print("-" * 80)
    print("  (Checking variations of app_opportunities)")

    # Try different table name variations
    table_variations = [
        'app_opportunities',
        'app_opportunities_trust',
        'public.app_opportunities_trust',
        'public_staging.app_opportunities_trust',
        '_public_staging.app_opportunities_trust',
        'staging.app_opportunities_trust'
    ]

    for table_name in table_variations:
        try:
            result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
            print(f"  ✓ {table_name}: EXISTS (count={result.count})")
        except Exception as e:
            error_str = str(e)[:100]
            print(f"  ✗ {table_name}: {error_str}")

    # 6. Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    try:
        result = supabase.table('app_opportunities_trust').select('*', count='exact').limit(1).execute()

        if result.count and result.count > 0:
            # Check if trust indicators are populated
            sample = result.data[0] if result.data else {}
            has_trust_data = (
                sample.get('trust_score') is not None or
                sample.get('trust_badge') is not None or
                sample.get('activity_score') is not None
            )

            if has_trust_data:
                print("\n✓ Trust indicators ARE being written to app_opportunities_trust")
                print("  Action: batch_opportunity_scoring.py should read from this table")
                print("  Check: Line 172-256 in batch_opportunity_scoring.py")
                print("  Verify: fetch_submissions() is querying app_opportunities_trust")
            else:
                print("\n✗ Trust indicators are NULL in app_opportunities_trust")
                print("  Possible issues:")
                print("    1. DLT pipeline writing to different schema")
                print("    2. Trust validation not running")
                print("    3. Trust fields not being populated")
                print("  Action: Check dlt_trust_pipeline.py execution logs")
        else:
            print("\n✗ app_opportunities_trust table is EMPTY")
            print("  Action: Run dlt_trust_pipeline.py to populate data")

    except Exception as e:
        print(f"\n✗ Could not determine status: {e}")

    print("\n" + "=" * 80)
    print("END OF INVESTIGATION")
    print("=" * 80)


if __name__ == "__main__":
    main()
