#!/usr/bin/env python3
"""
Test OpenRouter embedding functionality with text-embedding-3-small
"""

import os
import sys

sys.path.append('.')

from config.settings import get_settings
from transform.embedding_strategies import (
    EmbeddingStrategy,
    FakeEmbeddingProvider,
    OpenRouterEmbeddingProvider,
)


def test_openrouter_embeddings():
    """Test OpenRouter embedding provider functionality"""
    print("=" * 60)
    print("TESTING OPENROUTER EMBEDDINGS")
    print("=" * 60)

    # Check OpenRouter API key configuration
    print("\n1. Checking OpenRouter Configuration...")
    settings = get_settings()

    if not settings.openai_api_key or settings.openai_api_key == 'test_api_key':
        print("❌ OpenRouter API key not configured")
        print("   Set OPENROUTER_API_KEY environment variable")
        return False

    if 'openrouter' not in settings.openai_base_url.lower():
        print("❌ OpenRouter base URL not configured")
        print(f"   Current base URL: {settings.openai_base_url}")
        return False

    print(f"✅ OpenRouter API key configured (length: {len(settings.openai_api_key)})")
    print(f"✅ OpenRouter base URL: {settings.openai_base_url}")

    # Test OpenRouter Embedding Provider
    print("\n2. Testing OpenRouterEmbeddingProvider...")
    try:
        openrouter_provider = OpenRouterEmbeddingProvider(
            model="openai/text-embedding-3-small",
            dimensions=1536
        )

        print("✅ Provider initialized successfully")
        print(f"✅ Provider info: {openrouter_provider.get_provider_info()}")

        # Test connection
        connection_ok = openrouter_provider.test_connection()
        if connection_ok:
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return False

    except Exception as e:
        print(f"❌ Provider initialization failed: {e}")
        return False

    # Test embedding generation
    print("\n3. Testing Embedding Generation...")
    try:
        test_text = "RedditHarbor is a comprehensive Reddit data collection platform"
        embedding, metadata = openrouter_provider.generate_embedding(test_text)

        print("✅ Embedding generated successfully")
        print(f"✅ Dimensions: {len(embedding)}")
        print(f"✅ Provider: {metadata['provider']}")
        print(f"✅ Model: {metadata['model']}")
        print(f"✅ Cost estimate: ${metadata.get('cost_estimate', 0.0):.8f}")
        print(f"✅ Content preview: {metadata['content_preview'][:50]}...")

        # Show embedding sample
        print(f"✅ Embedding sample: {embedding[:5]}")

    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return False

    # Test with realistic opportunity text
    print("\n4. Testing with Real Opportunity Data...")
    try:
        opportunity_text = """
        App Title: AI-Powered Code Review Assistant
        Concept: An automated tool that analyzes code quality, suggests improvements, and provides security scanning for developers
        Subreddit: programming
        Problem: Developers struggle with manual code review process
        """

        embedding, metadata = openrouter_provider.generate_embedding(opportunity_text)

        print("✅ Opportunity embedding generated")
        print(f"✅ Text length: {len(opportunity_text)} characters")
        print(f"✅ Embedding dimensions: {len(embedding)}")
        print(f"✅ Estimated cost: ${metadata.get('cost_estimate', 0.0):.8f}")

    except Exception as e:
        print(f"❌ Opportunity embedding failed: {e}")
        return False

    # Test strategy with fallback
    print("\n5. Testing EmbeddingStrategy with Fallback...")
    try:
        openrouter_provider = OpenRouterEmbeddingProvider(dimensions=1536)
        fake_provider = FakeEmbeddingProvider(dimensions=1536)

        strategy = EmbeddingStrategy(
            primary_provider=openrouter_provider,
            fallback_provider=fake_provider
        )

        embedding, metadata = strategy.generate_embedding("Test strategy embedding")

        print("✅ Strategy test passed")
        print(f"✅ Provider used: {metadata.get('provider_used', 'unknown')}")
        print(f"✅ Embedding dimensions: {len(embedding)}")

    except Exception as e:
        print(f"❌ Strategy test failed: {e}")
        return False

    # Test with AgnoOpportunityAnalyzer
    print("\n6. Testing AgnoOpportunityAnalyzer with OpenRouter...")
    try:
        from models.reddit import RedditSubmission
        from transform.agno_analyzer import AgnoOpportunityAnalyzer

        # Create analyzer with OpenRouter embeddings
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            enable_embeddings=True,
            embedding_provider="openrouter"
        )

        # Create test submission
        submission = RedditSubmission(
            id="test_openrouter_123",
            title="Automated Testing Tool",
            text="Looking for a tool to automate unit testing and integration testing",
            author="test_user",
            subreddit="programming",
            created_at="2025-12-05T08:00:00Z"
        )

        # Run analysis
        print("   Running analysis with OpenRouter embeddings...")
        result = analyzer.analyze_submission(submission)

        if result.embedding:
            print("✅ Agno analysis with embeddings successful")
            print(f"✅ Analysis score: {result.final_score:.2f}")
            print(f"✅ Embedding dimensions: {len(result.embedding)}")
        else:
            print("❌ No embedding generated by Agno analyzer")
            return False

    except Exception as e:
        print(f"❌ Agno analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ ALL OPENROUTER EMBEDDING TESTS PASSED!")
    print("=" * 60)
    return True

def test_cost_comparison():
    """Compare costs between different providers"""
    print("\nCOST COMPARISON")
    print("-" * 40)

    test_text = "This is a test text for embedding cost comparison"

    # Fake provider (free)
    fake_provider = FakeEmbeddingProvider(dimensions=1536)
    _, fake_metadata = fake_provider.generate_embedding(test_text)

    # OpenRouter provider (estimated)
    openrouter_provider = OpenRouterEmbeddingProvider(dimensions=1536)
    _, openrouter_metadata = openrouter_provider.generate_embedding(test_text)

    print(f"Fake Provider: ${0.0} (free)")
    print(f"OpenRouter: ${openrouter_metadata.get('cost_estimate', 0.0):.8f}")

    # Estimate daily usage
    daily_opportunities = 100
    daily_cost = openrouter_metadata.get('cost_estimate', 0.0) * daily_opportunities
    print(f"\nEstimated daily cost ({daily_opportunities} opportunities): ${daily_cost:.4f}")
    print(f"Estimated monthly cost: ${daily_cost * 30:.2f}")

if __name__ == "__main__":
    print("Testing OpenRouter Embeddings with text-embedding-3-small")
    print("Using OpenRouter for flexibility and cost management")

    success = test_openrouter_embeddings()

    if success:
        test_cost_comparison()
        print("\n🎉 OpenRouter embeddings are ready for production use!")
    else:
        print("\n❌ Please fix configuration issues before using OpenRouter embeddings")
        sys.exit(1)
