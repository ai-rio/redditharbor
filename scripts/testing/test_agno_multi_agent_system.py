#!/usr/bin/env python3
"""
Comprehensive Multi-Agent Workflow Testing for Agno Framework
Tests individual agent performance, coordination, and orchestration
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

    from agent_tools.monetization_agno_analyzer import (
        MarketSegmentAgent,
        MonetizationAgnoAnalyzer,
        PaymentBehaviorAgent,
        PricePointAgent,
        WillingnessToPayAgent,
    )
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Ensure agno and agentops are installed")
    sys.exit(1)

class MultiAgentTestSuite:
    """Comprehensive test suite for Agno multi-agent system"""

    def __init__(self):
        self.test_results = {
            "test_session_id": f"multi_agent_test_{datetime.now().isoformat()}",
            "timestamp": datetime.now().isoformat(),
            "individual_agents": {},
            "coordination_tests": {},
            "performance_metrics": {},
            "agentops_tracking": {},
            "summary": {}
        }

        # Test cases for different scenarios
        self.test_cases = [
            {
                "name": "B2B High Budget",
                "text": "We're paying $300/month for Asana and it's too expensive. Team of 12. Looking for alternatives under $150/month. Budget is approved, need to decide by Q1.",
                "subreddit": "projectmanagement",
                "expected_segment": "B2B",
                "expected_wtp": "High"
            },
            {
                "name": "B2C Subscription Fatigue",
                "text": "I'm NOT willing to pay for another subscription app. Too many already. Looking for free alternatives to MyFitnessPal.",
                "subreddit": "fitness",
                "expected_segment": "B2C",
                "expected_wtp": "Low"
            },
            {
                "name": "Mixed Business Personal",
                "text": "Need a note-taking app for both work projects and personal tasks. Currently using Evernote, willing to pay around $5-10/month for something better.",
                "subreddit": "productivity",
                "expected_segment": "Mixed",
                "expected_wtp": "Medium"
            },
            {
                "name": "Enterprise High Urgency",
                "text": "Our company needs a CRM solution urgently. Currently using spreadsheets. Budget of around $5k-10k for the right tool. Need proposals ASAP.",
                "subreddit": "business",
                "expected_segment": "B2B",
                "expected_wtp": "Very High"
            }
        ]

    def test_individual_agents(self) -> dict[str, Any]:
        """Test each specialized agent individually"""
        print("\n🔬 TESTING INDIVIDUAL AGENTS")
        print("=" * 60)

        agent_results = {}

        try:
            # Initialize analyzer to get agents
            analyzer = MonetizationAgnoAnalyzer()

            # Test each agent separately
            agents_to_test = [
                ("WTP Analyst", analyzer.wtp_agent),
                ("Market Segment Analyst", analyzer.segment_agent),
                ("Price Point Analyst", analyzer.price_agent),
                ("Payment Behavior Analyst", analyzer.behavior_agent)
            ]

            test_prompt = "Analyze this text for monetization potential: We're paying $300/month for Asana and looking for alternatives under $150/month. Budget approved."

            for agent_name, agent in agents_to_test:
                print(f"\n🤖 Testing {agent_name}...")

                agent_metrics = {
                    "name": agent_name,
                    "success": False,
                    "response_time": 0,
                    "response_length": 0,
                    "error": None,
                    "result_quality": "unknown"
                }

                try:
                    start_time = time.time()
                    response = agent.run(test_prompt)
                    end_time = time.time()

                    response_time = end_time - start_time
                    response_length = len(str(response))

                    agent_metrics.update({
                        "success": True,
                        "response_time": response_time,
                        "response_length": response_length,
                        "response_preview": str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
                    })

                    # Quality assessment based on response characteristics
                    if agent_name == "WTP Analyst":
                        if "willingness" in str(response).lower() or "score" in str(response).lower():
                            agent_metrics["result_quality"] = "good"
                        else:
                            agent_metrics["result_quality"] = "needs_improvement"

                    elif agent_name == "Market Segment Analyst":
                        if "b2b" in str(response).lower() or "b2c" in str(response).lower():
                            agent_metrics["result_quality"] = "good"
                        else:
                            agent_metrics["result_quality"] = "needs_improvement"

                    elif agent_name == "Price Point Analyst":
                        if "$" in str(response) or "price" in str(response).lower():
                            agent_metrics["result_quality"] = "good"
                        else:
                            agent_metrics["result_quality"] = "needs_improvement"

                    elif agent_name == "Payment Behavior Analyst":
                        if "spending" in str(response).lower() or "payment" in str(response).lower():
                            agent_metrics["result_quality"] = "good"
                        else:
                            agent_metrics["result_quality"] = "needs_improvement"

                    print(f"✅ {agent_name}: {response_time:.2f}s, {response_length} chars, quality: {agent_metrics['result_quality']}")

                except Exception as e:
                    agent_metrics["error"] = str(e)
                    print(f"❌ {agent_name} failed: {e}")

                agent_results[agent_name] = agent_metrics

            self.test_results["individual_agents"] = agent_results

        except Exception as e:
            print(f"❌ Individual agent testing failed: {e}")
            self.test_results["individual_agents"]["error"] = str(e)

        return agent_results

    def test_agent_coordination(self) -> dict[str, Any]:
        """Test multi-agent coordination and orchestration"""
        print("\n🔗 TESTING AGENT COORDINATION")
        print("=" * 60)

        coordination_results = {}

        try:
            analyzer = MonetizationAgnoAnalyzer()

            # Test with multiple scenarios
            for i, test_case in enumerate(self.test_cases):
                print(f"\n📋 Test Case {i+1}: {test_case['name']}")

                test_metrics = {
                    "name": test_case["name"],
                    "success": False,
                    "total_time": 0,
                    "consensus_score": 0,
                    "coordination_quality": "unknown",
                    "error": None,
                    "final_result": {}
                }

                try:
                    start_time = time.time()

                    # Run full analysis
                    result = analyzer.analyze(
                        text=test_case["text"],
                        subreddit=test_case["subreddit"]
                    )

                    end_time = time.time()
                    total_time = end_time - start_time

                    # Evaluate coordination quality
                    consensus_score = 0

                    # Check if results match expectations
                    if result.customer_segment.lower() == test_case["expected_segment"].lower():
                        consensus_score += 33

                    # Check WTP expectations
                    expected_wtp = test_case["expected_wtp"].lower()
                    actual_wtp = result.willingness_to_pay_score

                    if expected_wtp == "very high" and actual_wtp >= 80:
                        consensus_score += 33
                    elif expected_wtp == "high" and actual_wtp >= 70:
                        consensus_score += 33
                    elif expected_wtp == "medium" and 50 <= actual_wtp < 70:
                        consensus_score += 33
                    elif expected_wtp == "low" and actual_wtp < 50:
                        consensus_score += 33

                    # Check for reasonable composite score
                    if 0 <= result.llm_monetization_score <= 100:
                        consensus_score += 34

                    coordination_quality = "excellent" if consensus_score >= 90 else \
                                        "good" if consensus_score >= 70 else \
                                        "needs_improvement" if consensus_score >= 50 else "poor"

                    test_metrics.update({
                        "success": True,
                        "total_time": total_time,
                        "consensus_score": consensus_score,
                        "coordination_quality": coordination_quality,
                        "final_result": {
                            "llm_monetization_score": result.llm_monetization_score,
                            "customer_segment": result.customer_segment,
                            "willingness_to_pay_score": result.willingness_to_pay_score,
                            "revenue_potential_score": result.revenue_potential_score,
                            "sentiment_toward_payment": result.sentiment_toward_payment,
                            "urgency_level": result.urgency_level
                        }
                    })

                    print(f"✅ {test_case['name']}: {total_time:.2f}s, consensus: {consensus_score}%, quality: {coordination_quality}")

                except Exception as e:
                    test_metrics["error"] = str(e)
                    print(f"❌ {test_case['name']} failed: {e}")

                coordination_results[f"test_{i+1}"] = test_metrics

            self.test_results["coordination_tests"] = coordination_results

        except Exception as e:
            print(f"❌ Coordination testing failed: {e}")
            self.test_results["coordination_tests"]["error"] = str(e)

        return coordination_results

    def test_performance_benchmarks(self) -> dict[str, Any]:
        """Test performance benchmarks and resource optimization"""
        print("\n📈 TESTING PERFORMANCE BENCHMARKS")
        print("=" * 60)

        performance_results = {}

        try:
            analyzer = MonetizationAgnoAnalyzer()

            # Performance test parameters
            test_iterations = 3
            performance_times = []
            memory_usage = []

            print(f"Running {test_iterations} performance test iterations...")

            for i in range(test_iterations):
                print(f"  Iteration {i+1}/{test_iterations}...")

                start_time = time.time()

                # Run analysis
                result = analyzer.analyze(
                    text="Looking for project management software for our team. Current solution is too expensive.",
                    subreddit="productivity"
                )

                end_time = time.time()
                iteration_time = end_time - start_time
                performance_times.append(iteration_time)

                print(f"    Time: {iteration_time:.2f}s, Score: {result.llm_monetization_score:.1f}")

            # Calculate performance metrics
            avg_time = sum(performance_times) / len(performance_times)
            min_time = min(performance_times)
            max_time = max(performance_times)

            performance_results = {
                "iterations": test_iterations,
                "average_response_time": avg_time,
                "min_response_time": min_time,
                "max_response_time": max_time,
                "performance_variance": max_time - min_time,
                "meets_benchmarks": {
                    "individual_agent": min_time <= 15,  # Individual agent should be under 15s
                    "multi_agent_coordination": avg_time <= 60,  # Full coordination should be under 60s
                    "consistency": max_time - min_time <= 10  # Variance should be under 10s
                }
            }

            print("\n📊 Performance Summary:")
            print(f"   Average Response Time: {avg_time:.2f}s")
            print(f"   Min/Max Time: {min_time:.2f}s / {max_time:.2f}s")
            print(f"   Variance: {performance_results['performance_variance']:.2f}s")

            benchmarks_met = sum(performance_results["meets_benchmarks"].values())
            print(f"   Benchmarks Met: {benchmarks_met}/3")

            self.test_results["performance_metrics"] = performance_results

        except Exception as e:
            print(f"❌ Performance testing failed: {e}")
            self.test_results["performance_metrics"]["error"] = str(e)

        return performance_results

    def test_agentops_observability(self) -> dict[str, Any]:
        """Test AgentOps integration and observability"""
        print("\n🔍 TESTING AGENTOPS OBSERVABILITY")
        print("=" * 60)

        observability_results = {}

        try:
            # Check if AgentOps API key is available
            if not os.getenv("AGENTOPS_API_KEY"):
                print("⚠️ AGENTOPS_API_KEY not found, skipping AgentOps tests")
                observability_results["status"] = "skipped_no_api_key"
                return observability_results

            analyzer = MonetizationAgnoAnalyzer()

            if not analyzer.agentops_enabled:
                print("⚠️ AgentOps not enabled, skipping tests")
                observability_results["status"] = "skipped_agentops_disabled"
                return observability_results

            print("✅ AgentOps initialized, running observability test...")

            start_time = time.time()

            # Run analysis to generate AgentOps traces
            result = analyzer.analyze(
                text="Testing AgentOps integration and observability tracking",
                subreddit="testing"
            )

            end_time = time.time()

            observability_results = {
                "status": "tested",
                "analysis_time": end_time - start_time,
                "agentops_enabled": analyzer.agentops_enabled,
                "session_id": analyzer.session_id,
                "trace_created": analyzer.agentops_trace is not None,
                "cost_tracking_available": hasattr(analyzer, 'get_cost_report'),
                "result": {
                    "monetization_score": result.llm_monetization_score,
                    "customer_segment": result.customer_segment,
                    "wtp_score": result.willingness_to_pay_score
                }
            }

            print("✅ AgentOps test completed:")
            print(f"   Analysis Time: {observability_results['analysis_time']:.2f}s")
            print(f"   AgentOps Enabled: {observability_results['agentops_enabled']}")
            print(f"   Session ID: {observability_results['session_id']}")
            print(f"   Trace Created: {observability_results['trace_created']}")

            if observability_results["cost_tracking_available"]:
                cost_report = analyzer.get_cost_report()
                observability_results["cost_report"] = cost_report
                print(f"   Cost Report Available: {cost_report}")

            self.test_results["agentops_tracking"] = observability_results

        except Exception as e:
            print(f"❌ AgentOps observability testing failed: {e}")
            observability_results["status"] = "failed"
            observability_results["error"] = str(e)
            self.test_results["agentops_tracking"] = observability_results

        return observability_results

    def generate_summary(self) -> dict[str, Any]:
        """Generate comprehensive test summary"""
        print("\n📋 GENERATING TEST SUMMARY")
        print("=" * 60)

        individual_agents = self.test_results.get("individual_agents", {})
        coordination_tests = self.test_results.get("coordination_tests", {})
        performance_metrics = self.test_results.get("performance_metrics", {})
        agentops_tracking = self.test_results.get("agentops_tracking", {})

        # Calculate success rates
        agent_success_rate = 0
        if individual_agents and "error" not in individual_agents:
            successful_agents = sum(1 for agent in individual_agents.values() if agent.get("success", False))
            total_agents = len(individual_agents)
            agent_success_rate = (successful_agents / total_agents * 100) if total_agents > 0 else 0

        coordination_success_rate = 0
        if coordination_tests and "error" not in coordination_tests:
            successful_tests = sum(1 for test in coordination_tests.values() if test.get("success", False))
            total_tests = len(coordination_tests)
            coordination_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # Calculate average consensus score
        avg_consensus = 0
        if coordination_tests and "error" not in coordination_tests:
            consensus_scores = [test.get("consensus_score", 0) for test in coordination_tests.values()]
            avg_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0

        # Check performance benchmarks
        benchmarks_met = 0
        total_benchmarks = 3
        if performance_metrics and "meets_benchmarks" in performance_metrics:
            benchmarks_met = sum(performance_metrics["meets_benchmarks"].values())

        # Check AgentOps status
        agentops_status = agentops_tracking.get("status", "unknown")

        # Overall assessment
        overall_status = "FAILED"
        if agent_success_rate >= 95 and coordination_success_rate >= 90 and avg_consensus >= 70:
            overall_status = "PASSED"
        elif agent_success_rate >= 80 and coordination_success_rate >= 70 and avg_consensus >= 60:
            overall_status = "WARNING"

        summary = {
            "overall_status": overall_status,
            "agent_success_rate": agent_success_rate,
            "coordination_success_rate": coordination_success_rate,
            "average_consensus_score": avg_consensus,
            "performance_benchmarks_met": f"{benchmarks_met}/{total_benchmarks}",
            "agentops_status": agentops_status,
            "test_completion_time": datetime.now().isoformat(),
            "key_findings": [
                f"Individual Agent Success Rate: {agent_success_rate:.1f}%",
                f"Coordination Success Rate: {coordination_success_rate:.1f}%",
                f"Average Consensus Score: {avg_consensus:.1f}%",
                f"Performance Benchmarks: {benchmarks_met}/{total_benchmarks} met",
                f"AgentOps Status: {agentops_status}"
            ],
            "recommendations": self._generate_recommendations(
                agent_success_rate, coordination_success_rate, avg_consensus, benchmarks_met
            )
        }

        self.test_results["summary"] = summary

        print(f"\n🎯 OVERALL STATUS: {overall_status}")
        print(f"   Agent Success Rate: {agent_success_rate:.1f}% (Target: ≥95%)")
        print(f"   Coordination Success Rate: {coordination_success_rate:.1f}% (Target: ≥90%)")
        print(f"   Average Consensus Score: {avg_consensus:.1f}% (Target: ≥70%)")
        print(f"   Performance Benchmarks: {benchmarks_met}/{total_benchmarks} met")
        print(f"   AgentOps Status: {agentops_status}")

        return summary

    def _generate_recommendations(self, agent_success: float, coordination_success: float,
                                consensus: float, benchmarks: int) -> list[str]:
        """Generate improvement recommendations based on test results"""
        recommendations = []

        if agent_success < 95:
            recommendations.append("Individual agent performance needs improvement - check agent configurations and prompts")

        if coordination_success < 90:
            recommendations.append("Agent coordination issues detected - review team orchestration logic")

        if consensus < 70:
            recommendations.append("Low consensus scores - improve inter-agent communication and result aggregation")

        if benchmarks < 3:
            recommendations.append("Performance benchmarks not met - optimize response times and reduce variance")

        if not recommendations:
            recommendations.append("All tests passed - consider increasing test complexity or adding edge cases")

        return recommendations

    def save_results(self, filename: str = None):
        """Save test results to file"""
        if filename is None:
            filename = f"/home/carlos/projects/redditharbor/docs/e2e-testing-guide/results/multi-agent-workflow-testing-{datetime.now().strftime('%Y-%m-%d')}.json"

        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)

        print(f"\n💾 Test results saved to: {filename}")
        return filename

    def run_comprehensive_test(self):
        """Run the complete multi-agent test suite"""
        print("🚀 STARTING COMPREHENSIVE MULTI-AGENT WORKFLOW TESTING")
        print("=" * 80)

        start_time = time.time()

        try:
            # Run all test phases
            self.test_individual_agents()
            self.test_agent_coordination()
            self.test_performance_benchmarks()
            self.test_agentops_observability()
            self.generate_summary()

            end_time = time.time()
            total_duration = end_time - start_time

            print(f"\n⏱️ Total Test Duration: {total_duration:.2f}s")

            # Save results
            results_file = self.save_results()

            return self.test_results

        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            raise


def main():
    """Main function to run multi-agent tests"""
    print("🤖 Multi-Agent Workflow Testing for RedditHarbor")
    print("=" * 60)

    test_suite = MultiAgentTestSuite()
    results = test_suite.run_comprehensive_test()

    return results


if __name__ == "__main__":
    main()
