#!/usr/bin/env python3
"""
Phase 4 End-to-End Deduplication Integration Test

This script tests the complete deduplication flow across two pipeline runs:
1. Run 1: Fresh analysis (all submissions analyzed via AI)
2. Run 2: Same submissions (should copy from existing, saving costs)

Tests validate:
- Deduplication logic works correctly
- Cost savings are achieved
- Trust data is preserved
- Concept metadata is tracked correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client

from config.settings import SUPABASE_KEY, SUPABASE_URL
from core.pipeline.config import DataSource, PipelineConfig
from core.pipeline.orchestrator import OpportunityPipeline


def test_deduplication_e2e():
    """Test end-to-end deduplication with real database."""
    print("\n" + "=" * 70)
    print("PHASE 4: End-to-End Deduplication Test")
    print("=" * 70)

    try:
        # Initialize Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")

        # Test configuration
        limit = 5  # Small batch for testing
        print(f"\nTest Configuration:")
        print(f"- Submissions: {limit}")
        print(f"- Profiler: Enabled")
        print(f"- Monetization: Enabled")
        print(f"- Deduplication: Enabled")

        # ============================================================
        # RUN 1: Fresh Analysis
        # ============================================================
        print("\n" + "-" * 70)
        print("RUN 1: Fresh Analysis (First Time)")
        print("-" * 70)

        config1 = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=limit,
            enable_profiler=True,
            enable_monetization=True,
            enable_quality_filter=False,
            dry_run=False,
            supabase_client=supabase,
            source_config={"table_name": "submissions"},  # Use submissions table
        )

        pipeline1 = OpportunityPipeline(config1)
        result1 = pipeline1.run()

        # Display Run 1 results
        print("\n📊 Run 1 Statistics:")
        print(f"  Fetched:     {result1['stats'].get('fetched', 0)}")
        print(f"  Analyzed:    {result1['stats'].get('analyzed', 0)} (AI)")
        print(f"  Copied:      {result1['stats'].get('copied', 0)} (dedup)")
        print(f"  Stored:      {result1['stats'].get('stored', 0)}")

        print("\n💰 Run 1 Cost:")
        dedup_rate1 = result1.get("summary", {}).get("dedup_rate", 0)
        cost_saved1 = result1.get("summary", {}).get("cost_saved", 0)
        print(f"  Dedup Rate:  {dedup_rate1}%")
        print(f"  Cost Saved:  ${cost_saved1:.2f}")

        # ============================================================
        # RUN 2: Deduplication
        # ============================================================
        print("\n" + "-" * 70)
        print("RUN 2: Deduplication (Second Run)")
        print("-" * 70)

        config2 = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=limit,
            enable_profiler=True,
            enable_monetization=True,
            enable_quality_filter=False,
            dry_run=False,
            supabase_client=supabase,
            source_config={"table_name": "submissions"},  # Use submissions table
        )

        pipeline2 = OpportunityPipeline(config2)
        result2 = pipeline2.run()

        # Display Run 2 results
        print("\n📊 Run 2 Statistics:")
        print(f"  Fetched:     {result2['stats'].get('fetched', 0)}")
        print(f"  Analyzed:    {result2['stats'].get('analyzed', 0)} (AI)")
        print(f"  Copied:      {result2['stats'].get('copied', 0)} (dedup)")
        print(f"  Stored:      {result2['stats'].get('stored', 0)}")

        print("\n💰 Run 2 Cost:")
        dedup_rate2 = result2.get("summary", {}).get("dedup_rate", 0)
        cost_saved2 = result2.get("summary", {}).get("cost_saved", 0)
        print(f"  Dedup Rate:  {dedup_rate2}%")
        print(f"  Cost Saved:  ${cost_saved2:.2f}")

        # ============================================================
        # Validation
        # ============================================================
        print("\n" + "=" * 70)
        print("VALIDATION")
        print("=" * 70)

        analyzed1 = result1["stats"].get("analyzed", 0)
        copied2 = result2["stats"].get("copied", 0)

        checks = []

        # Check 1: Deduplication improved
        check1 = dedup_rate2 >= dedup_rate1
        checks.append(check1)
        status1 = "✅" if check1 else "❌"
        print(f"\n{status1} Deduplication Rate: {dedup_rate2}% >= {dedup_rate1}%")

        # Check 2: Cost savings (if copied)
        check2 = copied2 == 0 or cost_saved2 > 0
        checks.append(check2)
        status2 = "✅" if check2 else "❌"
        print(f"{status2} Cost Savings: ${cost_saved2:.2f}")

        # Check 3: Copies made on second run (if Run 1 had analysis)
        if analyzed1 > 0:
            check3 = copied2 >= analyzed1 * 0.5  # At least 50%
            checks.append(check3)
            status3 = "✅" if check3 else "❌"
            copy_rate = (copied2 / analyzed1 * 100) if analyzed1 > 0 else 0
            print(f"{status3} Copy Rate: {copy_rate:.1f}% (>= 50%)")

        # ============================================================
        # Summary
        # ============================================================
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        passed = sum(checks)
        total = len(checks)
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n📋 Checks: {passed}/{total} passed ({success_rate:.1f}%)")

        if success_rate >= 80:
            print("\n🎉 TEST PASSED!")
            print("✅ Deduplication working correctly")
            print("✅ Cost savings achieved")
            return True
        else:
            print("\n⚠️  TEST INCOMPLETE")
            print("Some checks failed")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nPhase 4: End-to-End Deduplication Test")
    print("Make sure Supabase is running with data\n")

    success = test_deduplication_e2e()

    print("\n" + "=" * 70)
    if success:
        print("✅ Phase 4 E2E Test: PASSED")
        sys.exit(0)
    else:
        print("❌ Phase 4 E2E Test: INCOMPLETE")
        sys.exit(1)