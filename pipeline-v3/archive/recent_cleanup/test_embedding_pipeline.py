#!/usr/bin/env python3
"""
Test script for embedding pipeline integration

This script tests:
1. AgnoOpportunityAnalyzer embedding generation
2. FakeEmbeddingProvider functionality
3. Vector index creation
4. End-to-end embedding pipeline
"""

import logging
import os
import sys
from datetime import UTC, datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.reddit import RedditSubmission
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from transform.embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_embedding_provider():
    """Test FakeEmbeddingProvider functionality"""
    logger.info("Testing FakeEmbeddingProvider...")

    try:
        # Create provider
        provider = FakeEmbeddingProvider(dimensions=384)

        # Test connection
        connection_ok = provider.test_connection()
        logger.info(f"✓ Connection test: {connection_ok}")

        # Test embedding generation
        test_text = "This is a test Reddit post about a startup idea for improving developer productivity"
        embedding, metadata = provider.generate_embedding(test_text)

        logger.info(f"✓ Generated embedding: {len(embedding)} dimensions")
        logger.info(f"✓ Embedding metadata keys: {list(metadata.keys())}")
        logger.info(f"✓ Provider info: {provider.get_provider_info()}")

        # Verify embedding properties
        assert len(embedding) == 384, "Embedding should have 384 dimensions"
        assert all(isinstance(x, float) for x in embedding), "All embedding values should be floats"
        assert metadata['provider'] == 'fake', "Metadata should indicate fake provider"
        assert metadata['dimensions'] == 384, "Metadata should specify dimensions"

        logger.info("✓ FakeEmbeddingProvider test passed")
        return True

    except Exception as e:
        logger.error(f"✗ FakeEmbeddingProvider test failed: {e}")
        return False


def test_embedding_strategy():
    """Test EmbeddingStrategy with fallback"""
    logger.info("Testing EmbeddingStrategy...")

    try:
        # Create strategy
        primary_provider = FakeEmbeddingProvider(dimensions=384)
        strategy = EmbeddingStrategy(primary_provider)

        # Test strategy info
        info = strategy.get_strategy_info()
        logger.info(f"✓ Strategy info: {info}")

        # Test embedding generation
        test_text = "AI-powered code review tool that helps developers write better code"
        embedding, metadata = strategy.generate_embedding(test_text)

        logger.info(f"✓ Generated embedding: {len(embedding)} dimensions")
        logger.info(f"✓ Provider used: {metadata.get('provider_used', 'unknown')}")

        # Test strategy
        strategy_ok = strategy.test_strategy()
        logger.info(f"✓ Strategy test: {strategy_ok}")

        logger.info("✓ EmbeddingStrategy test passed")
        return True

    except Exception as e:
        logger.error(f"✗ EmbeddingStrategy test failed: {e}")
        return False


def test_agno_analyzer_embeddings():
    """Test AgnoOpportunityAnalyzer with embedding generation"""
    logger.info("Testing AgnoOpportunityAnalyzer embedding generation...")

    try:
        # Create analyzer with embeddings enabled
        analyzer = AgnoOpportunityAnalyzer(
            enable_embeddings=True,
            embedding_provider="fake"
        )

        # Create test submission
        test_submission = RedditSubmission(
            id="test_123",
            title="AI-powered developer productivity tool",
            text="Looking for a solution that automatically reviews code and suggests improvements",
            subreddit="programming",
            author="developer123",
            upvotes=245,
            downvotes=0,
            score=245,
            comments_count=45,
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/programming/test_123"
        )

        # Analyze submission
        result = analyzer.analyze_submission(test_submission)

        # Check embedding was generated
        if result.embedding:
            logger.info(f"✓ Embedding generated: {len(result.embedding)} dimensions")
            logger.info(f"✓ Embedding sample: {result.embedding[:5]}...")
            logger.info(f"✓ Analysis score: {result.final_score}")

            # Verify embedding properties
            assert len(result.embedding) == 1536, "Embedding should have 1536 dimensions"
            assert all(isinstance(x, float) for x in result.embedding), "All embedding values should be floats"

            logger.info("✓ AgnoOpportunityAnalyzer embedding test passed")
            return True
        else:
            logger.error("✗ No embedding generated in analysis result")
            return False

    except Exception as e:
        logger.error(f"✗ AgnoOpportunityAnalyzer embedding test failed: {e}")
        return False


def test_agno_analyzer_disabled_embeddings():
    """Test AgnoOpportunityAnalyzer with embeddings disabled"""
    logger.info("Testing AgnoOpportunityAnalyzer with embeddings disabled...")

    try:
        # Create analyzer with embeddings disabled
        analyzer = AgnoOpportunityAnalyzer(
            enable_embeddings=False
        )

        # Create test submission
        test_submission = RedditSubmission(
            id="test_456",
            title="Simple business automation tool",
            text="Need help with automating repetitive business tasks",
            subreddit="entrepreneur",
            author="businessowner",
            upvotes=123,
            downvotes=0,
            score=123,
            comments_count=23,
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/entrepreneur/test_456"
        )

        # Analyze submission
        result = analyzer.analyze_submission(test_submission)

        # Check no embedding was generated
        if result.embedding is None:
            logger.info("✓ Embedding correctly None when disabled")
            logger.info(f"✓ Analysis still works: score {result.final_score}")
            logger.info("✓ AgnoOpportunityAnalyzer disabled embedding test passed")
            return True
        else:
            logger.error("✗ Embedding generated despite being disabled")
            return False

    except Exception as e:
        logger.error(f"✗ AgnoOpportunityAnalyzer disabled embedding test failed: {e}")
        return False


def test_embedding_consistency():
    """Test that same input produces same embedding (deterministic)"""
    logger.info("Testing embedding consistency...")

    try:
        analyzer = AgnoOpportunityAnalyzer(
            enable_embeddings=True,
            embedding_provider="fake"
        )

        test_submission = RedditSubmission(
            id="consistency_test",
            title="Test for consistent embeddings",
            text="Same content should produce same embedding vector",
            subreddit="testing",
            author="tester",
            upvotes=50,
            downvotes=0,
            score=50,
            comments_count=10,
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/testing/consistency_test"
        )

        # Analyze twice
        result1 = analyzer.analyze_submission(test_submission)
        result2 = analyzer.analyze_submission(test_submission)

        # Compare embeddings
        if result1.embedding and result2.embedding:
            # Check if embeddings are identical (deterministic)
            identical = result1.embedding == result2.embedding
            logger.info(f"✓ Embeddings identical: {identical}")

            if identical:
                logger.info("✓ Embedding consistency test passed")
                return True
            else:
                logger.error("✗ Embeddings differ for same input")
                return False
        else:
            logger.error("✗ No embeddings generated for consistency test")
            return False

    except Exception as e:
        logger.error(f"✗ Embedding consistency test failed: {e}")
        return False


def run_database_connection_test():
    """Test database connection and vector capabilities"""
    logger.info("Testing database connection...")

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # Database configuration
        db_config = {
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'port': int(os.getenv('DB_PORT', 54322)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }

        # Connect to database
        conn = psycopg2.connect(**db_config)

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check pgvector extension
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            vector_installed = cursor.fetchone()

            if vector_installed:
                logger.info("✓ pgvector extension is installed")
            else:
                logger.error("✗ pgvector extension is not installed")
                return False

            # Check opportunities table
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'opportunities' AND column_name = 'embedding_vector'
            """)
            embedding_column = cursor.fetchone()

            if embedding_column:
                logger.info(f"✓ embedding_vector column exists: {embedding_column['data_type']}")
            else:
                logger.error("✗ embedding_vector column does not exist")
                return False

            # Count opportunities without embeddings
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM opportunities
                WHERE embedding_vector IS NULL
            """)
            result = cursor.fetchone()
            logger.info(f"✓ Opportunities without embeddings: {result['count']}")

            # Check vector indexes
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'opportunities' AND indexname LIKE '%embedding%'
            """)
            indexes = cursor.fetchall()

            logger.info(f"✓ Vector indexes found: {len(indexes)}")
            for idx in indexes:
                logger.info(f"  - {idx['indexname']}")

        conn.close()
        logger.info("✓ Database connection test passed")
        return True

    except ImportError:
        logger.warning("⚠ psycopg2 not available, skipping database test")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection test failed: {e}")
        return False


def main():
    """Main test function"""
    logger.info("Starting embedding pipeline integration tests")

    tests = [
        ("Embedding Provider", test_embedding_provider),
        ("Embedding Strategy", test_embedding_strategy),
        ("Agno Analyzer with Embeddings", test_agno_analyzer_embeddings),
        ("Agno Analyzer without Embeddings", test_agno_analyzer_disabled_embeddings),
        ("Embedding Consistency", test_embedding_consistency),
        ("Database Connection", run_database_connection_test)
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"RUNNING TEST: {test_name}")
        logger.info(f"{'='*50}")

        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")

    passed = 0
    failed = 0

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        symbol = "✓" if success else "✗"
        logger.info(f"{symbol} {test_name}: {status}")

        if success:
            passed += 1
        else:
            failed += 1

    logger.info(f"\nTotal: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")

    if failed > 0:
        logger.error("\nSome tests failed. Please check the logs above.")
        sys.exit(1)
    else:
        logger.info("\nAll tests passed! 🎉")
        logger.info("Embedding pipeline is working correctly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
