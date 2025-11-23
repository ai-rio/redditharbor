#!/usr/bin/env python3
"""
RedditHarbor ID Normalization Trigger Test Suite

This script comprehensively tests the PostgreSQL ID normalization trigger
implementation to ensure it matches Python's uuid.uuid5() behavior exactly.

Author: Data Engineering Team
Date: 2025-11-23
Version: 1.0.0

Test Coverage:
- PostgreSQL UUID5 generation vs Python uuid.uuid5() compatibility
- Trigger behavior on INSERT operations
- Trigger behavior on UPDATE operations
- Various input formats (UUID, Reddit ID, Reddit URL, arbitrary text)
- NULL and empty value handling
- Performance and concurrency testing
"""

import os
import sys
import json
import time
import uuid
import psycopg2
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import RedditHarbor modules
from core.utils.id_resolver import (
    REDDITHARBOR_NAMESPACE,
    generate_deterministic_uuid,
    resolve_submission_id
)


@dataclass
class TestCase:
    """Test case definition for ID normalization testing."""
    name: str
    input_value: str
    expected_source: Optional[str]  # "passthrough", "generated", or None for NULL
    description: str


@dataclass
class TestResult:
    """Test result container."""
    test_case: TestCase
    postgres_result: Optional[str]
    python_result: Optional[str]
    matches: bool
    error: Optional[str] = None


class IDNormalizationTester:
    """
    Comprehensive test suite for RedditHarbor ID normalization trigger.

    This class tests the PostgreSQL trigger implementation against the Python
    reference implementation to ensure identical behavior.
    """

    def __init__(self):
        """Initialize the tester with database connection."""
        self.conn = None
        self.test_results: List[TestResult] = []
        self.performance_results: Dict[str, float] = {}

        # Database connection parameters
        self.db_config = {
            'host': 'localhost',
            'port': 54331,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        }

        # Test cases covering all input formats
        self.test_cases = [
            # UUID passthrough tests
            TestCase(
                name="Valid UUID passthrough",
                input_value="67959699-bbd7-5213-8934-bbfccb37697b",
                expected_source="passthrough",
                description="Valid UUID should pass through unchanged"
            ),
            TestCase(
                name="Mixed case UUID",
                input_value="67959699-BBD7-5213-8934-BBFCCB37697B",
                expected_source="passthrough",
                description="Mixed case UUID should normalize to lowercase"
            ),
            TestCase(
                name="Different valid UUID",
                input_value="550e8400-e29b-41d4-a716-446655440000",
                expected_source="passthrough",
                description="Different valid UUID should pass through"
            ),

            # Reddit URL extraction tests
            TestCase(
                name="Reddit URL with subreddit",
                input_value="https://reddit.com/r/technology/comments/abc123/post_title",
                expected_source="generated",
                description="Extract Reddit ID from full URL and generate UUID"
            ),
            TestCase(
                name="Reddit URL without subreddit",
                input_value="https://reddit.com/comments/xyz789/post_title",
                expected_source="generated",
                description="Extract Reddit ID from URL without subreddit"
            ),
            TestCase(
                name="Reddit URL with www",
                input_value="https://www.reddit.com/r/python/comments/def456/my_post",
                expected_source="generated",
                description="Handle www.reddit.com URLs"
            ),

            # Reddit ID generation tests
            TestCase(
                name="Simple Reddit ID",
                input_value="abc123",
                expected_source="generated",
                description="Generate deterministic UUID from Reddit ID"
            ),
            TestCase(
                name="Reddit ID with numbers",
                input_value="1234567890",
                expected_source="generated",
                description="Generate UUID from numeric Reddit ID"
            ),
            TestCase(
                name="Reddit ID with mixed chars",
                input_value="AbCdEf123",
                expected_source="generated",
                description="Generate UUID from mixed character Reddit ID"
            ),

            # Arbitrary text tests
            TestCase(
                name="Arbitrary text",
                input_value="some_random_text",
                expected_source="generated",
                description="Generate deterministic UUID from arbitrary text"
            ),
            TestCase(
                name="Text with special chars",
                input_value="test@#$%^&*()",
                expected_source="generated",
                description="Handle special characters in input text"
            ),
            TestCase(
                name="Long text input",
                input_value="this_is_a_very_long_reddit_submission_id_that_might_occur_in_some_cases",
                expected_source="generated",
                description="Handle longer input strings"
            ),

            # NULL and empty value tests
            TestCase(
                name="NULL input",
                input_value=None,
                expected_source=None,
                description="NULL input should remain NULL"
            ),
            TestCase(
                name="Empty string",
                input_value="",
                expected_source=None,
                description="Empty string should become NULL"
            ),
            TestCase(
                name="Whitespace only",
                input_value="   ",
                expected_source=None,
                description="Whitespace-only string should become NULL"
            ),

            # Edge cases
            TestCase(
                name="Invalid UUID format",
                input_value="not-a-valid-uuid",
                expected_source="generated",
                description="Invalid UUID should be treated as text and generate UUID"
            ),
            TestCase(
                name="UUID-like but invalid",
                input_value="12345678-1234-1234-1234-123456789abc",  # Invalid format
                expected_source="generated",
                description="UUID-like string with invalid format should generate UUID"
            ),
        ]

    def connect(self) -> bool:
        """
        Establish database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = True  # Use autocommit for testing
            print("✓ Database connection established")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")

    def setup_test_table(self) -> bool:
        """
        Create a test table for trigger testing.

        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            with self.conn.cursor() as cursor:
                # Create test table with TEXT column to allow trigger processing
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_id_normalization (
                        id SERIAL PRIMARY KEY,
                        submission_id TEXT,
                        normalized_submission_id UUID,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        test_description TEXT
                    )
                """)

                # Create a custom trigger function for the test table
                cursor.execute("""
                    DROP TRIGGER IF EXISTS trigger_normalize_test_submission_id ON test_id_normalization;
                    DROP FUNCTION IF EXISTS normalize_test_submission_id();

                    CREATE OR REPLACE FUNCTION normalize_test_submission_id()
                    RETURNS TRIGGER
                    LANGUAGE plpgsql
                    AS $$
                    BEGIN
                        -- Normalize the submission_id using the resolver logic
                        NEW.normalized_submission_id := normalize_submission_id(NEW.submission_id);
                        RETURN NEW;
                    END;
                    $$;

                    CREATE TRIGGER trigger_normalize_test_submission_id
                        BEFORE INSERT OR UPDATE ON test_id_normalization
                        FOR EACH ROW
                        EXECUTE FUNCTION normalize_test_submission_id();
                """)

                # Clear any existing test data
                cursor.execute("TRUNCATE TABLE test_id_normalization")

            print("✓ Test table setup completed")
            return True
        except Exception as e:
            print(f"✗ Test table setup failed: {e}")
            return False

    def test_python_uuid5_compatibility(self) -> bool:
        """
        Test PostgreSQL uuid5_generate function vs Python uuid.uuid5().

        Returns:
            bool: True if compatibility test passed, False otherwise
        """
        print("\n🧪 Testing PostgreSQL vs Python UUID5 compatibility...")

        test_inputs = [
            "abc123",
            "test_string",
            "reddit_id_12345",
            "https://reddit.com/r/test/comments/abc123/title",
            "some_other_input",
            REDDITHARBOR_NAMESPACE.hex  # Test with namespace itself
        ]

        all_passed = True

        for test_input in test_inputs:
            try:
                # Generate UUID using Python
                python_uuid = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, test_input))

                # Generate UUID using PostgreSQL
                with self.conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT uuid5_generate(%s::UUID, %s)",
                        (str(REDDITHARBOR_NAMESPACE), test_input)
                    )
                    postgres_uuid = str(cursor.fetchone()[0])

                # Compare results
                if python_uuid.lower() == postgres_uuid.lower():
                    print(f"  ✓ '{test_input[:30]}...': {python_uuid}")
                else:
                    print(f"  ✗ '{test_input[:30]}...': Python={python_uuid}, PostgreSQL={postgres_uuid}")
                    all_passed = False

            except Exception as e:
                print(f"  ✗ '{test_input[:30]}...': Error - {e}")
                all_passed = False

        if all_passed:
            print("✓ All UUID5 compatibility tests passed")
        else:
            print("✗ Some UUID5 compatibility tests failed")

        return all_passed

    def test_trigger_behavior(self, test_case: TestCase) -> TestResult:
        """
        Test trigger behavior for a specific test case.

        Args:
            test_case: Test case to execute

        Returns:
            TestResult: Result of the test
        """
        try:
            # Get expected result from Python implementation
            python_resolution = resolve_submission_id(test_case.input_value)
            python_result = python_resolution.uuid if python_resolution else None

            # Test INSERT behavior
            with self.conn.cursor() as cursor:
                # Insert test data - the trigger will normalize the submission_id
                cursor.execute(
                    """
                    INSERT INTO test_id_normalization (submission_id, test_description)
                    VALUES (%s, %s)
                    RETURNING id, normalized_submission_id
                    """,
                    (test_case.input_value, test_case.description)
                )
                insert_result = cursor.fetchone()
                insert_id, postgres_result = insert_result

                # Test UPDATE behavior
                cursor.execute(
                    """
                    UPDATE test_id_normalization
                    SET submission_id = %s, test_description = %s
                    WHERE id = %s
                    RETURNING normalized_submission_id
                    """,
                    (test_case.input_value, f"{test_case.description} (updated)", insert_id)
                )
                update_result = cursor.fetchone()
                postgres_result_update = update_result[0]

                # Verify INSERT and UPDATE produce the same result
                if (postgres_result != postgres_result_update):
                    return TestResult(
                        test_case=test_case,
                        postgres_result=postgres_result,
                        python_result=python_result,
                        matches=False,
                        error=f"INSERT/UPDATE mismatch: INSERT={postgres_result}, UPDATE={postgres_result_update}"
                    )

            # Compare results
            matches = (
                (python_result is None and postgres_result is None) or
                (python_result is not None and postgres_result is not None and
                 str(python_result).lower() == str(postgres_result).lower())
            )

            return TestResult(
                test_case=test_case,
                postgres_result=str(postgres_result) if postgres_result else None,
                python_result=str(python_result) if python_result else None,
                matches=matches
            )

        except Exception as e:
            return TestResult(
                test_case=test_case,
                postgres_result=None,
                python_result=None,
                matches=False,
                error=str(e)
            )

    def run_all_tests(self) -> bool:
        """
        Run all test cases.

        Returns:
            bool: True if all tests passed, False otherwise
        """
        print(f"\n🧪 Running {len(self.test_cases)} test cases...")

        all_passed = True

        for test_case in self.test_cases:
            print(f"  Testing: {test_case.name}")
            result = self.test_trigger_behavior(test_case)
            self.test_results.append(result)

            if result.matches:
                print(f"    ✓ PASS: {result.python_result}")
            else:
                print(f"    ✗ FAIL: {result.error}")
                print(f"      Expected: {result.python_result}")
                print(f"      Got: {result.postgres_result}")
                all_passed = False

        passed_count = sum(1 for r in self.test_results if r.matches)
        print(f"\n📊 Test Results: {passed_count}/{len(self.test_cases)} passed")

        return all_passed

    def test_performance(self) -> Dict[str, float]:
        """
        Test performance of ID normalization operations.

        Returns:
            Dict[str, float]: Performance metrics in seconds
        """
        print("\n⚡ Performance testing...")

        test_input = "performance_test_12345"
        iterations = 1000

        # Test Python performance
        start_time = time.time()
        for _ in range(iterations):
            generate_deterministic_uuid(test_input)
        python_time = time.time() - start_time

        # Test PostgreSQL performance
        with self.conn.cursor() as cursor:
            start_time = time.time()
            for _ in range(iterations):
                cursor.execute(
                    "SELECT normalize_submission_id(%s)",
                    (test_input,)
                )
                cursor.fetchone()
            postgres_time = time.time() - start_time

        # Test trigger performance (INSERT)
        with self.conn.cursor() as cursor:
            start_time = time.time()
            for i in range(iterations):
                cursor.execute(
                    """
                    INSERT INTO test_id_normalization (submission_id, test_description)
                    VALUES (%s, %s)
                    """,
                    (f"{test_input}_{i}", f"Performance test {i}")
                )
            trigger_time = time.time() - start_time

        performance_results = {
            'python_uuid5': python_time,
            'postgres_function': postgres_time,
            'postgres_trigger': trigger_time
        }

        print(f"  Python uuid.uuid5(): {python_time:.4f}s ({iterations} ops)")
        print(f"  PostgreSQL function: {postgres_time:.4f}s ({iterations} ops)")
        print(f"  PostgreSQL trigger: {trigger_time:.4f}s ({iterations} ops)")

        self.performance_results = performance_results
        return performance_results

    def test_concurrent_operations(self) -> bool:
        """
        Test trigger behavior under concurrent operations.

        Returns:
            bool: True if concurrent test passed, False otherwise
        """
        print("\n🔄 Testing concurrent operations...")

        def insert_test_data(worker_id: int, num_inserts: int) -> List[Optional[str]]:
            """Worker function for concurrent inserts."""
            results = []
            try:
                conn = psycopg2.connect(**self.db_config)
                conn.autocommit = True

                with conn.cursor() as cursor:
                    for i in range(num_inserts):
                        input_value = f"concurrent_test_{worker_id}_{i}"
                        cursor.execute(
                            """
                            INSERT INTO test_id_normalization (submission_id, test_description)
                            VALUES (%s, %s)
                            RETURNING normalized_submission_id
                            """,
                            (input_value, f"Worker {worker_id}, Insert {i}")
                        )
                        result = cursor.fetchone()[0]
                        results.append(str(result) if result else None)

                conn.close()
                return results

            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                return [f"ERROR: {e}" for _ in range(num_inserts)]

        # Run concurrent operations
        num_workers = 5
        inserts_per_worker = 20

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(insert_test_data, i, inserts_per_worker)
                for i in range(num_workers)
            ]

            all_results = []
            for future in as_completed(futures):
                worker_results = future.result()
                all_results.extend(worker_results)

        concurrent_time = time.time() - start_time

        # Verify all operations completed successfully
        expected_total = num_workers * inserts_per_worker
        actual_total = len(all_results)
        errors = [r for r in all_results if r.startswith("ERROR:")]

        print(f"  Expected operations: {expected_total}")
        print(f"  Completed operations: {actual_total}")
        print(f"  Errors: {len(errors)}")
        print(f"  Total time: {concurrent_time:.4f}s")

        # Verify data consistency
        unique_results = set(all_results)
        expected_pattern = f"{str(generate_deterministic_uuid('concurrent_test_0_0'))[:8]}..."

        success = (
            actual_total == expected_total and
            len(errors) == 0 and
            len(unique_results) == actual_total  # All should be unique
        )

        if success:
            print("  ✓ Concurrent operations completed successfully")
        else:
            print("  ✗ Concurrent operations failed")

        return success

    def generate_report(self) -> str:
        """
        Generate comprehensive test report.

        Returns:
            str: Formatted test report
        """
        report = []
        report.append("# RedditHarbor ID Normalization Test Report")
        report.append("=" * 60)
        report.append(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Test Cases: {len(self.test_results)}")

        # Summary
        passed_count = sum(1 for r in self.test_results if r.matches)
        failed_count = len(self.test_results) - passed_count

        report.append(f"\n## Summary")
        report.append(f"- Passed: {passed_count}")
        report.append(f"- Failed: {failed_count}")
        report.append(f"- Success Rate: {(passed_count/len(self.test_results)*100):.1f}%")

        # Failed tests
        if failed_count > 0:
            report.append(f"\n## Failed Tests")
            for result in self.test_results:
                if not result.matches:
                    report.append(f"### {result.test_case.name}")
                    report.append(f"- Input: {result.test_case.input_value}")
                    report.append(f"- Expected: {result.python_result}")
                    report.append(f"- Got: {result.postgres_result}")
                    report.append(f"- Error: {result.error}")

        # Performance metrics
        if self.performance_results:
            report.append(f"\n## Performance Metrics")
            for operation, duration in self.performance_results.items():
                report.append(f"- {operation}: {duration:.4f}s")

        # Database info
        report.append(f"\n## Database Information")
        report.append(f"- Host: {self.db_config['host']}:{self.db_config['port']}")
        report.append(f"- Database: {self.db_config['database']}")
        report.append(f"- Namespace: {REDDITHARBOR_NAMESPACE}")

        return "\n".join(report)

    def cleanup(self):
        """Clean up test data and objects."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS test_id_normalization")
            print("✓ Test cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


def main():
    """
    Main test execution function.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("🚀 RedditHarbor ID Normalization Trigger Test Suite")
    print("=" * 60)

    tester = IDNormalizationTester()

    try:
        # Setup
        if not tester.connect():
            return 1

        if not tester.setup_test_table():
            return 1

        # Run tests
        all_tests_passed = True

        # 1. Test UUID5 compatibility
        if not tester.test_python_uuid5_compatibility():
            all_tests_passed = False

        # 2. Test trigger behavior
        if not tester.run_all_tests():
            all_tests_passed = False

        # 3. Test performance
        performance_results = tester.test_performance()

        # 4. Test concurrent operations
        if not tester.test_concurrent_operations():
            all_tests_passed = False

        # Generate report
        report = tester.generate_report()

        # Save report to file
        report_path = "/tmp/id_normalization_test_report.md"
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\n📄 Test report saved to: {report_path}")

        # Final result
        if all_tests_passed:
            print("\n🎉 All tests passed! ID normalization trigger is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed. Please review the implementation.")
            return 1

    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

    finally:
        tester.cleanup()
        tester.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)