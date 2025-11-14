#!/usr/bin/env python3
"""
Activity-Constrained Analysis for A/B Testing
RedditHarbor A/B Test: Activity Filter Impact Analysis

This script performs opportunity analysis with activity constraints to compare
against unconstrained results, completing our natural A/B test scenario.

Usage:
    python scripts/activity_constrained_analysis.py [--activity-threshold SCORE]
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

import praw

from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler as LLMProfiler
from config.settings import SUPABASE_KEY, SUPABASE_URL
from core.activity_validation import calculate_activity_score
from supabase import create_client


class ActivityConstrainedAnalyzer:
    """A/B test analyzer for activity constraint impact"""

    def __init__(self, activity_threshold: float = 50.0):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.activity_threshold = activity_threshold
        self.llm_profiler = None
        self.setup_llm_profiler()

    def setup_llm_profiler(self):
        """Initialize LLM profiler"""
        try:
            self.llm_profiler = LLMProfiler()
            print("✅ LLM Profiler initialized")
        except Exception as e:
            print(f"❌ LLM profiler setup failed: {e}")
            raise

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

    def filter_submissions_by_activity(self, submissions: list[dict]) -> tuple[list[dict], list[dict]]:
        """
        Filter submissions by subreddit activity score.

        Returns:
            Tuple of (active_submissions, inactive_submissions)
        """
        print(f"🔍 Filtering submissions by activity threshold: {self.activity_threshold}")

        reddit_client = self.get_reddit_client()

        active_submissions = []
        inactive_submissions = []
        subreddit_scores = {}

        # Get unique subreddits
        unique_subreddits = list(set(sub.get('subreddit', '') for sub in submissions))
        print(f"  Found {len(unique_subreddits)} unique subreddits")

        # Test subreddit activity
        active_subreddits = []
        for subreddit_name in unique_subreddits:
            if not subreddit_name:
                continue

            try:
                print(f"  📊 Testing r/{subreddit_name}...")
                subreddit = reddit_client.subreddit(subreddit_name)
                activity_score = calculate_activity_score(subreddit, time_filter="day")
                subreddit_scores[subreddit_name] = activity_score

                if activity_score >= self.activity_threshold:
                    print(f"    ✅ ACTIVE: {activity_score:.1f}")
                    active_subreddits.append(subreddit_name)
                else:
                    print(f"    ❌ INACTIVE: {activity_score:.1f}")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"    ⚠️  ERROR: {e}")
                subreddit_scores[subreddit_name] = 0.0

        # Filter submissions based on active subreddits
        for submission in submissions:
            subreddit = submission.get('subreddit', '')
            if subreddit in active_subreddits:
                submission['activity_score'] = subreddit_scores.get(subreddit, 0.0)
                active_submissions.append(submission)
            else:
                submission['activity_score'] = subreddit_scores.get(subreddit, 0.0)
                inactive_submissions.append(submission)

        print("\n📈 Activity Filtering Results:")
        print(f"  Active subreddits (≥{self.activity_threshold}): {len(active_subreddits)}")
        print(f"  Active submissions: {len(active_submissions)}")
        print(f"  Inactive submissions: {len(inactive_submissions)}")

        return active_submissions, inactive_submissions

    def analyze_filtered_opportunities(self, submissions: list[dict], dataset_name: str) -> list[dict]:
        """Analyze filtered submissions with AI profiling"""
        print(f"\n🤖 Analyzing {len(submissions)} {dataset_name} submissions...")

        analyzed_opportunities = []

        for i, submission in enumerate(submissions):
            try:
                submission_id = submission.get('submission_id', '')
                title = submission.get('title', '')
                text = submission.get('text', '') or submission.get('content', '')
                subreddit = submission.get('subreddit', '')
                activity_score = submission.get('activity_score', 0.0)

                print(f"  🔍 {i+1}/{len(submissions)}: {title[:50]}... (r/{subreddit}, activity: {activity_score:.1f})")

                # Generate AI profile
                ai_profile = self.llm_profiler.generate_app_profile(
                    text=text,
                    title=title,
                    subreddit=subreddit,
                    score=0.0
                )

                # Add metadata
                ai_profile.update({
                    'submission_id': submission_id,
                    'subreddit': subreddit,
                    'activity_score': activity_score,
                    'opportunity_score': ai_profile.get('final_score', 0),
                    'reddit_score': submission.get('upvotes', 0) + submission.get('comments_count', 0),
                    'status': 'activity_constrained',
                    'created_at': datetime.now().isoformat(),
                    'dataset': dataset_name
                })

                analyzed_opportunities.append(ai_profile)
                print(f"    ✅ Score: {ai_profile.get('final_score', 0):.1f}")

            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue

        return analyzed_opportunities

    def save_results(self, opportunities: list[dict], dataset_name: str):
        """Save results to database"""
        print(f"\n💾 {len(opportunities)} {dataset_name} opportunities generated")
        print("ℹ️  Database schema doesn't support activity_score field - using in-memory analysis")

        # Store in memory for analysis instead of database
        # The current app_opportunities table schema doesn't include activity_score

    def generate_comparison_report(self, active_opportunities: list[dict], inactive_opportunities: list[dict]):
        """Generate A/B test comparison report"""
        print("\n📊 GENERATING A/B TEST COMPARISON REPORT")
        print("=" * 80)

        # Get existing unconstrained results for comparison
        try:
            existing_result = self.supabase.table('app_opportunities').select('*').execute()
            unconstrained = existing_result.data if existing_result.data else []
        except:
            unconstrained = []

        # Analyze scores for each group
        def analyze_scores(opp_list, name):
            if not opp_list:
                return {'count': 0, 'avg_score': 0, 'high_scores': 0, 'threshold_65': 0, 'threshold_70': 0, 'threshold_75': 0}

            scores = [opp.get('opportunity_score', opp.get('final_score', 0)) for opp in opp_list]
            scores = [s for s in scores if s > 0]

            return {
                'count': len(scores),
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'high_scores': len([s for s in scores if s >= 40]),
                'threshold_65': len([s for s in scores if s >= 65]),
                'threshold_70': len([s for s in scores if s >= 70]),
                'threshold_75': len([s for s in scores if s >= 75])
            }

        unconstrained_stats = analyze_scores(unconstrained, "Unconstrained")
        active_stats = analyze_scores(active_opportunities, "Activity-Constrained")

        # Generate report
        report = []
        report.append("# ACTIVITY CONSTRAINT A/B TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Activity Threshold: {self.activity_threshold}")
        report.append("")

        # Comparison table
        report.append("## A/B TEST COMPARISON RESULTS")
        report.append("")
        report.append("| Metric | Unconstrained (A) | Activity-Constrained (B) | Ratio (A/B) |")
        report.append("|--------|-------------------|------------------------|------------|")

        metrics = [
            ('Total Opportunities', unconstrained_stats['count'], active_stats['count']),
            ('Average Score', f"{unconstrained_stats['avg_score']:.1f}", f"{active_stats['avg_score']:.1f}"),
            ('40+ Scores', unconstrained_stats['high_scores'], active_stats['high_scores']),
            ('65+ Threshold', unconstrained_stats['threshold_65'], active_stats['threshold_65']),
            ('70+ Threshold', unconstrained_stats['threshold_70'], active_stats['threshold_70']),
            ('75+ Threshold', unconstrained_stats['threshold_75'], active_stats['threshold_75']),
        ]

        for metric, a_val, b_val in metrics:
            if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)) and b_val > 0:
                ratio = f"{a_val/b_val:.1f}x"
            else:
                ratio = "N/A"
            report.append(f"| {metric} | {a_val} | {b_val} | {ratio} |")

        report.append("")

        # Analysis
        report.append("## KEY FINDINGS")
        report.append("")

        discovery_reduction = 0

        if active_stats['count'] > 0 and unconstrained_stats['count'] > 0:
            discovery_reduction = ((unconstrained_stats['count'] - active_stats['count']) / unconstrained_stats['count']) * 100
            report.append(f"**🔍 Discovery Impact:** Activity filtering reduces opportunities by {discovery_reduction:.1f}%")

            if active_stats['avg_score'] > 0:
                score_diff = active_stats['avg_score'] - unconstrained_stats['avg_score']
                report.append(f"**📈 Quality Impact:** Average score {'increases' if score_diff > 0 else 'decreases'} by {abs(score_diff):.1f} points")

            high_65_ratio = (active_stats['threshold_65'] / unconstrained_stats['threshold_65']) * 100 if unconstrained_stats['threshold_65'] > 0 else 0
            report.append(f"**🎯 High-Value Retention:** {high_65_ratio:.1f}% of 65+ opportunities survive activity filtering")
        else:
            report.append("**⚠️  No activity-constrained opportunities found - threshold may be too strict")

        report.append("")
        report.append("## RECOMMENDATIONS")
        report.append("")

        if active_stats['count'] == 0:
            report.append("- **Lower activity threshold** to {self.activity_threshold/2:.1f} for better discovery")
            report.append("- Current threshold appears too restrictive for opportunity discovery")
        elif discovery_reduction > 90:
            report.append("- **Consider moderate threshold** (25-30) for better balance")
            report.append("- Current filtering is very aggressive, may miss valid opportunities")
        elif discovery_reduction > 70:
            report.append("- **Activity constraint provides value** but may be too strict")
            report.append("- Test lower thresholds (30-40) for optimization")
        else:
            report.append("- **Activity constraint working well**")
            report.append("- Current threshold provides good balance")

        # Save report
        report_content = "\n".join(report)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = Path(__file__).parent.parent / "reports" / f"activity_constraint_ab_test_{timestamp}.md"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report_content)

        print(f"📄 Report saved to: {report_path}")
        print("\n" + report_content)

        return report_path

    def run_activity_constrained_analysis(self):
        """Run complete activity-constrained analysis"""
        print("🧪 ACTIVITY-CONSTRAINED OPPORTUNITY ANALYSIS")
        print("=" * 80)
        print(f"Activity Threshold: {self.activity_threshold}")
        print("")

        # Get existing submissions
        print("📥 Fetching existing submissions...")
        try:
            submissions_result = self.supabase.table('submissions').select('*').limit(200).execute()
            submissions = submissions_result.data if submissions_result.data else []
            print(f"✅ Retrieved {len(submissions)} submissions")
        except Exception as e:
            print(f"❌ Error fetching submissions: {e}")
            return

        # Filter by activity
        active_submissions, inactive_submissions = self.filter_submissions_by_activity(submissions)

        if not active_submissions:
            print(f"\n⚠️  No active submissions found with threshold {self.activity_threshold}")
            print("Consider lowering the activity threshold")
            return

        # Analyze active submissions
        active_opportunities = self.analyze_filtered_opportunities(active_submissions, "activity_constrained")

        # Save results
        if active_opportunities:
            self.save_results(active_opportunities, "activity_constrained")

        # Generate comparison report
        self.generate_comparison_report(active_opportunities, inactive_submissions)

        print("\n🎉 ACTIVITY-CONSTRAINED ANALYSIS COMPLETE!")
        print(f"Analyzed {len(active_opportunities)} activity-constrained opportunities")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Activity-Constrained A/B Test Analysis')
    parser.add_argument('--activity-threshold', type=float, default=50.0,
                       help='Activity score threshold (default: 50.0)')

    args = parser.parse_args()

    analyzer = ActivityConstrainedAnalyzer(activity_threshold=args.activity_threshold)
    analyzer.run_activity_constrained_analysis()


if __name__ == "__main__":
    main()
