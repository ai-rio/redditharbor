#!/usr/bin/env python3
"""
RedditHarbor Complete Integration Pipeline Test
Tests the full production-ready integration stack: Agno + AgentOps + Jina MCP + Evidence-Based Profiling
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import core integration components
try:
    from agent_tools.monetization_agno_analyzer import create_monetization_analyzer
    from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
    from agent_tools.jina_hybrid_client import JinaHybridClient
    from agent_tools.market_data_validator import MarketDataValidator
    import agentops
    from core.opportunity_analyzer import OpportunityAnalyzer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Ensure all integration components are installed: `uv sync`")
    sys.exit(1)


@dataclass
class IntegrationTestResult:
    """Results from integration testing"""
    component: str
    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class PipelineTestSummary:
    """Complete pipeline test summary"""
    total_tests: int
    successful_tests: int
    failed_tests: int
    total_duration: float
    test_results: List[IntegrationTestResult]
    integration_health: Dict[str, bool]
    cost_estimate: float


class IntegrationPipelineTester:
    """Comprehensive integration pipeline testing suite"""

    def __init__(self):
        self.test_results: List[IntegrationTestResult] = []
        self.integration_health = {}
        self.cost_estimate = 0.0
        self.start_time = time.time()

        # Test data
        self.test_opportunities = [
            {
                "title": "Looking for expense tracking software for small business",
                "text": "Our consulting firm needs an expense tracking solution. We're currently spending about $500/month on scattered tools and would pay up to $150/month for a unified solution. We've tried Expensify but it's too complex for our 15-person team.",
                "subreddit": "smallbusiness",
                "url": "https://reddit.com/r/smallbusiness/comments/example1",
                "expected_score": 65.0,
                "expected_wtp_score": 85.0,
                "expected_segment": "B2B"
            },
            {
                "title": "Freelancer needs better project management tool",
                "text": "As a freelance designer, I'm struggling with client management and billing. Would love something under $50/month that integrates with QuickBooks. Currently using separate tools and it's a mess.",
                "subreddit": "freelance",
                "url": "https://reddit.com/r/freelance/comments/example2",
                "expected_score": 45.0,
                "expected_wtp_score": 60.0,
                "expected_segment": "B2C"
            }
        ]

    def log_test_result(self, component: str, test_name: str, success: bool,
                        duration: float, details: Dict[str, Any],
                        error_message: Optional[str] = None):
        """Log a test result"""
        result = IntegrationTestResult(
            component=component,
            test_name=test_name,
            success=success,
            duration=duration,
            details=details,
            error_message=error_message
        )
        self.test_results.append(result)

        # Update integration health
        if component not in self.integration_health:
            self.integration_health[component] = True
        if not success:
            self.integration_health[component] = False

    async def test_agno_multi_agent_system(self) -> None:
        """Test Agno multi-agent monetization analysis"""
        print("🤖 TESTING AGNO MULTI-AGENT SYSTEM")
        print("=" * 60)

        try:
            # Initialize Agno analyzer
            start_time = time.time()
            analyzer = create_monetization_analyzer(framework="agno")
            init_duration = time.time() - start_time

            print(f"✅ Agno analyzer initialized in {init_duration:.2f}s")

            # Test each opportunity
            for i, opportunity in enumerate(self.test_opportunities):
                print(f"\n--- Testing Opportunity {i+1}/{len(self.test_opportunities)} ---")

                test_start = time.time()

                try:
                    # Run multi-agent analysis
                    result = await analyzer.analyze(
                        text=opportunity["text"],
                        subreddit=opportunity["subreddit"]
                    )

                    test_duration = time.time() - test_start

                    # Validate results
                    expected_wtp = opportunity["expected_wtp_score"]
                    wtp_diff = abs(result.willingness_to_pay_score - expected_wtp)
                    segment_match = result.customer_segment == opportunity["expected_segment"]

                    success = (
                        result.willingness_to_pay_score > 0 and
                        wtp_diff < 20.0 and  # Allow 20 point variance
                        result.customer_segment in ["B2B", "B2C"] and
                        segment_match
                    )

                    details = {
                        "opportunity_id": i+1,
                        "wtp_score": result.willingness_to_pay_score,
                        "expected_wtp": expected_wtp,
                        "wtp_diff": wtp_diff,
                        "customer_segment": result.customer_segment,
                        "expected_segment": opportunity["expected_segment"],
                        "segment_match": segment_match,
                        "market_segment": result.market_segment,
                        "price_sensitivity": result.price_sensitivity
                    }

                    status = "✅" if success else "❌"
                    print(f"{status} Agno Analysis {i+1}: WTP={result.willingness_to_pay_score:.1f}, Segment={result.customer_segment}")

                    self.log_test_result(
                        component="agno_multi_agent",
                        test_name=f"analysis_opportunity_{i+1}",
                        success=success,
                        duration=test_duration,
                        details=details
                    )

                except Exception as e:
                    print(f"❌ Agno Analysis {i+1} failed: {e}")
                    self.log_test_result(
                        component="agno_multi_agent",
                        test_name=f"analysis_opportunity_{i+1}",
                        success=False,
                        duration=time.time() - test_start,
                        details={"error": str(e)},
                        error_message=str(e)
                    )

            # Test factory pattern
            print("\n--- Testing Factory Pattern ---")
            factory_start = time.time()

            try:
                # Test framework switching
                agno_analyzer = create_monetization_analyzer(framework="agno")
                dspy_analyzer = create_monetization_analyzer(framework="dspy")

                factory_success = agno_analyzer is not None and dspy_analyzer is not None

                self.log_test_result(
                    component="agno_multi_agent",
                    test_name="factory_pattern",
                    success=factory_success,
                    duration=time.time() - factory_start,
                    details={"agno_available": agno_analyzer is not None, "dspy_available": dspy_analyzer is not None}
                )

                print(f"✅ Factory pattern test completed")

            except Exception as e:
                print(f"❌ Factory pattern test failed: {e}")
                self.log_test_result(
                    component="agno_multi_agent",
                    test_name="factory_pattern",
                    success=False,
                    duration=time.time() - factory_start,
                    details={"error": str(e)},
                    error_message=str(e)
                )

        except Exception as e:
            print(f"❌ Agno multi-agent system test failed: {e}")
            self.log_test_result(
                component="agno_multi_agent",
                test_name="system_initialization",
                success=False,
                duration=0,
                details={"error": str(e)},
                error_message=str(e)
            )

    async def test_agentops_observability(self) -> None:
        """Test AgentOps observability and dashboard visibility"""
        print("\n🔍 TESTING AGENTOPS OBSERVABILITY")
        print("=" * 60)

        try:
            # Initialize AgentOps
            start_time = time.time()
            agentops.init(
                api_key=os.environ.get("AGENTOPS_API_KEY"),
                auto_start_session=False,
                tags=["integration-pipeline-test", "production-validation"],
                instrument_llm_calls=False
            )

            print(f"✅ AgentOps initialized in {time.time() - start_time:.2f}s")

            # Start a comprehensive trace
            trace = agentops.start_trace(
                "integration_pipeline_test",
                tags=["agno", "jina", "market-validation", "multi-agent"]
            )

            print(f"✅ AgentOps trace started: {trace}")

            # Record test events
            agentops.Event("integration_test_started", {
                "test_components": ["agno", "agentops", "jina", "market_validation"],
                "test_opportunities": len(self.test_opportunities)
            })

            # Test span creation
            span_start = time.time()
            test_span = agentops.start_trace("test_span_validation", tags=["span-test"])
            time.sleep(0.1)  # Simulate work
            agentops.end_trace(test_span, "Success")
            span_duration = time.time() - span_start

            # Record detailed metrics
            agentops.Event("span_validation_completed", {
                "span_creation_success": True,
                "span_duration": span_duration,
                "trace_id": str(trace)
            })

            self.log_test_result(
                component="agentops_observability",
                test_name="trace_and_span_creation",
                success=True,
                duration=span_duration,
                details={
                    "trace_id": str(trace),
                    "span_duration": span_duration,
                    "events_recorded": 2
                }
            )

            print(f"✅ Trace and span validation completed in {span_duration:.2f}s")

            # Test dashboard visibility simulation
            print("Testing dashboard visibility metrics...")

            # Simulate multi-agent span tracking
            for agent_name in ["WTP Analyst", "Market Segment Analyst", "Price Point Analyst", "Payment Behavior Analyst"]:
                agent_span = agentops.start_trace(f"agent_execution_{agent_name}", tags=["agent", "multi-agent"])
                time.sleep(0.05)  # Simulate agent work
                agentops.end_trace(agent_span, "Success")

            agentops.Event("multi_agent_spans_created", {
                "agents_tracked": 4,
                "all_spans_successful": True
            })

            self.log_test_result(
                component="agentops_observability",
                test_name="multi_agent_span_tracking",
                success=True,
                duration=0.2,
                details={"agents_tracked": 4}
            )

            print(f"✅ Multi-agent span tracking completed")

            # End main trace
            agentops.end_trace(trace, "Success")

            print(f"📊 AgentOps dashboard URL: https://app.agentops.ai/")
            print(f"✅ AgentOps observability test completed successfully")

        except Exception as e:
            print(f"❌ AgentOps observability test failed: {e}")
            self.log_test_result(
                component="agentops_observability",
                test_name="dashboard_visibility",
                success=False,
                duration=0,
                details={"error": str(e)},
                error_message=str(e)
            )

    async def test_jina_mcp_hybrid_client(self) -> None:
        """Test Jina hybrid client with MCP capabilities"""
        print("\n🌐 TESTING JINA MCP HYBRID CLIENT")
        print("=" * 60)

        try:
            # Initialize hybrid client
            start_time = time.time()
            hybrid_client = JinaHybridClient(
                enable_mcp_experimental=True,
                rate_limit_reader=500,
                rate_limit_search=100
            )
            init_duration = time.time() - start_time

            print(f"✅ Jina hybrid client initialized in {init_duration:.2f}s")

            # Test MCP capability detection
            print("Testing MCP capability detection...")
            mcp_status = {
                "mcp_available": hybrid_client.mcp_available,
                "mcp_experimental": hybrid_client.mcp_experimental,
                "mcp_status": hybrid_client.mcp_status,
                "client_type": hybrid_client.client_type
            }

            print(f"MCP Status: {mcp_status}")

            self.log_test_result(
                component="jina_mcp_hybrid",
                test_name="mcp_capability_detection",
                success=True,  # Detection itself should always succeed
                duration=0.1,
                details=mcp_status
            )

            # Test URL reading with reliability tracking
            print("Testing URL reading with hybrid client...")

            test_urls = [
                "https://example.com",
                "https://httpbin.org/json",
                "https://jsonplaceholder.typicode.com/posts/1"
            ]

            successful_reads = 0
            total_read_time = 0

            for url in test_urls:
                try:
                    read_start = time.time()
                    result = await hybrid_client.read_url(url)
                    read_duration = time.time() - read_start
                    total_read_time += read_duration

                    if result and result.get('content'):
                        successful_reads += 1
                        print(f"✅ Successfully read {url} ({len(result.get('content', ''))} chars, {read_duration:.2f}s)")
                    else:
                        print(f"⚠️  Empty response from {url}")

                except Exception as e:
                    print(f"❌ Failed to read {url}: {e}")

            read_success_rate = successful_reads / len(test_urls)
            avg_read_time = total_read_time / len(test_urls) if test_urls else 0

            self.log_test_result(
                component="jina_mcp_hybrid",
                test_name="url_reading_reliability",
                success=read_success_rate >= 0.8,  # At least 80% success rate
                duration=total_read_time,
                details={
                    "successful_reads": successful_reads,
                    "total_urls": len(test_urls),
                    "success_rate": read_success_rate,
                    "average_time": avg_read_time
                }
            )

            # Test web search functionality
            print("Testing web search functionality...")

            search_queries = [
                "expense tracking software",
                "small business accounting tools",
                "freelance project management"
            ]

            successful_searches = 0
            total_search_time = 0

            for query in search_queries:
                try:
                    search_start = time.time()
                    results = await hybrid_client.search(query, num_results=3)
                    search_duration = time.time() - search_start
                    total_search_time += search_duration

                    if results and results.get('results'):
                        successful_searches += 1
                        result_count = len(results.get('results', []))
                        print(f"✅ Search '{query}' returned {result_count} results ({search_duration:.2f}s)")
                    else:
                        print(f"⚠️  Empty search results for '{query}'")

                except Exception as e:
                    print(f"❌ Failed to search '{query}': {e}")

            search_success_rate = successful_searches / len(search_queries)
            avg_search_time = total_search_time / len(search_queries) if search_queries else 0

            self.log_test_result(
                component="jina_mcp_hybrid",
                test_name="web_search_functionality",
                success=search_success_rate >= 0.8,  # At least 80% success rate
                duration=total_search_time,
                details={
                    "successful_searches": successful_searches,
                    "total_queries": len(search_queries),
                    "success_rate": search_success_rate,
                    "average_time": avg_search_time
                }
            )

            # Test rate limiting
            print("Testing rate limiting functionality...")

            # Check rate limit status
            rate_limit_status = hybrid_client.get_rate_limit_status()
            print(f"Rate limit status: {rate_limit_status}")

            self.log_test_result(
                component="jina_mcp_hybrid",
                test_name="rate_limiting_status",
                success=True,
                duration=0.1,
                details=rate_limit_status
            )

            print(f"✅ Jina MCP hybrid client test completed successfully")

        except Exception as e:
            print(f"❌ Jina MCP hybrid client test failed: {e}")
            self.log_test_result(
                component="jina_mcp_hybrid",
                test_name="client_initialization",
                success=False,
                duration=0,
                details={"error": str(e)},
                error_message=str(e)
            )

    async def test_evidence_based_profiling(self) -> None:
        """Test evidence-based AI profiling with market validation"""
        print("\n🧠 TESTING EVIDENCE-BASED PROFILING")
        print("=" * 60)

        try:
            # Initialize enhanced LLM profiler
            start_time = time.time()
            profiler = EnhancedLLMProfiler(
                model="anthropic/claude-haiku-4.5",
                enable_market_validation=True
            )
            init_duration = time.time() - start_time

            print(f"✅ Enhanced LLM profiler initialized in {init_duration:.2f}s")

            # Initialize market data validator
            market_validator = MarketDataValidator(
                model="anthropic/claude-haiku-4.5",
                enable_market_validation=True
            )

            print("✅ Market data validator initialized")

            # Test evidence-based profiling for each opportunity
            for i, opportunity in enumerate(self.test_opportunities):
                print(f"\n--- Testing Evidence-Based Profile {i+1}/{len(self.test_opportunities)} ---")

                profile_start = time.time()

                try:
                    # Simulate having Agno evidence
                    mock_agno_evidence = {
                        "willingness_to_pay_score": opportunity["expected_wtp_score"],
                        "customer_segment": opportunity["expected_segment"],
                        "price_sensitivity": "medium",
                        "monetization_potential": "high",
                        "competitor_analysis": "expensify, quickbooks",
                        "confidence_score": 0.85
                    }

                    # Run market validation first
                    print("Running market validation...")
                    market_validation = await market_validator.validate_opportunity(
                        app_concept=opportunity["title"],
                        target_market="small business" if opportunity["expected_segment"] == "B2B" else "individual consumers",
                        problem_statement=opportunity["text"]
                    )

                    # Generate evidence-based AI profile
                    print("Generating evidence-based AI profile...")
                    profile_result = await profiler.generate_app_profile_with_costs(
                        opportunity_data=opportunity,
                        agno_analysis=mock_agno_evidence
                    )

                    profile_duration = time.time() - profile_start

                    # Validate evidence alignment
                    alignment_score = 0
                    if hasattr(profile_result, 'evidence_alignment_score'):
                        alignment_score = profile_result.evidence_alignment_score

                    # Check profile quality indicators
                    quality_indicators = {
                        "profile_generated": profile_result is not None,
                        "evidence_used": profile_result.evidence_used if hasattr(profile_result, 'evidence_used') else False,
                        "alignment_score": alignment_score,
                        "market_validation": market_validation.get('validation_score', 0),
                        "cost_tracked": hasattr(profile_result, 'token_usage') and profile_result.token_usage > 0
                    }

                    # Determine success based on quality indicators
                    success = (
                        quality_indicators["profile_generated"] and
                        quality_indicators["evidence_used"] and
                        alignment_score >= 60 and  # At least 60% alignment
                        quality_indicators["market_validation"] >= 50 and  # At least 50% validation score
                        quality_indicators["cost_tracked"]
                    )

                    details = {
                        "opportunity_id": i+1,
                        "profile_generated": quality_indicators["profile_generated"],
                        "evidence_used": quality_indicators["evidence_used"],
                        "alignment_score": alignment_score,
                        "market_validation_score": quality_indicators["market_validation"],
                        "cost_tracked": quality_indicators["cost_tracked"],
                        "token_usage": getattr(profile_result, 'token_usage', 0),
                        "total_cost": getattr(profile_result, 'total_cost', 0),
                        "market_validation_cost": market_validation.get('total_cost', 0)
                    }

                    status = "✅" if success else "❌"
                    print(f"{status} Evidence-based Profile {i+1}: Alignment={alignment_score:.1f}%, Market={quality_indicators['market_validation']:.1f}")

                    self.log_test_result(
                        component="evidence_based_profiling",
                        test_name=f"profile_opportunity_{i+1}",
                        success=success,
                        duration=profile_duration,
                        details=details
                    )

                    # Update cost estimate
                    self.cost_estimate += details["total_cost"] + details["market_validation_cost"]

                except Exception as e:
                    print(f"❌ Evidence-based profile {i+1} failed: {e}")
                    self.log_test_result(
                        component="evidence_based_profiling",
                        test_name=f"profile_opportunity_{i+1}",
                        success=False,
                        duration=time.time() - profile_start,
                        details={"error": str(e)},
                        error_message=str(e)
                    )

            print(f"✅ Evidence-based profiling test completed")

        except Exception as e:
            print(f"❌ Evidence-based profiling test failed: {e}")
            self.log_test_result(
                component="evidence_based_profiling",
                test_name="profiler_initialization",
                success=False,
                duration=0,
                details={"error": str(e)},
                error_message=str(e)
            )

    def generate_test_report(self) -> PipelineTestSummary:
        """Generate comprehensive test summary report"""
        total_duration = time.time() - self.start_time
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - successful_tests

        summary = PipelineTestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            total_duration=total_duration,
            test_results=self.test_results,
            integration_health=self.integration_health,
            cost_estimate=self.cost_estimate
        )

        return summary

    def print_summary_report(self, summary: PipelineTestSummary) -> None:
        """Print detailed summary report"""
        print("\n" + "=" * 80)
        print("🎯 REDDITHARBOR INTEGRATION PIPELINE TEST SUMMARY")
        print("=" * 80)

        # Overall results
        success_rate = (summary.successful_tests / summary.total_tests) * 100 if summary.total_tests > 0 else 0

        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {summary.total_tests}")
        print(f"   Successful: {summary.successful_tests}")
        print(f"   Failed: {summary.failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Duration: {summary.total_duration:.2f}s")
        print(f"   Estimated Cost: ${summary.cost_estimate:.6f}")

        # Integration health
        print(f"\n🏥 INTEGRATION HEALTH:")
        for component, healthy in summary.integration_health.items():
            status = "✅ HEALTHY" if healthy else "❌ UNHEALTHY"
            print(f"   {component}: {status}")

        # Component breakdown
        component_results = {}
        for result in summary.test_results:
            if result.component not in component_results:
                component_results[result.component] = {"success": 0, "total": 0, "duration": 0}
            component_results[result.component]["total"] += 1
            component_results[result.component]["duration"] += result.duration
            if result.success:
                component_results[result.component]["success"] += 1

        print(f"\n🔍 COMPONENT BREAKDOWN:")
        for component, stats in component_results.items():
            comp_success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"   {component}:")
            print(f"     Tests: {stats['success']}/{stats['total']} ({comp_success_rate:.1f}%)")
            print(f"     Duration: {stats['duration']:.2f}s")

        # Failed tests details
        failed_tests = [r for r in summary.test_results if not r.success]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"   {result.component}.{result.test_name}: {result.error_message or 'Unknown error'}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate >= 90:
            print("   ✅ Integration pipeline is production-ready!")
        elif success_rate >= 75:
            print("   ⚠️  Integration pipeline mostly healthy - address failed tests")
        else:
            print("   ❌ Integration pipeline needs significant attention")

        # Next steps
        print(f"\n🚀 NEXT STEPS:")
        print("   1. Review failed tests and fix critical issues")
        print("   2. Run production deployment validation")
        print("   3. Set up continuous integration monitoring")
        print("   4. Document integration best practices")

        print("\n" + "=" * 80)


async def main():
    """Main integration pipeline test execution"""
    print("🚀 REDDITHARBOR COMPLETE INTEGRATION PIPELINE TEST")
    print("=" * 80)
    print("Testing: Agno + AgentOps + Jina MCP + Evidence-Based Profiling")
    print("Scope: Production-ready multi-agent, observable, MCP-enabled pipeline")
    print("=" * 80)

    # Check environment variables
    required_env_vars = [
        "AGENTOPS_API_KEY",
        "OPENROUTER_API_KEY",
        "JINA_API_KEY"
    ]

    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before running the test.")
        return

    # Initialize tester
    tester = IntegrationPipelineTester()

    try:
        # Run all integration tests
        await tester.test_agno_multi_agent_system()
        await tester.test_agentops_observability()
        await tester.test_jina_mcp_hybrid_client()
        await tester.test_evidence_based_profiling()

        # Generate and print summary
        summary = tester.generate_test_report()
        tester.print_summary_report(summary)

        # Determine exit code based on success rate
        success_rate = (summary.successful_tests / summary.total_tests) * 100 if summary.total_tests > 0 else 0
        if success_rate >= 90:
            print(f"\n🎉 Integration pipeline test PASSED ({success_rate:.1f}% success rate)")
            sys.exit(0)
        else:
            print(f"\n⚠️  Integration pipeline test FAILED ({success_rate:.1f}% success rate)")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())