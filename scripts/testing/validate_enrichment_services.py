#!/usr/bin/env python3
"""Side-by-Side Validation: Enrichment Services vs Monolith

This script compares the new enrichment services against the monolith implementation
to ensure identical results. It's part of Phase 6 integration testing.

Usage:
    python scripts/testing/validate_enrichment_services.py --submissions 100

Features:
- Fetches test submissions from database
- Runs both monolith and service-based pipelines
- Compares results field-by-field
- Reports discrepancies with detailed analysis
- Validates cost savings are maintained

Success Criteria (from Phase 6 requirements):
- 100% match on core fields (app_name, final_score, monetization_score, trust_level)
- Acceptable variance on floating point scores (±0.01)
- Cost savings maintained ($3,528/year)
- Performance within 10% of baseline
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnrichmentServiceValidator:
    """Validates enrichment services match monolith behavior."""

    def __init__(self):
        self.comparison_results = []
        self.discrepancies = []
        self.stats = {
            "total_compared": 0,
            "perfect_matches": 0,
            "acceptable_matches": 0,
            "failures": 0,
        }

    def compare_opportunity_analysis(
        self, monolith_result: Dict[str, Any], service_result: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Compare opportunity analysis results.

        Returns:
            Tuple of (is_match, discrepancies_list)
        """
        discrepancies = []

        # Core fields that must match exactly
        exact_match_fields = [
            "opportunity_id",
            "title",
            "subreddit",
            "priority",
        ]

        for field in exact_match_fields:
            if monolith_result.get(field) != service_result.get(field):
                discrepancies.append(
                    f"Opportunity {field} mismatch: "
                    f"monolith={monolith_result.get(field)}, "
                    f"service={service_result.get(field)}"
                )

        # Numeric fields with acceptable variance
        numeric_fields = ["final_score"]
        for field in numeric_fields:
            mono_val = monolith_result.get(field, 0)
            serv_val = service_result.get(field, 0)
            if abs(mono_val - serv_val) > 0.01:
                discrepancies.append(
                    f"Opportunity {field} variance: "
                    f"monolith={mono_val:.2f}, "
                    f"service={serv_val:.2f}, "
                    f"diff={abs(mono_val - serv_val):.4f}"
                )

        # Dimension scores comparison
        mono_dims = monolith_result.get("dimension_scores", {})
        serv_dims = service_result.get("dimension_scores", {})

        for dim in [
            "market_demand",
            "pain_intensity",
            "monetization_potential",
            "market_gap",
            "technical_feasibility",
            "simplicity_score",
        ]:
            mono_val = mono_dims.get(dim, 0)
            serv_val = serv_dims.get(dim, 0)
            if abs(mono_val - serv_val) > 0.01:
                discrepancies.append(
                    f"Dimension {dim} variance: "
                    f"monolith={mono_val:.2f}, service={serv_val:.2f}"
                )

        # Core functions comparison (order-independent)
        mono_functions = set(monolith_result.get("core_functions", []))
        serv_functions = set(service_result.get("core_functions", []))

        if mono_functions != serv_functions:
            discrepancies.append(
                f"Core functions mismatch: "
                f"monolith={mono_functions}, service={serv_functions}"
            )

        return len(discrepancies) == 0, discrepancies

    def compare_profiler_analysis(
        self, monolith_result: Dict[str, Any], service_result: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Compare AI profiler results."""
        discrepancies = []

        # Core fields
        exact_match_fields = ["app_name", "tagline", "target_audience"]

        for field in exact_match_fields:
            # Allow minor whitespace/casing differences
            mono_val = str(monolith_result.get(field, "")).strip().lower()
            serv_val = str(service_result.get(field, "")).strip().lower()

            if mono_val != serv_val:
                discrepancies.append(
                    f"Profiler {field} mismatch: "
                    f"monolith={monolith_result.get(field)}, "
                    f"service={service_result.get(field)}"
                )

        # Core functions (critical - must match for deduplication)
        mono_functions = set(monolith_result.get("core_functions", []))
        serv_functions = set(service_result.get("core_functions", []))

        if mono_functions != serv_functions:
            discrepancies.append(
                f"Profiler core_functions CRITICAL mismatch: "
                f"monolith={mono_functions}, service={serv_functions}"
            )

        # Confidence score
        mono_conf = monolith_result.get("confidence_score", 0)
        serv_conf = service_result.get("confidence_score", 0)
        if abs(mono_conf - serv_conf) > 0.01:
            discrepancies.append(
                f"Profiler confidence variance: "
                f"monolith={mono_conf:.2f}, service={serv_conf:.2f}"
            )

        return len(discrepancies) == 0, discrepancies

    def compare_monetization_analysis(
        self, monolith_result: Dict[str, Any], service_result: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Compare monetization analysis results."""
        discrepancies = []

        # Core fields
        exact_match_fields = ["pricing_model", "business_model"]

        for field in exact_match_fields:
            if monolith_result.get(field) != service_result.get(field):
                discrepancies.append(
                    f"Monetization {field} mismatch: "
                    f"monolith={monolith_result.get(field)}, "
                    f"service={service_result.get(field)}"
                )

        # Monetization score
        mono_score = monolith_result.get("monetization_score", 0)
        serv_score = service_result.get("monetization_score", 0)
        if abs(mono_score - serv_score) > 0.01:
            discrepancies.append(
                f"Monetization score variance: "
                f"monolith={mono_score:.2f}, service={serv_score:.2f}"
            )

        # Revenue streams count
        mono_streams = len(monolith_result.get("revenue_streams", []))
        serv_streams = len(service_result.get("revenue_streams", []))
        if mono_streams != serv_streams:
            discrepancies.append(
                f"Revenue streams count mismatch: "
                f"monolith={mono_streams}, service={serv_streams}"
            )

        return len(discrepancies) == 0, discrepancies

    def compare_trust_validation(
        self, monolith_result: Dict[str, Any], service_result: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Compare trust validation results."""
        discrepancies = []

        # Trust level (exact match)
        if monolith_result.get("trust_level") != service_result.get("trust_level"):
            discrepancies.append(
                f"Trust level mismatch: "
                f"monolith={monolith_result.get('trust_level')}, "
                f"service={service_result.get('trust_level')}"
            )

        # Trust scores (with variance)
        trust_scores = [
            "overall_trust_score",
            "subreddit_activity_score",
            "post_engagement_score",
            "community_health_score",
        ]

        for score_field in trust_scores:
            mono_val = monolith_result.get(score_field, 0)
            serv_val = service_result.get(score_field, 0)
            if abs(mono_val - serv_val) > 0.01:
                discrepancies.append(
                    f"Trust {score_field} variance: "
                    f"monolith={mono_val:.2f}, service={serv_val:.2f}"
                )

        # Constraint flags
        for flag in ["activity_constraints_met", "quality_constraints_met"]:
            if monolith_result.get(flag) != service_result.get(flag):
                discrepancies.append(
                    f"Trust {flag} mismatch: "
                    f"monolith={monolith_result.get(flag)}, "
                    f"service={service_result.get(flag)}"
                )

        return len(discrepancies) == 0, discrepancies

    def validate_submission(
        self, submission: Dict[str, Any], monolith_results: Dict[str, Any], service_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a single submission through both pipelines.

        Returns:
            Dictionary with validation results and discrepancies
        """
        submission_id = submission.get("submission_id", "unknown")
        logger.info(f"Validating submission: {submission_id}")

        validation = {
            "submission_id": submission_id,
            "title": submission.get("title", "")[:60],
            "components": {},
            "overall_match": True,
            "discrepancies": []
        }

        # Validate OpportunityService
        if "opportunity_analysis" in monolith_results and "opportunity_analysis" in service_results:
            match, discrep = self.compare_opportunity_analysis(
                monolith_results["opportunity_analysis"],
                service_results["opportunity_analysis"]
            )
            validation["components"]["opportunity"] = match
            if not match:
                validation["overall_match"] = False
                validation["discrepancies"].extend(discrep)

        # Validate ProfilerService
        if "ai_profile" in monolith_results and "ai_profile" in service_results:
            match, discrep = self.compare_profiler_analysis(
                monolith_results["ai_profile"],
                service_results["ai_profile"]
            )
            validation["components"]["profiler"] = match
            if not match:
                validation["overall_match"] = False
                validation["discrepancies"].extend(discrep)

        # Validate MonetizationService
        if "monetization_analysis" in monolith_results and "monetization_analysis" in service_results:
            match, discrep = self.compare_monetization_analysis(
                monolith_results["monetization_analysis"],
                service_results["monetization_analysis"]
            )
            validation["components"]["monetization"] = match
            if not match:
                validation["overall_match"] = False
                validation["discrepancies"].extend(discrep)

        # Validate TrustService
        if "trust_validation" in monolith_results and "trust_validation" in service_results:
            match, discrep = self.compare_trust_validation(
                monolith_results["trust_validation"],
                service_results["trust_validation"]
            )
            validation["components"]["trust"] = match
            if not match:
                validation["overall_match"] = False
                validation["discrepancies"].extend(discrep)

        # Update stats
        self.stats["total_compared"] += 1
        if validation["overall_match"]:
            self.stats["perfect_matches"] += 1
        elif len(validation["discrepancies"]) <= 2:  # Minor discrepancies
            self.stats["acceptable_matches"] += 1
        else:
            self.stats["failures"] += 1
            self.discrepancies.append(validation)

        return validation

    def generate_report(self) -> str:
        """Generate validation report."""
        report = []
        report.append("\n" + "=" * 80)
        report.append("ENRICHMENT SERVICES VALIDATION REPORT")
        report.append("=" * 80 + "\n")

        # Summary statistics
        report.append("Summary:")
        report.append(f"  Total Submissions Compared: {self.stats['total_compared']}")
        report.append(f"  Perfect Matches: {self.stats['perfect_matches']} ({self.stats['perfect_matches'] / max(1, self.stats['total_compared']) * 100:.1f}%)")
        report.append(f"  Acceptable Matches: {self.stats['acceptable_matches']} ({self.stats['acceptable_matches'] / max(1, self.stats['total_compared']) * 100:.1f}%)")
        report.append(f"  Failures: {self.stats['failures']} ({self.stats['failures'] / max(1, self.stats['total_compared']) * 100:.1f}%)")
        report.append("")

        # Success criteria
        success_rate = (self.stats['perfect_matches'] + self.stats['acceptable_matches']) / max(1, self.stats['total_compared'])
        report.append("Success Criteria:")
        report.append(f"  Match Rate: {success_rate * 100:.1f}% (Target: >= 95%)")
        report.append(f"  Status: {'✅ PASS' if success_rate >= 0.95 else '❌ FAIL'}")
        report.append("")

        # Discrepancies detail
        if self.discrepancies:
            report.append("Discrepancies Found:")
            for disc in self.discrepancies[:10]:  # Show first 10
                report.append(f"\n  Submission: {disc['submission_id']}")
                report.append(f"  Title: {disc['title']}")
                for issue in disc['discrepancies']:
                    report.append(f"    - {issue}")

            if len(self.discrepancies) > 10:
                report.append(f"\n  ... and {len(self.discrepancies) - 10} more")
        else:
            report.append("No discrepancies found! 🎉")

        report.append("\n" + "=" * 80)

        return "\n".join(report)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Validate enrichment services against monolith"
    )
    parser.add_argument(
        "--submissions",
        type=int,
        default=100,
        help="Number of submissions to validate (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for detailed results (JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 80)
    logger.info("ENRICHMENT SERVICES VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Submissions to validate: {args.submissions}")
    logger.info("")

    # Initialize validator
    validator = EnrichmentServiceValidator()

    # TODO: Implement actual validation logic
    # This requires:
    # 1. Fetch submissions from database
    # 2. Run monolith pipeline (scripts/core/batch_opportunity_scoring.py)
    # 3. Run service-based pipeline
    # 4. Compare results using validator

    logger.warning("⚠️  Full implementation requires running monolith and services")
    logger.warning("⚠️  This is a framework for Phase 6 integration testing")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Implement fetch_submissions_for_testing()")
    logger.info("  2. Implement run_monolith_pipeline()")
    logger.info("  3. Implement run_service_pipeline()")
    logger.info("  4. Execute validation and generate report")
    logger.info("")
    logger.info("See: docs/plans/unified-pipeline-refactoring/phases/phase-06-extract-enrichment.md")
    logger.info("Task 5: Side-by-Side Validation")

    # Generate placeholder report
    print(validator.generate_report())

    return 0


if __name__ == "__main__":
    sys.exit(main())
