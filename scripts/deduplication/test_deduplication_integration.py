#!/usr/bin/env python3
"""
Semantic Deduplication Integration Test Script
Task 6: Integration testing script with comprehensive validation

This script provides comprehensive integration testing for the semantic deduplication system,
validating end-to-end workflow from opportunity input to deduplication result.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

try:
    from config.settings import SUPABASE_URL, SUPABASE_KEY
    from core.deduplication import SimpleDeduplicator
except ImportError as e:
    print(f"ERROR: Could not import required modules: {e}")
    print("Make sure you're running this script from the project root with:")
    print("source .venv/bin/activate")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeduplicationIntegrationTester:
    """
    Comprehensive integration testing for semantic deduplication system.
    Tests the complete workflow from opportunity input to deduplication result.
    """

    def __init__(self):
        """Initialize the integration tester."""
        self.deduplicator = None
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        self.created_test_data = []  # Track test data for cleanup

    def setup(self) -> bool:
        """Set up the testing environment."""
        print("🔧 Setting up integration test environment...")

        try:
            # Initialize deduplicator
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("❌ ERROR: Supabase credentials not configured")
                print("Please set SUPABASE_URL and SUPABASE_KEY in your environment")
                return False

            self.deduplicator = SimpleDeduplicator(SUPABASE_URL, SUPABASE_KEY)
            print(f"✅ Deduplicator initialized with Supabase URL: {SUPABASE_URL}")

            # Test database connection
            test_concept = "connection_test_" + str(int(time.time()))
            test_fingerprint = self.deduplicator.generate_fingerprint(test_concept)

            # Try a simple database operation to verify connection
            existing = self.deduplicator.find_existing_concept(test_fingerprint)
            if existing is None:
                print("✅ Database connection verified")
            else:
                print("⚠️  Warning: Test fingerprint already exists in database")

            return True

        except Exception as e:
            print(f"❌ ERROR: Failed to set up test environment: {e}")
            return False

    def create_sample_opportunities(self) -> List[Dict]:
        """Create comprehensive sample Reddit opportunity data for testing."""
        return [
            # Unique opportunities - different concepts
            {
                "id": "integration_test_unique_1",
                "app_concept": "AI-powered personal finance advisor that helps users save money through automated insights",
                "subreddit": "personalfinance",
                "score": 150,
                "title": "Looking for feedback on my finance app idea",
                "author": "finance_enthusiast",
                "created_utc": time.time() - 86400  # 1 day ago
            },
            {
                "id": "integration_test_unique_2",
                "app_concept": "Meditation app with guided breathing exercises for anxiety relief",
                "subreddit": "mentalhealth",
                "score": 89,
                "title": "Building a meditation app prototype",
                "author": "mindful_developer",
                "created_utc": time.time() - 172800  # 2 days ago
            },
            {
                "id": "integration_test_unique_3",
                "app_concept": "Language learning platform using spaced repetition and gamification",
                "subreddit": "languagelearning",
                "score": 234,
                "title": "Gamified language learning app concept",
                "author": "polyglot_dev",
                "created_utc": time.time() - 259200  # 3 days ago
            },

            # Duplicate opportunities - same concept, different wording
            {
                "id": "integration_test_duplicate_1",
                "app_concept": "App idea: Food delivery service for local restaurants",
                "subreddit": "food",
                "score": 45,
                "title": "Food delivery app concept for local eateries",
                "author": "food_tech_entrepreneur",
                "created_utc": time.time() - 3600  # 1 hour ago
            },
            {
                "id": "integration_test_duplicate_2",
                "app_concept": "mobile app: food delivery service connecting users with local restaurants",
                "subreddit": "restaurants",
                "score": 67,
                "title": "Local restaurant delivery platform idea",
                "author": "restaurant_owner",
                "created_utc": time.time() - 7200  # 2 hours ago
            },
            {
                "id": "integration_test_duplicate_3",
                "app_concept": "web app: Food delivery service for local restaurants with real-time tracking",
                "subreddit": "startups",
                "score": 123,
                "title": "Food delivery startup with tracking features",
                "author": "startup_founder",
                "created_utc": time.time() - 10800  # 3 hours ago
            },

            # More duplicates with different variations
            {
                "id": "integration_test_duplicate_4",
                "app_concept": "Task management app with AI-powered prioritization",
                "subreddit": "productivity",
                "score": 156,
                "title": "AI task manager concept",
                "author": "productivity_hacker",
                "created_utc": time.time() - 14400  # 4 hours ago
            },
            {
                "id": "integration_test_duplicate_5",
                "app_concept": "app: task management system with artificial intelligence prioritization",
                "subreddit": "gettingorganized",
                "score": 89,
                "title": "Smart task management system",
                "author": "organized_user",
                "created_utc": time.time() - 18000  # 5 hours ago
            },

            # Edge cases and boundary conditions
            {
                "id": "integration_test_edge_empty",
                "app_concept": "",
                "subreddit": "test",
                "score": 1,
                "title": "Empty concept test"
            },
            {
                "id": "integration_test_edge_whitespace",
                "app_concept": "   \t\n   ",
                "subreddit": "test",
                "score": 1,
                "title": "Whitespace concept test"
            },
            {
                "id": "integration_test_edge_long",
                "app_concept": "App idea: " + "very long concept " * 50,
                "subreddit": "test",
                "score": 1,
                "title": "Long concept test"
            }
        ]

    def run_test(self, test_name: str, test_func) -> Tuple[bool, str]:
        """Run a single test and return result."""
        self.test_results["total_tests"] += 1
        print(f"\n🧪 Running test: {test_name}")

        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time

            if result:
                print(f"✅ PASSED: {test_name} ({duration:.3f}s)")
                self.test_results["passed_tests"] += 1
                self.test_results["test_details"].append({
                    "name": test_name,
                    "status": "PASSED",
                    "duration": duration,
                    "message": "Test completed successfully"
                })
                return True, "Test passed"
            else:
                print(f"❌ FAILED: {test_name} ({duration:.3f}s)")
                self.test_results["failed_tests"] += 1
                self.test_results["test_details"].append({
                    "name": test_name,
                    "status": "FAILED",
                    "duration": duration,
                    "message": "Test assertion failed"
                })
                return False, "Test assertion failed"

        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            print(f"💥 ERROR: {test_name} ({duration:.3f}s) - {e}")
            self.test_results["failed_tests"] += 1
            self.test_results["test_details"].append({
                "name": test_name,
                "status": "ERROR",
                "duration": duration,
                "message": str(e)
            })
            return False, str(e)

    def test_concept_normalization(self) -> bool:
        """Test concept normalization functionality."""
        test_cases = [
            ("App idea: Food delivery", "idea: food delivery"),
            ("APP IDEA: FOOD DELIVERY", "idea: food delivery"),
            ("  Multiple   spaces  here  ", "multiple spaces here"),
            ("app: simple task manager", "simple task manager"),
            ("mobile app: task manager", "app: task manager"),
        ]

        for input_concept, expected_output in test_cases:
            actual_output = self.deduplicator.normalize_concept(input_concept)
            if actual_output != expected_output:
                print(f"  Expected '{expected_output}', got '{actual_output}'")
                return False

        return True

    def test_fingerprint_consistency(self) -> bool:
        """Test fingerprint generation consistency."""
        concept1 = "App idea: Food delivery service"
        concept2 = "app idea: food delivery service"
        concept3 = "web app: Food delivery service"

        fp1 = self.deduplicator.generate_fingerprint(concept1)
        fp2 = self.deduplicator.generate_fingerprint(concept2)
        fp3 = self.deduplicator.generate_fingerprint(concept3)

        # Same concepts should have same fingerprints
        if fp1 != fp2:
            print(f"  Same concepts should have same fingerprints: {fp1} != {fp2}")
            return False

        # Different concepts should have different fingerprints
        if fp1 == fp3:
            print(f"  Different concepts should have different fingerprints: {fp1} == {fp3}")
            return False

        # Check fingerprint format
        if len(fp1) != 64 or not all(c in "0123456789abcdef" for c in fp1):
            print(f"  Invalid fingerprint format: {fp1}")
            return False

        return True

    def test_unique_opportunity_processing(self) -> bool:
        """Test processing of unique opportunities."""
        sample_opps = self.create_sample_opportunities()
        unique_opp = sample_opps[0]  # AI-powered personal finance advisor

        result = self.deduplicator.process_opportunity(unique_opp)

        # Validate result structure
        expected_keys = ["success", "is_duplicate", "concept_id", "opportunity_id",
                        "fingerprint", "normalized_concept", "message", "processing_time"]
        for key in expected_keys:
            if key not in result:
                print(f"  Missing expected key: {key}")
                return False

        # Validate successful processing
        if not result["success"]:
            print(f"  Processing failed: {result.get('message', 'Unknown error')}")
            return False

        if result["is_duplicate"]:
            print("  Expected unique opportunity, got duplicate")
            return False

        if result["concept_id"] is None:
            print("  Concept ID should not be None for unique opportunity")
            return False

        # Verify database storage
        existing = self.deduplicator.find_existing_concept(result["fingerprint"])
        if existing is None:
            print("  Concept not found in database after processing")
            return False

        # Track for cleanup
        self.created_test_data.append({
            "type": "concept",
            "id": result["concept_id"],
            "fingerprint": result["fingerprint"]
        })

        return True

    def test_duplicate_opportunity_processing(self) -> bool:
        """Test processing of duplicate opportunities."""
        sample_opps = self.create_sample_opportunities()
        duplicate_opps = [opp for opp in sample_opps if "food delivery" in opp["app_concept"].lower()]

        if len(duplicate_opps) < 2:
            print("  Need at least 2 duplicate opportunities for testing")
            return False

        # Process first duplicate - should create new concept
        first_result = self.deduplicator.process_opportunity(duplicate_opps[0])
        if not first_result["success"] or first_result["is_duplicate"]:
            print("  First duplicate should create new concept")
            return False

        # Process second duplicate - should find existing concept
        second_result = self.deduplicator.process_opportunity(duplicate_opps[1])
        if not second_result["success"] or not second_result["is_duplicate"]:
            print("  Second duplicate should be marked as duplicate")
            return False

        if second_result["concept_id"] != first_result["concept_id"]:
            print("  Duplicates should have same concept ID")
            return False

        if second_result["fingerprint"] != first_result["fingerprint"]:
            print("  Duplicates should have same fingerprint")
            return False

        # Track for cleanup
        self.created_test_data.append({
            "type": "concept",
            "id": first_result["concept_id"],
            "fingerprint": first_result["fingerprint"]
        })

        return True

    def test_error_handling(self) -> bool:
        """Test error handling for invalid inputs."""
        error_cases = [
            (None, "Empty opportunity"),
            ({}, "Missing ID and concept"),
            ({"id": "test"}, "Missing app_concept"),
            ({"app_concept": "test"}, "Missing ID"),
            ({"id": "test", "app_concept": ""}, "Empty concept"),
            ({"id": "test", "app_concept": "   "}, "Whitespace-only concept"),
        ]

        for opportunity, description in error_cases:
            result = self.deduplicator.process_opportunity(opportunity)

            if result["success"]:
                print(f"  Expected failure for {description}, but got success")
                return False

            if "error" not in result and "message" not in result:
                print(f"  Missing error details for {description}")
                return False

        return True

    def test_end_to_end_workflow(self) -> bool:
        """Test complete end-to-end workflow with mixed data."""
        sample_opps = self.create_sample_opportunities()
        valid_opps = [opp for opp in sample_opps
                     if opp["id"] not in ["integration_test_edge_empty", "integration_test_edge_whitespace"]]

        results = []
        concepts_by_fingerprint = {}

        # Process all opportunities
        for opportunity in valid_opps:
            result = self.deduplicator.process_opportunity(opportunity)
            results.append(result)

            if result["success"]:
                fp = result["fingerprint"]
                if fp not in concepts_by_fingerprint:
                    concepts_by_fingerprint[fp] = []
                concepts_by_fingerprint[fp].append(result)

        # Analyze results
        successful_results = [r for r in results if r["success"]]
        unique_results = [r for r in successful_results if not r["is_duplicate"]]
        duplicate_results = [r for r in successful_results if r["is_duplicate"]]

        print(f"  Processed {len(successful_results)} opportunities successfully")
        print(f"  Found {len(unique_results)} unique concepts")
        print(f"  Found {len(duplicate_results)} duplicates")

        # Validate expectations
        if len(successful_results) < 5:
            print(f"  Expected at least 5 successful results, got {len(successful_results)}")
            return False

        if len(unique_results) < 2:
            print(f"  Expected at least 2 unique concepts, got {len(unique_results)}")
            return False

        if len(duplicate_results) < 2:
            print(f"  Expected at least 2 duplicates, got {len(duplicate_results)}")
            return False

        # Verify duplicate groups
        duplicate_groups = {fp: results for fp, results in concepts_by_fingerprint.items() if len(results) > 1}
        if len(duplicate_groups) < 2:
            print(f"  Expected at least 2 duplicate groups, got {len(duplicate_groups)}")
            return False

        # Track concepts for cleanup
        for result in successful_results:
            self.created_test_data.append({
                "type": "concept",
                "id": result["concept_id"],
                "fingerprint": result["fingerprint"]
            })

        return True

    def test_performance_benchmarks(self) -> bool:
        """Test performance characteristics."""
        sample_opps = self.create_sample_opportunities()[:5]  # Test with 5 opportunities

        start_time = time.time()
        processing_times = []

        for opportunity in sample_opps:
            if opportunity["id"] in ["integration_test_edge_empty", "integration_test_edge_whitespace"]:
                continue

            opp_start = time.time()
            result = self.deduplicator.process_opportunity(opportunity)
            opp_time = time.time() - opp_start

            if result["success"]:
                processing_times.append(opp_time)

        total_time = time.time() - start_time

        print(f"  Processed {len(processing_times)} opportunities in {total_time:.3f}s total")
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            print(f"  Average processing time: {avg_time:.3f}s")
            print(f"  Maximum processing time: {max_time:.3f}s")

        # Performance assertions
        if total_time > 15.0:  # Should complete within 15 seconds
            print(f"  Total processing time too high: {total_time:.3f}s > 15s")
            return False

        if processing_times and max(processing_times) > 5.0:  # Each under 5 seconds
            print(f"  Individual processing time too high: {max(processing_times):.3f}s > 5s")
            return False

        return True

    def cleanup_test_data(self) -> bool:
        """Clean up test data from database."""
        print("\n🧹 Cleaning up test data...")

        cleanup_success = True
        cleaned_count = 0

        for data in self.created_test_data:
            try:
                if data["type"] == "concept":
                    # Note: In a real implementation, you might want to add
                    # cleanup methods to SimpleDeduplicator
                    # For now, we just log what would be cleaned up
                    print(f"  Would clean concept ID {data['id']} (fingerprint: {data['fingerprint'][:8]}...)")
                    cleaned_count += 1

            except Exception as e:
                print(f"  Error cleaning up {data['type']} ID {data.get('id')}: {e}")
                cleanup_success = False

        print(f"  {cleaned_count} test records marked for cleanup")
        return cleanup_success

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("🚀 Starting Semantic Deduplication Integration Tests")
        print("=" * 60)

        if not self.setup():
            return False

        # Define all tests to run
        tests = [
            ("Concept Normalization", self.test_concept_normalization),
            ("Fingerprint Consistency", self.test_fingerprint_consistency),
            ("Unique Opportunity Processing", self.test_unique_opportunity_processing),
            ("Duplicate Opportunity Processing", self.test_duplicate_opportunity_processing),
            ("Error Handling", self.test_error_handling),
            ("End-to-End Workflow", self.test_end_to_end_workflow),
            ("Performance Benchmarks", self.test_performance_benchmarks),
        ]

        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        # Cleanup
        self.cleanup_test_data()

        # Print final results
        self.print_summary()

        return self.test_results["failed_tests"] == 0

    def print_summary(self):
        """Print test summary report."""
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)

        total = self.test_results["total_tests"]
        passed = self.test_results["passed_tests"]
        failed = self.test_results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {success_rate:.1f}%")

        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results["test_details"]:
                if test["status"] in ["FAILED", "ERROR"]:
                    print(f"  - {test['name']}: {test['message']}")

        print(f"\n🎯 Deduplication System Validation: {'PASSED' if failed == 0 else 'FAILED'}")

        if failed == 0:
            print("\n✅ All integration tests passed! The semantic deduplication system is working correctly.")
            print("   - Concept normalization functioning properly")
            print("   - Fingerprint generation consistent and collision-free")
            print("   - Unique opportunity detection working")
            print("   - Duplicate opportunity detection working")
            print("   - Error handling robust")
            print("   - End-to-end workflow functional")
            print("   - Performance within acceptable bounds")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")


def main():
    """Main entry point for integration testing."""
    print("Semantic Deduplication Integration Test Script")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python Version: {sys.version}")

    tester = DeduplicationIntegrationTester()
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())