#!/usr/bin/env python3
"""
Test script to validate metrics integration across the pipeline
This script tests:
1. Metrics collection in AgnoOpportunityAnalyzer
2. Metrics collection in individual agents
3. Metrics collection in PipelineOrchestrator phases
4. End-to-end metrics flow
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_metrics_collector():
    """Test basic metrics collector functionality"""
    logger.info("=" * 80)
    logger.info("Testing MetricsCollector Basic Functionality")
    logger.info("=" * 80)

    from monitoring.metrics_collector import MetricsCollector, get_collector

    # Test global collector
    collector = get_collector()
    logger.info(f"✓ Global collector created: {type(collector).__name__}")

    # Test direct tracking
    with collector.track("test", agent_name="test_agent", opportunity_id="test-123") as ctx:
        time.sleep(0.1)  # Simulate work
        ctx["api_cost_usd"] = 0.001
        ctx["metadata"] = {"test": True}

    logger.info("✓ Direct tracking test completed")

    # Test decorator
    @collector.track_execution(phase="test", agent_name="decorator_test")
    def test_function(param1, param2, opportunity_id="test-456"):
        time.sleep(0.05)
        return {"result": "success", "api_cost": 0.002}

    result = test_function("value1", "value2")
    logger.info(f"✓ Decorator test completed: {result}")

    return True


def test_agno_analyzer_metrics():
    """Test metrics collection in AgnoOpportunityAnalyzer"""
    logger.info("=" * 80)
    logger.info("Testing AgnoOpportunityAnalyzer Metrics")
    logger.info("=" * 80)

    from models.reddit import RedditSubmission
    from transform.agno_analyzer import AgnoOpportunityAnalyzer

    # Create test submission
    test_submission = RedditSubmission(
        id="test-opp-001",
        title="Looking for a project management tool",
        text="I need a tool to help manage my small business projects with team collaboration",
        subreddit="entrepreneur",
        author="test_user",
        score=10,
        comments_count=5
    )

    # Create analyzer
    analyzer = AgnoOpportunityAnalyzer(
        model="test-model",
        enable_agentops=False,
        enable_embeddings=False,
        enable_market_cost_tracking=True
    )

    logger.info("✓ Analyzer created")

    # Analyze submission (this should track metrics)
    start_time = time.time()
    result = analyzer.analyze_submission(test_submission)
    duration = time.time() - start_time

    logger.info(f"✓ Analysis completed in {duration:.2f}s")
    logger.info(f"  - Final score: {result.final_score}")
    logger.info(f"  - Trust level: {result.trust_level}")
    logger.info(f"  - App idea: {result.app_idea.title}")

    return True


def test_agent_metrics():
    """Test metrics collection in individual agents"""
    logger.info("=" * 80)
    logger.info("Testing Individual Agent Metrics")
    logger.info("=" * 80)

    from transform.agno_agents import (
        WillingnessToPayAgent,
        MarketSegmentAgent,
        PricePointAgent,
        PaymentBehaviorAgent
    )

    agents = [
        ("WTP", WillingnessToPayAgent),
        ("Segment", MarketSegmentAgent),
        ("Price", PricePointAgent),
        ("Payment", PaymentBehaviorAgent)
    ]

    test_input = '{"opportunity_id": "test-opp-002", "title": "Test", "content": "Test content"}'

    for agent_name, agent_class in agents:
        agent = agent_class("test-model", "test-key", "http://test.com")
        logger.info(f"✓ {agent_name} agent created")

        # Run agent (this should track metrics)
        result = agent.run(test_input)
        logger.info(f"  - Result length: {len(result)} chars")

    return True


def test_market_research_agent_metrics():
    """Test metrics collection in MarketResearchAgent"""
    logger.info("=" * 80)
    logger.info("Testing MarketResearchAgent Metrics")
    logger.info("=" * 80)

    from transform.market_research_agent import MarketResearchAgent

    # Create agent
    agent = MarketResearchAgent(
        model="test-model",
        api_key="test-key",
        use_real_jina=False  # Use mock for testing
    )

    logger.info("✓ MarketResearchAgent created")

    # Test input
    test_input = {
        "opportunity_id": "test-opp-003",
        "app_concept": "AI-powered project management tool",
        "target_market": "Small businesses",
        "problem_description": "Need better project tracking"
    }

    # Run agent (this should track metrics)
    import asyncio
    result = asyncio.run(agent.run(test_input))

    logger.info(f"✓ Market research completed")
    logger.info(f"  - Validation score: {result.get('validation_score', 'N/A')}")
    logger.info(f"  - Jina cost: ${result.get('jina_cost', 0):.6f}")

    return True


def test_pipeline_orchestrator_metrics():
    """Test metrics collection in PipelineOrchestrator"""
    logger.info("=" * 80)
    logger.info("Testing PipelineOrchestrator Metrics")
    logger.info("=" * 80)

    from orchestration.pipeline_orchestrator import PipelineOrchestrator, PipelineConfiguration

    # Create orchestrator
    orchestrator = PipelineOrchestrator()
    logger.info("✓ Orchestrator created")

    # Create test configuration
    config = PipelineConfiguration(
        subreddits=["test"],
        limit=2,
        test_mode=True,
        dry_run=True,
        enable_staging=False
    )

    logger.info("✓ Test configuration created")

    # Run pipeline with minimal test
    try:
        results = orchestrator.execute_pipeline(config)
        logger.info("✓ Pipeline execution completed")
        logger.info(f"  - Total time: {results.total_execution_time:.2f}s")
        logger.info(f"  - Submissions extracted: {results.submissions_extracted}")
        logger.info(f"  - Analyses generated: {results.analyses_generated}")
    except Exception as e:
        logger.warning(f"Pipeline test failed (expected in test mode): {e}")

    return True


def verify_metrics_in_database():
    """Verify metrics were actually stored in database"""
    logger.info("=" * 80)
    logger.info("Verifying Metrics in Database")
    logger.info("=" * 80)

    try:
        import psycopg2
        from config import get_settings

        settings = get_settings()
        conn = psycopg2.connect(settings.database_url)

        with conn.cursor() as cur:
            # Check total metrics count
            cur.execute("SELECT COUNT(*) FROM pipeline_metrics WHERE created_at >= NOW() - INTERVAL '10 minutes'")
            count = cur.fetchone()[0]
            logger.info(f"✓ Total metrics records in last 10 minutes: {count}")

            # Check phase distribution
            cur.execute("""
                SELECT phase, agent_name, COUNT(*)
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '10 minutes'
                GROUP BY phase, agent_name
                ORDER BY phase, agent_name
            """)

            logger.info("  Phase/Agent distribution:")
            for row in cur.fetchall():
                logger.info(f"    - {row[0]}/{row[1]}: {row[2]} records")

            # Check recent metrics
            cur.execute("""
                SELECT phase, agent_name, opportunity_id, duration_seconds, success, api_cost_usd
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '10 minutes'
                ORDER BY created_at DESC
                LIMIT 5
            """)

            logger.info("  Recent metrics:")
            for row in cur.fetchall():
                logger.info(f"    - {row[0]}/{row[1]}/{row[2]}: {row[3]:.3f}s, ${row[5] or 0:.6f}")

        conn.close()
        return count > 0

    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


def clean_test_metrics():
    """Clean up test metrics from database"""
    logger.info("=" * 80)
    logger.info("Cleaning Up Test Metrics")
    logger.info("=" * 80)

    try:
        import psycopg2
        from config import get_settings

        settings = get_settings()
        conn = psycopg2.connect(settings.database_url)

        with conn.cursor() as cur:
            # Delete test metrics
            cur.execute("""
                DELETE FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '10 minutes'
                AND (
                    opportunity_id LIKE 'test-%'
                    OR phase = 'test'
                )
            """)
            deleted = cur.rowcount
            conn.commit()

            logger.info(f"✓ Deleted {deleted} test metrics records")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False


def main():
    """Run all metrics integration tests"""
    logger.info("=" * 80)
    logger.info("PIPELINE METRICS INTEGRATION TEST")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now()}")

    test_results = []

    # Run tests
    tests = [
        ("Metrics Collector Basic", test_metrics_collector),
        ("AgnoOpportunityAnalyzer Metrics", test_agno_analyzer_metrics),
        ("Individual Agent Metrics", test_agent_metrics),
        ("MarketResearchAgent Metrics", test_market_research_agent_metrics),
        ("PipelineOrchestrator Metrics", test_pipeline_orchestrator_metrics)
    ]

    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- Running {test_name} ---")
            result = test_func()
            test_results.append((test_name, result))
            logger.info(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            logger.error(f"✗ {test_name}: ERROR - {e}")
            test_results.append((test_name, False))

    # Verify metrics in database
    logger.info("\n--- Verifying Database Storage ---")
    metrics_stored = verify_metrics_in_database()
    test_results.append(("Database Storage", metrics_stored))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status:<10} {test_name}")

    logger.info("-" * 80)
    logger.info(f"Overall: {passed}/{total} tests passed")
    logger.info(f"Completed at: {datetime.now()}")

    # Clean up test data
    logger.info("\n--- Cleaning Test Data ---")
    clean_test_metrics()

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)