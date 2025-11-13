#!/usr/bin/env python3
"""
A/B Score Threshold Testing - Enhanced Implementation Strategy Scenario 2
Tests different score thresholds to find optimal settings for opportunity discovery

Based on enhanced-chunks documentation:
- Compare results with different thresholds (30, 35, 40, 45, 50)
- Analyze opportunity quantity vs quality trade-offs
- Find optimal threshold for maximum ROI
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client


class ABThresholdTester:
    """A/B testing for different score thresholds"""

    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.test_thresholds = [30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0]
        self.results = {}

    def collect_new_data_for_testing(self, subreddits: list[str], limit: int = 200):
        """
        Collect fresh Reddit data for A/B testing
        Since we only have 3 valid opportunities, we need more data
        """
        print("🔄 COLLECTING FRESH DATA FOR A/B TESTING")
        print("=" * 60)

        # Import collection modules
        try:
            from core.dlt_collection import collect_problem_posts

            all_posts = []
            print(f"Collecting from {len(subreddits)} subreddits...")

            for subreddit in subreddits:
                print(f"  📥 Collecting from r/{subreddit}...")
                try:
                    posts = collect_problem_posts(
                        subreddits=[subreddit],
                        limit=limit // len(subreddits),
                        sort_type="hot"
                    )
                    all_posts.extend(posts)
                    print(f"    ✓ Found {len(posts)} problem posts")
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"    ❌ Error collecting from r/{subreddit}: {e}")

            print(f"\n📊 Total posts collected: {len(all_posts)}")

            # Load to database using DLT
            if all_posts:
                import dlt

                # Transform for DLT
                transformed_posts = []
                for post in all_posts:
                    transformed_post = {
                        'id': post.get('id', ''),
                        'title': post.get('title', ''),
                        'selftext': post.get('selftext', ''),
                        'url': post.get('url', ''),
                        'subreddit': post.get('subreddit', ''),
                        'score': post.get('score', 0),
                        'num_comments': post.get('num_comments', 0),
                        'created_utc': post.get('created_utc', 0),
                        'author': post.get('author', ''),
                        'is_self': post.get('is_self', False),
                        'collected_at': datetime.now().isoformat()
                    }
                    transformed_posts.append(transformed_post)

                # Use new dataset to avoid schema conflicts
                connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

                pipeline = dlt.pipeline(
                    pipeline_name="ab_testing_pipeline",
                    destination=dlt.destinations.postgres(connection_string),
                    dataset_name="ab_testing_data"
                )

                load_info = pipeline.run(
                    transformed_posts,
                    table_name="ab_testing_submissions",
                    write_disposition="append",
                    primary_key="id"
                )

                print(f"✅ Loaded {len(transformed_posts)} posts to database for A/B testing")
                return True
            else:
                print("⚠️ No posts collected")
                return False

        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False

    def run_threshold_analysis(self, dataset_table: str = "submissions"):
        """
        Analyze existing opportunity data with different thresholds
        """
        print("\n🧪 A/B THRESHOLD TESTING")
        print("=" * 60)
        print("Analyzing existing opportunity data with different thresholds...")
        print("")

        # Use app_opportunities table where AI results are actually stored
        all_results = self.supabase.table('app_opportunities').select('count', count='exact').execute()
        total_count = all_results.count if all_results.count else 0
        print(f"🔍 DEBUG: Total records in app_opportunities: {total_count}")

        # Get a sample to see the structure
        sample_result = self.supabase.table('app_opportunities').select('*').limit(5).execute()
        if sample_result.data:
            print(f"🔍 DEBUG: Sample record keys: {list(sample_result.data[0].keys())}")
            print(f"🔍 DEBUG: First final_score value: {sample_result.data[0].get('final_score', 'NOT_FOUND')}")

        # Get existing AI opportunities for analysis
        results_result = self.supabase.table('app_opportunities').select('*').limit(100).execute()

        if not results_result.data:
            print("❌ No AI opportunities found for testing")
            return {}

        print(f"📊 Dataset: {len(results_result.data)} opportunities")
        print(f"🎯 Testing thresholds: {', '.join(map(str, self.test_thresholds))}")
        print("")

        threshold_results = {}

        # Analyze existing results with different thresholds
        all_scores = []
        for opp in results_result.data:
            score = opp.get('final_score') or opp.get('opportunity_score', 0)
            if score:
                all_scores.append(score)

        print(f"📈 Score range: {min(all_scores) if all_scores else 0:.1f} - {max(all_scores) if all_scores else 0:.1f}")
        print("")

        for threshold in self.test_thresholds:
            print(f"🔄 Analyzing threshold: {threshold}")
            print("-" * 40)

            # Filter opportunities by threshold - use opportunity_score if final_score is None
            filtered_opps = []
            for opp in results_result.data:
                score = opp.get('final_score') or opp.get('opportunity_score', 0)
                if score and score >= threshold:
                    opp['effective_score'] = score
                    filtered_opps.append(opp)

            # Analyze results for this threshold
            analysis = self._analyze_threshold_results(threshold, filtered_opps, all_scores)
            threshold_results[threshold] = analysis

            print(f"✅ Threshold {threshold}:")
            print(f"   Opportunities found: {analysis['total_opportunities']}")
            print(f"   Average score: {analysis['avg_score']:.1f}")
            print(f"   High scorers (40+): {analysis['high_scorers']}")
            print(f"   AI profiles available: {analysis['ai_profiles']}")
            print(f"   Hit rate: {analysis['hit_rate']:.1f}%")
            print("")

        return threshold_results

    def _run_ai_scoring(self, submissions: list[dict], threshold: float) -> bool:
        """Run AI opportunity scoring with specified threshold"""
        try:
            # Import the AI scoring system
            import os
            os.environ['SCORE_THRESHOLD'] = str(threshold)

            # For now, simulate AI scoring since we need to test different thresholds
            # In production, this would call: scripts/batch_opportunity_scoring.py
            print(f"   Running AI analysis with threshold {threshold}...")

            # Simulate processing time
            time.sleep(3)

            return True

        except Exception as e:
            print(f"   ❌ Error in AI scoring: {e}")
            return False

    def _analyze_threshold_results(self, threshold: float, opportunities: list[dict], all_scores: list[float] = None) -> dict[str, Any]:
        """Analyze results for a specific threshold"""

        if not opportunities:
            return {
                'threshold': threshold,
                'total_opportunities': 0,
                'avg_score': 0,
                'high_scorers': 0,
                'ai_profiles': 0,
                'processing_time': 0,
                'hit_rate': 0
            }

        # Calculate metrics
        total_opps = len(opportunities)
        scores = [opp.get('effective_score', opp.get('final_score') or opp.get('opportunity_score', 0)) for opp in opportunities]
        avg_score = sum(scores) / len(scores) if scores else 0
        high_scorers = len([s for s in scores if s >= 40])

        # Count AI profiles (opportunities with concepts)
        ai_profiles = len([opp for opp in opportunities if len(opp.get('app_concept', '').strip()) > 10])

        # Calculate hit rate (opportunities vs total processed)
        total_processed = len(all_scores) if all_scores else len(results_result.data) if 'results_result' in locals() else 100
        hit_rate = (total_opps / total_processed * 100) if total_processed > 0 else 0

        return {
            'threshold': threshold,
            'total_opportunities': total_opps,
            'avg_score': avg_score,
            'high_scorers': high_scorers,
            'ai_profiles': ai_profiles,
            'processing_time': 0.1,  # Analysis time
            'hit_rate': hit_rate,
            'score_distribution': self._get_score_distribution(scores)
        }

    def _get_score_distribution(self, scores: list[float]) -> dict[str, int]:
        """Get distribution of scores"""
        distribution = {
            '30-39': 0,
            '40-49': 0,
            '50-59': 0,
            '60-69': 0,
            '70+': 0
        }

        for score in scores:
            if 30 <= score < 40:
                distribution['30-39'] += 1
            elif 40 <= score < 50:
                distribution['40-49'] += 1
            elif 50 <= score < 60:
                distribution['50-59'] += 1
            elif 60 <= score < 70:
                distribution['60-69'] += 1
            elif score >= 70:
                distribution['70+'] += 1

        return distribution

    def generate_ab_report(self, results: dict[float, dict]) -> str:
        """Generate comprehensive A/B testing report"""

        report = []
        report.append("# A/B THRESHOLD TESTING REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary table
        report.append("## THRESHOLD COMPARISON SUMMARY")
        report.append("")
        report.append("| Threshold | Opportunities | Avg Score | 40+ Scores | AI Profiles |")
        report.append("|----------|--------------|-----------|------------|-------------|")

        for threshold in sorted(results.keys()):
            result = results[threshold]
            report.append(f"| {threshold:<8.0f} | {result['total_opportunities']:<12} | {result['avg_score']:<9.1f} | {result['high_scorers']:<10} | {result['ai_profiles']:<11} |")

        report.append("")

        # Analysis
        report.append("## THRESHOLD ANALYSIS")
        report.append("")

        # Find optimal thresholds for different metrics
        max_opps_threshold = max(results.keys(), key=lambda k: results[k]['total_opportunities'])
        max_score_threshold = max(results.keys(), key=lambda k: results[k]['avg_score'])
        max_profiles_threshold = max(results.keys(), key=lambda k: results[k]['ai_profiles'])

        report.append(f"**📊 Quantity Threshold (Most Opportunities):** {max_opps_threshold}")
        report.append(f"- Opportunities: {results[max_opps_threshold]['total_opportunities']}")
        report.append(f"- Average Score: {results[max_opps_threshold]['avg_score']:.1f}")
        report.append("")

        report.append(f"**🎯 Quality Threshold (Highest Average Score):** {max_score_threshold}")
        report.append(f"- Average Score: {results[max_score_threshold]['avg_score']:.1f}")
        report.append(f"- Opportunities: {results[max_score_threshold]['total_opportunities']}")
        report.append("")

        report.append(f"**🤖 AI Profile Threshold (Most AI Profiles):** {max_profiles_threshold}")
        report.append(f"- AI Profiles: {results[max_profiles_threshold]['ai_profiles']}")
        report.append(f"- Opportunities: {results[max_profiles_threshold]['total_opportunities']}")
        report.append("")

        # Score distribution analysis
        report.append("## SCORE DISTRIBUTION ANALYSIS")
        report.append("")

        for threshold in sorted(results.keys()):
            result = results[threshold]
            dist = result['score_distribution']

            report.append(f"### Threshold {threshold}:")
            report.append(f"- 30-39 points: {dist['30-39']}")
            report.append(f"- 40-49 points: {dist['40-49']}")
            report.append(f"- 50-59 points: {dist['50-59']}")
            report.append(f"- 60-69 points: {dist['60-69']}")
            report.append(f"- 70+ points: {dist['70+']}")
            report.append("")

        # Recommendations
        report.append("## RECOMMENDATIONS")
        report.append("")

        # ROI analysis (opportunities vs quality)
        best_roi_threshold = None
        best_roi_score = 0

        for threshold in results.keys():
            result = results[threshold]
            # ROI = (opportunities * avg_score) / processing_time
            roi = (result['total_opportunities'] * result['avg_score']) / max(result['processing_time'], 1)

            if roi > best_roi_score:
                best_roi_score = roi
                best_roi_threshold = threshold

        if best_roi_threshold:
            report.append(f"**🏆 Optimal Threshold (Best ROI):** {best_roi_threshold}")
            report.append(f"- ROI Score: {best_roi_score:.1f}")
            report.append("- Balance of quantity and quality")
            report.append("")

        # Strategic recommendations
        report.append("**💡 Strategic Recommendations:**")
        report.append("")

        if results.get(40.0, {}).get('total_opportunities', 0) > 0:
            report.append("- **40.0 threshold** appears to be the sweet spot for viable opportunities")

        if results.get(50.0, {}).get('total_opportunities', 0) > 0:
            report.append("- **50.0+ thresholds** produce rare but high-quality opportunities")

        report.append("- Use **30.0 threshold** for broad market research")
        report.append("- Use **40.0 threshold** for production-ready opportunities")
        report.append("- Use **50.0+ thresholds** for premium/high-value opportunities")

        return "\n".join(report)

    def save_report(self, report: str, filename: str = None):
        """Save the A/B testing report"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ab_threshold_report_{timestamp}.md"

        report_path = project_root / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"📄 Report saved to: {report_path}")
        return report_path

def main():
    """Main execution"""
    print("🧪 A/B SCORE THRESHOLD TESTING")
    print("Enhanced Implementation Strategy - Scenario 2")
    print("=" * 60)

    tester = ABThresholdTester()

    # Option 1: Use existing data (if available)
    print("📊 Analyzing existing data with different thresholds...")
    results = tester.run_threshold_analysis()

    if results:
        # Generate and save report
        report = tester.generate_ab_report(results)
        report_path = tester.save_report(report)

        print("\n🎉 A/B THRESHOLD TESTING COMPLETE!")
        print(f"Report saved to: {report_path}")

        # Show key findings
        best_threshold = max(results.keys(), key=lambda k: results[k]['total_opportunities'] * results[k]['avg_score'])
        print(f"\n🏆 RECOMMENDED THRESHOLD: {best_threshold}")
        print("Based on optimal balance of quantity and quality")

        return True
    else:
        print("\n⚠️ No results generated")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
