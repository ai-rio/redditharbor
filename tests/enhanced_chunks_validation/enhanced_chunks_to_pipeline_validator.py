#!/usr/bin/env python3
"""
Enhanced Chunks to DLT Pipeline Validation Framework

This script provides rigorous, evidence-based validation that maps the enhanced chunks
documentation requirements to the actual DLT trust pipeline implementation.

CRITICAL SUCCESS CRITERIA (Based on Enhanced Chunks Documentation):
1. Activity Constraint Enforcement: DLT_MIN_ACTIVITY_SCORE must be properly applied
2. Realistic Score Distribution: 70+ scores should be rare (1-3% occurrence)
3. Pre-AI Filtering: Must avoid expensive LLM calls on low-quality data
4. Cost Optimization: 90%+ cost reduction through pre-filtering
5. Trust Layer Separation: Trust validation is customer-facing ONLY, not filtering
6. Performance Targets: <10s processing time per post
7. Zero Pipeline Failures: All stages must complete successfully

EVIDENCE REQUIREMENTS:
- Concrete database queries showing actual vs expected distributions
- Pipeline metrics demonstrating cost savings
- Pass/fail criteria with measurable thresholds
- A/B test results comparing constrained vs unconstrained performance

Based on enhanced chunks documentation:
- Chunk 3: DLT Activity Validation System requirements
- Chunk 8: Activity Constraint A/B Test findings (20-100x yield difference)
- Archive: Working pre-filtering implementation that was bypassed
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import RedditHarbor components
from config.settings import DLT_MIN_ACTIVITY_SCORE, SUPABASE_KEY, SUPABASE_URL
from core.dlt_collection import collect_problem_posts
from supabase import create_client

# Configure logging with detailed evidence tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - EVIDENCE: %(message)s',
    handlers=[
        logging.FileHandler(f'pipeline_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineEvidenceValidator:
    """
    Evidence-based pipeline validator that maps enhanced chunks requirements
    to actual DLT trust pipeline performance.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.start_time = time.time()
        self.evidence_log = []

        # CRITICAL SUCCESS THRESHOLDS (from enhanced chunks documentation)
        self.CRITICAL_THRESHOLDS = {
            'max_high_score_rate': 3.0,  # % of posts scoring 70+ (should be rare)
            'min_cost_savings': 90.0,    # % cost reduction from pre-filtering
            'max_processing_time': 10.0, # seconds per post
            'min_activity_enforcement': 95.0,  # % of posts with activity validation
            'max_pipeline_failure_rate': 0.0,  # % pipeline failures allowed
            'min_trust_separation': 100.0  # % trust scores independent of AI scores
        }

        self.validation_results = {
            'evidence_summary': {},
            'critical_failures': [],
            'cost_analysis': {},
            'performance_metrics': {},
            'compliance_score': 0.0,
            'production_ready': False,
            'evidence_log': self.evidence_log
        }

    def log_evidence(self, category: str, finding: str, metric_value: float = None, pass_fail: bool = None):
        """Log concrete evidence for validation"""
        evidence_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'finding': finding,
            'metric_value': metric_value,
            'pass_fail': pass_fail,
            'evidence_type': 'measurable'
        }
        self.evidence_log.append(evidence_entry)

        # Log to console with evidence marker
        status = "✅ PASS" if pass_fail else "❌ FAIL" if pass_fail is False else "📊 INFO"
        metric_str = f" (Value: {metric_value})" if metric_value is not None else ""
        logger.info(f"{status} - {category}: {finding}{metric_str}")

    def validate_activity_constraint_enforcement(self) -> tuple[bool, dict]:
        """
        CRITICAL VALIDATION: Activity constraints must be properly enforced
        Evidence from enhanced chunks shows this was bypassed causing 20-100x yield inflation
        """
        logger.info("🔍 CRITICAL VALIDATION: Activity Constraint Enforcement")

        try:
            # Check current DLT configuration
            configured_threshold = DLT_MIN_ACTIVITY_SCORE
            self.log_evidence("Configuration", f"DLT_MIN_ACTIVITY_SCORE set to {configured_threshold}",
                            configured_threshold, configured_threshold >= 25.0)

            # Test actual DLT collection to verify activity validation
            test_posts = collect_problem_posts(
                subreddits=["test", "lowactivity"],  # Test with potentially low-activity subreddits
                limit=5,
                test_mode=False
            )

            # Verify activity scores are being calculated and applied
            activity_scores = []
            posts_with_validation = []

            for post in test_posts:
                # Check if post has activity validation
                if 'activity_score' in post or 'dlt_activity_validated' in post:
                    activity_score = post.get('activity_score', 0)
                    activity_scores.append(activity_score)
                    posts_with_validation.append(post)
                    self.log_evidence("Activity Validation",
                                    f"Post activity score: {activity_score}",
                                    activity_score, activity_score >= configured_threshold)
                else:
                    self.log_evidence("Activity Validation",
                                    "Post missing activity validation data",
                                    None, False)

            # Calculate enforcement rate
            enforcement_rate = len(posts_with_validation) / len(test_posts) * 100 if test_posts else 0
            target_enforcement = self.CRITICAL_THRESHOLDS['min_activity_enforcement']

            activity_enforced = enforcement_rate >= target_enforcement
            self.log_evidence("Activity Constraint Enforcement",
                            f"Enforcement rate: {enforcement_rate:.1f}% (target: ≥{target_enforcement}%)",
                            enforcement_rate, activity_enforced)

            result = {
                'configured_threshold': configured_threshold,
                'posts_tested': len(test_posts),
                'posts_with_validation': len(posts_with_validation),
                'enforcement_rate': enforcement_rate,
                'activity_scores': activity_scores,
                'critical_pass': activity_enforced
            }

            if not activity_enforced:
                self.validation_results['critical_failures'].append(
                    f"Activity constraint enforcement: {enforcement_rate:.1f}% < {target_enforcement}%"
                )

            return activity_enforced, result

        except Exception as e:
            self.log_evidence("Activity Constraint Enforcement", f"Validation failed: {e}", None, False)
            self.validation_results['critical_failures'].append(f"Activity constraint validation error: {e}")
            return False, {'error': str(e)}

    def validate_realistic_score_distribution(self) -> tuple[bool, dict]:
        """
        CRITICAL VALIDATION: Score distribution must match documented expectations
        Enhanced chunks shows 70+ scores should be rare (1-3%), but we were getting 20-100x more
        """
        logger.info("🔍 CRITICAL VALIDATION: Realistic Score Distribution")

        try:
            # Connect to database to get actual AI scores
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Get recent opportunity scores from database
            response = supabase.table('app_opportunities').select('opportunity_score').execute()

            if not response.data:
                self.log_evidence("Score Distribution", "No opportunity scores found in database", None, False)
                return False, {'error': 'No data available'}

            scores = [item['opportunity_score'] for item in response.data if item.get('opportunity_score')]

            if not scores:
                self.log_evidence("Score Distribution", "No valid opportunity scores in database", None, False)
                return False, {'error': 'No valid scores'}

            # Calculate score distribution
            total_scores = len(scores)
            high_scores_70_plus = len([s for s in scores if s >= 70])
            high_scores_65_plus = len([s for s in scores if s >= 65])
            high_scores_60_plus = len([s for s in scores if s >= 60])

            # Calculate percentages
            high_score_rate_70 = (high_scores_70_plus / total_scores) * 100
            high_score_rate_65 = (high_scores_65_plus / total_scores) * 100
            high_score_rate_60 = (high_scores_60_plus / total_scores) * 100

            # CRITICAL: Enhanced chunks documentation expects 70+ scores to be rare (1-3%)
            max_high_score_rate = self.CRITICAL_THRESHOLDS['max_high_score_rate']
            distribution_realistic = high_score_rate_70 <= max_high_score_rate

            self.log_evidence("Score Distribution (70+)",
                            f"{high_scores_70_plus}/{total_scores} posts ({high_score_rate_70:.1f}%)",
                            high_score_rate_70, distribution_realistic)

            self.log_evidence("Score Distribution (65+)",
                            f"{high_scores_65_plus}/{total_scores} posts ({high_score_rate_65:.1f}%)",
                            high_score_rate_65, high_score_rate_65 <= 10.0)  # More lenient for 65+

            self.log_evidence("Score Distribution (60+)",
                            f"{high_scores_60_plus}/{total_scores} posts ({high_score_rate_60:.1f}%)",
                            high_score_rate_60, high_score_rate_60 <= 15.0)  # More lenient for 60+

            # Additional distribution analysis
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            self.log_evidence("Score Statistics",
                            f"Average: {avg_score:.1f}, Range: {min_score:.1f}-{max_score:.1f}",
                            avg_score, True)

            result = {
                'total_scores': total_scores,
                'high_scores_70_plus': high_scores_70_plus,
                'high_scores_65_plus': high_scores_65_plus,
                'high_scores_60_plus': high_scores_60_plus,
                'high_score_rate_70': high_score_rate_70,
                'high_score_rate_65': high_score_rate_65,
                'high_score_rate_60': high_score_rate_60,
                'average_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'distribution_realistic': distribution_realistic,
                'critical_pass': distribution_realistic
            }

            if not distribution_realistic:
                self.validation_results['critical_failures'].append(
                    f"Score distribution unrealistic: {high_score_rate_70:.1f}% > {max_high_score_rate}%"
                )

            return distribution_realistic, result

        except Exception as e:
            self.log_evidence("Score Distribution", f"Analysis failed: {e}", None, False)
            self.validation_results['critical_failures'].append(f"Score distribution error: {e}")
            return False, {'error': str(e)}

    def validate_cost_optimization(self) -> tuple[bool, dict]:
        """
        CRITICAL VALIDATION: Pre-AI filtering must achieve significant cost savings
        Enhanced chunks evidence shows pre-filtering was bypassed causing massive costs
        """
        logger.info("🔍 CRITICAL VALIDATION: Cost Optimization Through Pre-Filtering")

        try:
            # Import and test the actual DLT trust pipeline
            from scripts.dlt.dlt_trust_pipeline import (
                MIN_COMMENT_COUNT,
                MIN_ENGAGEMENT_SCORE,
                MIN_PROBLEM_KEYWORDS,
                should_analyze_with_ai,
            )

            self.log_evidence("Cost Configuration",
                            f"Pre-filter thresholds: Engagement≥{MIN_ENGAGEMENT_SCORE}, Comments≥{MIN_COMMENT_COUNT}, Keywords≥{MIN_PROBLEM_KEYWORDS}",
                            None, True)

            # Get sample posts from database to test filtering efficiency
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table('submissions').select('title, upvotes, num_comments, content').limit(100).execute()

            if not response.data:
                self.log_evidence("Cost Optimization", "No posts available for filtering test", None, False)
                return False, {'error': 'No data available'}

            posts = response.data
            total_posts = len(posts)
            filtered_posts = 0
            ai_calls_needed = 0

            # Test pre-filtering on actual data
            for post in posts:
                # Create post dict in expected format
                post_data = {
                    'title': post.get('title', ''),
                    'text': post.get('content', ''),
                    'upvotes': post.get('upvotes', 0),
                    'comments_count': post.get('num_comments', 0)
                }

                if should_analyze_with_ai(post_data):
                    ai_calls_needed += 1
                else:
                    filtered_posts += 1

            # Calculate cost savings
            filtering_rate = (filtered_posts / total_posts) * 100
            ai_call_rate = (ai_calls_needed / total_posts) * 100
            cost_savings = filtering_rate  # Each filtered post saves one LLM call

            target_savings = self.CRITICAL_THRESHOLDS['min_cost_savings']
            cost_optimized = cost_savings >= target_savings

            self.log_evidence("Cost Optimization",
                            f"Posts filtered: {filtered_posts}/{total_posts} ({filtering_rate:.1f}%)",
                            filtering_rate, True)

            self.log_evidence("Cost Optimization",
                            f"AI calls needed: {ai_calls_needed}/{total_posts} ({ai_call_rate:.1f}%)",
                            ai_call_rate, True)

            self.log_evidence("Cost Savings",
                            f"Cost savings: {cost_savings:.1f}% (target: ≥{target_savings}%)",
                            cost_savings, cost_optimized)

            # Calculate estimated cost savings
            estimated_cost_per_call = 0.05  # Conservative estimate
            monthly_posts = 3000  # Estimated monthly volume
            estimated_monthly_savings = (filtered_posts / total_posts) * monthly_posts * estimated_cost_per_call

            self.log_evidence("Cost Projection",
                            f"Estimated monthly savings: ${estimated_monthly_savings:.2f}",
                            estimated_monthly_savings, True)

            result = {
                'posts_tested': total_posts,
                'posts_filtered': filtered_posts,
                'ai_calls_needed': ai_calls_needed,
                'filtering_rate': filtering_rate,
                'ai_call_rate': ai_call_rate,
                'cost_savings_percent': cost_savings,
                'estimated_monthly_savings': estimated_monthly_savings,
                'target_savings': target_savings,
                'cost_optimized': cost_optimized,
                'critical_pass': cost_optimized
            }

            if not cost_optimized:
                self.validation_results['critical_failures'].append(
                    f"Cost optimization insufficient: {cost_savings:.1f}% < {target_savings}%"
                )

            return cost_optimized, result

        except Exception as e:
            self.log_evidence("Cost Optimization", f"Validation failed: {e}", None, False)
            self.validation_results['critical_failures'].append(f"Cost optimization error: {e}")
            return False, {'error': str(e)}

    def validate_trust_layer_separation(self) -> tuple[bool, dict]:
        """
        CRITICAL VALIDATION: Trust layer must be customer-facing ONLY, not filtering criteria
        Enhanced chunks clarification: trust layer provides social proof, not acceptance decisions
        """
        logger.info("🔍 CRITICAL VALIDATION: Trust Layer Separation")

        try:
            # Get data with both AI scores and trust scores
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Query posts with both scoring systems
            response = supabase.table('app_opportunities').select('opportunity_score, trust_score, trust_level').execute()

            if not response.data:
                self.log_evidence("Trust Layer Separation", "No combined score data available", None, False)
                return False, {'error': 'No data available'}

            scored_posts = [post for post in response.data if post.get('opportunity_score') and post.get('trust_score')]

            if len(scored_posts) < 10:
                self.log_evidence("Trust Layer Separation", f"Insufficient data points: {len(scored_posts)}", None, False)
                return False, {'error': 'Insufficient data'}

            # Analyze correlation between AI scores and trust scores
            high_ai_low_trust = 0
            low_ai_high_trust = 0
            independent_scores = 0

            for post in scored_posts:
                ai_score = post['opportunity_score']
                trust_score = post['trust_score']

                # Check for independence (trust layer shouldn't just mirror AI scores)
                if ai_score >= 70 and trust_score < 50:
                    high_ai_low_trust += 1
                elif ai_score < 50 and trust_score >= 70:
                    low_ai_high_trust += 1

                # Calculate score difference (independence indicator)
                score_diff = abs(ai_score - trust_score)
                if score_diff > 20:  # Significant difference indicates independence
                    independent_scores += 1

            total_scored = len(scored_posts)
            independence_rate = (independent_scores / total_scored) * 100
            target_independence = self.CRITICAL_THRESHOLDS['min_trust_separation']

            trust_separated = independence_rate >= target_independence

            self.log_evidence("Trust Independence",
                            f"Independent scores: {independent_scores}/{total_scored} ({independence_rate:.1f}%)",
                            independence_rate, trust_separated)

            self.log_evidence("Trust Analysis",
                            f"High AI/Low Trust: {high_ai_low_trust}, Low AI/High Trust: {low_ai_high_trust}",
                            None, True)

            # Verify trust scores aren't just mirroring AI scores
            correlation_independence = (high_ai_low_trust + low_ai_high_trust) > 0
            self.log_evidence("Trust Correlation",
                            f"Trust layer shows independent scoring: {correlation_independence}",
                            None, correlation_independence)

            result = {
                'total_scored_posts': total_scored,
                'independent_scores': independent_scores,
                'independence_rate': independence_rate,
                'high_ai_low_trust': high_ai_low_trust,
                'low_ai_high_trust': low_ai_high_trust,
                'trust_separated': trust_separated and correlation_independence,
                'correlation_independence': correlation_independence,
                'critical_pass': trust_separated and correlation_independence
            }

            if not (trust_separated and correlation_independence):
                self.validation_results['critical_failures'].append(
                    f"Trust layer not properly separated: {independence_rate:.1f}% < {target_independence}%"
                )

            return trust_separated and correlation_independence, result

        except Exception as e:
            self.log_evidence("Trust Layer Separation", f"Validation failed: {e}", None, False)
            self.validation_results['critical_failures'].append(f"Trust layer separation error: {e}")
            return False, {'error': str(e)}

    def validate_pipeline_performance(self) -> tuple[bool, dict]:
        """Validate pipeline meets performance targets"""
        logger.info("🔍 VALIDATION: Pipeline Performance")

        try:
            # Test actual DLT trust pipeline performance
            from scripts.dlt.dlt_trust_pipeline import (
                analyze_opportunities_with_ai,
                collect_posts_with_activity_validation,
            )

            # Small performance test
            test_start = time.time()

            # Test collection performance
            collection_start = time.time()
            posts = collect_posts_with_activity_validation(
                subreddits=["SaaS"],  # Single subreddit for focused test
                limit=5,
                test_mode=False
            )
            collection_time = time.time() - collection_start

            # Test AI analysis performance (if posts collected)
            analysis_time = 0
            if posts:
                analysis_start = time.time()
                analyzed_posts = analyze_opportunities_with_ai(posts, test_mode=True, score_threshold=40.0)
                analysis_time = time.time() - analysis_start

            total_test_time = time.time() - test_start
            total_posts_processed = len(posts)

            # Calculate performance metrics
            time_per_post = total_test_time / max(total_posts_processed, 1)
            target_time_per_post = self.CRITICAL_THRESHOLDS['max_processing_time']

            performance_acceptable = time_per_post <= target_time_per_post

            self.log_evidence("Performance",
                            f"Total time: {total_test_time:.2f}s for {total_posts_processed} posts",
                            None, True)

            self.log_evidence("Performance",
                            f"Time per post: {time_per_post:.2f}s (target: ≤{target_time_per_post}s)",
                            time_per_post, performance_acceptable)

            result = {
                'posts_processed': total_posts_processed,
                'total_time': total_test_time,
                'collection_time': collection_time,
                'analysis_time': analysis_time,
                'time_per_post': time_per_post,
                'target_time_per_post': target_time_per_post,
                'performance_acceptable': performance_acceptable,
                'critical_pass': performance_acceptable
            }

            if not performance_acceptable:
                self.validation_results['critical_failures'].append(
                    f"Performance target missed: {time_per_post:.2f}s > {target_time_per_post}s"
                )

            return performance_acceptable, result

        except Exception as e:
            self.log_evidence("Pipeline Performance", f"Performance test failed: {e}", None, False)
            self.validation_results['critical_failures'].append(f"Performance test error: {e}")
            return False, {'error': str(e)}

    def calculate_compliance_score(self) -> float:
        """Calculate overall compliance score based on all validations"""

        critical_validations = [
            self.validation_results.get('activity_constraint', {}).get('critical_pass', False),
            self.validation_results.get('score_distribution', {}).get('critical_pass', False),
            self.validation_results.get('cost_optimization', {}).get('critical_pass', False),
            self.validation_results.get('trust_separation', {}).get('critical_pass', False),
            self.validation_results.get('pipeline_performance', {}).get('critical_pass', False)
        ]

        passed_critical = sum(critical_validations)
        total_critical = len(critical_validations)

        # Critical validations have 80% weight
        critical_score = (passed_critical / total_critical) * 80 if total_critical > 0 else 0

        # Evidence quality has 20% weight (based on evidence log completeness)
        evidence_categories = len(set(e['category'] for e in self.evidence_log))
        evidence_quality = min(evidence_categories / 10.0 * 20, 20)  # Max 20 points

        compliance_score = critical_score + evidence_quality

        return compliance_score

    def run_comprehensive_validation(self) -> dict:
        """
        Run complete evidence-based validation of DLT trust pipeline
        against enhanced chunks documentation requirements
        """
        logger.info("🚀 STARTING COMPREHENSIVE EVIDENCE-BASED VALIDATION")
        logger.info("Mapping Enhanced Chunks Documentation → DLT Trust Pipeline")
        logger.info("=" * 80)

        validation_start = time.time()

        # CRITICAL VALIDATION 1: Activity Constraint Enforcement
        activity_pass, activity_result = self.validate_activity_constraint_enforcement()
        self.validation_results['activity_constraint'] = activity_result

        # CRITICAL VALIDATION 2: Realistic Score Distribution
        distribution_pass, distribution_result = self.validate_realistic_score_distribution()
        self.validation_results['score_distribution'] = distribution_result

        # CRITICAL VALIDATION 3: Cost Optimization
        cost_pass, cost_result = self.validate_cost_optimization()
        self.validation_results['cost_optimization'] = cost_result

        # CRITICAL VALIDATION 4: Trust Layer Separation
        trust_pass, trust_result = self.validate_trust_layer_separation()
        self.validation_results['trust_separation'] = trust_result

        # CRITICAL VALIDATION 5: Pipeline Performance
        performance_pass, performance_result = self.validate_pipeline_performance()
        self.validation_results['pipeline_performance'] = performance_result

        # Calculate compliance score
        compliance_score = self.calculate_compliance_score()
        self.validation_results['compliance_score'] = compliance_score

        # Determine production readiness
        all_critical_passed = all([
            activity_pass, distribution_pass, cost_pass, trust_pass, performance_pass
        ])

        production_ready = all_critical_passed and compliance_score >= 80.0
        self.validation_results['production_ready'] = production_ready

        # Calculate total validation time
        validation_time = time.time() - validation_start

        # Generate final report
        self.generate_evidence_report(validation_time)

        return self.validation_results

    def generate_evidence_report(self, validation_time: float):
        """Generate comprehensive evidence-based report"""

        logger.info("\n" + "=" * 80)
        logger.info("📋 EVIDENCE-BASED VALIDATION REPORT")
        logger.info("=" * 80)

        # Summary status
        production_ready = self.validation_results['production_ready']
        compliance_score = self.validation_results['compliance_score']

        if production_ready:
            logger.info("🎉 PRODUCTION READINESS: ✅ APPROVED")
        else:
            logger.info("❌ PRODUCTION READINESS: FAILED - CRITICAL ISSUES FOUND")

        logger.info(f"📊 COMPLIANCE SCORE: {compliance_score:.1f}/100")
        logger.info(f"⏱️  VALIDATION TIME: {validation_time:.2f}s")

        # Critical validation results
        logger.info("\n🔍 CRITICAL VALIDATION RESULTS:")

        validations = [
            ('Activity Constraint Enforcement', 'activity_constraint'),
            ('Realistic Score Distribution', 'score_distribution'),
            ('Cost Optimization', 'cost_optimization'),
            ('Trust Layer Separation', 'trust_separation'),
            ('Pipeline Performance', 'pipeline_performance')
        ]

        for validation_name, result_key in validations:
            result = self.validation_results.get(result_key, {})
            status = "✅ PASS" if result.get('critical_pass', False) else "❌ FAIL"
            logger.info(f"  {validation_name}: {status}")

        # Critical failures
        critical_failures = self.validation_results.get('critical_failures', [])
        if critical_failures:
            logger.info("\n🚨 CRITICAL FAILURES REQUIRING IMMEDIATE ATTENTION:")
            for failure in critical_failures:
                logger.info(f"  ❌ {failure}")

        # Evidence summary
        logger.info(f"\n📊 EVIDENCE COLLECTED: {len(self.evidence_log)} measurements")
        evidence_categories = set(e['category'] for e in self.evidence_log)
        logger.info(f"📋 EVIDENCE CATEGORIES: {len(evidence_categories)} different areas tested")

        # Cost analysis
        cost_result = self.validation_results.get('cost_optimization', {})
        if cost_result.get('estimated_monthly_savings'):
            logger.info(f"💰 ESTIMATED MONTHLY SAVINGS: ${cost_result['estimated_monthly_savings']:.2f}")

        # Performance summary
        perf_result = self.validation_results.get('pipeline_performance', {})
        if perf_result.get('time_per_post'):
            logger.info(f"⚡ PERFORMANCE: {perf_result['time_per_post']:.2f}s per post")

        logger.info("=" * 80)

        if not production_ready:
            logger.info("🛠️  RECOMMENDATION: Address critical failures before production deployment")
            logger.info("💡 IMPACT: Each critical failure represents significant production risk")
        else:
            logger.info("✅ RECOMMENDATION: Pipeline ready for production deployment")
            logger.info("🎯 EVIDENCE: All critical validations passed with concrete measurements")


def main():
    """Main validation runner"""
    parser = argparse.ArgumentParser(description='Enhanced Chunks to DLT Pipeline Evidence Validator')
    parser.add_argument('--strict-mode', action='store_true', default=True,
                       help='Enable strict validation mode (default: True)')
    parser.add_argument('--output', type=str,
                       help='Output JSON file for validation results')
    parser.add_argument('--evidence-report', type=str,
                       help='Output file for detailed evidence report')

    args = parser.parse_args()

    # Run comprehensive validation
    validator = PipelineEvidenceValidator(strict_mode=args.strict_mode)
    results = validator.run_comprehensive_validation()

    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"💾 Validation results saved to {args.output}")

    # Save evidence report if specified
    if args.evidence_report:
        evidence_report = {
            'validation_summary': {
                'production_ready': results['production_ready'],
                'compliance_score': results['compliance_score'],
                'critical_failures_count': len(results['critical_failures']),
                'evidence_measurements_count': len(results['evidence_log'])
            },
            'detailed_evidence': results['evidence_log'],
            'critical_failures': results['critical_failures']
        }

        with open(args.evidence_report, 'w') as f:
            json.dump(evidence_report, f, indent=2, default=str)
        logger.info(f"📋 Evidence report saved to {args.evidence_report}")

    # Exit with appropriate code
    production_ready = results.get('production_ready', False)
    sys.exit(0 if production_ready else 1)


if __name__ == "__main__":
    main()
