"""Validate database schema for deduplication integration.

This script validates that all required tables and columns exist in the database
before integrating deduplication logic into the unified pipeline.

Usage:
    python scripts/testing/validate_deduplication_schema.py
"""

from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client


# Required schema for deduplication
REQUIRED_SCHEMA = {
    "opportunities_unified": ["submission_id", "business_concept_id"],
    "business_concepts": ["id", "has_agno_analysis", "has_profiler_analysis"],
    "llm_monetization_analysis": [
        "business_concept_id",
        "copied_from_primary",
        "willingness_to_pay_score",
        "customer_segment",
        "payment_sentiment",
        "urgency_level",
    ],
    "workflow_results": [
        "opportunity_id",
        "copied_from_primary",
        "app_name",
        "core_functions",
    ],
}


def validate_deduplication_schema() -> bool:
    """
    Validate required tables and columns exist.

    Returns:
        bool: True if schema is valid, raises ValueError otherwise

    Raises:
        ValueError: If schema validation fails
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("🔍 Validating deduplication schema...")
    print(f"   Database: {SUPABASE_URL}")
    print()

    validation_results = []
    failed_validations = []

    for table, columns in REQUIRED_SCHEMA.items():
        try:
            # Test query to validate table and columns exist
            response = supabase.table(table).select(",".join(columns)).limit(1).execute()
            validation_results.append((table, len(columns), True, None))
            print(f"  ✅ {table}: {len(columns)} columns validated")
        except Exception as e:
            validation_results.append((table, len(columns), False, str(e)))
            failed_validations.append((table, columns, e))
            print(f"  ❌ {table}: FAILED - {e}")

    print()
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    if not failed_validations:
        print("✅ Schema validation passed - deduplication can proceed")
        print()
        print("Tables validated:")
        for table, col_count, _, _ in validation_results:
            print(f"  • {table}: {col_count} columns")
        print()
        print("Next steps:")
        print("  1. Proceed with Phase 1: Integrate Deduplication Classes")
        print("  2. Run Phase 0 local AI test")
        return True
    else:
        print("❌ Schema validation FAILED")
        print()
        print("Missing/invalid tables:")
        for table, columns, error in failed_validations:
            print(f"  • {table}")
            print(f"    Required columns: {', '.join(columns)}")
            print(f"    Error: {error}")
        print()
        print("Action required:")
        print("  1. Run database migrations: supabase db push")
        print("  2. Check migrations/002_add_comprehensive_enrichment_fields.sql")
        print("  3. Re-run this validation script")

        raise ValueError(
            f"Schema validation failed for {len(failed_validations)} table(s). "
            f"See details above."
        )


if __name__ == "__main__":
    try:
        validate_deduplication_schema()
    except ValueError as e:
        print()
        print("=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        exit(1)
