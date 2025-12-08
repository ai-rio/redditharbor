#!/usr/bin/env python3
"""
Test script for new embedding providers
Validates Cohere, Voyage AI, Jina AI, and Google Vertex AI integrations
"""

import logging
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.local'))

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transform.embedding_factory import EmbeddingFactory
from transform.embedding_strategies import EmbeddingStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_provider(provider_type: str, model: str = None, dimensions: int = None, api_key: str = None) -> dict[str, Any]:
    """
    Test a specific embedding provider

    Args:
        provider_type: Type of provider to test
        model: Model name (optional)
        dimensions: Expected dimensions (optional)
        api_key: API key (optional)

    Returns:
        Dictionary with test results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing provider: {provider_type}")
    logger.info(f"{'='*60}")

    test_results = {
        'provider': provider_type,
        'model': model,
        'dimensions': dimensions,
        'tests': {},
        'success': True,
        'error': None
    }

    try:
        # Create provider
        logger.info(f"Creating {provider_type} provider...")
        strategy = EmbeddingFactory.create_provider(
            provider_type=provider_type,
            model=model,
            dimensions=dimensions,
            api_key=api_key
        )

        # Test provider info
        logger.info("\n1. Testing provider info...")
        provider_info = strategy.primary_provider.get_provider_info()
        test_results['tests']['provider_info'] = {
            'success': True,
            'info': provider_info
        }
        logger.info("   ✓ Provider info retrieved")
        logger.info(f"   - Model: {provider_info.get('model', 'unknown')}")
        logger.info(f"   - Dimensions: {provider_info.get('dimensions', 'unknown')}")
        logger.info(f"   - Capabilities: {provider_info.get('capabilities', [])}")

        # Test connection
        logger.info("\n2. Testing connection...")
        connection_ok = strategy.primary_provider.test_connection()
        test_results['tests']['connection'] = {
            'success': connection_ok,
            'message': 'Connected successfully' if connection_ok else 'Connection failed'
        }
        if not connection_ok:
            test_results['success'] = False
            test_results['error'] = 'Connection test failed'
            return test_results
        logger.info("   ✓ Connection successful")

        # Test embedding generation
        logger.info("\n3. Testing embedding generation...")
        test_text = "Reddit is a social news aggregation and discussion website."
        test_metadata = {
            'source': 'test',
            'content_type': 'sample'
        }

        start_time = time.time()
        embedding, metadata = strategy.generate_embedding(test_text, test_metadata)
        end_time = time.time()

        # Validate embedding
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) > 0, "Embedding should not be empty"
        assert all(isinstance(x, float) for x in embedding), "All embedding values should be floats"

        test_results['tests']['embedding_generation'] = {
            'success': True,
            'dimensions': len(embedding),
            'latency_ms': round((end_time - start_time) * 1000, 2),
            'metadata': metadata
        }
        logger.info("   ✓ Embedding generated successfully")
        logger.info(f"   - Dimensions: {len(embedding)}")
        logger.info(f"   - Latency: {test_results['tests']['embedding_generation']['latency_ms']}ms")
        logger.info(f"   - Provider used: {metadata.get('provider_used', 'unknown')}")

        # Test batch processing (small batch)
        logger.info("\n4. Testing batch processing...")
        batch_texts = [
            "First test sentence for batch processing.",
            "Second test sentence with different content.",
            "Third test sentence to verify batch functionality."
        ]

        batch_start = time.time()
        batch_results = []
        for i, text in enumerate(batch_texts):
            embedding, _ = strategy.generate_embedding(text, {'batch_index': i})
            batch_results.append(embedding)
        batch_end = time.time()

        test_results['tests']['batch_processing'] = {
            'success': True,
            'batch_size': len(batch_texts),
            'total_latency_ms': round((batch_end - batch_start) * 1000, 2),
            'avg_latency_per_item_ms': round((batch_end - batch_start) * 1000 / len(batch_texts), 2)
        }
        logger.info("   ✓ Batch processing completed")
        logger.info(f"   - Batch size: {len(batch_texts)}")
        logger.info(f"   - Total latency: {test_results['tests']['batch_processing']['total_latency_ms']}ms")
        logger.info(f"   - Avg per item: {test_results['tests']['batch_processing']['avg_latency_per_item_ms']}ms")

        # Test error handling with fallback
        logger.info("\n5. Testing fallback strategy...")
        if provider_type != "fake":  # Create a strategy with fake fallback
            primary_provider = strategy.primary_provider
            fake_provider = EmbeddingFactory._create_single_provider("fake", dimensions=primary_provider.get_vector_dimensions())
            fallback_strategy = EmbeddingStrategy(primary_provider, fake_provider)

            # This should work normally
            embedding, _ = fallback_strategy.generate_embedding("Test with fallback", {'test': 'fallback'})
            test_results['tests']['fallback'] = {
                'success': True,
                'message': 'Fallback strategy initialized correctly'
            }
            logger.info("   ✓ Fallback strategy configured")
        else:
            test_results['tests']['fallback'] = {
                'success': True,
                'message': 'Fake provider doesn\'t need fallback'
            }

    except Exception as e:
        logger.error(f"Error testing {provider_type}: {e}")
        test_results['success'] = False
        test_results['error'] = str(e)

    return test_results


def main():
    """Main test function"""
    logger.info("\n" + "="*60)
    logger.info("RedditHarbor Embedding Provider Test Suite")
    logger.info("="*60 + "\n")

    # Get API keys from environment or use placeholders
    api_keys = {
        'cohere': os.getenv('COHERE_API_KEY'),
        'voyage': os.getenv('VOYAGE_API_KEY'),
        'jina': os.getenv('JINA_API_KEY'),
        'vertexai': os.getenv('GOOGLE_PROJECT_ID'),  # Using project_id for Vertex AI
        'openai': os.getenv('OPENAI_API_KEY')
    }

    # Test configuration
    test_configs = [
        {
            'provider': 'fake',
            'model': None,
            'dimensions': 1536,
            'api_key': None,
            'skip_reason': None
        },
        {
            'provider': 'openai',
            'model': 'text-embedding-3-small',
            'dimensions': 1536,
            'api_key': api_keys['openai'],
            'skip_reason': 'No OpenAI API key' if not api_keys['openai'] else None
        },
        {
            'provider': 'cohere',
            'model': 'embed-english-v3.0',
            'dimensions': 1024,
            'api_key': api_keys['cohere'],
            'skip_reason': 'No Cohere API key' if not api_keys['cohere'] else None
        },
        {
            'provider': 'voyage',
            'model': 'voyage-large-2',
            'dimensions': 1536,
            'api_key': api_keys['voyage'],
            'skip_reason': 'No Voyage AI API key' if not api_keys['voyage'] else None
        },
        {
            'provider': 'jina',
            'model': 'jina-embeddings-v3',
            'dimensions': 1024,
            'api_key': api_keys['jina'],
            'skip_reason': 'No Jina AI API key' if not api_keys['jina'] else None
        },
        {
            'provider': 'vertexai',
            'model': 'textembedding-gecko@003',
            'dimensions': 768,
            'api_key': api_keys['vertexai'],
            'skip_reason': 'No Google Cloud project configured' if not api_keys['vertexai'] else None
        }
    ]

    # Run tests
    all_results = []
    summary = {
        'total_tests': 0,
        'successful_tests': 0,
        'failed_tests': 0,
        'skipped_tests': 0
    }

    for config in test_configs:
        if config['skip_reason']:
            logger.info(f"\nSkipping {config['provider']}: {config['skip_reason']}")
            summary['skipped_tests'] += 1
            continue

        summary['total_tests'] += 1
        # Convert 'provider' to 'provider_type' for the function call
        provider_config = {k: v for k, v in config.items() if k != 'skip_reason'}
        if 'provider' in provider_config:
            provider_config['provider_type'] = provider_config.pop('provider')
        result = test_provider(**provider_config)
        all_results.append(result)

        if result['success']:
            summary['successful_tests'] += 1
            logger.info(f"\n✓ {config['provider']} test completed successfully")
        else:
            summary['failed_tests'] += 1
            logger.error(f"\n✗ {config['provider']} test failed: {result['error']}")

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    logger.info(f"Total tests: {summary['total_tests']}")
    logger.info(f"Successful: {summary['successful_tests']}")
    logger.info(f"Failed: {summary['failed_tests']}")
    logger.info(f"Skipped: {summary['skipped_tests']}")

    # Performance comparison
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE COMPARISON")
    logger.info("="*60)

    for result in all_results:
        if result['success'] and 'embedding_generation' in result['tests']:
            test = result['tests']['embedding_generation']
            logger.info(f"\n{result['provider'].upper()}:")
            logger.info(f"  - Latency: {test['latency_ms']}ms")
            logger.info(f"  - Dimensions: {test['dimensions']}")

            if 'batch_processing' in result['tests']:
                batch = result['tests']['batch_processing']
                logger.info(f"  - Batch (size {batch['batch_size']}): {batch['avg_latency_per_item_ms']}ms per item")

    # Recommendations
    logger.info("\n" + "="*60)
    logger.info("RECOMMENDATIONS")
    logger.info("="*60)

    if summary['successful_tests'] > 0:
        logger.info("\nBased on test results:")

        # Find fastest provider
        fastest = None
        min_latency = float('inf')

        for result in all_results:
            if result['success'] and 'embedding_generation' in result['tests']:
                latency = result['tests']['embedding_generation']['latency_ms']
                if latency < min_latency:
                    min_latency = latency
                    fastest = result['provider']

        if fastest:
            logger.info(f"  - Fastest provider: {fastest} ({min_latency}ms)")

        logger.info("\n  Provider recommendations:")
        logger.info("  - Cohere: Best for enterprise production use")
        logger.info("  - Voyage AI: Most cost-effective with OpenAI compatibility")
        logger.info("  - Jina AI: Good balance of cost and performance with async support")
        logger.info("  - Vertex AI: Best for Google Cloud infrastructure integration")

        logger.info("\n  Migration path:")
        logger.info("  1. Start with Voyage AI (easiest migration from OpenAI)")
        logger.info("  2. Implement Cohere for enterprise features")
        logger.info("  3. Keep local sentence-transformers as fallback")

    logger.info("\nTest complete! Check the results above for detailed information.")


if __name__ == "__main__":
    main()
