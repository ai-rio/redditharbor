#!/usr/bin/env python3
"""
Jina Market Research Example

This example demonstrates how to use the Jina client architecture for
Phase 3 Market Research Integration. It shows:
- Jina client initialization
- Web search for competitors
- Content extraction from URLs
- Structured data extraction with LLM
- Redis caching with configurable TTL
- Cost tracking and optimization
- MarketResearchAgent integration

Usage:
    python examples/jina_market_research_example.py [--real-api]
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import components
from config.settings import get_settings

try:
    from transform.jina_client import JinaClient, SearchResult, JinaResponse
    from transform.caching.jina_cache import get_jina_cache
    from transform.market_research_agent import MarketResearchAgent
    from transform.validation_evidence_pydantic import ValidationEvidence
    JINA_AVAILABLE = True
except ImportError as e:
    print(f"Jina components not available: {str(e)}")
    JINA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_jina_client_usage(use_real_api: bool = False):
    """
    Example demonstrating Jina client usage
    """
    if not JINA_AVAILABLE:
        logger.error("Jina components not available")
        return

    logger.info("=== Jina Client Usage Example ===")

    # Get settings
    settings = get_settings()

    # Initialize Jina client
    jina_client = JinaClient(
        api_key=settings.jina_api_key if use_real_api else None,
        llm_model=settings.jina_llm_model,
        llm_api_key=settings.jina_llm_api_key or settings.openai_api_key,
        llm_base_url=settings.jina_llm_base_url,
        enable_caching=settings.jina_enable_cache,
        enable_cost_tracking=settings.jina_enable_cost_tracking,
        rate_limit=settings.jina_rate_limit,
        timeout=settings.jina_timeout,
        max_retries=settings.jina_max_retries
    )

    try:
        # Example 1: Web Search
        logger.info("\n1. Performing web search for competitors...")
        search_query = "project management software pricing competitors B2B"

        if use_real_api:
            try:
                results = await jina_client.search_web(
                    query=search_query,
                    num_results=5
                )
                logger.info(f"Found {len(results)} search results:")
                for i, result in enumerate(results, 1):
                    logger.info(f"  {i}. {result.title}")
                    logger.info(f"     URL: {result.url}")
                    logger.info(f"     Description: {result.description[:100]}...")
            except Exception as e:
                logger.error(f"Search failed: {str(e)}")
                return
        else:
            logger.info(f"Would search for: {search_query}")
            logger.info("(Use --real-api to perform actual search)")

        # Example 2: Content Extraction
        logger.info("\n2. Extracting content from URL...")
        example_url = "https://example.com/pricing"

        if use_real_api:
            try:
                content = await jina_client.read_url(example_url)
                logger.info(f"Extracted {len(content.content)} characters from {content.url}")
                logger.info(f"Title: {content.title}")
                logger.info(f"Content preview: {content.content[:200]}...")
            except Exception as e:
                logger.error(f"Content extraction failed: {str(e)}")
                return
        else:
            logger.info(f"Would extract content from: {example_url}")
            logger.info("(Use --real-api to perform actual extraction)")

        # Example 3: Structured Data Extraction
        logger.info("\n3. Extracting structured pricing data...")
        sample_content = """
        # Pricing Plans

        ## Basic Plan - $10/month
        - Up to 10 users
        - 10GB storage
        - Email support

        ## Pro Plan - $25/month
        - Unlimited users
        - 100GB storage
        - Priority support

        ## Enterprise - Custom pricing
        - Custom features
        - Dedicated support
        """

        if use_real_api:
            try:
                pricing = await jina_client.extract_competitor_pricing(
                    content=sample_content,
                    source_url="https://example.com/pricing"
                )
                if pricing:
                    logger.info(f"Extracted pricing for: {pricing.company_name}")
                    logger.info(f"Pricing model: {pricing.pricing_model}")
                    logger.info(f"Target market: {pricing.target_market}")
                    logger.info(f"Confidence: {pricing.confidence}%")
                    logger.info("Pricing tiers:")
                    for tier in pricing.pricing_tiers:
                        logger.info(f"  - {tier['name']}: {tier.get('price', 'N/A')}")
            except Exception as e:
                logger.error(f"Pricing extraction failed: {str(e)}")
        else:
            logger.info("Would extract structured pricing from content")
            logger.info("(Use --real-api to perform actual extraction)")

        # Example 4: Cost Tracking
        logger.info("\n4. Cost tracking summary:")
        cost_summary = jina_client.get_cost_summary()
        for key, value in cost_summary.items():
            logger.info(f"  {key}: {value}")

    finally:
        await jina_client.close()


async def example_market_research_agent(use_real_api: bool = False):
    """
    Example demonstrating MarketResearchAgent usage
    """
    if not JINA_AVAILABLE:
        logger.error("Jina components not available")
        return

    logger.info("\n=== MarketResearchAgent Example ===")

    # Initialize agent
    async with MarketResearchAgent(
        jina_api_key=get_settings().jina_api_key if use_real_api else None,
        validation_threshold=70.0,
        max_competitors=3,
        max_launches=2,
        enable_cost_tracking=True,
        use_real_jina=use_real_api
    ) as agent:

        # Example opportunity to validate
        opportunity = {
            "app_concept": "AI-powered project management assistant",
            "target_market": "B2B SaaS",
            "problem_description": "Teams struggle with task prioritization and resource allocation"
        }

        logger.info(f"\nValidating opportunity: {opportunity['app_concept']}")
        logger.info(f"Target market: {opportunity['target_market']}")
        logger.info(f"Problem: {opportunity['problem_description']}")

        # Check if validation should be triggered
        test_score = 75.0  # Above threshold
        if agent.should_validate_opportunity(test_score):
            logger.info(f"Score {test_score} >= threshold {agent.validation_threshold}, triggering validation...")

            # Perform market validation
            result = await agent.run(opportunity)

            # Display results
            logger.info("\n=== Market Validation Results ===")
            logger.info(f"Validation Score: {result['validation_score']}/100")
            logger.info(f"Data Quality Score: {result['data_quality_score']}/100")
            logger.info(f"Total Cost: ${result['jina_cost']:.6f}")

            logger.info("\nCompetitor Pricing:")
            for competitor in result['competitor_pricing']:
                logger.info(f"  - {competitor['company']}: {competitor['pricing_model']}")
                for tier in competitor.get('tiers', []):
                    logger.info(f"    * {tier['name']}: {tier.get('price', 'N/A')}")

            logger.info("\nMarket Size:")
            if result['market_size']:
                market = result['market_size']
                logger.info(f"  TAM: {market.get('tam', 'N/A')}")
                logger.info(f"  SAM: {market.get('sam', 'N/A')}")
                logger.info(f"  Growth: {market.get('growth', 'N/A')}")
                logger.info(f"  Source: {market.get('source', 'N/A')}")

            logger.info("\nSimilar Product Launches:")
            for launch in result['similar_launches']:
                logger.info(f"  - {launch['product']} on {launch['platform']}")
                logger.info(f"    Upvotes: {launch['upvotes']}")
                logger.info(f"    Comments: {launch['comments']}")

            logger.info(f"\nReasoning: {result['reasoning']}")

            logger.info(f"\nEvidence URLs: {len(result['evidence_urls'])}")
            for url in result['evidence_urls']:
                logger.info(f"  - {url}")

            # Get cost summary
            cost_summary = agent.get_cost_summary()
            logger.info(f"\nCost Summary:")
            logger.info(f"  Total Validations: {cost_summary['validation_count']}")
            logger.info(f"  Total Cost: ${cost_summary['total_cost']:.6f}")
            logger.info(f"  Average Cost per Validation: ${cost_summary['average_cost_per_validation']:.6f}")
        else:
            logger.info(f"Score {test_score} below threshold, skipping validation")


async def example_caching_performance():
    """
    Example demonstrating caching performance and cost savings
    """
    if not JINA_AVAILABLE:
        logger.error("Jina components not available")
        return

    logger.info("\n=== Caching Performance Example ===")

    # Initialize cache
    settings = get_settings()
    cache = await get_jina_cache(
        redis_url=settings.jina_redis_url,
        redis_db=settings.jina_redis_db,
        default_ttl={
            "competitor_pricing": settings.jina_cache_ttl_competitor,
            "market_size": settings.jina_cache_ttl_market,
            "product_launch": settings.jina_cache_ttl_launch
        }
    )

    try:
        # Example cache operations
        app_concept = "Project Management Tool"
        target_market = "B2B SaaS"

        # Simulate cached data
        test_data = {
            "company_name": "TestCompetitor",
            "pricing_model": "subscription",
            "pricing_tiers": [
                {"name": "Basic", "price": "$10/mo"},
                {"name": "Pro", "price": "$25/mo"}
            ],
            "target_market": "B2B",
            "source_url": "https://example.com/pricing",
            "confidence": 85.0
        }

        # Cache data
        logger.info(f"Caching competitor data for: {app_concept}")
        await cache.set(
            data_type="competitor_pricing",
            app_concept=app_concept,
            target_market=target_market,
            data=test_data
        )

        # Retrieve from cache
        logger.info("Retrieving from cache...")
        cached_data = await cache.get(
            data_type="competitor_pricing",
            app_concept=app_concept,
            target_market=target_market
        )

        if cached_data:
            logger.info("Cache hit! Data retrieved successfully")
            logger.info(f"Company: {cached_data['company_name']}")
            logger.info(f"Pricing: {cached_data['pricing_model']}")
        else:
            logger.error("Cache miss - data not found")

        # Get cache statistics
        stats = await cache.get_stats()
        logger.info("\nCache Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

        # Estimate cost savings
        savings = cache.estimate_cost_savings()
        logger.info("\nCost Savings Estimate:")
        logger.info(f"  Cache hits: {savings['cache_hits']}")
        logger.info(f"  Estimated cost saved: ${savings['estimated_cost_saved']:.6f}")

        # Demonstrate cache invalidation
        logger.info("\nInvalidating competitor pricing cache...")
        invalidated = await cache.invalidate(data_type="competitor_pricing")
        logger.info(f"Invalidated {invalidated} cache entries")

    finally:
        await cache.close()


async def main():
    """
    Main function to run all examples
    """
    parser = argparse.ArgumentParser(description="Jina Market Research Examples")
    parser.add_argument(
        "--real-api",
        action="store_true",
        help="Use real Jina API (requires API keys in environment)"
    )
    parser.add_argument(
        "--component",
        choices=["client", "agent", "cache", "all"],
        default="all",
        help="Which component to demonstrate"
    )

    args = parser.parse_args()

    logger.info("Jina Market Research Integration Examples")
    logger.info("=========================================")

    if args.real_api:
        logger.warning("Using real Jina API - this will incur costs!")
        logger.info("Make sure you have JINA_API_KEY and OPENROUTER_API_KEY set in your environment")
    else:
        logger.info("Running in demo mode (no API calls will be made)")
        logger.info("Use --real-api to make actual API calls")

    try:
        if args.component in ["client", "all"]:
            await example_jina_client_usage(use_real_api=args.real_api)

        if args.component in ["agent", "all"]:
            await example_market_research_agent(use_real_api=args.real_api)

        if args.component in ["cache", "all"]:
            await example_caching_performance()

        logger.info("\n✅ All examples completed successfully!")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Examples interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error running examples: {str(e)}")
        raise


if __name__ == "__main__":
    # Check for Jina availability
    if not JINA_AVAILABLE:
        print("❌ Jina components not available")
        print("Please ensure all dependencies are installed:")
        print("  pip install httpx litellm redis")
        sys.exit(1)

    # Run examples
    asyncio.run(main())