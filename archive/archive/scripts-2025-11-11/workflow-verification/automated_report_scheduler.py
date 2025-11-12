#!/usr/bin/env python3
"""
RedditHarbor Automated Report Scheduler
Provides scheduled and on-demand report generation with validation checkpoints
Based on E2E testing guide recommendations and production-validated configurations
"""

import sys
import schedule
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class AutomatedReportScheduler:
    def __init__(self):
        self.config_file = Path("config/automation_config.json")
        self.log_dir = Path("automation_logs")
        self.log_dir.mkdir(exist_ok=True)

        # Default configuration based on testing guide findings
        self.default_config = {
            "scheduling": {
                "daily_reports": True,
                "weekly_reports": True,
                "daily_time": "09:00",
                "weekly_day": "monday",
                "weekly_time": "09:00"
            },
            "pipeline_config": {
                "min_activity_score": 35.0,
                "min_opportunity_score": 25.0,
                "time_filter": "week",
                "target_subreddits": [
                    "investing", "stocks", "financialindependence",
                    "realestateinvesting", "productivity",
                    "selfimprovement", "entrepreneur", "startups"
                ],
                "min_ai_score": 20
            },
            "validation": {
                "min_ai_profiles_threshold": 3,
                "min_reddit_posts_threshold": 50,
                "max_pipeline_duration_minutes": 60,
                "require_evidence_strength": 15.0
            },
            "notifications": {
                "success_notifications": True,
                "failure_alerts": True,
                "performance_metrics": True
            }
        }

        self.config = self.load_config()
        self.performance_history = []

    def load_config(self) -> Dict:
        """Load automation configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                return {**self.default_config, **user_config}
            except Exception as e:
                print(f"⚠️ Error loading config, using defaults: {e}")

        # Save default config for future use
        self.config_file.parent.mkdir(exist_ok=True)
        self.save_config(self.default_config)
        return self.default_config

    def save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving config: {e}")

    def log_event(self, event_type: str, message: str, data: Optional[Dict] = None):
        """Log automation events with timestamps"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "data": data or {}
        }

        # Log to daily file
        log_file = self.log_dir / f"automation_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Also print to console for immediate feedback
        print(f"[{timestamp}] {event_type}: {message}")

    def run_e2e_pipeline(self, trigger_source: str = "scheduled") -> bool:
        """Run E2E pipeline with validation checkpoints"""
        start_time = datetime.now()

        self.log_event("pipeline_start", f"E2E Pipeline triggered by {trigger_source}")

        try:
            # Import and run the E2E pipeline
            from e2e_report_pipeline import E2EReportPipeline

            pipeline = E2EReportPipeline()
            success, summary = pipeline.run_complete_pipeline(
                dry_run=False,
                skip_collection=False,
                skip_profiling=False
            )

            # Calculate performance metrics
            duration = (datetime.now() - start_time).total_seconds() / 60

            performance_metrics = {
                "duration_minutes": duration,
                "success": success,
                "trigger_source": trigger_source,
                "ai_profiles_count": summary.get('ai_profiles_count', 0) if summary else 0,
                "reddit_submissions_count": summary.get('reddit_submissions_count', 0) if summary else 0,
                "pipeline_success_rate": 100 if success else 0
            }

            self.performance_history.append(performance_metrics)

            # Validation checkpoints based on testing guide
            validation_results = self.run_validation_checkpoints(summary, performance_metrics)

            self.log_event("pipeline_complete",
                         f"Pipeline completed in {duration:.1f} minutes",
                         {"metrics": performance_metrics, "validation": validation_results})

            return success and validation_results["passed"]

        except Exception as e:
            self.log_event("pipeline_error", f"Pipeline failed: {str(e)}")
            return False

    def run_validation_checkpoints(self, summary: Optional[Dict], metrics: Dict) -> Dict:
        """Run validation checkpoints based on E2E testing guide findings"""
        validation_config = self.config["validation"]

        validation_results = {
            "passed": True,
            "checks": []
        }

        if not summary:
            validation_results["passed"] = False
            validation_results["checks"].append({
                "check": "pipeline_summary_missing",
                "status": "FAILED",
                "message": "Pipeline summary not available"
            })
            return validation_results

        # Check 1: Minimum AI profiles threshold
        ai_profiles_count = summary.get('ai_profiles_count', 0)
        min_ai_threshold = validation_config["min_ai_profiles_threshold"]

        if ai_profiles_count >= min_ai_threshold:
            validation_results["checks"].append({
                "check": "ai_profiles_threshold",
                "status": "PASSED",
                "message": f"{ai_profiles_count} profiles >= {min_ai_threshold} threshold"
            })
        else:
            validation_results["passed"] = False
            validation_results["checks"].append({
                "check": "ai_profiles_threshold",
                "status": "FAILED",
                "message": f"{ai_profiles_count} profiles < {min_ai_threshold} threshold"
            })

        # Check 2: Pipeline duration
        duration = metrics.get('duration_minutes', 0)
        max_duration = validation_config["max_pipeline_duration_minutes"]

        if duration <= max_duration:
            validation_results["checks"].append({
                "check": "pipeline_duration",
                "status": "PASSED",
                "message": f"{duration:.1f}min <= {max_duration}min limit"
            })
        else:
            validation_results["checks"].append({
                "check": "pipeline_duration",
                "status": "WARNING",
                "message": f"{duration:.1f}min > {max_duration}min limit"
            })

        # Check 3: Configuration compliance
        config_used = summary.get('configuration_used', {})
        expected_config = self.config["pipeline_config"]

        config_compliant = (
            config_used.get('min_activity_score') == expected_config['min_activity_score'] and
            config_used.get('min_opportunity_score') == expected_config['min_opportunity_score'] and
            config_used.get('time_filter') == expected_config['time_filter']
        )

        if config_compliant:
            validation_results["checks"].append({
                "check": "configuration_compliance",
                "status": "PASSED",
                "message": "Using validated sweet spot configuration"
            })
        else:
            validation_results["checks"].append({
                "check": "configuration_compliance",
                "status": "WARNING",
                "message": "Configuration differs from validated sweet spot"
            })

        return validation_results

    def daily_report_job(self):
        """Scheduled daily report generation job"""
        self.log_event("scheduled_job", "Starting daily report generation")
        success = self.run_e2e_pipeline("daily_schedule")

        if success:
            self.log_event("scheduled_job_success", "Daily reports generated successfully")
        else:
            self.log_event("scheduled_job_failure", "Daily report generation failed")

    def weekly_report_job(self):
        """Scheduled weekly comprehensive report generation job"""
        self.log_event("scheduled_job", "Starting weekly comprehensive report generation")

        # For weekly reports, we might want to run with more comprehensive settings
        # or include additional analysis
        success = self.run_e2e_pipeline("weekly_schedule")

        if success:
            self.log_event("scheduled_job_success", "Weekly reports generated successfully")
            self.generate_weekly_summary()
        else:
            self.log_event("scheduled_job_failure", "Weekly report generation failed")

    def generate_weekly_summary(self):
        """Generate weekly performance summary"""
        if not self.performance_history:
            return

        # Filter last week's performance
        one_week_ago = datetime.now() - timedelta(days=7)
        weekly_performance = [
            p for p in self.performance_history
            if datetime.fromisoformat(p.get('timestamp', '') or datetime.now().isoformat()) > one_week_ago
        ]

        if not weekly_performance:
            return

        # Calculate weekly metrics
        total_runs = len(weekly_performance)
        successful_runs = sum(1 for p in weekly_performance if p.get('success', False))
        avg_duration = sum(p.get('duration_minutes', 0) for p in weekly_performance) / total_runs
        total_ai_profiles = sum(p.get('ai_profiles_count', 0) for p in weekly_performance)

        weekly_summary = {
            "week_ending": datetime.now().isoformat(),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": (successful_runs / total_runs) * 100,
            "average_duration_minutes": avg_duration,
            "total_ai_profiles_generated": total_ai_profiles,
            "daily_average_ai_profiles": total_ai_profiles / 7
        }

        # Save weekly summary
        summary_file = self.log_dir / f"weekly_summary_{datetime.now().strftime('%Y%m%d')}.json"
        with open(summary_file, 'w') as f:
            json.dump(weekly_summary, f, indent=2)

        self.log_event("weekly_summary", f"Weekly summary generated: {successful_runs}/{total_runs} successful")

    def setup_scheduler(self):
        """Setup the scheduler with configured jobs"""
        config = self.config["scheduling"]

        if config["daily_reports"]:
            schedule.every().day.at(config["daily_time"]).do(self.daily_report_job)
            self.log_event("scheduler_setup", f"Daily reports scheduled at {config['daily_time']}")

        if config["weekly_reports"]:
            getattr(schedule.every(), config["weekly_day"]).at(config["weekly_time"]).do(self.weekly_report_job)
            self.log_event("scheduler_setup", f"Weekly reports scheduled on {config['weekly_day']}s at {config['weekly_time']}")

    def run_scheduler(self):
        """Run the scheduler continuously"""
        self.log_event("scheduler_start", "Starting automated report scheduler")

        self.setup_scheduler()

        print("🤖 RedditHarbor Automated Report Scheduler")
        print("=" * 50)
        print("📅 Scheduled Jobs:")
        schedule.print_jobs()
        print("\n🔄 Running scheduler... (Press Ctrl+C to stop)")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.log_event("scheduler_stop", "Scheduler stopped by user")
            print("\n🛑 Scheduler stopped")

    def run_on_demand_report(self):
        """Run on-demand report generation"""
        self.log_event("on_demand_trigger", "Manual report generation requested")
        success = self.run_e2e_pipeline("on_demand")

        if success:
            print("✅ On-demand report generation completed successfully")
        else:
            print("❌ On-demand report generation failed")

        return success

    def show_status(self):
        """Show current scheduler status and performance metrics"""
        print("📊 RedditHarbor Report Scheduler Status")
        print("=" * 50)

        # Configuration
        config = self.config["scheduling"]
        print(f"📅 Daily Reports: {'✅' if config['daily_reports'] else '❌'} at {config['daily_time']}")
        print(f"📅 Weekly Reports: {'✅' if config['weekly_reports'] else '❌'} on {config['weekly_day']}s at {config['weekly_time']}")

        # Recent performance
        if self.performance_history:
            recent_runs = self.performance_history[-10:]  # Last 10 runs
            successful_runs = sum(1 for p in recent_runs if p.get('success', False))
            avg_duration = sum(p.get('duration_minutes', 0) for p in recent_runs) / len(recent_runs)

            print(f"\n📈 Recent Performance (last {len(recent_runs)} runs):")
            print(f"✅ Success Rate: {successful_runs}/{len(recent_runs)} ({(successful_runs/len(recent_runs))*100:.1f}%)")
            print(f"⏱️ Average Duration: {avg_duration:.1f} minutes")

            if recent_runs:
                last_run = recent_runs[-1]
                last_run_time = datetime.fromisoformat(last_run.get('timestamp', ''))
                print(f"🕐 Last Run: {last_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"🧠 AI Profiles Generated: {last_run.get('ai_profiles_count', 0)}")

        # Scheduled jobs
        print(f"\n⏰ Scheduled Jobs:")
        schedule.print_jobs()

def main():
    parser = argparse.ArgumentParser(description='RedditHarbor Automated Report Scheduler')
    parser.add_argument('--run-once', action='store_true', help='Run one-time on-demand report generation')
    parser.add_argument('--status', action='store_true', help='Show scheduler status and exit')
    parser.add_argument('--config', action='store_true', help='Show current configuration')

    args = parser.parse_args()

    try:
        scheduler = AutomatedReportScheduler()

        if args.config:
            print("📋 Current Configuration:")
            print(json.dumps(scheduler.config, indent=2))
            return

        if args.status:
            scheduler.show_status()
            return

        if args.run_once:
            scheduler.run_on_demand_report()
            return

        # Run the continuous scheduler
        scheduler.run_scheduler()

    except KeyboardInterrupt:
        print("\n🛑 Scheduler stopped by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Scheduler error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()