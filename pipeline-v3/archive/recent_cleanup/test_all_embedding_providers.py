#!/usr/bin/env python3
"""
Test all available embedding providers
"""

import os
import sys

sys.path.append('.')

from transform.embedding_factory import EmbeddingFactory
from transform.embedding_strategies import FakeEmbeddingProvider


def test_embedding_providers():
    """Test all available embedding providers"""
    print("=" * 60)
    print("TESTING ALL EMBEDDING PROVIDERS")
    print("=" * 60)

    # Get provider information
    print("\n1. Available Providers:")
    providers_info = EmbeddingFactory.get_provider_info()
    for provider, info in providers_info.items():
        print(f"\n{provider.upper()}:")
        print(f"  Description: {info['description']}")
        print(f"  Cost: {info['cost']}")
        print(f"  Dimensions: {info['dimensions']}")
        print(f"  Use Case: {info['use_case']}")
        if 'note' in info:
            print(f"  Note: {info['note']}")

    # Test Fake Provider (always works)
    print("\n2. Testing Fake Provider...")
    try:
        fake_strategy = EmbeddingFactory.create_provider("fake")
        embedding, metadata = fake_strategy.generate_embedding("Test text")
        print(f"✅ Fake provider: {len(embedding)} dimensions")
        print(f"   Provider: {metadata['provider']}")
    except Exception as e:
        print(f"❌ Fake provider failed: {e}")

    # Test Local Provider (if available)
    print("\n3. Testing Local Provider...")
    try:
        local_strategy = EmbeddingFactory.create_provider("local")
        embedding, metadata = local_strategy.generate_embedding(
            "Test local embedding generation"
        )
        print(f"✅ Local provider: {len(embedding)} dimensions")
        print(f"   Model: {metadata['model']}")
        print(f"   Cost: ${metadata['cost_estimate']}")
    except Exception as e:
        print(f"⚠️  Local provider not available: {e}")
        print("   Install with: pip install sentence-transformers torch")

    # Test OpenAI Provider (if API key available)
    print("\n4. Testing OpenAI Provider...")
    openai_key = os.getenv("OPENAI_EMBEDDINGS_API_KEY")
    if openai_key:
        try:
            openai_strategy = EmbeddingFactory.create_provider("openai")
            embedding, metadata = openai_strategy.generate_embedding(
                "Test OpenAI embedding generation"
            )
            print(f"✅ OpenAI provider: {len(embedding)} dimensions")
            print(f"   Model: {metadata['model']}")
            if 'usage' in metadata:
                print(f"   Tokens: {metadata['usage']}")
        except Exception as e:
            print(f"❌ OpenAI provider failed: {e}")
    else:
        print("⚠️  OpenAI API key not configured")
        print("   Set OPENAI_EMBEDDINGS_API_KEY environment variable")

    # Test Fallback Strategy
    print("\n5. Testing Fallback Strategy (Fake → Local)...")
    try:
        fallback_strategy = EmbeddingFactory.create_provider(
            "local",
            fallback_provider="fake"
        )
        embedding, metadata = fallback_strategy.generate_embedding("Test fallback")
        provider_used = metadata.get('provider_used', 'unknown')
        print(f"✅ Fallback strategy: {provider_used} provider used")
        print(f"   Dimensions: {len(embedding)}")
    except Exception as e:
        print(f"❌ Fallback strategy failed: {e}")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    print("\nFor RedditHarbor embedding needs:")
    print("• Development: Use 'fake' provider (free, deterministic)")
    print("• Production: Use 'openai' provider (high quality)")
    print("• Cost optimization: Use 'local' provider (free)")
    print("• Hybrid: Use 'openai' with 'local' fallback")

    print("\nConfiguration examples:")
    print("  EMBEDDING_PROVIDER=fake        # For testing")
    print("  EMBEDDING_PROVIDER=openai      # For production")
    print("  EMBEDDING_PROVIDER=local       # For cost savings")

if __name__ == "__main__":
    test_embedding_providers()
