#!/usr/bin/env python3
"""
Database Cleanup Plan Execution Script

Executes all 6 phases of the database cleanup plan:
1. Backup & Validate
2. Migration to SQLModel
3. Cleanup Duplicate Tables
4. Drop Unused Schemas
5. Code Updates
6. Verification

This script uses Docker to access the PostgreSQL database.
"""

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


# Database connection details
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "54331",
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
}

# Backup directory
BACKUP_DIR = Path("/home/carlos/projects/redditharbor-core-functions-fix/archive/database_cleanup")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Execution report
REPORT = {
    "timestamp": datetime.now().isoformat(),
    "phases": {},
    "errors": [],
}


def log_phase(phase: str, message: str) -> None:
    """Log a phase execution message."""
    print(f"\n{'=' * 80}")
    print(f"[{phase}] {message}")
    print(f"{'=' * 80}\n")
    if phase not in REPORT["phases"]:
        REPORT["phases"][phase] = []
    REPORT["phases"][phase].append(message)


def execute_sql(conn: Any, sql: str, fetch: bool = False) -> Any:
    """Execute SQL and optionally fetch results."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return None
    except Exception as e:
        conn.rollback()
        print(f"SQL Error: {e}")
        print(f"Query: {sql[:200]}...")
        REPORT["errors"].append({"sql": sql[:200], "error": str(e)})
        raise


def phase1_backup_validate(conn: Any) -> dict[str, Any]:
    """Phase 1: Backup & Validate all opportunity data."""
    log_phase("PHASE 1", "Backup & Validate")

    # Check if app_opportunities table exists
    check_sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'app_opportunities'
        AND table_name = 'app_opportunities'
    );
    """
    exists = execute_sql(conn, check_sql, fetch=True)[0]["exists"]

    if not exists:
        print("⚠️  app_opportunities.app_opportunities table does not exist")
        print("Checking for alternative locations...")

        # Find all opportunity-related tables
        find_tables_sql = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name LIKE '%opportunit%'
        ORDER BY table_schema, table_name;
        """
        tables = execute_sql(conn, find_tables_sql, fetch=True)
        print("\nFound opportunity-related tables:")
        for table in tables:
            print(f"  - {table['table_schema']}.{table['table_name']}")

        return {"backup_file": None, "row_count": 0, "real_opportunities": []}

    # Export all data from app_opportunities.app_opportunities
    export_sql = """
    SELECT * FROM app_opportunities.app_opportunities
    ORDER BY created_utc;
    """
    rows = execute_sql(conn, export_sql, fetch=True)

    print(f"Found {len(rows)} total opportunities in app_opportunities.app_opportunities")

    # Save full backup
    backup_file = BACKUP_DIR / f"app_opportunities_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if rows:
        fieldnames = list(rows[0].keys())
        with open(backup_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                # Convert JSON fields to strings
                row_data = {}
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        row_data[key] = json.dumps(value)
                    elif isinstance(value, datetime):
                        row_data[key] = value.isoformat()
                    else:
                        row_data[key] = value
                writer.writerow(row_data)

        print(f"✅ Full backup saved to: {backup_file}")

    # Identify real opportunities (exclude test data)
    real_opportunities = [
        row for row in rows
        if row.get("submission_id") and not any(
            prefix in row["submission_id"].lower()
            for prefix in ["debug_", "char_", "test_", "final_"]
        )
    ]

    print(f"\n📊 Data Analysis:")
    print(f"  - Total opportunities: {len(rows)}")
    print(f"  - Real opportunities: {len(real_opportunities)}")
    print(f"  - Test data: {len(rows) - len(real_opportunities)}")

    if real_opportunities:
        print(f"\n✅ Real Opportunities:")
        for opp in real_opportunities:
            print(f"  - {opp.get('submission_id')}: {opp.get('title', 'N/A')[:60]}")

        # Save real opportunities separately
        real_backup_file = BACKUP_DIR / f"real_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(real_backup_file, "w") as f:
            # Convert datetime objects to strings
            real_data = []
            for opp in real_opportunities:
                opp_dict = dict(opp)
                for key, value in opp_dict.items():
                    if isinstance(value, datetime):
                        opp_dict[key] = value.isoformat()
                real_data.append(opp_dict)
            json.dump(real_data, f, indent=2)
        print(f"✅ Real opportunities saved to: {real_backup_file}")

    return {
        "backup_file": str(backup_file),
        "real_backup_file": str(real_backup_file) if real_opportunities else None,
        "row_count": len(rows),
        "real_count": len(real_opportunities),
        "real_opportunities": real_opportunities,
    }


def phase2_migration(conn: Any, real_opportunities: list[dict]) -> dict[str, Any]:
    """Phase 2: Migrate real opportunities to public.opportunities."""
    log_phase("PHASE 2", "Migration to SQLModel")

    if not real_opportunities:
        print("⚠️  No real opportunities to migrate")
        return {"migrated": 0, "skipped": 0}

    migrated = 0
    skipped = 0

    for opp in real_opportunities:
        submission_id = opp.get("submission_id")

        # Check if already exists
        check_sql = """
        SELECT id FROM public.opportunities
        WHERE submission_id = %s;
        """
        with conn.cursor() as cur:
            cur.execute(check_sql, (submission_id,))
            exists = cur.fetchone()

        if exists:
            print(f"⏭️  Skipping {submission_id} (already exists)")
            skipped += 1
            continue

        # Prepare data mapping
        analysis_data = {
            "app_concept": opp.get("app_concept"),
            "problem_description": opp.get("problem_description"),
        }

        metrics_data = {
            "opportunity_score": opp.get("opportunity_score"),
            "monetization_score": opp.get("monetization_score"),
            "confidence_score": opp.get("confidence_score"),
        }

        # Insert into public.opportunities
        insert_sql = """
        INSERT INTO public.opportunities (
            submission_id, subreddit, title,
            wtp_score, final_score, confidence_score, trust_level,
            analysis, metrics,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            COALESCE(%s, NOW()), NOW()
        )
        RETURNING id;
        """

        # Get scores with proper defaults (NOT NULL constraints)
        wtp_score = opp.get("opportunity_score") or opp.get("willingness_to_pay_score") or 0.0
        final_score = opp.get("final_score") or 0.0
        confidence_score = opp.get("trust_score") or opp.get("confidence_score") or 75.0
        trust_level = opp.get("trust_level") or "MEDIUM"

        with conn.cursor() as cur:
            cur.execute(
                insert_sql,
                (
                    submission_id,
                    opp.get("subreddit") or "unknown",
                    opp.get("title") or "Untitled",
                    float(wtp_score),
                    float(final_score),
                    float(confidence_score),
                    trust_level,
                    json.dumps(analysis_data),
                    json.dumps(metrics_data),
                    opp.get("created_utc"),
                ),
            )
            new_id = cur.fetchone()[0]
            conn.commit()

        print(f"✅ Migrated {submission_id} (ID: {new_id})")
        migrated += 1

    print(f"\n📊 Migration Summary:")
    print(f"  - Migrated: {migrated}")
    print(f"  - Skipped (duplicates): {skipped}")

    return {"migrated": migrated, "skipped": skipped}


def phase3_cleanup_tables(conn: Any) -> dict[str, Any]:
    """Phase 3: Cleanup duplicate/legacy tables."""
    log_phase("PHASE 3", "Cleanup Duplicate Tables")

    tables_to_drop = [
        ("public", "app_opportunities__monetization_keywords"),
        ("public", "app_opportunities_backup_20251202"),
        ("public", "opportunities_legacy"),
        ("public", "opportunities_unified"),
        ("public", "opportunity_analysis"),
        ("public", "opportunity_scores"),
    ]

    dropped = []
    not_found = []

    for schema, table in tables_to_drop:
        # Check if table exists
        check_sql = """
        SELECT
            schemaname, tablename,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables
        WHERE schemaname = %s AND tablename = %s;
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(check_sql, (schema, table))
            table_info = cur.fetchone()

        if not table_info:
            print(f"⏭️  Table {schema}.{table} not found")
            not_found.append(f"{schema}.{table}")
            continue

        # Get row count
        count_sql = f'SELECT COUNT(*) as count FROM "{schema}"."{table}";'
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(count_sql)
            row_count = cur.fetchone()["count"]

        size_mb = table_info["size_bytes"] / (1024 * 1024)
        print(f"🗑️  Dropping {schema}.{table} ({row_count} rows, {size_mb:.2f} MB)")

        # Drop table
        drop_sql = f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE;'
        execute_sql(conn, drop_sql)

        print(f"✅ Dropped {schema}.{table}")
        dropped.append({"schema": schema, "table": table, "rows": row_count, "size_mb": size_mb})

    print(f"\n📊 Cleanup Summary:")
    print(f"  - Dropped: {len(dropped)} tables")
    print(f"  - Not found: {len(not_found)} tables")

    return {"dropped": dropped, "not_found": not_found}


def phase4_drop_schemas(conn: Any) -> dict[str, Any]:
    """Phase 4: Drop unused schemas."""
    log_phase("PHASE 4", "Drop Unused Schemas")

    schemas_to_check = [
        "app_opportunities",
        "app_opportunities_staging",
    ]

    dropped_schemas = []
    not_found = []

    for schema in schemas_to_check:
        # Check if schema exists
        check_sql = """
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = %s;
        """
        with conn.cursor() as cur:
            cur.execute(check_sql, (schema,))
            exists = cur.fetchone()

        if not exists:
            print(f"⏭️  Schema {schema} not found")
            not_found.append(schema)
            continue

        # List tables in schema
        list_tables_sql = """
        SELECT tablename FROM pg_tables
        WHERE schemaname = %s;
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(list_tables_sql, (schema,))
            tables = cur.fetchall()

        table_count = len(tables)
        print(f"🗑️  Dropping schema {schema} ({table_count} tables)")
        for table in tables:
            print(f"    - {table['tablename']}")

        # Drop schema
        drop_sql = f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;'
        execute_sql(conn, drop_sql)

        print(f"✅ Dropped schema {schema}")
        dropped_schemas.append({"schema": schema, "table_count": table_count})

    # Handle public_staging - just drop app_opportunities table if it exists
    print("\n🔍 Checking public_staging.app_opportunities...")
    check_staging_sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public_staging'
        AND table_name = 'app_opportunities'
    );
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(check_staging_sql)
        staging_exists = cur.fetchone()["exists"]

    if staging_exists:
        print("🗑️  Dropping public_staging.app_opportunities")
        execute_sql(conn, 'DROP TABLE IF EXISTS "public_staging"."app_opportunities" CASCADE;')
        print("✅ Dropped public_staging.app_opportunities")
    else:
        print("⏭️  public_staging.app_opportunities not found")

    print(f"\n📊 Schema Cleanup Summary:")
    print(f"  - Dropped schemas: {len(dropped_schemas)}")
    print(f"  - Not found: {len(not_found)}")

    return {"dropped_schemas": dropped_schemas, "not_found": not_found}


def phase5_code_updates() -> dict[str, Any]:
    """Phase 5: Search for and document code references."""
    log_phase("PHASE 5", "Code Updates")

    project_root = Path("/home/carlos/projects/redditharbor-core-functions-fix")

    # Search for app_opportunities references
    print("🔍 Searching for 'app_opportunities' references in code...")

    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", "app_opportunities", str(project_root)],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout:
            references = result.stdout.strip().split("\n")
            print(f"Found {len(references)} references:")
            for ref in references[:20]:  # Show first 20
                print(f"  {ref}")
            if len(references) > 20:
                print(f"  ... and {len(references) - 20} more")
        else:
            references = []
            print("✅ No 'app_opportunities' references found in Python files")
    except Exception as e:
        print(f"⚠️  Error searching for references: {e}")
        references = []

    # Search for DLT pipeline references
    print("\n🔍 Searching for DLT opportunity pipeline references...")

    try:
        dlt_result = subprocess.run(
            ["grep", "-r", "--include=*.py", "-E", "dlt.*opportunit|@dlt.resource.*opportunit", str(project_root)],
            capture_output=True,
            text=True,
        )

        if dlt_result.returncode == 0 and dlt_result.stdout:
            dlt_references = dlt_result.stdout.strip().split("\n")
            print(f"Found {len(dlt_references)} DLT references:")
            for ref in dlt_references[:10]:
                print(f"  {ref}")
        else:
            dlt_references = []
            print("✅ No DLT opportunity pipeline references found")
    except Exception as e:
        print(f"⚠️  Error searching for DLT references: {e}")
        dlt_references = []

    return {
        "app_opportunities_references": len(references) if references else 0,
        "dlt_references": len(dlt_references) if dlt_references else 0,
    }


def phase6_verification(conn: Any) -> dict[str, Any]:
    """Phase 6: Verify cleanup and data integrity."""
    log_phase("PHASE 6", "Verification")

    # Check public.opportunities
    print("🔍 Verifying public.opportunities...")
    check_sql = """
    SELECT COUNT(*) as count FROM public.opportunities;
    """
    count = execute_sql(conn, check_sql, fetch=True)[0]["count"]
    print(f"✅ public.opportunities has {count} rows")

    # List all schemas
    print("\n🔍 Current database schemas:")
    schemas_sql = """
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
    ORDER BY schema_name;
    """
    schemas = execute_sql(conn, schemas_sql, fetch=True)
    for schema in schemas:
        print(f"  - {schema['schema_name']}")

    # List opportunity-related tables
    print("\n🔍 Remaining opportunity-related tables:")
    tables_sql = """
    SELECT table_schema, table_name,
           pg_total_relation_size(table_schema||'.'||table_name) as size_bytes
    FROM information_schema.tables
    WHERE table_name LIKE '%opportunit%'
    AND table_schema NOT IN ('information_schema', 'pg_catalog')
    ORDER BY table_schema, table_name;
    """
    tables = execute_sql(conn, tables_sql, fetch=True)

    if tables:
        print(f"Found {len(tables)} opportunity-related tables:")
        for table in tables:
            size_mb = table["size_bytes"] / (1024 * 1024)
            print(f"  - {table['table_schema']}.{table['table_name']} ({size_mb:.2f} MB)")
    else:
        print("  None (✅ All cleaned up)")

    return {
        "opportunities_count": count,
        "schemas": [s["schema_name"] for s in schemas],
        "remaining_tables": len(tables),
    }


def save_report() -> None:
    """Save execution report to file."""
    report_file = BACKUP_DIR / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Convert datetime objects to strings for JSON serialization
    def convert_datetime(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        return obj

    serializable_report = convert_datetime(REPORT)

    with open(report_file, "w") as f:
        json.dump(serializable_report, f, indent=2)
    print(f"\n📋 Execution report saved to: {report_file}")


def main() -> None:
    """Execute all phases of the database cleanup plan."""
    print("=" * 80)
    print("DATABASE CLEANUP PLAN EXECUTION")
    print("=" * 80)
    print(f"Started at: {REPORT['timestamp']}")
    print(f"Backup directory: {BACKUP_DIR}")
    print("=" * 80)

    try:
        # Connect to database
        print("\n🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected successfully")

        # Execute phases
        backup_result = phase1_backup_validate(conn)
        REPORT["backup"] = backup_result

        migration_result = phase2_migration(conn, backup_result.get("real_opportunities", []))
        REPORT["migration"] = migration_result

        cleanup_result = phase3_cleanup_tables(conn)
        REPORT["cleanup"] = cleanup_result

        schema_result = phase4_drop_schemas(conn)
        REPORT["schema_cleanup"] = schema_result

        code_result = phase5_code_updates()
        REPORT["code_updates"] = code_result

        verification_result = phase6_verification(conn)
        REPORT["verification"] = verification_result

        # Close connection
        conn.close()
        print("\n✅ Database connection closed")

        # Save report
        save_report()

        # Print summary
        print("\n" + "=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        print(f"✅ Backup: {backup_result.get('row_count', 0)} total, {backup_result.get('real_count', 0)} real opportunities")
        print(f"✅ Migration: {migration_result.get('migrated', 0)} migrated, {migration_result.get('skipped', 0)} skipped")
        print(f"✅ Tables dropped: {len(cleanup_result.get('dropped', []))}")
        print(f"✅ Schemas dropped: {len(schema_result.get('dropped_schemas', []))}")
        print(f"✅ Final opportunities count: {verification_result.get('opportunities_count', 0)}")
        print(f"✅ Remaining opportunity tables: {verification_result.get('remaining_tables', 0)}")

        if REPORT["errors"]:
            print(f"\n⚠️  Errors encountered: {len(REPORT['errors'])}")
            for error in REPORT["errors"][:5]:
                print(f"  - {error}")

        print("\n✅ Cleanup plan execution completed successfully!")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        REPORT["fatal_error"] = str(e)
        save_report()
        sys.exit(1)


if __name__ == "__main__":
    main()
