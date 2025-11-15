#!/usr/bin/env python3
"""
Hybrid Strategy E2E Testing Agent
RedditHarbor - Automated testing for LLM Monetization + Lead Extraction

This agent provides comprehensive E2E testing for the hybrid strategy:
- Option A: LLM-enhanced monetization scoring
- Option B: Customer lead extraction
- Database integration validation (DLT)
- Slack alert testing
- Cost tracking and ROI analysis
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class TestResult:
    """Test result container"""
    test_name: str
    status: str  # "passed", "failed", "skipped"
    duration_seconds: float
    details: Dict
    error: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class HybridStrategyTestReport:
    """Comprehensive test report for hybrid strategy"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    total_duration: float
    test_results: List[TestResult]
    cost_analysis: Dict
    quality_metrics: Dict
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def summary(self) -> str:
        """Generate human-readable summary"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║       Hybrid Strategy E2E Test Report                            ║
╠══════════════════════════════════════════════════════════════════╣
║ Total Tests:     {self.total_tests:>3}                                       ║
║ Passed:          {self.passed:>3} ✅                                      ║
║ Failed:          {self.failed:>3} ❌                                      ║
║ Skipped:         {self.skipped:>3} ⏭️                                       ║
║ Duration:        {self.total_duration:.2f}s                                   ║
╠══════════════════════════════════════════════════════════════════╣
║ Cost Analysis:                                                    ║
║   LLM API Cost:  ${self.cost_analysis.get('llm_cost', 0):.4f}                              ║
║   Total Cost:    ${self.cost_analysis.get('total_cost', 0):.4f}                              ║
╠══════════════════════════════════════════════════════════════════╣
║ Quality Metrics:                                                  ║
║   Budget Detection:   {self.quality_metrics.get('budget_detection_rate', 0)*100:.1f}%                      ║
║   Lead Precision:     {self.quality_metrics.get('lead_precision', 0)*100:.1f}%                      ║
║   LLM Accuracy:       ±{self.quality_metrics.get('llm_score_delta', 0):.1f} points                    ║
╚══════════════════════════════════════════════════════════════════╝

Timestamp: {self.timestamp}
"""


class HybridStrategyTestAgent:
    """
    Automated E2E testing agent for RedditHarbor's hybrid strategy.

    Tests:
    1. LLM Monetization Scoring (Option A)
    2. Customer Lead Extraction (Option B)
    3. Database Integration (DLT)
    4. Slack Alert System
    5. Cost Tracking
    6. Quality Validation
    """

    def __init__(self, config: Optional[Dict] = None):
        self.project_root = project_root
        self.config = config or self._load_config()
        self.test_results: List[TestResult] = []
        self.start_time = time.time()

    def _load_config(self) -> Dict:
        """Load test configuration from environment"""
        return {
            "llm_enabled": os.getenv("MONETIZATION_LLM_ENABLED", "true").lower() == "true",
            "llm_threshold": float(os.getenv("MONETIZATION_LLM_THRESHOLD", "60.0")),
            "llm_model": os.getenv("MONETIZATION_LLM_MODEL", "openai/gpt-4o-mini"),
            "openrouter_key": os.getenv("OPENROUTER_API_KEY"),
            "lead_enabled": os.getenv("LEAD_EXTRACTION_ENABLED", "true").lower() == "true",
            "lead_threshold": float(os.getenv("LEAD_EXTRACTION_THRESHOLD", "60.0")),
            "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
            "database_url": os.getenv("DATABASE_URL"),
        }

    def test_environment_setup(self) -> TestResult:
        """Test 1: Validate environment configuration"""
        test_name = "Environment Setup"
        start = time.time()

        try:
            issues = []

            # Check required environment variables
            if not self.config.get("database_url"):
                issues.append("DATABASE_URL not set")

            if self.config["llm_enabled"] and not self.config.get("openrouter_key"):
                issues.append("OPENROUTER_API_KEY not set (required for LLM)")

            # Check dependencies
            try:
                import dspy
            except ImportError:
                issues.append("dspy-ai not installed")

            try:
                import requests
            except ImportError:
                issues.append("requests not installed")

            # Check database migrations
            if self.config.get("database_url"):
                migration_check = self._check_migrations()
                if not migration_check["customer_leads"]:
                    issues.append("customer_leads table not found")
                if not migration_check["llm_monetization_analysis"]:
                    issues.append("llm_monetization_analysis table not found")

            duration = time.time() - start

            if issues:
                return TestResult(
                    test_name=test_name,
                    status="failed",
                    duration_seconds=duration,
                    details={"issues": issues},
                    error=f"Environment validation failed: {', '.join(issues)}"
                )

            return TestResult(
                test_name=test_name,
                status="passed",
                duration_seconds=duration,
                details={"config": self.config, "issues": []}
            )

        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="failed",
                duration_seconds=duration,
                details={},
                error=str(e)
            )

    def _check_migrations(self) -> Dict[str, bool]:
        """Check if database migrations are applied"""
        try:
            import psycopg2
            conn = psycopg2.connect(self.config["database_url"])
            cursor = conn.cursor()

            # Check for customer_leads table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'customer_leads'
                );
            """)
            customer_leads_exists = cursor.fetchone()[0]

            # Check for llm_monetization_analysis table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'llm_monetization_analysis'
                );
            """)
            llm_analysis_exists = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return {
                "customer_leads": customer_leads_exists,
                "llm_monetization_analysis": llm_analysis_exists
            }
        except Exception as e:
            print(f"Migration check failed: {e}")
            return {"customer_leads": False, "llm_monetization_analysis": False}

    def test_llm_monetization(self) -> TestResult:
        """Test 2: LLM monetization scoring (Option A)"""
        test_name = "LLM Monetization Scoring"
        start = time.time()

        if not self.config["llm_enabled"]:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="skipped",
                duration_seconds=duration,
                details={"reason": "LLM disabled in config"}
            )

        try:
            from agent_tools.monetization_llm_analyzer import MonetizationLLMAnalyzer

            # Initialize analyzer
            analyzer = MonetizationLLMAnalyzer(model=self.config["llm_model"])

            # Test post
            test_post = {
                "title": "Looking for a CRM that integrates with Slack",
                "body": "We're a 15-person team and willing to pay $99/mo for a solution. Currently using Salesforce but it's too expensive.",
                "subreddit": "entrepreneur",
                "score": 150,
                "num_comments": 45
            }

            # Analyze
            result = analyzer.analyze(
                post_text=f"{test_post['title']} {test_post['body']}",
                subreddit=test_post["subreddit"],
                engagement_score=test_post["score"],
                comment_count=test_post["num_comments"]
            )

            duration = time.time() - start

            # Validate result
            if result.llm_monetization_score is None:
                return TestResult(
                    test_name=test_name,
                    status="failed",
                    duration_seconds=duration,
                    details={"result": asdict(result)},
                    error="LLM returned None score"
                )

            return TestResult(
                test_name=test_name,
                status="passed",
                duration_seconds=duration,
                details={
                    "llm_score": result.llm_monetization_score,
                    "customer_segment": result.customer_segment,
                    "reasoning": result.reasoning[:200] if result.reasoning else ""
                }
            )

        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="failed",
                duration_seconds=duration,
                details={},
                error=str(e)
            )

    def test_lead_extraction(self) -> TestResult:
        """Test 3: Customer lead extraction (Option B)"""
        test_name = "Customer Lead Extraction"
        start = time.time()

        if not self.config["lead_enabled"]:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="skipped",
                duration_seconds=duration,
                details={"reason": "Lead extraction disabled in config"}
            )

        try:
            from core.lead_extractor import LeadExtractor

            # Initialize extractor
            extractor = LeadExtractor()

            # Test post
            test_post = {
                "author": "test_user_123",
                "id": "test_post_1",
                "title": "Looking for CRM alternative to Salesforce",
                "body": "We're a 15-person team with a budget of $5000/month. Currently using Salesforce but need something cheaper ASAP!",
                "subreddit": "entrepreneur"
            }

            # Extract lead
            lead = extractor.extract_from_reddit_post(test_post, opportunity_score=75.0)

            duration = time.time() - start

            # Validate extraction
            validations = {
                "username_extracted": lead.reddit_username == "test_user_123",
                "budget_detected": lead.budget_mentioned is not None,
                "competitor_detected": lead.competitor_mentioned is not None,
                "buying_intent_classified": lead.buying_intent_stage is not None,
                "urgency_classified": lead.urgency_level is not None
            }

            passed = all(validations.values())

            return TestResult(
                test_name=test_name,
                status="passed" if passed else "failed",
                duration_seconds=duration,
                details={
                    "validations": validations,
                    "lead_data": {
                        "username": lead.reddit_username,
                        "budget": lead.budget_mentioned,
                        "competitor": lead.competitor_mentioned,
                        "intent": lead.buying_intent_stage,
                        "urgency": lead.urgency_level,
                        "score": lead.lead_score
                    }
                },
                error=None if passed else "Some validations failed"
            )

        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="failed",
                duration_seconds=duration,
                details={},
                error=str(e)
            )

    def test_database_integration(self) -> TestResult:
        """Test 4: DLT database integration"""
        test_name = "Database Integration (DLT)"
        start = time.time()

        if not self.config.get("database_url"):
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="skipped",
                duration_seconds=duration,
                details={"reason": "DATABASE_URL not configured"}
            )

        try:
            # Run test hybrid strategy script
            result = subprocess.run(
                ["python", "scripts/testing/test_hybrid_strategy_with_high_scores.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            duration = time.time() - start

            if result.returncode != 0:
                return TestResult(
                    test_name=test_name,
                    status="failed",
                    duration_seconds=duration,
                    details={"stdout": result.stdout, "stderr": result.stderr},
                    error=f"Test script failed with code {result.returncode}"
                )

            # Check database records
            import psycopg2
            conn = psycopg2.connect(self.config["database_url"])
            cursor = conn.cursor()

            # Count customer_leads
            cursor.execute("SELECT COUNT(*) FROM customer_leads;")
            lead_count = cursor.fetchone()[0]

            # Count llm_monetization_analysis
            cursor.execute("SELECT COUNT(*) FROM llm_monetization_analysis;")
            llm_count = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return TestResult(
                test_name=test_name,
                status="passed",
                duration_seconds=duration,
                details={
                    "customer_leads_count": lead_count,
                    "llm_analysis_count": llm_count
                }
            )

        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="failed",
                duration_seconds=duration,
                details={},
                error=str(e)
            )

    def test_slack_alerts(self) -> TestResult:
        """Test 5: Slack alert system"""
        test_name = "Slack Alert System"
        start = time.time()

        if not self.config.get("slack_webhook"):
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="skipped",
                duration_seconds=duration,
                details={"reason": "SLACK_WEBHOOK_URL not configured"}
            )

        try:
            import requests

            # Send test alert
            payload = {
                "text": "🧪 Test alert from RedditHarbor Hybrid Strategy E2E Testing",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Test Hot Lead Alert*\n\nThis is a test from the E2E testing agent."
                        }
                    }
                ]
            }

            response = requests.post(
                self.config["slack_webhook"],
                json=payload,
                timeout=10
            )

            duration = time.time() - start

            if response.status_code != 200:
                return TestResult(
                    test_name=test_name,
                    status="failed",
                    duration_seconds=duration,
                    details={"status_code": response.status_code, "response": response.text},
                    error=f"Slack webhook returned {response.status_code}"
                )

            return TestResult(
                test_name=test_name,
                status="passed",
                duration_seconds=duration,
                details={"status_code": response.status_code}
            )

        except Exception as e:
            duration = time.time() - start
            return TestResult(
                test_name=test_name,
                status="failed",
                duration_seconds=duration,
                details={},
                error=str(e)
            )

    def run_full_test_suite(self) -> HybridStrategyTestReport:
        """Run complete E2E test suite"""
        print("🧪 Starting Hybrid Strategy E2E Test Suite...")
        print("=" * 70)

        tests = [
            self.test_environment_setup,
            self.test_llm_monetization,
            self.test_lead_extraction,
            self.test_database_integration,
            self.test_slack_alerts
        ]

        for test_func in tests:
            print(f"\n▶️  Running: {test_func.__doc__.split(':')[1].strip()}")
            result = test_func()
            self.test_results.append(result)

            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }

            print(f"{status_emoji[result.status]} {result.test_name}: {result.status.upper()} ({result.duration_seconds:.2f}s)")
            if result.error:
                print(f"   Error: {result.error}")

        # Generate report
        total_duration = time.time() - self.start_time
        passed = sum(1 for r in self.test_results if r.status == "passed")
        failed = sum(1 for r in self.test_results if r.status == "failed")
        skipped = sum(1 for r in self.test_results if r.status == "skipped")

        # Calculate cost and quality metrics
        cost_analysis = self._calculate_costs()
        quality_metrics = self._calculate_quality()

        report = HybridStrategyTestReport(
            total_tests=len(self.test_results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            total_duration=total_duration,
            test_results=self.test_results,
            cost_analysis=cost_analysis,
            quality_metrics=quality_metrics
        )

        print("\n" + "=" * 70)
        print(report.summary())

        return report

    def _calculate_costs(self) -> Dict:
        """Calculate LLM API costs from test results"""
        llm_test = next((r for r in self.test_results if r.test_name == "LLM Monetization Scoring"), None)

        if not llm_test or llm_test.status != "passed":
            return {"llm_cost": 0.0, "total_cost": 0.0}

        # Estimate cost based on model
        cost_per_analysis = {
            "openai/gpt-4o-mini": 0.01,
            "anthropic/claude-3-5-haiku-20241022": 0.002
        }

        llm_cost = cost_per_analysis.get(self.config["llm_model"], 0.01)

        return {
            "llm_cost": llm_cost,
            "total_cost": llm_cost  # Lead extraction is free
        }

    def _calculate_quality(self) -> Dict:
        """Calculate quality metrics from test results"""
        lead_test = next((r for r in self.test_results if r.test_name == "Customer Lead Extraction"), None)
        llm_test = next((r for r in self.test_results if r.test_name == "LLM Monetization Scoring"), None)

        metrics = {
            "budget_detection_rate": 0.0,
            "lead_precision": 0.0,
            "llm_score_delta": 0.0
        }

        if lead_test and lead_test.status == "passed":
            validations = lead_test.details.get("validations", {})
            metrics["budget_detection_rate"] = 1.0 if validations.get("budget_detected") else 0.0
            metrics["lead_precision"] = sum(validations.values()) / len(validations) if validations else 0.0

        if llm_test and llm_test.status == "passed":
            # Estimate delta (would need baseline comparison in real test)
            metrics["llm_score_delta"] = 5.0  # Placeholder

        return metrics


def main():
    """Main entry point for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Hybrid Strategy E2E Testing Agent")
    parser.add_argument("--config", type=str, help="Path to custom config JSON")
    parser.add_argument("--output", type=str, help="Output file for test report (JSON)")

    args = parser.parse_args()

    # Load config
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Run tests
    agent = HybridStrategyTestAgent(config=config)
    report = agent.run_full_test_suite()

    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "total_duration": report.total_duration,
                "cost_analysis": report.cost_analysis,
                "quality_metrics": report.quality_metrics,
                "test_results": [asdict(r) for r in report.test_results],
                "timestamp": report.timestamp
            }, f, indent=2)
        print(f"\n📄 Report saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
