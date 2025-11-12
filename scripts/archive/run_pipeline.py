#!/usr/bin/env python3
"""
Script 4 of 4: Pipeline Orchestration
RedditHarbor Clean Pipeline - Main Pipeline Controller

Coordinates the 3 core scripts in sequence.
Single responsibility: Orchestrate collect → analyze → report pipeline
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY


class PipelineOrchestrator:
    """Main pipeline orchestrator for the 4-script clean pipeline"""

    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.start_time = datetime.now()

        # Pipeline configuration
        self.config = {
            'collection': {
                'target_subreddits': [
                    'productivity',
                    'selfimprovement',
                    'entrepreneur',
                    'startups',
                    'personalfinance',
                    'financialindependence',
                    'investing',
                    'stocks',
                    'technology',
                    'programming',
                    'learnprogramming',
                    'saas',
                    'sidehustle',
                    'freelance',
                    'digitalnomad',
                    'SoftwareEngineering'
                ],
                'submissions_per_subreddit': 50
            },
            'analysis': {
                'limit': 100,
                'min_score_threshold': 30.0
            },
            'reporting': {
                'limit': 25,
                'min_score': 35.0
            }
        }

    def print_banner(self):
        """Print pipeline banner"""
        print("🚀 RedditHarbor Clean Pipeline")
        print("=" * 60)
        print("4-Script Architecture: Reddit → Analysis → Reports → Output")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        status = {
            'collection': {'completed': False, 'records_processed': 0},
            'analysis': {'completed': False, 'profiles_generated': 0},
            'reporting': {'completed': False, 'reports_created': 0}
        }

        try:
            # Check submissions count
            submissions_response = self.supabase.table('submissions').select('*', count='exact').execute()
            if submissions_response.data:
                status['collection']['records_processed'] = len(submissions_response.data)

            # Check app opportunities count
            opportunities_response = self.supabase.table('app_opportunities').select('*', count='exact').execute()
            if opportunities_response.data:
                status['analysis']['profiles_generated'] = len(opportunities_response.data)

            # Check reports directory
            reports_dir = Path("reports")
            if reports_dir.exists():
                report_files = list(reports_dir.glob("*.md"))
                status['reporting']['reports_created'] = len(report_files)

        except Exception as e:
            print(f"⚠️ Could not get pipeline status: {e}")

        return status

    def run_collection_stage(self) -> bool:
        """Run data collection stage"""
        print("\n" + "="*60)
        print("STAGE 1: REDDIT DATA COLLECTION")
        print("="*60)

        try:
            # Import collection script
            from collect_reddit_data import RedditDataCollector

            collector = RedditDataCollector()
            stored_count = collector.run_collection(
                target_subreddits=self.config['collection']['target_subreddits'],
                submissions_per_subreddit=self.config['collection']['submissions_per_subreddit']
            )

            if stored_count > 0:
                print(f"✅ Collection stage completed: {stored_count} submissions stored")
                return True
            else:
                print("⚠️ Collection stage completed but no submissions stored")
                return False

        except Exception as e:
            print(f"❌ Collection stage failed: {e}")
            return False

    def run_analysis_stage(self) -> bool:
        """Run opportunity analysis stage"""
        print("\n" + "="*60)
        print("STAGE 2: AI OPPORTUNITY ANALYSIS")
        print("="*60)

        try:
            # Import analysis script
            from analyze_opportunities import OpportunityAnalyzer

            analyzer = OpportunityAnalyzer()
            stored_count = analyzer.run_analysis(
                limit=self.config['analysis']['limit'],
                min_score_threshold=self.config['analysis']['min_score_threshold']
            )

            if stored_count > 0:
                print(f"✅ Analysis stage completed: {stored_count} AI profiles stored")
                return True
            else:
                print("⚠️ Analysis stage completed but no profiles stored")
                return False

        except Exception as e:
            print(f"❌ Analysis stage failed: {e}")
            return False

    def run_reporting_stage(self) -> bool:
        """Run report generation stage"""
        print("\n" + "="*60)
        print("STAGE 3: REPORT GENERATION")
        print("="*60)

        try:
            # Import reporting script
            from generate_reports import ReportGenerator

            generator = ReportGenerator()
            reports_count = generator.run_report_generation(
                limit=self.config['reporting']['limit'],
                min_score=self.config['reporting']['min_score']
            )

            if reports_count > 0:
                print(f"✅ Reporting stage completed: {reports_count} reports generated")
                return True
            else:
                print("⚠️ Reporting stage completed but no reports generated")
                return False

        except Exception as e:
            print(f"❌ Reporting stage failed: {e}")
            return False

    def print_final_summary(self, start_status: Dict[str, Any], end_status: Dict[str, Any]):
        """Print final pipeline summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print("")

        # Stage results
        submissions_added = end_status['collection']['records_processed'] - start_status['collection']['records_processed']
        profiles_added = end_status['analysis']['profiles_generated'] - start_status['analysis']['profiles_generated']
        reports_added = end_status['reporting']['reports_created'] - start_status['reporting']['reports_created']

        print("STAGE RESULTS:")
        print(f"📥 Collection: +{submissions_added} submissions (total: {end_status['collection']['records_processed']})")
        print(f"🧠 Analysis: +{profiles_added} AI profiles (total: {end_status['analysis']['profiles_generated']})")
        print(f"📄 Reporting: +{reports_added} reports (total: {end_status['reporting']['reports_created']})")
        print("")

        # Success assessment
        stages_completed = sum([
            submissions_added > 0,
            profiles_added > 0,
            reports_added > 0
        ])

        if stages_completed == 3:
            print("🎉 PIPELINE SUCCESS: All stages completed successfully!")
        elif stages_completed >= 2:
            print("✅ PIPELINE PARTIAL SUCCESS: Most stages completed")
        else:
            print("⚠️ PIPELINE LIMITED: Few stages completed")

        print("")
        print("OUTPUT LOCATIONS:")
        print(f"📊 Database: {end_status['collection']['records_processed']} submissions in 'submissions' table")
        print(f"🎯 AI Profiles: {end_status['analysis']['profiles_generated']} profiles in 'app_opportunities' table")
        reports_dir = Path("reports")
        if reports_dir.exists():
            print(f"📋 Reports: {end_status['reporting']['reports_created']} files in {reports_dir}/")

        print("")
        print("🔄 To run again: python scripts/run_pipeline.py")
        print("📊 To monitor: Check Supabase Studio at http://127.0.0.1:54323")

    def run_full_pipeline(self) -> bool:
        """Run the complete 3-stage pipeline"""
        self.print_banner()

        # Get initial status
        print("🔍 Checking initial pipeline status...")
        start_status = self.get_pipeline_status()
        print(f"Initial state: {start_status['collection']['records_processed']} submissions, "
              f"{start_status['analysis']['profiles_generated']} profiles, "
              f"{start_status['reporting']['reports_created']} reports")

        # Run pipeline stages
        stage_results = []

        # Stage 1: Collection
        stage_results.append(self.run_collection_stage())
        time.sleep(2)  # Brief pause between stages

        # Stage 2: Analysis
        stage_results.append(self.run_analysis_stage())
        time.sleep(2)  # Brief pause between stages

        # Stage 3: Reporting
        stage_results.append(self.run_reporting_stage())

        # Get final status and print summary
        end_status = self.get_pipeline_status()
        self.print_final_summary(start_status, end_status)

        # Return overall success
        return all(stage_results)

    def run_individual_stage(self, stage: str) -> bool:
        """Run a single pipeline stage"""
        self.print_banner()
        print(f"Running individual stage: {stage.upper()}")

        # Get initial status
        start_status = self.get_pipeline_status()

        # Run requested stage
        if stage == 'collection':
            success = self.run_collection_stage()
        elif stage == 'analysis':
            success = self.run_analysis_stage()
        elif stage == 'reporting':
            success = self.run_reporting_stage()
        else:
            print(f"❌ Unknown stage: {stage}")
            print("Valid stages: collection, analysis, reporting")
            return False

        # Print stage summary
        end_status = self.get_pipeline_status()
        print(f"\nStage {stage.upper()}: {'✅ SUCCESS' if success else '❌ FAILED'}")

        return success


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='RedditHarbor Clean Pipeline Orchestrator')
    parser.add_argument('--stage',
                       choices=['collection', 'analysis', 'reporting'],
                       help='Run individual pipeline stage (default: run full pipeline)')
    parser.add_argument('--collection-limit', type=int, default=50,
                       help='Submissions per subreddit (default: 50)')
    parser.add_argument('--analysis-limit', type=int, default=100,
                       help='Submissions to analyze (default: 100)')
    parser.add_argument('--reporting-limit', type=int, default=25,
                       help='Reports to generate (default: 25)')

    args = parser.parse_args()

    try:
        orchestrator = PipelineOrchestrator()

        # Update configuration based on command line args
        if args.collection_limit != 50:
            orchestrator.config['collection']['submissions_per_subreddit'] = args.collection_limit
        if args.analysis_limit != 100:
            orchestrator.config['analysis']['limit'] = args.analysis_limit
        if args.reporting_limit != 25:
            orchestrator.config['reporting']['limit'] = args.reporting_limit

        # Run pipeline
        if args.stage:
            success = orchestrator.run_individual_stage(args.stage)
        else:
            success = orchestrator.run_full_pipeline()

        return success

    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)