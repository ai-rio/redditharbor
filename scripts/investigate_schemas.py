#!/usr/bin/env python3
"""
Investigate database schemas and trust indicator tables.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json

def main():
    """Investigate schemas and tables."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("=" * 80)
    print("SCHEMA INVESTIGATION REPORT")
    print("=" * 80)

    # 1. Query all schemas
    print("\n1. ALL SCHEMAS IN DATABASE")
    print("-" * 80)
    schemas_query = """
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
    ORDER BY schema_name;
    """
    try:
        result = supabase.rpc('exec_sql', {'query': schemas_query}).execute()
        print(f"Schemas found: {result.data}")
    except Exception as e:
        # Try direct query approach
        print(f"RPC approach failed, trying direct query: {e}")
        # Use raw SQL query via PostgREST
        from supabase.lib.client_options import ClientOptions
        import requests

        # Query using raw SQL
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'params=single-object'
        }

        # Let's try a different approach - query pg_namespace
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={'query': schemas_query}
        )

        if response.status_code == 200:
            print(f"Schemas: {response.json()}")
        else:
            print(f"Failed to query schemas: {response.status_code} - {response.text}")

    # 2. Check for app_opportunities_trust in different schemas
    print("\n2. SEARCHING FOR app_opportunities_trust TABLE")
    print("-" * 80)

    tables_query = """
    SELECT
        table_schema,
        table_name,
        table_type
    FROM information_schema.tables
    WHERE table_name LIKE '%opportunities%'
       OR table_name LIKE '%trust%'
    ORDER BY table_schema, table_name;
    """

    print("Tables with 'opportunities' or 'trust' in name:")

    # Try direct table access for known schemas
    for schema in ['public', 'public_staging', '_public_staging', 'staging']:
        print(f"\n  Checking schema: {schema}")
        table_check = f"""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = '{schema}'
          AND (table_name LIKE '%opportunities%' OR table_name LIKE '%trust%')
        ORDER BY table_name;
        """
        print(f"    Query: {table_check}")

    # 3. Try to count rows in known table locations
    print("\n3. ROW COUNTS IN KNOWN TABLE LOCATIONS")
    print("-" * 80)

    # Try public_staging schema first
    try:
        print("\n  Attempting: public_staging.app_opportunities_trust")
        result = supabase.table('app_opportunities_trust').select('*', count='exact').limit(0).execute()
        print(f"    Success! Row count: {result.count}")
    except Exception as e:
        print(f"    Error: {e}")

    # Try public schema
    try:
        print("\n  Attempting: public.app_opportunities_trust")
        result = supabase.table('app_opportunities_trust').select('*', count='exact').limit(0).execute()
        print(f"    Success! Row count: {result.count}")
    except Exception as e:
        print(f"    Error: {e}")

    # 4. Sample data from staging if it exists
    print("\n4. SAMPLE DATA WITH TRUST INDICATORS")
    print("-" * 80)

    try:
        print("\n  Querying app_opportunities_trust (default schema):")
        result = supabase.table('app_opportunities_trust').select('*').limit(5).execute()
        print(f"    Rows returned: {len(result.data)}")
        if result.data:
            print("\n    Sample record:")
            print(json.dumps(result.data[0], indent=2, default=str))

            # Check for trust columns
            trust_columns = [col for col in result.data[0].keys() if 'trust' in col.lower()]
            print(f"\n    Trust-related columns found: {trust_columns}")

            # Show trust values
            print("\n    Trust indicator values in first 5 rows:")
            for i, row in enumerate(result.data, 1):
                trust_vals = {col: row.get(col) for col in trust_columns}
                print(f"      Row {i}: {trust_vals}")
    except Exception as e:
        print(f"    Error: {e}")

    # 5. Check DLT state tables to understand schema routing
    print("\n5. DLT STATE TABLES (Schema Configuration)")
    print("-" * 80)

    for table_name in ['_dlt_loads', '_dlt_version', '_dlt_pipeline_state']:
        try:
            print(f"\n  Checking: {table_name}")
            result = supabase.table(table_name).select('*').limit(3).execute()
            print(f"    Rows: {len(result.data)}")
            if result.data:
                print(f"    Sample: {json.dumps(result.data[0], indent=2, default=str)[:500]}...")
        except Exception as e:
            print(f"    Not found or error: {e}")

    print("\n" + "=" * 80)
    print("END OF INVESTIGATION")
    print("=" * 80)

if __name__ == "__main__":
    main()
