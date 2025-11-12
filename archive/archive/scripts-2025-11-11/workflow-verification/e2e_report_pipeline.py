#!/usr/bin/env python3
"""
RedditHarbor E2E Report Generation Pipeline
Integrates DLT pre-filtering with database-connected report generation
Based on comprehensive testing guide findings and production-validated configurations
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta
import json
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class E2EReportPipeline:
    def __init__(self):
        self.pipeline_start = datetime.now()
        self.output_dir = Path("pipeline_results")
        self.output_dir.mkdir(exist_ok=True)

        # Production-validated configuration from testing guide
        self.sweet_spot_config = {
            'min_activity_score': 35.0,
            'min_opportunity_score': 25.0,
            'time_filter': 'week',
            'target_subreddits': [
                'investing', 'stocks', 'financialindependence',
                'realestateinvesting', 'productivity',
                'selfimprovement', 'entrepreneur', 'startups'
            ]
        }

        print("🚀 REDDITHARBOR E2E REPORT GENERATION PIPELINE")
        print("=" * 70)
        print("📊 Configuration: Production-validated sweet spot")
        print(f"🎯 Activity Score: ≥{self.sweet_spot_config['min_activity_score']}")
        print(f"🧠 Opportunity Score: ≥{self.sweet_spot_config['min_opportunity_score']}")
        print(f"⏰ Time Filter: {self.sweet_spot_config['time_filter']}")
        print(f"📍 Target Subreddits: {len(self.sweet_spot_config['target_subreddits'])}")

    def run_dlt_collection(self, dry_run=False):
        """Run DLT activity collection with production configuration"""
        print("\n📡 PHASE 1: DLT ACTIVITY COLLECTION")
        print("-" * 50)

        cmd = [
            'source', '.venv/bin/activate', '&&',
            'python', 'scripts/run_dlt_activity_collection.py',
            '--subreddits', ','.join(self.sweet_spot_config['target_subreddits']),
            '--min-activity', str(self.sweet_spot_config['min_activity_score']),
            '--min-opportunity-score', str(self.sweet_spot_config['min_opportunity_score']),
            '--time-filter', self.sweet_spot_config['time_filter'],
            '--verbose'
        ]

        if dry_run:
            cmd.append('--dry-run')

        cmd_str = ' '.join(cmd)

        print(f"🔄 Running: {cmd_str}")

        try:
            # Run DLT collection
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )

            # Log results
            dlt_log = self.output_dir / f"dlt_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(dlt_log, 'w') as f:
                f.write(f"DLT Collection Log - {datetime.now()}\n")
                f.write(f"Command: {cmd_str}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"\nSTDOUT:\n{result.stdout}\n")
                f.write(f"\nSTDERR:\n{result.stderr}\n")

            if result.returncode == 0:
                print("✅ DLT collection completed successfully")
                return True
            else:
                print(f"❌ DLT collection failed with code {result.returncode}")
                print(f"📄 Log saved to: {dlt_log}")
                return False

        except subprocess.TimeoutExpired:
            print("⏰ DLT collection timed out after 30 minutes")
            return False
        except Exception as e:
            print(f"❌ DLT collection error: {e}")
            return False

    def run_ai_profiling(self, min_score=20):
        """Run AI opportunity profiling on collected data"""
        print("\n🧠 PHASE 2: AI OPPORTUNITY PROFILING")
        print("-" * 50)

        cmd = [
            'source', '.venv/bin/activate', '&&',
            'python', 'scripts/batch_opportunity_scoring.py',
            '--verbose',
            '--min-score', str(min_score)
        ]

        cmd_str = ' '.join(cmd)
        print(f"🔄 Running AI profiling with min score: {min_score}")

        try:
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=2400  # 40 minutes
            )

            # Log results
            ai_log = self.output_dir / f"ai_profiling_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(ai_log, 'w') as f:
                f.write(f"AI Profiling Log - {datetime.now()}\n")
                f.write(f"Command: {cmd_str}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"\nSTDOUT:\n{result.stdout}\n")
                f.write(f"\nSTDERR:\n{result.stderr}\n")

            if result.returncode == 0:
                print("✅ AI profiling completed successfully")

                # Extract profiling metrics from output
                output_lines = result.stdout.split('\n')
                profiles_created = 0
                avg_score = 0

                for line in output_lines:
                    if "profiles generated" in line.lower():
                        profiles_created = line.split()[-2]
                    elif "average score" in line.lower():
                        avg_score = line.split()[-1]

                print(f"📊 Generated {profiles_created} AI profiles")
                print(f"📈 Average opportunity score: {avg_score}")
                return True
            else:
                print(f"❌ AI profiling failed with code {result.returncode}")
                print(f"📄 Log saved to: {ai_log}")
                return False

        except subprocess.TimeoutExpired:
            print("⏰ AI profiling timed out after 40 minutes")
            return False
        except Exception as e:
            print(f"❌ AI profiling error: {e}")
            return False

    def generate_db_connected_reports(self):
        """Generate database-connected reports"""
        print("\n📊 PHASE 3: DATABASE-CONNECTED REPORT GENERATION")
        print("-" * 50)

        cmd = [
            'source', '.venv/bin/activate', '&&',
            'python', 'scripts/generate_db_connected_reports.py'
        ]

        cmd_str = ' '.join(cmd)
        print("🔄 Generating live database-connected reports...")

        try:
            result = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )

            # Log results
            report_log = self.output_dir / f"report_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(report_log, 'w') as f:
                f.write(f"Report Generation Log - {datetime.now()}\n")
                f.write(f"Command: {cmd_str}\n")
                f.write(f"Exit Code: {result.returncode}\n")
                f.write(f"\nSTDOUT:\n{result.stdout}\n")
                f.write(f"\nSTDERR:\n{result.stderr}\n")

            if result.returncode == 0:
                print("✅ Report generation completed successfully")

                # Extract metrics from output
                output_lines = result.stdout.split('\n')
                reports_generated = 0

                for line in output_lines:
                    if "database-connected AI profile reports" in line.lower():
                        reports_generated = line.split()[1]

                print(f"📝 Generated {reports_generated} database-connected reports")
                print(f"📁 Location: db_connected_reports/")
                return True
            else:
                print(f"❌ Report generation failed with code {result.returncode}")
                print(f"📄 Log saved to: {report_log}")
                return False

        except subprocess.TimeoutExpired:
            print("⏰ Report generation timed out after 10 minutes")
            return False
        except Exception as e:
            print(f"❌ Report generation error: {e}")
            return False

    def validate_pipeline_results(self):
        """Validate pipeline results and generate summary"""
        print("\n✅ PHASE 4: PIPELINE VALIDATION & SUMMARY")
        print("-" * 50)

        try:
            # Check database connection
            from supabase import create_client
            from config.settings import SUPABASE_URL, SUPABASE_KEY

            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Get AI profiles count
            profiles_response = supabase.table('app_opportunities').select('count', count='exact').execute()
            ai_profiles_count = profiles_response.count or 0

            # Get Reddit submissions count
            reddit_response = supabase.table('reddit_submissions').select('count', count='exact').execute()
            reddit_count = reddit_response.count or 0

            # Calculate pipeline duration
            pipeline_duration = datetime.now() - self.pipeline_start

            # Generate pipeline summary
            summary = {
                'pipeline_completed_at': datetime.now().isoformat(),
                'pipeline_duration_minutes': pipeline_duration.total_seconds() / 60,
                'ai_profiles_count': ai_profiles_count,
                'reddit_submissions_count': reddit_count,
                'configuration_used': self.sweet_spot_config,
                'success_rate': 100 if ai_profiles_count > 0 else 0,
                'reports_location': 'db_connected_reports/'
            }

            # Save summary
            summary_file = self.output_dir / f"pipeline_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            # Display results
            print(f"🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"⏰ Duration: {pipeline_duration.total_seconds() / 60:.1f} minutes")
            print(f"🧠 AI Profiles: {ai_profiles_count}")
            print(f"📊 Reddit Submissions: {reddit_count:,}")
            print(f"📁 Reports: db_connected_reports/")
            print(f"📋 Summary: {summary_file}")

            return summary

        except Exception as e:
            print(f"❌ Validation error: {e}")
            return None

    def run_complete_pipeline(self, dry_run=False, skip_collection=False, skip_profiling=False):
        """Run the complete E2E pipeline"""
        print(f"\n🚀 STARTING COMPLETE E2E PIPELINE")
        print(f"📅 Started: {self.pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")

        pipeline_success = True

        # Phase 1: DLT Collection (if not skipped)
        if not skip_collection:
            if not self.run_dlt_collection(dry_run=dry_run):
                pipeline_success = False
                if not dry_run:
                    print("⚠️ DLT collection failed, but continuing pipeline...")
        else:
            print("⏭️ Skipping DLT collection (as requested)")

        # Phase 2: AI Profiling (if not skipped)
        if not skip_profiling:
            if not self.run_ai_profiling():
                pipeline_success = False
                if not dry_run:
                    print("⚠️ AI profiling failed, but continuing pipeline...")
        else:
            print("⏭️ Skipping AI profiling (as requested)")

        # Phase 3: Report Generation
        if not self.generate_db_connected_reports():
            pipeline_success = False

        # Phase 4: Validation
        summary = self.validate_pipeline_results()

        if pipeline_success and summary:
            print(f"\n🎯 E2E PIPELINE STATUS: ✅ SUCCESS")
        else:
            print(f"\n🚨 E2E PIPELINE STATUS: ⚠️ COMPLETED WITH ISSUES")

        return pipeline_success, summary

def main():
    parser = argparse.ArgumentParser(description='RedditHarbor E2E Report Generation Pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Run DLT collection in dry-run mode')
    parser.add_argument('--skip-collection', action='store_true', help='Skip DLT collection phase')
    parser.add_argument('--skip-profiling', action='store_true', help='Skip AI profiling phase')
    parser.add_argument('--min-score', type=int, default=20, help='Minimum opportunity score for AI profiling')

    args = parser.parse_args()

    try:
        pipeline = E2EReportPipeline()
        success, summary = pipeline.run_complete_pipeline(
            dry_run=args.dry_run,
            skip_collection=args.skip_collection,
            skip_profiling=args.skip_profiling
        )

        if success:
            print(f"\n🎉 Pipeline completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️ Pipeline completed with some issues")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n🛑 Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()