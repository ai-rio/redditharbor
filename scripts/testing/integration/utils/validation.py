"""
Pre-test validation utilities for Phase 8 integration testing.

Validates database state before running tests to ensure clean data foundation.
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


class ValidationError(Exception):
    """Raised when pre-test validation fails."""
    pass


def validate_uuid_format(value: str) -> bool:
    """
    Check if a string is a valid UUID format.

    Args:
        value: String to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    if not value:
        return False
    return bool(UUID_PATTERN.match(value.lower()))


def validate_submission_id_formats(supabase_client) -> Dict[str, any]:
    """
    Validate that all submission_ids in the database are clean UUIDs.

    This is a critical pre-test validation that ensures the clean-break
    implementation is working correctly and all IDs are normalized.

    Args:
        supabase_client: Supabase client instance

    Returns:
        Dict with validation results:
        {
            "passed": bool,
            "total_submissions": int,
            "non_uuid_count": int,
            "sample_invalid_ids": List[Dict],
            "validation_time": str
        }

    Raises:
        ValidationError: If validation fails with details
    """
    print("🔍 Validating submission_id formats in database...")

    validation_start = datetime.now()

    # Query for total submission count
    total_result = supabase_client.table('submissions').select('id', count='exact').execute()
    total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data)

    # Get all submission IDs
    all_submissions = supabase_client.table('submissions').select('id, title').execute()

    # Check each ID
    invalid_ids = []
    for submission in all_submissions.data:
        submission_id = submission.get('id')
        if not validate_uuid_format(submission_id):
            invalid_ids.append({
                'id': submission_id,
                'title': submission.get('title', 'N/A')
            })

    validation_end = datetime.now()
    duration = (validation_end - validation_start).total_seconds()

    result = {
        'passed': len(invalid_ids) == 0,
        'total_submissions': total_count,
        'non_uuid_count': len(invalid_ids),
        'sample_invalid_ids': invalid_ids[:5],  # First 5 problematic IDs
        'validation_time': f"{duration:.2f}s"
    }

    # Print results
    if result['passed']:
        print(f"✅ ID format validation PASSED")
        print(f"   - Total submissions checked: {result['total_submissions']}")
        print(f"   - All submission_ids are clean UUIDs")
        print(f"   - Validation time: {result['validation_time']}")
        print()
    else:
        print(f"❌ ID format validation FAILED")
        print(f"   - Total submissions: {result['total_submissions']}")
        print(f"   - Non-UUID formats found: {result['non_uuid_count']}")
        print()
        print("Sample problematic IDs:")
        for idx, invalid in enumerate(result['sample_invalid_ids'], 1):
            print(f"   {idx}. ID: {invalid['id']}")
            print(f"      Title: {invalid['title'][:60]}...")
        print()
        print("Fix: Ensure clean-break ID normalization is working correctly")
        print("See: docs/clean-break-implementation/00-problem-statement.md")
        print()

        # Raise error to stop test execution
        raise ValidationError(
            f"Found {result['non_uuid_count']} submissions with non-UUID format. "
            f"Tests cannot proceed with mixed ID formats."
        )

    return result


def validate_table_exists(supabase_client, table_name: str) -> bool:
    """
    Validate that a required table exists in the database.

    Args:
        supabase_client: Supabase client instance
        table_name: Name of table to check

    Returns:
        True if table exists, False otherwise
    """
    try:
        result = supabase_client.table(table_name).select('*', count='exact').limit(1).execute()
        return True
    except Exception as e:
        print(f"❌ Table '{table_name}' does not exist or is not accessible")
        print(f"   Error: {str(e)}")
        return False


def validate_minimum_data_available(
    supabase_client,
    table_name: str,
    min_count: int,
    filters: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Validate that sufficient test data is available.

    Args:
        supabase_client: Supabase client instance
        table_name: Table to check
        min_count: Minimum number of records required
        filters: Optional filters to apply (e.g., {"reddit_score": ">= 50"})

    Returns:
        Dict with validation results

    Raises:
        ValidationError: If insufficient data available
    """
    query = supabase_client.table(table_name).select('*', count='exact')

    # Apply filters if provided
    if filters:
        for field, condition in filters.items():
            # Parse condition (e.g., "gte.20" → field >= 20)
            if '.' in condition:
                op, value = condition.split('.', 1)
                query = query.filter(field, op, value)
            else:
                query = query.filter(field, 'eq', condition)

    result = query.execute()
    actual_count = result.count if hasattr(result, 'count') else len(result.data)

    if actual_count < min_count:
        raise ValidationError(
            f"Insufficient data in '{table_name}': found {actual_count}, need {min_count}"
        )

    return {
        'passed': True,
        'table': table_name,
        'required_count': min_count,
        'actual_count': actual_count
    }


def validate_required_fields(
    supabase_client,
    table_name: str,
    required_fields: List[str],
    sample_size: int = 10
) -> Dict[str, any]:
    """
    Validate that required fields exist and have data.

    Args:
        supabase_client: Supabase client instance
        table_name: Table to check
        required_fields: List of field names that must exist
        sample_size: Number of records to sample

    Returns:
        Dict with validation results

    Raises:
        ValidationError: If required fields are missing
    """
    # Get sample records
    result = supabase_client.table(table_name).select(','.join(required_fields)).limit(sample_size).execute()

    if not result.data:
        raise ValidationError(f"No data found in '{table_name}'")

    # Check field coverage
    missing_fields = []
    for field in required_fields:
        if field not in result.data[0]:
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(
            f"Missing required fields in '{table_name}': {', '.join(missing_fields)}"
        )

    return {
        'passed': True,
        'table': table_name,
        'required_fields': required_fields,
        'sample_size': len(result.data)
    }


def run_all_pre_test_validations(supabase_client) -> Dict[str, any]:
    """
    Run all pre-test validations for Phase 8 integration testing.

    This is the main entry point for test validation. It runs all checks
    and returns a comprehensive validation report.

    Args:
        supabase_client: Supabase client instance

    Returns:
        Dict with complete validation results

    Raises:
        ValidationError: If any validation fails
    """
    print("=" * 80)
    print("PRE-TEST VALIDATION: Phase 8 Integration Testing")
    print("=" * 80)
    print()

    validations = {}

    try:
        # 1. Validate submission_id formats (CRITICAL)
        print("1. Checking submission_id formats (clean-break validation)...")
        validations['id_formats'] = validate_submission_id_formats(supabase_client)

        # 2. Validate required tables exist
        print("2. Checking required tables...")
        required_tables = ['submissions', 'app_opportunities', 'opportunities_unified']
        for table in required_tables:
            if not validate_table_exists(supabase_client, table):
                raise ValidationError(f"Required table '{table}' is missing")
        print(f"   ✅ All {len(required_tables)} required tables exist")
        print()

        # 3. Validate minimum data available
        print("3. Checking minimum data availability...")
        validations['data_availability'] = validate_minimum_data_available(
            supabase_client,
            'submissions',
            min_count=5,
            filters={'score': 'gte.20'}
        )
        print(f"   ✅ Sufficient test data: {validations['data_availability']['actual_count']} submissions")
        print()

        # 4. Validate submission table has required fields
        print("4. Checking required fields in submissions table...")
        validations['submission_fields'] = validate_required_fields(
            supabase_client,
            'submissions',
            required_fields=['id', 'title', 'selftext', 'score', 'num_comments'],
            sample_size=5
        )
        print(f"   ✅ All required fields present")
        print()

        print("=" * 80)
        print("✅ ALL PRE-TEST VALIDATIONS PASSED")
        print("=" * 80)
        print()
        print("Database is ready for Phase 8 integration testing!")
        print()

        return {
            'passed': True,
            'validations': validations,
            'timestamp': datetime.now().isoformat()
        }

    except ValidationError as e:
        print("=" * 80)
        print("❌ PRE-TEST VALIDATION FAILED")
        print("=" * 80)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Tests cannot proceed until validation issues are resolved.")
        print()
        raise


if __name__ == '__main__':
    """
    Run pre-test validation from command line.

    Usage:
        python scripts/testing/integration/utils/validation.py
    """
    import os
    from supabase import create_client

    # Load environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
        print("   Set them in .env.local or export them")
        exit(1)

    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)

    # Run validations
    try:
        result = run_all_pre_test_validations(supabase)
        exit(0)
    except ValidationError:
        exit(1)
