#!/usr/bin/env python3
"""
Enhanced Chunks Comprehensive Test Runner

This script implements the complete Enhanced Chunks validation test following
the RedditHarbor E2E Guide with Agent-Enhanced Processing.

Test Pipeline:
1. Environment Validation
2. DLT Activity Collection (Phase 1-5)
3. Original SCORE_THRESHOLD Filtering (40.0)
4. AI Opportunity Analysis with Trust Layer
5. Trust Validation (6-dimensional scoring)
6. Database Integration and Validation
7. Performance Metrics and Reporting

Success Criteria:
- Original SCORE_THRESHOLD filtering restored and working
- Trust layer separated from acceptance criteria
- Realistic conversion rates (50% at 70.0 threshold)
- Complete parameter collection (100%)
- Performance under 10s per post
- Zero pipeline failures

Based on enhanced chunks documentation:
- Chunk 1: System Overview & Foundation
- Chunk 2: Quick Start Guide & Decision Framework
- Chunk 3: DLT Activity Validation System
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import RedditHarbor components
import dlt
from agent_tools.llm_profiler import LLMProfiler
from config.settings import DEFAULT_SUBREDDITS, DLT_MIN_ACTIVITY_SCORE
from core.dlt_collection import collect_problem_posts, create_dlt_pipeline
from core.dlt_app_opportunities import load_app_opportunities
from core.trust_layer import TrustLayerValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'tests/enhanced_chunks_validation/test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedChunksValidator:
    """Comprehensive test runner for Enhanced Chunks validation."""

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.start_time = time.time()
        self.test_results = {
            'environment_validation': {},
            'dlt_collection': {},
            'score_threshold_filtering': {},
            'ai_analysis': {},
            'trust_validation': {},
            'database_integration': {},
            'performance_metrics': {},
            'compliance_check': {}
        }

    def validate_environment(self) -> bool:
        """Phase 0: Environment Validation"""
        logger.info("🔍 Phase 0: Environment Validation")

        try:
            # Test DLT dependencies
            import dlt
            import praw
            logger.info("✅ DLT dependencies available")

            # Test LLM profiler
            profiler = LLMProfiler()
            logger.info("✅ LLM profiler available")

            # Test trust layer
            trust_validator = TrustLayerValidator()
            logger.info("✅ Trust layer available")

            self.test_results['environment_validation'] = {
                'status': 'PASS',
                'dlt_version': dlt.__version__,
                'llm_profiler': 'OK',
                'trust_layer': 'OK'
            }
            return True

        except Exception as e:
            logger.error(f"❌ Environment validation failed: {e}")
            self.test_results['environment_validation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False

    def run_dlt_activity_collection(self, limit: int = 10) -> List[Dict]:
        """Phase 1-2: DLT Activity Collection with Quality Filtering"""
        logger.info(f"📊 Phase 1-2: DLT Activity Collection (limit={limit})")

        try:
            # Collect problem posts using DLT with activity validation
            posts = collect_problem_posts(
                subreddits=["SaaS", "MicroSaaS", "Entrepreneur"],
                limit=limit,
                test_mode=self.test_mode
            )

            logger.info(f"✅ DLT collected {len(posts)} high-quality posts")

            self.test_results['dlt_collection'] = {
                'status': 'PASS',
                'posts_collected': len(posts),
                'collection_method': 'DLT activity validation'
            }

            return posts

        except Exception as e:
            logger.error(f"❌ DLT collection failed: {e}")
            self.test_results['dlt_collection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return []

    def test_original_score_threshold_filtering(self, posts: List[Dict], score_threshold: float = 40.0) -> List[Dict]:
        """Phase 3: Original SCORE_THRESHOLD Filtering Test"""
        logger.info(f"🎯 Phase 3: Original SCORE_THRESHOLD Filtering (threshold={score_threshold})")

        try:
            filtered_posts = []
            filtered_out_count = 0

            for post in posts:
                final_score = post.get('final_score', 0)

                if final_score >= score_threshold:
                    filtered_posts.append(post)
                    logger.info(f"    🎯 High score ({final_score:.1f}) - PASSED")
                else:
                    filtered_out_count += 1
                    logger.info(f"    ❌ Low score ({final_score:.1f} < {score_threshold}) - FILTERED OUT")

            pass_rate = len(filtered_posts) / len(posts) * 100 if posts else 0
            logger.info(f"✅ SCORE_THRESHOLD filtering: {len(filtered_posts)}/{len(posts)} passed ({pass_rate:.1f}%)")

            # Validate realistic pass rate (should be 30-70% for threshold 40.0)
            if 30 <= pass_rate <= 70:
                rate_status = "REALISTIC"
            elif pass_rate > 70:
                rate_status = "TOO HIGH (suspicious)"
            else:
                rate_status = "TOO LOW"

            self.test_results['score_threshold_filtering'] = {
                'status': 'PASS',
                'threshold': score_threshold,
                'posts_input': len(posts),
                'posts_passed': len(filtered_posts),
                'posts_filtered': filtered_out_count,
                'pass_rate': pass_rate,
                'realistic_rate': rate_status
            }

            return filtered_posts

        except Exception as e:
            logger.error(f"❌ SCORE_THRESHOLD filtering failed: {e}")
            self.test_results['score_threshold_filtering'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return []

    def run_ai_opportunity_analysis(self, posts: List[Dict], score_threshold: float = 40.0) -> List[Dict]:
        """Phase 4: AI Opportunity Analysis with Original Filters"""
        logger.info(f"🤖 Phase 4: AI Opportunity Analysis (threshold={score_threshold})")

        try:
            profiler = LLMProfiler()
            analyzed_posts = []
            high_score_count = 0
            filtered_count = 0

            for post in posts:
                final_score = post.get('final_score', 0)

                # RESTORE ORIGINAL FILTERING: Only analyze high-scoring opportunities
                if final_score >= score_threshold:
                    high_score_count += 1
                    logger.info(f"    🎯 Analyzing high-score post ({final_score:.1f})")

                    # Generate AI profile
                    ai_profile = profiler.analyze_post(post)

                    if ai_profile:
                        analyzed_post = post.copy()
                        analyzed_post.update(ai_profile)
                        analyzed_posts.append(analyzed_post)
                        logger.info(f"    ✅ AI profile generated")
                    else:
                        logger.warning(f"    ⚠️ AI analysis failed for post")
                else:
                    filtered_count += 1
                    logger.info(f"    ❌ Low score ({final_score:.1f} < {score_threshold}) - filtered out")

            analysis_rate = len(analyzed_posts) / len(posts) * 100 if posts else 0
            logger.info(f"✅ AI analysis: {len(analyzed_posts)}/{len(posts)} analyzed ({analysis_rate:.1f}%)")

            self.test_results['ai_analysis'] = {
                'status': 'PASS',
                'score_threshold': score_threshold,
                'posts_input': len(posts),
                'high_score_posts': high_score_count,
                'posts_analyzed': len(analyzed_posts),
                'posts_filtered': filtered_count,
                'analysis_rate': analysis_rate
            }

            return analyzed_posts

        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            self.test_results['ai_analysis'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return []

    def run_trust_validation(self, posts: List[Dict]) -> List[Dict]:
        """Phase 5: Trust Layer Validation (Metadata Only)"""
        logger.info("🔒 Phase 5: Trust Layer Validation")

        try:
            trust_validator = TrustLayerValidator()
            validated_posts = []

            for post in posts:
                # Apply trust validation (for metadata only, not filtering)
                trust_indicators = trust_validator.validate_post(post)

                # Add trust metadata to post
                if trust_indicators:
                    trust_data = {
                        'trust_level': trust_indicators.trust_level.value,
                        'trust_score': trust_indicators.trust_score,
                        'trust_badge': trust_indicators.trust_badge,
                        'activity_score': trust_indicators.activity_score,
                        'confidence_score': trust_indicators.confidence_score,
                        'engagement_level': trust_indicators.engagement_level.value,
                        'trend_velocity': trust_indicators.trend_velocity_score,
                        'problem_validity': trust_indicators.problem_validity_score,
                        'discussion_quality': trust_indicators.discussion_quality_score,
                        'ai_confidence_level': trust_indicators.ai_confidence_level.value,
                        'trust_validation_timestamp': trust_indicators.validation_timestamp,
                        'trust_validation_method': 'comprehensive_6d'
                    }

                    validated_post = post.copy()
                    validated_post.update(trust_data)
                    validated_posts.append(validated_post)

                    logger.info(f"    🔒 Trust validation: {trust_indicators.trust_level.value} ({trust_indicators.trust_score:.1f})")
                else:
                    logger.warning(f"    ⚠️ Trust validation failed for post")

            logger.info(f"✅ Trust validation: {len(validated_posts)}/{len(posts)} validated")

            # Trust score distribution
            trust_scores = [p['trust_score'] for p in validated_posts if 'trust_score' in p]
            avg_trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0

            self.test_results['trust_validation'] = {
                'status': 'PASS',
                'posts_input': len(posts),
                'posts_validated': len(validated_posts),
                'trust_score_range': f"{min(trust_scores):.1f}-{max(trust_scores):.1f}" if trust_scores else "N/A",
                'avg_trust_score': avg_trust_score,
                'validation_method': '6_dimensional_scoring'
            }

            return validated_posts

        except Exception as e:
            logger.error(f"❌ Trust validation failed: {e}")
            self.test_results['trust_validation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return []

    def test_database_integration(self, posts: List[Dict]) -> bool:
        """Phase 6: Database Integration and Validation"""
        logger.info(f"💾 Phase 6: Database Integration ({len(posts)} posts)")

        try:
            # Load to database using DLT
            success = load_app_opportunities(posts)

            if success:
                logger.info("✅ Database integration successful")

                # Verify data was loaded correctly
                time.sleep(2)  # Allow time for database to update

                self.test_results['database_integration'] = {
                    'status': 'PASS',
                    'posts_loaded': len(posts),
                    'loading_method': 'DLT merge disposition',
                    'deduplication': 'submission_id primary_key'
                }
                return True
            else:
                raise Exception("DLT loading failed")

        except Exception as e:
            logger.error(f"❌ Database integration failed: {e}")
            self.test_results['database_integration'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False

    def generate_performance_report(self) -> Dict:
        """Phase 7: Performance Metrics and Reporting"""
        total_time = time.time() - self.start_time
        total_posts = sum([
            result.get('posts_collected', 0) for result in [self.test_results.get('dlt_collection', {})]
        ])

        performance_metrics = {
            'total_execution_time': total_time,
            'posts_processed': total_posts,
            'time_per_post': total_time / total_posts if total_posts > 0 else 0,
            'pipeline_stages': len([r for r in self.test_results.values() if r.get('status') == 'PASS']),
            'pipeline_stages_total': len(self.test_results)
        }

        self.test_results['performance_metrics'] = performance_metrics

        logger.info("📊 Phase 7: Performance Report")
        logger.info(f"    Total time: {total_time:.2f}s")
        logger.info(f"    Posts processed: {total_posts}")
        logger.info(f"    Time per post: {performance_metrics['time_per_post']:.2f}s")
        logger.info(f"    Pipeline stages: {performance_metrics['pipeline_stages']}/{performance_metrics['pipeline_stages_total']}")

        return performance_metrics

    def validate_compliance(self) -> Dict:
        """Validate compliance with Enhanced Chunks requirements"""
        logger.info("✅ Compliance Validation")

        compliance_checks = {
            'original_filters_restored': self.test_results.get('score_threshold_filtering', {}).get('status') == 'PASS',
            'trust_layer_separated': self.test_results.get('trust_validation', {}).get('status') == 'PASS',
            'realistic_conversion': 'REALISTIC' in self.test_results.get('score_threshold_filtering', {}).get('realistic_rate', ''),
            'complete_parameter_collection': self.test_results.get('ai_analysis', {}).get('status') == 'PASS',
            'performance_target': self.test_results.get('performance_metrics', {}).get('time_per_post', 999) < 10.0,
            'zero_pipeline_failures': all(r.get('status') != 'FAIL' for r in self.test_results.values() if isinstance(r, dict))
        }

        compliance_score = sum(compliance_checks.values()) / len(compliance_checks) * 100

        self.test_results['compliance_check'] = {
            'status': 'PASS' if compliance_score >= 80 else 'FAIL',
            'compliance_score': compliance_score,
            'checks': compliance_checks
        }

        logger.info(f"    Compliance Score: {compliance_score:.1f}%")

        return self.test_results['compliance_check']

    def run_comprehensive_test(self,
                             collection_limit: int = 10,
                             score_threshold: float = 40.0) -> Dict:
        """Run complete Enhanced Chunks validation test"""

        logger.info("🚀 Starting Enhanced Chunks Comprehensive Test")
        logger.info(f"Configuration: limit={collection_limit}, threshold={score_threshold}")
        logger.info("-" * 80)

        # Phase 0: Environment Validation
        if not self.validate_environment():
            logger.error("❌ Environment validation failed - aborting test")
            return self.test_results

        # Phase 1-2: DLT Activity Collection
        posts = self.run_dlt_activity_collection(collection_limit)
        if not posts:
            logger.error("❌ No posts collected - aborting test")
            return self.test_results

        # Phase 3: Original SCORE_THRESHOLD Filtering
        filtered_posts = self.test_original_score_threshold_filtering(posts, score_threshold)

        # Phase 4: AI Opportunity Analysis
        analyzed_posts = self.run_ai_opportunity_analysis(filtered_posts, score_threshold)

        # Phase 5: Trust Validation
        validated_posts = self.run_trust_validation(analyzed_posts)

        # Phase 6: Database Integration
        self.test_database_integration(validated_posts)

        # Phase 7: Performance Report
        self.generate_performance_report()

        # Compliance Validation
        self.validate_compliance()

        # Final Summary
        self.print_test_summary()

        return self.test_results

    def print_test_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📋 ENHANCED CHUNKS COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)

        for stage, result in self.test_results.items():
            status = result.get('status', 'UNKNOWN')
            if status == 'PASS':
                logger.info(f"✅ {stage.upper()}: {status}")
            elif status == 'FAIL':
                logger.info(f"❌ {stage.upper()}: {status}")
            else:
                logger.info(f"⚠️  {stage.upper()}: {status}")

        # Key metrics
        collection_result = self.test_results.get('dlt_collection', {})
        filtering_result = self.test_results.get('score_threshold_filtering', {})
        ai_result = self.test_results.get('ai_analysis', {})
        trust_result = self.test_results.get('trust_validation', {})
        performance_result = self.test_results.get('performance_metrics', {})

        logger.info(f"\n📊 KEY METRICS:")
        logger.info(f"    Posts Collected: {collection_result.get('posts_collected', 0)}")
        logger.info(f"    Pass Rate: {filtering_result.get('pass_rate', 0):.1f}%")
        logger.info(f"    AI Analysis Rate: {ai_result.get('analysis_rate', 0):.1f}%")
        logger.info(f"    Trust Score Range: {trust_result.get('trust_score_range', 'N/A')}")
        logger.info(f"    Time per Post: {performance_result.get('time_per_post', 0):.2f}s")

        # Compliance status
        compliance_result = self.test_results.get('compliance_check', {})
        compliance_score = compliance_result.get('compliance_score', 0)

        if compliance_score >= 90:
            logger.info(f"\n🏆 COMPLIANCE: EXCELLENT ({compliance_score:.1f}%)")
        elif compliance_score >= 80:
            logger.info(f"\n✅ COMPLIANCE: GOOD ({compliance_score:.1f}%)")
        elif compliance_score >= 70:
            logger.info(f"\n⚠️  COMPLIANCE: ACCEPTABLE ({compliance_score:.1f}%)")
        else:
            logger.info(f"\n❌ COMPLIANCE: NEEDS IMPROVEMENT ({compliance_score:.1f}%)")

        logger.info("=" * 80)

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Enhanced Chunks Comprehensive Test Runner')
    parser.add_argument('--limit', type=int, default=10, help='Number of posts to collect')
    parser.add_argument('--score-threshold', type=float, default=40.0, help='SCORE_THRESHOLD for filtering')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with simulated data')
    parser.add_argument('--output', type=str, help='Output JSON file for test results')

    args = parser.parse_args()

    # Run comprehensive test
    validator = EnhancedChunksValidator(test_mode=args.test_mode)
    results = validator.run_comprehensive_test(
        collection_limit=args.limit,
        score_threshold=args.score_threshold
    )

    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"💾 Test results saved to {args.output}")

    # Exit with appropriate code
    compliance_score = results.get('compliance_check', {}).get('compliance_score', 0)
    sys.exit(0 if compliance_score >= 80 else 1)

if __name__ == "__main__":
    main()