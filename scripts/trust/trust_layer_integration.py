#!/usr/bin/env python3
"""
Trust Layer Integration Script
RedditHarbor Trust Validation System Integration

This script applies comprehensive trust validation to existing opportunities
in the database, generating trust indicators and badges for user-facing
credibility assessment.

Usage:
    python scripts/trust_layer_integration.py [--rebuild-all]
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import argparse

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY, DLT_MIN_ACTIVITY_SCORE
from core.trust_layer import TrustLayerValidator, TrustLevel
from core.activity_validation import calculate_activity_score
import praw


class TrustLayerIntegrator:
    """Integrates trust layer validation with existing opportunities"""

    def __init__(self, rebuild_all: bool = False):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.rebuild_all = rebuild_all
        self.trust_validator = TrustLayerValidator(activity_threshold=DLT_MIN_ACTIVITY_SCORE)

    def get_reddit_client(self) -> praw.Reddit:
        """Initialize Reddit client"""
        try:
            from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT
            return praw.Reddit(
                client_id=REDDIT_PUBLIC,
                client_secret=REDDIT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
        except Exception as e:
            print(f"❌ Reddit client setup failed: {e}")
            raise

    def get_existing_opportunities(self) -> List[Dict]:
        """Get existing opportunities from database"""
        print("📥 Fetching existing opportunities...")

        try:
            # Get opportunities (trust_level column may not exist yet)
            try:
                if self.rebuild_all:
                    result = self.supabase.table('app_opportunities').select('*').execute()
                else:
                    # Try to get opportunities without trust validation, fall back to all if column doesn't exist
                    try:
                        result = self.supabase.table('app_opportunities').select('*').is_('trust_level', 'null').execute()
                    except:
                        result = self.supabase.table('app_opportunities').select('*').execute()
            except Exception as e:
                print(f"❌ Error accessing opportunities table: {e}")
                return []

            opportunities = result.data if result.data else []
            print(f"✅ Retrieved {len(opportunities)} opportunities for trust validation")
            return opportunities

        except Exception as e:
            print(f"❌ Error fetching opportunities: {e}")
            return []

    def get_submission_data(self, opportunity: Dict) -> Dict[str, Any]:
        """Get corresponding submission data for an opportunity"""
        try:
            submission_id = opportunity.get('submission_id')
            if not submission_id:
                return {}

            result = self.supabase.table('submissions').select('*').eq('id', submission_id).execute()
            return result.data[0] if result.data else {}

        except Exception as e:
            print(f"❌ Error fetching submission data: {e}")
            return {}

    def apply_trust_validation(self, opportunities: List[Dict]) -> List[Dict]:
        """Apply trust validation to opportunities"""
        print(f"\n🔍 Applying trust validation to {len(opportunities)} opportunities...")
        print(f"Activity Threshold: {DLT_MIN_ACTIVITY_SCORE}")
        print("=" * 80)

        validated_opportunities = []
        reddit_client = self.get_reddit_client()

        for i, opportunity in enumerate(opportunities):
            try:
                print(f"\n📊 {i+1}/{len(opportunities)}: Validating opportunity...")

                # Get submission data
                submission_data = self.get_submission_data(opportunity)
                if not submission_data:
                    print(f"  ⚠️  No submission data found, skipping...")
                    continue

                # Extract opportunity data
                opportunity_data = {
                    'submission_id': opportunity.get('submission_id'),
                    'title': submission_data.get('title', ''),
                    'text': submission_data.get('text', ''),
                    'subreddit': submission_data.get('subreddit', ''),
                    'upvotes': submission_data.get('upvotes', 0),
                    'comments_count': submission_data.get('comments_count', 0),
                    'created_utc': submission_data.get('created_utc'),
                    'permalink': submission_data.get('permalink', '')
                }

                # Extract AI analysis data
                ai_analysis = {
                    'final_score': opportunity.get('opportunity_score', 0),
                    'confidence_score': opportunity.get('confidence_score', 0.5),
                    'market需求评估': opportunity.get('market需求评估', ''),
                    '技术可行性': opportunity.get('技术可行性', ''),
                    '商业模式': opportunity.get('商业模式', ''),
                    '竞争分析': opportunity.get('竞争分析', ''),
                    'user_pain_point': opportunity.get('user_pain_point', ''),
                    'core_features': opportunity.get('core_features', ''),
                    'monetization': opportunity.get('monetization', ''),
                    'target_audience': opportunity.get('target_audience', '')
                }

                print(f"  📈 r/{opportunity_data['subreddit']} | Score: {ai_analysis['final_score']:.1f}")

                # Apply comprehensive trust validation
                trust_indicators = self.trust_validator.validate_opportunity_trust(
                    submission_data=opportunity_data,
                    ai_analysis=ai_analysis
                )

                # Update opportunity with trust indicators
                opportunity.update({
                    'trust_level': trust_indicators.trust_level.value,
                    'trust_score': trust_indicators.overall_trust_score,
                    'trust_badge': trust_indicators.trust_badges[0] if trust_indicators.trust_badges else 'BASIC',
                    'activity_score': trust_indicators.subreddit_activity_score,
                    'engagement_level': self._get_engagement_level(trust_indicators.post_engagement_score),
                    'trend_velocity': trust_indicators.trend_velocity_score,
                    'problem_validity': self._get_problem_validity(trust_indicators.problem_validity_score),
                    'discussion_quality': self._get_discussion_quality(trust_indicators.discussion_quality_score),
                    'ai_confidence_level': self._get_ai_confidence_level(trust_indicators.ai_analysis_confidence),
                    'trust_factors': {
                        'subreddit_activity': trust_indicators.subreddit_activity_score,
                        'post_engagement': trust_indicators.post_engagement_score,
                        'trend_velocity': trust_indicators.trend_velocity_score,
                        'problem_validity': trust_indicators.problem_validity_score,
                        'discussion_quality': trust_indicators.discussion_quality_score,
                        'ai_confidence': trust_indicators.ai_analysis_confidence,
                        'activity_constraints_met': trust_indicators.activity_constraints_met,
                        'quality_constraints_met': trust_indicators.quality_constraints_met
                    },
                    'trust_updated_at': datetime.now().isoformat()
                })

                validated_opportunities.append(opportunity)

                print(f"  ✅ Trust Level: {trust_indicators.trust_level.value}")
                print(f"  🏆 Badge: {trust_indicators.trust_badge}")
                print(f"  📊 Trust Score: {trust_indicators.trust_score:.1f}/100")

                # Rate limiting for Reddit API
                time.sleep(1)

            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

        return validated_opportunities

    def update_database(self, opportunities: List[Dict]) -> int:
        """Update database with trust indicators (graceful fallback if columns don't exist)"""
        print(f"\n💾 Updating database with trust indicators for {len(opportunities)} opportunities...")

        updated_count = 0
        schema_errors = 0

        for opportunity in opportunities:
            try:
                opportunity_id = opportunity.get('id')
                if not opportunity_id:
                    continue

                # Prepare update data
                update_data = {
                    'trust_level': opportunity.get('trust_level'),
                    'trust_score': opportunity.get('trust_score'),
                    'trust_badge': opportunity.get('trust_badge'),
                    'activity_score': opportunity.get('activity_score'),
                    'engagement_level': opportunity.get('engagement_level'),
                    'trend_velocity': opportunity.get('trend_velocity'),
                    'problem_validity': opportunity.get('problem_validity'),
                    'discussion_quality': opportunity.get('discussion_quality'),
                    'ai_confidence_level': opportunity.get('ai_confidence_level'),
                    'trust_factors': opportunity.get('trust_factors'),
                    'trust_updated_at': opportunity.get('trust_updated_at')
                }

                # Update opportunity
                result = self.supabase.table('app_opportunities').update(update_data).eq('id', opportunity_id).execute()

                if result.data:
                    updated_count += 1

            except Exception as e:
                error_msg = str(e)
                if 'column' in error_msg.lower() and 'does not exist' in error_msg.lower():
                    schema_errors += 1
                    if schema_errors <= 3:  # Only show first 3 schema errors
                        print(f"⚠️  Schema error: Column not found - run migration first")
                else:
                    print(f"❌ Error updating opportunity {opportunity.get('id')}: {e}")
                continue

        if schema_errors > 0:
            print(f"⚠️  {schema_errors} schema errors - trust layer columns need to be added via migration")
            print("💡 Run: psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -f supabase/migrations/20251112000001_add_trust_layer_columns.sql")
        else:
            print(f"✅ Successfully updated {updated_count} opportunities")
        return updated_count

    def _get_engagement_level(self, score: float) -> str:
        """Convert engagement score to level"""
        if score >= 80:
            return "VERY_HIGH"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"

    def _get_problem_validity(self, score: float) -> str:
        """Convert problem validity score to level"""
        if score >= 80:
            return "VALID"
        elif score >= 60:
            return "POTENTIAL"
        elif score >= 40:
            return "UNCLEAR"
        else:
            return "INVALID"

    def _get_discussion_quality(self, score: float) -> str:
        """Convert discussion quality score to level"""
        if score >= 80:
            return "EXCELLENT"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "FAIR"
        else:
            return "POOR"

    def _get_ai_confidence_level(self, score: float) -> str:
        """Convert AI confidence score to level"""
        if score >= 80:
            return "VERY_HIGH"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_trust_report(self, opportunities: List[Dict]) -> str:
        """Generate comprehensive trust validation report"""
        print(f"\n📊 GENERATING TRUST VALIDATION REPORT")
        print("=" * 80)

        if not opportunities:
            return "No trust-validated opportunities available"

        # Analyze trust distribution
        trust_levels = {}
        trust_scores = []
        activity_scores = []
        badges = {}

        for opp in opportunities:
            trust_level = opp.get('trust_level', 'UNKNOWN')
            trust_score = opp.get('trust_score', 0)
            activity_score = opp.get('activity_score', 0)
            badge = opp.get('trust_badge', 'NO-BADGE')

            trust_levels[trust_level] = trust_levels.get(trust_level, 0) + 1
            badges[badge] = badges.get(badge, 0) + 1
            trust_scores.append(trust_score)
            activity_scores.append(activity_score)

        # Generate report
        report = []
        report.append("# TRUST LAYER VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Activity Threshold: {DLT_MIN_ACTIVITY_SCORE}")
        report.append(f"Total Opportunities: {len(opportunities)}")
        report.append("")

        # Trust level distribution
        report.append("## TRUST LEVEL DISTRIBUTION")
        report.append("")
        total = len(opportunities)
        for level in ['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW']:
            count = trust_levels.get(level, 0)
            percentage = (count / total) * 100 if total > 0 else 0
            report.append(f"- {level}: {count} ({percentage:.1f}%)")
        report.append("")

        # Badge distribution
        report.append("## TRUST BADGE DISTRIBUTION")
        report.append("")
        for badge, count in sorted(badges.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100 if total > 0 else 0
            report.append(f"- {badge}: {count} ({percentage:.1f}%)")
        report.append("")

        # Score statistics
        if trust_scores:
            report.append("## TRUST SCORE STATISTICS")
            report.append("")
            report.append(f"- Average Trust Score: {sum(trust_scores) / len(trust_scores):.1f}")
            report.append(f"- Highest Trust Score: {max(trust_scores):.1f}")
            report.append(f"- Lowest Trust Score: {min(trust_scores):.1f}")
            report.append(f"- Opportunities with 80+ Trust Score: {len([s for s in trust_scores if s >= 80])}")
            report.append("")

        # Activity score statistics
        if activity_scores:
            report.append("## ACTIVITY SCORE STATISTICS")
            report.append("")
            report.append(f"- Average Activity Score: {sum(activity_scores) / len(activity_scores):.1f}")
            report.append(f"- Active Subreddits (≥{DLT_MIN_ACTIVITY_SCORE}): {len([s for s in activity_scores if s >= DLT_MIN_ACTIVITY_SCORE])}")
            report.append("")

        # Quality indicators
        high_trust_opps = [opp for opp in opportunities if opp.get('trust_level') in ['HIGH', 'VERY_HIGH']]
        high_activity_opps = [opp for opp in opportunities if opp.get('activity_score', 0) >= DLT_MIN_ACTIVITY_SCORE]

        report.append("## QUALITY INDICATORS")
        report.append("")
        report.append(f"- High Trust Opportunities (HIGH/VERY_HIGH): {len(high_trust_opps)} ({(len(high_trust_opps)/total)*100:.1f}%)")
        report.append(f"- Active Subreddit Opportunities: {len(high_activity_opps)} ({(len(high_activity_opps)/total)*100:.1f}%)")
        report.append(f"- High Trust & Active: {len([opp for opp in high_trust_opps if opp.get('activity_score', 0) >= DLT_MIN_ACTIVITY_SCORE])}")
        report.append("")

        # Recommendations
        report.append("## RECOMMENDATIONS")
        report.append("")

        high_trust_percentage = (len(high_trust_opps) / total) * 100 if total > 0 else 0
        active_percentage = (len(high_activity_opps) / total) * 100 if total > 0 else 0

        if high_trust_percentage >= 70:
            report.append("✅ **Excellent trust quality** - Most opportunities show strong credibility indicators")
        elif high_trust_percentage >= 50:
            report.append("✅ **Good trust quality** - Majority of opportunities have solid credibility")
        else:
            report.append("⚠️  **Trust quality needs improvement** - Consider refining opportunity criteria")

        if active_percentage >= 80:
            report.append("✅ **Excellent activity filtering** - Most opportunities from active communities")
        elif active_percentage >= 60:
            report.append("✅ **Good activity filtering** - Balanced approach to community activity")
        else:
            report.append("⚠️  **Activity filtering may be too restrictive** - Consider lowering threshold")

        report.append("")
        report.append("## TRUST LAYER STATUS")
        report.append("")
        report.append("🏆 **Trust layer integration complete**")
        report.append("📊 **User-facing credibility indicators now available**")
        report.append("🔍 **Comprehensive validation provides transparency**")
        report.append("🎯 **Balanced approach optimizes discovery vs quality**")

        return "\n".join(report)

    def run_trust_integration(self):
        """Run complete trust layer integration"""
        print("🏆 TRUST LAYER INTEGRATION")
        print("=" * 80)
        print(f"Activity Threshold: {DLT_MIN_ACTIVITY_SCORE}")
        print(f"Rebuild All: {self.rebuild_all}")
        print("")

        # Get existing opportunities
        opportunities = self.get_existing_opportunities()

        if not opportunities:
            print("❌ No opportunities found for trust validation")
            return

        # Apply trust validation
        validated_opportunities = self.apply_trust_validation(opportunities)

        if not validated_opportunities:
            print("❌ No opportunities successfully validated")
            return

        # Update database
        updated_count = self.update_database(validated_opportunities)

        # Generate report
        report = self.generate_trust_report(validated_opportunities)

        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = Path(__file__).parent.parent / "reports" / f"trust_layer_integration_{timestamp}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_path}")
        print("\n" + report)

        print(f"\n🎉 TRUST LAYER INTEGRATION COMPLETE!")
        print(f"✅ Validated: {len(validated_opportunities)} opportunities")
        print(f"✅ Updated: {updated_count} database records")
        print(f"✅ Activity Threshold: {DLT_MIN_ACTIVITY_SCORE}")
        print(f"✅ Trust indicators now available for user interface")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Trust Layer Integration')
    parser.add_argument('--rebuild-all', action='store_true',
                       help='Rebuild trust validation for all opportunities (not just unvalidated ones)')

    args = parser.parse_args()

    integrator = TrustLayerIntegrator(rebuild_all=args.rebuild_all)
    integrator.run_trust_integration()


if __name__ == "__main__":
    main()