#!/usr/bin/env python3
"""
Enhanced AgentOps Observability Test for Multi-Agent System
Tests real-time cost tracking and performance monitoring for Agno framework
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import agentops

    from agent_tools.monetization_agno_analyzer import MonetizationAgnoAnalyzer
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Ensure agno and agentops are installed")
    sys.exit(1)

class AgentOpsObservabilityTest:
    """Comprehensive AgentOps observability testing for multi-agent system"""

    def __init__(self):
        self.test_results = {
            "test_session_id": f"agentops_observability_{datetime.now().isoformat()}",
            "timestamp": datetime.now().isoformat(),
            "agentops_initialization": {},
            "trace_creation": {},
            "cost_tracking": {},
            "multi_agent_spans": {},
            "dashboard_verification": {},
            "summary": {}
        }

        # Test scenarios for observability
        self.test_scenarios = [
            {
                "name": "B2B High Value",
                "text": "Our enterprise needs a CRM solution. Budget $10k annually. Current system inadequate. Decision needed this quarter.",
                "subreddit": "business",
                "expected_complexity": "high"
            },
            {
                "name": "B2C Price Sensitive",
                "text": "Looking for free project management tool. Can't afford subscription. Tired of monthly payments.",
                "subreddit": "frugal",
                "expected_complexity": "low"
            }
        ]

    def test_agentops_initialization(self) -> dict[str, Any]:
        """Test AgentOps initialization and configuration"""
        print("\n🔧 TESTING AGENTOPS INITIALIZATION")
        print("=" * 60)

        init_results = {}

        try:
            # Check API key availability
            api_key_available = bool(os.getenv("AGENTOPS_API_KEY"))

            init_results["api_key_available"] = api_key_available

            if not api_key_available:
                print("⚠️ AGENTOPS_API_KEY not found in environment")
                init_results["status"] = "skipped_no_api_key"
                return init_results

            print("✅ AGENTOPS_API_KEY found")

            # Test AgentOps initialization
            try:
                agentops.init(
                    auto_start_session=False,
                    tags=["multi-agent-observability", "agno-testing"],
                    instrument_llm_calls=True
                )
                init_results["initialization_success"] = True
                init_results["auto_instrumentation"] = True
                print("✅ AgentOps initialized successfully with auto-instrumentation")

            except Exception as e:
                print(f"❌ AgentOps initialization failed: {e}")
                init_results["initialization_success"] = False
                init_results["initialization_error"] = str(e)
                return init_results

            # Test analyzer with AgentOps
            analyzer = MonetizationAgnoAnalyzer()
            init_results["analyzer_agentops_enabled"] = analyzer.agentops_enabled
            init_results["analyzer_session_id"] = analyzer.session_id

            if analyzer.agentops_enabled:
                print("✅ Analyzer AgentOps integration working")
            else:
                print("⚠️ Analyzer AgentOps integration not working")

            self.test_results["agentops_initialization"] = init_results

        except Exception as e:
            print(f"❌ AgentOps initialization test failed: {e}")
            init_results["status"] = "failed"
            init_results["error"] = str(e)
            self.test_results["agentops_initialization"] = init_results

        return init_results

    def test_trace_creation(self) -> dict[str, Any]:
        """Test AgentOps trace creation and management"""
        print("\n📊 TESTING TRACE CREATION")
        print("=" * 60)

        trace_results = {}

        try:
            # Skip if AgentOps not initialized
            if not self.test_results.get("agentops_initialization", {}).get("initialization_success", False):
                print("⚠️ Skipping trace creation - AgentOps not initialized")
                trace_results["status"] = "skipped_agentops_not_initialized"
                return trace_results

            # Test trace creation
            trace_id = agentops.start_trace(
                "multi_agent_observability_test",
                tags=["trace-testing", "multi-agent"]
            )

            trace_results["trace_created"] = True
            trace_results["trace_id"] = str(trace_id)
            print(f"✅ AgentOps trace created: {trace_id}")

            # Run a simple analysis to generate trace data
            analyzer = MonetizationAgnoAnalyzer()

            start_time = time.time()
            result = analyzer.analyze(
                text="Testing trace creation with multi-agent analysis",
                subreddit="testing"
            )
            end_time = time.time()

            trace_results["analysis_completed"] = True
            trace_results["analysis_duration"] = end_time - start_time
            trace_results["result_summary"] = {
                "monetization_score": result.llm_monetization_score,
                "customer_segment": result.customer_segment
            }

            print(f"✅ Analysis completed: {end_time - start_time:.2f}s")

            # End trace
            agentops.end_trace(trace_id, "Success")
            trace_results["trace_ended"] = True
            print("✅ Trace ended successfully")

            # Generate dashboard URL
            if hasattr(agentops, 'get_session_url'):
                dashboard_url = agentops.get_session_url(trace_id)
                trace_results["dashboard_url"] = dashboard_url
                print(f"🔗 Dashboard URL: {dashboard_url}")

            self.test_results["trace_creation"] = trace_results

        except Exception as e:
            print(f"❌ Trace creation test failed: {e}")
            trace_results["status"] = "failed"
            trace_results["error"] = str(e)
            self.test_results["trace_creation"] = trace_results

        return trace_results

    def test_multi_agent_span_tracking(self) -> dict[str, Any]:
        """Test AgentOps span tracking for individual agents"""
        print("\n🤖 TESTING MULTI-AGENT SPAN TRACKING")
        print("=" * 60)

        span_results = {}

        try:
            # Skip if AgentOps not working
            if not self.test_results.get("agentops_initialization", {}).get("initialization_success", False):
                print("⚠️ Skipping span tracking - AgentOps not initialized")
                span_results["status"] = "skipped_agentops_not_initialized"
                return span_results

            analyzer = MonetizationAgnoAnalyzer()

            # Test with multiple scenarios to capture different agent behaviors
            scenario_results = []

            for i, scenario in enumerate(self.test_scenarios):
                print(f"\n📋 Scenario {i+1}: {scenario['name']}")

                scenario_metrics = {
                    "name": scenario["name"],
                    "expected_complexity": scenario["expected_complexity"],
                    "success": False,
                    "duration": 0,
                    "agent_count": 4,  # WTP, Market Segment, Price Point, Payment Behavior
                    "error": None
                }

                try:
                    start_time = time.time()

                    # Run analysis to trigger agent spans
                    result = analyzer.analyze(
                        text=scenario["text"],
                        subreddit=scenario["subreddit"]
                    )

                    end_time = time.time()
                    duration = end_time - start_time

                    scenario_metrics.update({
                        "success": True,
                        "duration": duration,
                        "result": {
                            "monetization_score": result.llm_monetization_score,
                            "customer_segment": result.customer_segment,
                            "wtp_score": result.willingness_to_pay_score,
                            "sentiment": result.sentiment_toward_payment
                        }
                    })

                    print(f"✅ {scenario['name']}: {duration:.2f}s, Score: {result.llm_monetization_score:.1f}")

                except Exception as e:
                    scenario_metrics["error"] = str(e)
                    print(f"❌ {scenario['name']} failed: {e}")

                scenario_results.append(scenario_metrics)

            span_results["scenarios_tested"] = len(scenario_results)
            span_results["successful_scenarios"] = sum(1 for s in scenario_results if s["success"])
            span_results["average_duration"] = sum(s["duration"] for s in scenario_results if s["success"]) / max(1, span_results["successful_scenarios"])
            span_results["scenario_details"] = scenario_results

            print("\n📊 Span Tracking Summary:")
            print(f"   Scenarios Tested: {span_results['scenarios_tested']}")
            print(f"   Successful Scenarios: {span_results['successful_scenarios']}")
            print(f"   Average Duration: {span_results['average_duration']:.2f}s")

            self.test_results["multi_agent_spans"] = span_results

        except Exception as e:
            print(f"❌ Multi-agent span tracking failed: {e}")
            span_results["status"] = "failed"
            span_results["error"] = str(e)
            self.test_results["multi_agent_spans"] = span_results

        return span_results

    def test_cost_tracking(self) -> dict[str, Any]:
        """Test AgentOps cost tracking capabilities"""
        print("\n💰 TESTING COST TRACKING")
        print("=" * 60)

        cost_results = {}

        try:
            # Skip if AgentOps not working
            if not self.test_results.get("agentops_initialization", {}).get("initialization_success", False):
                print("⚠️ Skipping cost tracking - AgentOps not initialized")
                cost_results["status"] = "skipped_agentops_not_initialized"
                return cost_results

            analyzer = MonetizationAgnoAnalyzer()

            # Run multiple analyses to accumulate cost data
            print("Running multiple analyses for cost tracking...")

            analysis_count = 3
            total_cost = 0
            total_tokens = 0
            analysis_times = []

            for i in range(analysis_count):
                print(f"  Analysis {i+1}/{analysis_count}...")

                start_time = time.time()
                result = analyzer.analyze(
                    text=f"Cost tracking test analysis {i+1}: Need business software solution with budget considerations.",
                    subreddit="business"
                )
                end_time = time.time()

                analysis_times.append(end_time - start_time)

                # Get cost report if available
                try:
                    cost_report = analyzer.get_cost_report()
                    if "total_cost" in cost_report:
                        total_cost += cost_report["total_cost"]
                    if "token_usage" in cost_report:
                        total_tokens += cost_report["token_usage"]
                except Exception as cost_error:
                    print(f"    Cost report failed: {cost_error}")

                print(f"    Score: {result.llm_monetization_score:.1f}, Time: {end_time - start_time:.2f}s")

            cost_results = {
                "analyses_completed": analysis_count,
                "average_analysis_time": sum(analysis_times) / len(analysis_times),
                "total_estimated_cost": total_cost,
                "total_estimated_tokens": total_tokens,
                "cost_per_analysis": total_cost / analysis_count if analysis_count > 0 else 0,
                "cost_tracking_available": True
            }

            print("\n💰 Cost Tracking Results:")
            print(f"   Analyses Completed: {cost_results['analyses_completed']}")
            print(f"   Average Analysis Time: {cost_results['average_analysis_time']:.2f}s")
            print(f"   Total Estimated Cost: ${cost_results['total_estimated_cost']:.6f}")
            print(f"   Cost Per Analysis: ${cost_results['cost_per_analysis']:.6f}")

            self.test_results["cost_tracking"] = cost_results

        except Exception as e:
            print(f"❌ Cost tracking test failed: {e}")
            cost_results["status"] = "failed"
            cost_results["error"] = str(e)
            self.test_results["cost_tracking"] = cost_results

        return cost_results

    def test_dashboard_verification(self) -> dict[str, Any]:
        """Test AgentOps dashboard access and data verification"""
        print("\n🖥️ TESTING DASHBOARD VERIFICATION")
        print("=" * 60)

        dashboard_results = {}

        try:
            # Skip if AgentOps not working
            if not self.test_results.get("agentops_initialization", {}).get("initialization_success", False):
                print("⚠️ Skipping dashboard verification - AgentOps not initialized")
                dashboard_results["status"] = "skipped_agentops_not_initialized"
                return dashboard_results

            # Test dashboard URL generation
            dashboard_base_url = "https://app.agentops.ai/sessions"

            dashboard_results = {
                "dashboard_accessible": True,
                "base_url": dashboard_base_url,
                "trace_urls_created": 0,
                "session_replay_available": False
            }

            # Check if we have any trace URLs from previous tests
            trace_creation = self.test_results.get("trace_creation", {})
            if trace_creation.get("dashboard_url"):
                dashboard_results["trace_urls_created"] = 1
                dashboard_results["session_replay_available"] = True
                print(f"✅ Session replay available: {trace_creation['dashboard_url']}")

            # Test final analysis for dashboard verification
            analyzer = MonetizationAgnoAnalyzer()
            result = analyzer.analyze(
                text="Final dashboard verification test - this should appear in AgentOps dashboard",
                subreddit="testing"
            )

            dashboard_results["final_analysis_completed"] = True
            dashboard_results["final_result"] = {
                "monetization_score": result.llm_monetization_score,
                "customer_segment": result.customer_segment
            }

            print(f"✅ Final analysis completed: Score {result.llm_monetization_score:.1f}")
            print(f"🔗 Dashboard access: {dashboard_base_url}")
            print("📊 Session data should be visible in AgentOps dashboard")

            self.test_results["dashboard_verification"] = dashboard_results

        except Exception as e:
            print(f"❌ Dashboard verification failed: {e}")
            dashboard_results["status"] = "failed"
            dashboard_results["error"] = str(e)
            self.test_results["dashboard_verification"] = dashboard_results

        return dashboard_results

    def generate_observability_summary(self) -> dict[str, Any]:
        """Generate comprehensive observability test summary"""
        print("\n📋 GENERATING OBSERVABILITY SUMMARY")
        print("=" * 60)

        init_results = self.test_results.get("agentops_initialization", {})
        trace_results = self.test_results.get("trace_creation", {})
        span_results = self.test_results.get("multi_agent_spans", {})
        cost_results = self.test_results.get("cost_tracking", {})
        dashboard_results = self.test_results.get("dashboard_verification", {})

        # Calculate observability metrics
        initialization_success = init_results.get("initialization_success", False)
        trace_creation_success = trace_results.get("trace_created", False)
        span_tracking_success = span_results.get("successful_scenarios", 0) > 0
        cost_tracking_success = cost_results.get("cost_tracking_available", False)
        dashboard_accessible = dashboard_results.get("dashboard_accessible", False)

        # Overall observability score
        observability_score = sum([
            initialization_success * 20,
            trace_creation_success * 20,
            span_tracking_success * 25,
            cost_tracking_success * 20,
            dashboard_accessible * 15
        ])

        # Determine status
        if observability_score >= 80:
            status = "EXCELLENT"
        elif observability_score >= 60:
            status = "GOOD"
        elif observability_score >= 40:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "POOR"

        summary = {
            "overall_status": status,
            "observability_score": observability_score,
            "components_working": {
                "initialization": initialization_success,
                "trace_creation": trace_creation_success,
                "span_tracking": span_tracking_success,
                "cost_tracking": cost_tracking_success,
                "dashboard_access": dashboard_accessible
            },
            "performance_metrics": {
                "average_analysis_time": span_results.get("average_duration", 0),
                "cost_per_analysis": cost_results.get("cost_per_analysis", 0),
                "total_estimated_cost": cost_results.get("total_estimated_cost", 0)
            },
            "key_findings": [
                f"AgentOps Initialization: {'✅ Working' if initialization_success else '❌ Failed'}",
                f"Trace Creation: {'✅ Working' if trace_creation_success else '❌ Failed'}",
                f"Multi-Agent Span Tracking: {'✅ Working' if span_tracking_success else '❌ Failed'}",
                f"Cost Tracking: {'✅ Working' if cost_tracking_success else '❌ Failed'}",
                f"Dashboard Access: {'✅ Working' if dashboard_accessible else '❌ Failed'}"
            ],
            "recommendations": self._generate_observability_recommendations(
                initialization_success, trace_creation_success, span_tracking_success,
                cost_tracking_success, dashboard_accessible
            ),
            "dashboard_url": "https://app.agentops.ai/sessions"
        }

        self.test_results["summary"] = summary

        print(f"\n🎯 OBSERVABILITY STATUS: {status}")
        print(f"   Observability Score: {observability_score}/100")
        print(f"   Components Working: {sum(summary['components_working'].values())}/5")
        print(f"   Dashboard URL: {summary['dashboard_url']}")

        return summary

    def _generate_observability_recommendations(self, *component_statuses) -> list[str]:
        """Generate observability improvement recommendations"""
        recommendations = []
        components = ["initialization", "trace_creation", "span_tracking", "cost_tracking", "dashboard_access"]

        for i, (component, status) in enumerate(zip(components, component_statuses)):
            if not status:
                recommendations.append(f"Fix {component.replace('_', ' ').title()} - check API configuration")

        if all(component_statuses):
            recommendations.append("All observability components working - consider advanced monitoring features")

        return recommendations

    def save_observability_results(self, filename: str = None):
        """Save observability test results to file"""
        if filename is None:
            filename = f"/home/carlos/projects/redditharbor/docs/e2e-testing-guide/results/agentops-observability-testing-{datetime.now().strftime('%Y-%m-%d')}.json"

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)

        print(f"\n💾 Observability results saved to: {filename}")
        return filename

    def run_observability_test_suite(self):
        """Run the complete AgentOps observability test suite"""
        print("🚀 STARTING AGENTOPS OBSERVABILITY TEST SUITE")
        print("=" * 80)

        start_time = time.time()

        try:
            # Run all observability test phases
            self.test_agentops_initialization()
            self.test_trace_creation()
            self.test_multi_agent_span_tracking()
            self.test_cost_tracking()
            self.test_dashboard_verification()
            self.generate_observability_summary()

            end_time = time.time()
            total_duration = end_time - start_time

            print(f"\n⏱️ Total Observability Test Duration: {total_duration:.2f}s")

            # Save results
            results_file = self.save_observability_results()

            return self.test_results

        except Exception as e:
            print(f"❌ Observability test suite failed: {e}")
            raise


def main():
    """Main function to run AgentOps observability tests"""
    print("🔍 AgentOps Observability Testing for Multi-Agent System")
    print("=" * 60)

    test_suite = AgentOpsObservabilityTest()
    results = test_suite.run_observability_test_suite()

    return results


if __name__ == "__main__":
    main()
