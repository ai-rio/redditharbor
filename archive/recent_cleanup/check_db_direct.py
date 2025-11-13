#!/usr/bin/env python3
"""
Direct database check using HTTP API (no dependencies).
"""
import json
import os
import sys
from pathlib import Path
from urllib import request, error

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env.local manually
env_file = project_root / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key] = val

SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

def query_table(table_name, select_clause='*', limit=5):
    """Query a table using Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?select={select_clause}&limit={limit}"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Prefer': 'count=exact'
    }

    try:
        req = request.Request(url, headers=headers)
        with request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Get count from Content-Range header
            content_range = response.headers.get('Content-Range')
            count = None
            if content_range:
                # Format: 0-4/100 or */100
                parts = content_range.split('/')
                if len(parts) == 2:
                    count = int(parts[1]) if parts[1] != '*' else None
            return {'data': data, 'count': count, 'status': response.status}
    except error.HTTPError as e:
        return {'error': str(e), 'status': e.code}
    except Exception as e:
        return {'error': str(e), 'status': 0}

def main():
    """Check database tables and trust indicators."""
    print("=" * 80)
    print("DATABASE DIRECT CHECK (HTTP API)")
    print("=" * 80)
    print(f"Supabase URL: {SUPABASE_URL}")

    # 1. Check app_opportunities_trust table
    print("\n1. app_opportunities_trust TABLE")
    print("-" * 80)

    result = query_table('app_opportunities_trust', select_clause='*', limit=0)
    if 'error' in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Table exists")
        print(f"  Row count: {result.get('count', 'unknown')}")

    # 2. Get sample data with trust indicators
    if 'error' not in result and result.get('count', 0) > 0:
        print("\n2. SAMPLE DATA WITH TRUST INDICATORS")
        print("-" * 80)

        result = query_table(
            'app_opportunities_trust',
            select_clause='submission_id,title,trust_score,trust_badge,activity_score,trust_level',
            limit=10
        )

        if 'error' not in result:
            data = result['data']
            print(f"  Retrieved {len(data)} rows")

            if data:
                # Check for NULL values
                null_counts = {
                    'trust_score': sum(1 for r in data if r.get('trust_score') is None),
                    'trust_badge': sum(1 for r in data if r.get('trust_badge') is None),
                    'activity_score': sum(1 for r in data if r.get('activity_score') is None),
                    'trust_level': sum(1 for r in data if r.get('trust_level') is None),
                }

                print("\n  NULL value analysis:")
                for field, count in null_counts.items():
                    pct = (count / len(data)) * 100
                    print(f"    {field}: {count}/{len(data)} ({pct:.1f}% NULL)")

                # Show sample values
                print("\n  Sample records:")
                for i, row in enumerate(data[:3], 1):
                    print(f"\n  Record {i}:")
                    print(f"    submission_id: {row.get('submission_id', 'N/A')[:50]}")
                    print(f"    title: {row.get('title', 'N/A')[:60]}...")
                    print(f"    trust_score: {row.get('trust_score')}")
                    print(f"    trust_badge: {row.get('trust_badge')}")
                    print(f"    activity_score: {row.get('activity_score')}")
                    print(f"    trust_level: {row.get('trust_level')}")

    # 3. Check DLT state tables
    print("\n3. DLT STATE TABLES")
    print("-" * 80)

    for table_name in ['_dlt_loads', '_dlt_version', '_dlt_pipeline_state']:
        result = query_table(table_name, select_clause='*', limit=0)
        if 'error' in result:
            print(f"  {table_name}: Not found or inaccessible")
        else:
            print(f"  {table_name}: {result.get('count', '?')} rows")

    # 4. Check workflow_results table (where batch scoring writes)
    print("\n4. WORKFLOW_RESULTS TABLE (Batch Scoring Target)")
    print("-" * 80)

    result = query_table('workflow_results', select_clause='*', limit=0)
    if 'error' in result:
        print(f"  ✗ Error: {result['error']}")
    else:
        print(f"  ✓ Table exists")
        print(f"  Row count: {result.get('count', 'unknown')}")

    # 5. Summary and recommendation
    print("\n" + "=" * 80)
    print("SUMMARY AND RECOMMENDATION")
    print("=" * 80)

    # Check app_opportunities_trust status
    app_opp_result = query_table('app_opportunities_trust',
                                  select_clause='trust_score,trust_badge',
                                  limit=10)

    if 'error' in app_opp_result:
        print("\n✗ app_opportunities_trust table NOT ACCESSIBLE")
        print("  Recommendation: Check DLT pipeline configuration")
        print("  Check if table was created in a different schema")
    elif not app_opp_result.get('data'):
        print("\n⚠️  app_opportunities_trust table is EMPTY")
        print("  Recommendation: Run dlt_trust_pipeline.py to populate")
    else:
        # Check if trust indicators are populated
        data = app_opp_result['data']
        null_trust = sum(1 for r in data if r.get('trust_score') is None)

        if null_trust == len(data):
            print("\n✗ Trust indicators are ALL NULL")
            print("  Issue: DLT pipeline wrote data but trust indicators missing")
            print("  Possible causes:")
            print("    1. Trust validation step failed/skipped")
            print("    2. Trust fields not mapped correctly")
            print("    3. Schema mismatch between pipeline and table")
        elif null_trust > len(data) * 0.5:
            print(f"\n⚠️  Trust indicators MOSTLY NULL ({null_trust}/{len(data)})")
            print("  Issue: Partial trust validation")
            print("  Recommendation: Check trust layer integration")
        else:
            print(f"\n✓ Trust indicators are populated ({len(data)-null_trust}/{len(data)} have values)")
            print("  Status: DLT pipeline is working correctly")
            print("  Recommendation: batch_opportunity_scoring.py should read from")
            print("                  app_opportunities_trust table")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
