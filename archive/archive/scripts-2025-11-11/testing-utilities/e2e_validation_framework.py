#!/usr/bin/env python3
"""
RedditHarbor E2E Validation Framework
Implements validation checkpoints based on comprehensive testing guide findings
Provides quality assurance and performance monitoring for the E2E workflow
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class E2EValidationFramework:
    def __init__(self):
        self.validation_dir = Path("validation_results")
        self.validation_dir.mkdir(exist_ok=True)

        # Validation thresholds based on testing guide findings
        self.validation_thresholds = {
            "pipeline_performance": {
                "max_total_duration_minutes": 60,
                "max_dlt_duration_minutes": 30,
                "max_ai_profiling_duration_minutes": 40,
                "max_report_generation_duration_minutes": 10
            },
            "data_quality": {
                "min_ai_profiles_threshold": 3,
                "min_reddit_posts_threshold": 50,
                "min_avg_opportunity_score": 25.0,
                "max_function_count_violations": 0,
                "required_evidence_strength": 15.0
            },
            "configuration_compliance": {
                "required_min_activity_score": 35.0,
                "required_min_opportunity_score": 25.0,
                "required_time_filter": "week",
                "target_subreddit_count": 8
            },
            "production_readiness": {
                "success_rate_threshold": 80.0,
                "data_freshness_hours": 24,
                "database_connectivity_required": True,
                "api_response_time_seconds": 5
            }
        }

        self.validation_history = []
        self.test_results = {}

    def validate_pipeline_performance(self, pipeline_logs: Dict) -> Dict:
        """Validate pipeline performance against testing guide benchmarks"""
        print("🔍 VALIDATING: Pipeline Performance")

        performance_results = {
            "category": "pipeline_performance",
            "passed": True,
            "checks": []
        }

        # Check total pipeline duration
        total_duration = pipeline_logs.get("total_duration_minutes", 0)
        max_duration = self.validation_thresholds["pipeline_performance"]["max_total_duration_minutes"]

        if total_duration <= max_duration:
            performance_results["checks"].append({
                "check": "total_pipeline_duration",
                "status": "PASSED",
                "message": f"Total duration {total_duration:.1f}min ≤ {max_duration}min threshold",
                "value": total_duration,
                "threshold": max_duration
            })
        else:
            performance_results["passed"] = False
            performance_results["checks"].append({
                "check": "total_pipeline_duration",
                "status": "FAILED",
                "message": f"Total duration {total_duration:.1f}min > {max_duration}min threshold",
                "value": total_duration,
                "threshold": max_duration
            })

        # Check phase-specific durations if available
        phase_durations = pipeline_logs.get("phase_durations", {})
        for phase, duration in phase_durations.items():
            max_phase_duration = self.validation_thresholds["pipeline_performance"].get(f"max_{phase}_duration_minutes", float('inf'))

            if duration <= max_phase_duration:
                performance_results["checks"].append({
                    "check": f"{phase}_duration",
                    "status": "PASSED",
                    "message": f"{phase.title()} duration {duration:.1f}min ≤ {max_phase_duration}min",
                    "value": duration,
                    "threshold": max_phase_duration
                })
            else:
                performance_results["passed"] = False
                performance_results["checks"].append({
                    "check": f"{phase}_duration",
                    "status": "FAILED",
                    "message": f"{phase.title()} duration {duration:.1f}min > {max_phase_duration}min",
                    "value": duration,
                    "threshold": max_phase_duration
                })

        return performance_results

    def validate_data_quality(self, pipeline_summary: Dict) -> Dict:
        """Validate data quality against testing guide requirements"""
        print("🔍 VALIDATING: Data Quality")

        quality_results = {
            "category": "data_quality",
            "passed": True,
            "checks": []
        }

        thresholds = self.validation_thresholds["data_quality"]

        # Check AI profiles count
        ai_profiles_count = pipeline_summary.get("ai_profiles_count", 0)
        min_profiles = thresholds["min_ai_profiles_threshold"]

        if ai_profiles_count >= min_profiles:
            quality_results["checks"].append({
                "check": "ai_profiles_count",
                "status": "PASSED",
                "message": f"{ai_profiles_count} AI profiles ≥ {min_profiles} threshold",
                "value": ai_profiles_count,
                "threshold": min_profiles
            })
        else:
            quality_results["passed"] = False
            quality_results["checks"].append({
                "check": "ai_profiles_count",
                "status": "FAILED",
                "message": f"{ai_profiles_count} AI profiles < {min_profiles} threshold",
                "value": ai_profiles_count,
                "threshold": min_profiles
            })

        # Check Reddit posts count
        reddit_count = pipeline_summary.get("reddit_submissions_count", 0)
        min_posts = thresholds["min_reddit_posts_threshold"]

        if reddit_count >= min_posts:
            quality_results["checks"].append({
                "check": "reddit_submissions_count",
                "status": "PASSED",
                "message": f"{reddit_count:,} Reddit posts ≥ {min_posts:,} threshold",
                "value": reddit_count,
                "threshold": min_posts
            })
        else:
            quality_results["passed"] = False
            quality_results["checks"].append({
                "check": "reddit_submissions_count",
                "status": "FAILED",
                "message": f"{reddit_count:,} Reddit posts < {min_posts:,} threshold",
                "value": reddit_count,
                "threshold": min_posts
            })

        # Validate function count compliance (critical for production)
        if "function_count_analysis" in pipeline_summary:
            func_analysis = pipeline_summary["function_count_analysis"]
            violations = func_analysis.get("violations_count", 0)
            max_violations = thresholds["max_function_count_violations"]

            if violations <= max_violations:
                quality_results["checks"].append({
                    "check": "function_count_compliance",
                    "status": "PASSED",
                    "message": f"{violations} function count violations ≤ {max_violations} threshold",
                    "value": violations,
                    "threshold": max_violations
                })
            else:
                quality_results["passed"] = False
                quality_results["checks"].append({
                    "check": "function_count_compliance",
                    "status": "FAILED",
                    "message": f"{violations} function count violations > {max_violations} threshold",
                    "value": violations,
                    "threshold": max_violations
                })

        # Check evidence strength
        avg_evidence_strength = pipeline_summary.get("avg_evidence_strength", 0)
        min_evidence = thresholds["required_evidence_strength"]

        if avg_evidence_strength >= min_evidence:
            quality_results["checks"].append({
                "check": "evidence_strength",
                "status": "PASSED",
                "message": f"Evidence strength {avg_evidence_strength:.1f} ≥ {min_evidence:.1f} threshold",
                "value": avg_evidence_strength,
                "threshold": min_evidence
            })
        else:
            quality_results["checks"].append({
                "check": "evidence_strength",
                "status": "WARNING",
                "message": f"Evidence strength {avg_evidence_strength:.1f} < {min_evidence:.1f} threshold",
                "value": avg_evidence_strength,
                "threshold": min_evidence
            })

        return quality_results

    def validate_configuration_compliance(self, config_used: Dict) -> Dict:
        """Validate that pipeline uses production-validated sweet spot configuration"""
        print("🔍 VALIDATING: Configuration Compliance")

        compliance_results = {
            "category": "configuration_compliance",
            "passed": True,
            "checks": []
        }

        thresholds = self.validation_thresholds["configuration_compliance"]

        # Check activity score configuration
        activity_score = config_used.get("min_activity_score", 0)
        required_activity = thresholds["required_min_activity_score"]

        if activity_score == required_activity:
            compliance_results["checks"].append({
                "check": "activity_score_configuration",
                "status": "PASSED",
                "message": f"Activity score {activity_score} matches validated configuration",
                "value": activity_score,
                "threshold": required_activity
            })
        else:
            compliance_results["passed"] = False
            compliance_results["checks"].append({
                "check": "activity_score_configuration",
                "status": "FAILED",
                "message": f"Activity score {activity_score} != validated {required_activity}",
                "value": activity_score,
                "threshold": required_activity
            })

        # Check opportunity score configuration
        opportunity_score = config_used.get("min_opportunity_score", 0)
        required_opportunity = thresholds["required_min_opportunity_score"]

        if opportunity_score == required_opportunity:
            compliance_results["checks"].append({
                "check": "opportunity_score_configuration",
                "status": "PASSED",
                "message": f"Opportunity score {opportunity_score} matches validated configuration",
                "value": opportunity_score,
                "threshold": required_opportunity
            })
        else:
            compliance_results["passed"] = False
            compliance_results["checks"].append({
                "check": "opportunity_score_configuration",
                "status": "FAILED",
                "message": f"Opportunity score {opportunity_score} != validated {required_opportunity}",
                "value": opportunity_score,
                "threshold": required_opportunity
            })

        # Check time filter
        time_filter = config_used.get("time_filter", "")
        required_filter = thresholds["required_time_filter"]

        if time_filter == required_filter:
            compliance_results["checks"].append({
                "check": "time_filter_configuration",
                "status": "PASSED",
                "message": f"Time filter '{time_filter}' matches validated configuration",
                "value": time_filter,
                "threshold": required_filter
            })
        else:
            compliance_results["passed"] = False
            compliance_results["checks"].append({
                "check": "time_filter_configuration",
                "status": "FAILED",
                "message": f"Time filter '{time_filter}' != validated '{required_filter}'",
                "value": time_filter,
                "threshold": required_filter
            })

        # Check target subreddit count
        target_subreddits = config_used.get("target_subreddits", [])
        required_count = thresholds["target_subreddit_count"]

        if len(target_subreddits) == required_count:
            compliance_results["checks"].append({
                "check": "subreddit_count_configuration",
                "status": "PASSED",
                "message": f"{len(target_subreddits)} target subreddits matches validated configuration",
                "value": len(target_subreddits),
                "threshold": required_count
            })
        else:
            compliance_results["checks"].append({
                "check": "subreddit_count_configuration",
                "status": "WARNING",
                "message": f"{len(target_subreddits)} target subreddits != validated {required_count}",
                "value": len(target_subreddits),
                "threshold": required_count
            })

        return compliance_results

    def validate_production_readiness(self, system_metrics: Dict) -> Dict:
        """Validate production readiness based on comprehensive criteria"""
        print("🔍 VALIDATING: Production Readiness")

        readiness_results = {
            "category": "production_readiness",
            "passed": True,
            "checks": []
        }

        thresholds = self.validation_thresholds["production_readiness"]

        # Check database connectivity
        if system_metrics.get("database_connected", False):
            readiness_results["checks"].append({
                "check": "database_connectivity",
                "status": "PASSED",
                "message": "Database connectivity verified"
            })
        else:
            readiness_results["passed"] = False
            readiness_results["checks"].append({
                "check": "database_connectivity",
                "status": "FAILED",
                "message": "Database connectivity failed"
            })

        # Check data freshness
        last_update = system_metrics.get("last_data_update")
        if last_update:
            last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            freshness_hours = (datetime.now(last_update_time.tzinfo) - last_update_time).total_seconds() / 3600
            max_freshness = thresholds["data_freshness_hours"]

            if freshness_hours <= max_freshness:
                readiness_results["checks"].append({
                    "check": "data_freshness",
                    "status": "PASSED",
                    "message": f"Data freshness {freshness_hours:.1f}h ≤ {max_freshness}h threshold",
                    "value": freshness_hours,
                    "threshold": max_freshness
                })
            else:
                readiness_results["checks"].append({
                    "check": "data_freshness",
                    "status": "WARNING",
                    "message": f"Data freshness {freshness_hours:.1f}h > {max_freshness}h threshold",
                    "value": freshness_hours,
                    "threshold": max_freshness
                })

        # Check historical success rate
        if len(self.validation_history) >= 5:  # Need at least 5 previous runs
            recent_success_rate = self.calculate_recent_success_rate()
            min_success_rate = thresholds["success_rate_threshold"]

            if recent_success_rate >= min_success_rate:
                readiness_results["checks"].append({
                    "check": "historical_success_rate",
                    "status": "PASSED",
                    "message": f"Recent success rate {recent_success_rate:.1f}% ≥ {min_success_rate:.1f}% threshold",
                    "value": recent_success_rate,
                    "threshold": min_success_rate
                })
            else:
                readiness_results["passed"] = False
                readiness_results["checks"].append({
                    "check": "historical_success_rate",
                    "status": "FAILED",
                    "message": f"Recent success rate {recent_success_rate:.1f}% < {min_success_rate:.1f}% threshold",
                    "value": recent_success_rate,
                    "threshold": min_success_rate
                })

        return readiness_results

    def calculate_recent_success_rate(self, window_size: int = 10) -> float:
        """Calculate success rate for recent validation runs"""
        recent_validations = self.validation_history[-window_size:]
        if not recent_validations:
            return 0.0

        successful_runs = sum(1 for v in recent_validations if v.get("overall_passed", False))
        return (successful_runs / len(recent_validations)) * 100

    def run_comprehensive_validation(self, pipeline_logs: Dict, pipeline_summary: Dict, system_metrics: Dict) -> Dict:
        """Run all validation categories and return comprehensive results"""
        print("🧪 RUNNING COMPREHENSIVE E2E VALIDATION")
        print("=" * 60)

        validation_start = datetime.now()

        # Run all validation categories
        performance_results = self.validate_pipeline_performance(pipeline_logs)
        quality_results = self.validate_data_quality(pipeline_summary)
        compliance_results = self.validate_configuration_compliance(pipeline_summary.get("configuration_used", {}))
        readiness_results = self.validate_production_readiness(system_metrics)

        # Compile comprehensive results
        comprehensive_results = {
            "validation_timestamp": validation_start.isoformat(),
            "validation_duration_minutes": (datetime.now() - validation_start).total_seconds() / 60,
            "overall_passed": all([
                performance_results["passed"],
                quality_results["passed"],
                compliance_results["passed"],
                readiness_results["passed"]
            ]),
            "validation_categories": {
                "pipeline_performance": performance_results,
                "data_quality": quality_results,
                "configuration_compliance": compliance_results,
                "production_readiness": readiness_results
            },
            "summary": {
                "total_checks": sum(len(cat["checks"]) for cat in [
                    performance_results, quality_results, compliance_results, readiness_results
                ]),
                "passed_checks": sum(
                    1 for cat in [performance_results, quality_results, compliance_results, readiness_results]
                    for check in cat["checks"]
                    if check["status"] == "PASSED"
                ),
                "failed_checks": sum(
                    1 for cat in [performance_results, quality_results, compliance_results, readiness_results]
                    for check in cat["checks"]
                    if check["status"] == "FAILED"
                ),
                "warning_checks": sum(
                    1 for cat in [performance_results, quality_results, compliance_results, readiness_results]
                    for check in cat["checks"]
                    if check["status"] == "WARNING"
                )
            }
        }

        # Add to validation history
        self.validation_history.append(comprehensive_results)

        # Save validation results
        self.save_validation_results(comprehensive_results)

        # Display results summary
        self.display_validation_summary(comprehensive_results)

        return comprehensive_results

    def save_validation_results(self, results: Dict):
        """Save validation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_results_{timestamp}.json"
        filepath = self.validation_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📁 Validation results saved: {filepath}")
        except Exception as e:
            print(f"❌ Error saving validation results: {e}")

    def display_validation_summary(self, results: Dict):
        """Display validation results summary"""
        print("\n📊 VALIDATION RESULTS SUMMARY")
        print("=" * 50)

        # Overall status
        status_emoji = "✅" if results["overall_passed"] else "❌"
        print(f"{status_emoji} Overall Status: {'PASSED' if results['overall_passed'] else 'FAILED'}")

        # Summary stats
        summary = results["summary"]
        print(f"📋 Total Checks: {summary['total_checks']}")
        print(f"✅ Passed: {summary['passed_checks']}")
        print(f"⚠️ Warnings: {summary['warning_checks']}")
        print(f"❌ Failed: {summary['failed_checks']}")

        # Category breakdown
        print(f"\n📈 Category Results:")
        for category_name, category_results in results["validation_categories"].items():
            status_emoji = "✅" if category_results["passed"] else "❌"
            print(f"{status_emoji} {category_name.replace('_', ' ').title()}: {'PASSED' if category_results['passed'] else 'FAILED'}")

        # Failed checks detail
        failed_checks = [
            check for cat in results["validation_categories"].values()
            for check in cat["checks"]
            if check["status"] == "FAILED"
        ]

        if failed_checks:
            print(f"\n❌ Failed Checks:")
            for check in failed_checks:
                print(f"   • {check['message']}")

        # Warning checks detail
        warning_checks = [
            check for cat in results["validation_categories"].values()
            for check in cat["checks"]
            if check["status"] == "WARNING"
        ]

        if warning_checks:
            print(f"\n⚠️ Warning Checks:")
            for check in warning_checks:
                print(f"   • {check['message']}")

        print(f"\n⏱️ Validation completed in {results['validation_duration_minutes']:.2f} minutes")

    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report for management"""
        if not self.validation_history:
            return "No validation history available"

        # Calculate metrics from validation history
        total_validations = len(self.validation_history)
        successful_validations = sum(1 for v in self.validation_history if v["overall_passed"])
        overall_success_rate = (successful_validations / total_validations) * 100

        # Recent performance (last 10 validations)
        recent_validations = self.validation_history[-10:]
        recent_success_rate = sum(1 for v in recent_validations if v["overall_passed"]) / len(recent_validations) * 100

        # Category performance
        category_performance = {}
        for category in ["pipeline_performance", "data_quality", "configuration_compliance", "production_readiness"]:
            category_successes = sum(
                1 for v in self.validation_history
                if v["validation_categories"][category]["passed"]
            )
            category_performance[category] = (category_successes / total_validations) * 100

        report_lines = [
            "# 🧪 REDDITHARBOR E2E VALIDATION REPORT",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Period:** {total_validations} validation runs",
            "",
            "## 📊 OVERALL PERFORMANCE",
            "",
            f"**Total Success Rate:** {overall_success_rate:.1f}% ({successful_validations}/{total_validations})",
            f"**Recent Success Rate:** {recent_success_rate:.1f}% (last 10 runs)",
            f"**Production Readiness:** {'✅ PRODUCTION READY' if recent_success_rate >= 80 else '⚠️ NEEDS ATTENTION'}",
            "",
            "## 📈 CATEGORY PERFORMANCE",
            "",
            "| Category | Success Rate | Status |",
            "|----------|--------------|--------|"
        ]

        for category, success_rate in category_performance.items():
            status = "✅ GOOD" if success_rate >= 90 else "⚠️ MONITOR" if success_rate >= 70 else "❌ ISSUE"
            category_name = category.replace('_', ' ').title()
            report_lines.append(f"| {category_name} | {success_rate:.1f}% | {status} |")

        # Recent validation details
        report_lines.extend([
            "",
            "## 🕐 RECENT VALIDATIONS",
            ""
        ])

        for validation in recent_validations[-5:]:
            timestamp = validation["validation_timestamp"]
            passed = validation["overall_passed"]
            total_checks = validation["summary"]["total_checks"]
            passed_checks = validation["summary"]["passed_checks"]

            status_emoji = "✅" if passed else "❌"
            report_lines.append(f"**{timestamp}** {status_emoji} {passed_checks}/{total_checks} checks passed")

        report_lines.extend([
            "",
            "## 🎯 RECOMMENDATIONS",
            ""
        ])

        if recent_success_rate >= 90:
            report_lines.append("- ✅ **Excellent Performance**: System is performing at production level")
            report_lines.append("- 🚀 **Ready for Scaling**: Consider increasing automation frequency")
        elif recent_success_rate >= 70:
            report_lines.append("- ⚠️ **Monitor Performance**: System is functional but needs attention")
            report_lines.append("- 🔍 **Investigate Failures**: Review failed checks for patterns")
        else:
            report_lines.append("- 🚨 **Immediate Action Required**: Success rate below acceptable threshold")
            report_lines.append("- 🛑 **Pause Automation**: Consider pausing scheduled runs until issues resolved")

        report_lines.extend([
            "",
            "---",
            "",
            f"*Report generated by RedditHarbor E2E Validation Framework*",
            f"*Last validation: {self.validation_history[-1]['validation_timestamp'] if self.validation_history else 'N/A'}*"
        ])

        return "\n".join(report_lines)

def main():
    """Main execution for standalone validation"""
    parser = argparse.ArgumentParser(description='RedditHarbor E2E Validation Framework')
    parser.add_argument('--generate-report', action='store_true', help='Generate management report')
    parser.add_argument('--check-history', action='store_true', help='Show validation history summary')

    args = parser.parse_args()

    try:
        validator = E2EValidationFramework()

        if args.generate_report:
            report = validator.generate_validation_report()
            print(report)

            # Save report
            report_file = Path("validation_results") / f"management_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\n📁 Report saved: {report_file}")
            return

        if args.check_history:
            if not validator.validation_history:
                print("📝 No validation history available")
                return

            total_validations = len(validator.validation_history)
            recent_success_rate = validator.calculate_recent_success_rate()

            print(f"📚 VALIDATION HISTORY SUMMARY")
            print(f"Total Validations: {total_validations}")
            print(f"Recent Success Rate: {recent_success_rate:.1f}% (last 10 runs)")
            print(f"Overall Success Rate: {(sum(1 for v in validator.validation_history if v['overall_passed']) / total_validations) * 100:.1f}%")
            return

        print("🧪 RedditHarbor E2E Validation Framework")
        print("Use --generate-report for management reports")
        print("Use --check-history for validation history")

    except Exception as e:
        print(f"❌ Validation framework error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()