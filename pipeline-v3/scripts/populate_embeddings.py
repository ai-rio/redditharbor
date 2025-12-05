#!/usr/bin/env python3
"""
Script to populate embeddings for existing opportunities in the database

This script:
1. Connects to the PostgreSQL database
2. Fetches existing opportunities without embeddings
3. Generates embeddings using FakeEmbeddingProvider
4. Updates the database with generated embeddings
5. Provides progress reporting and error handling
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transform.embedding_strategies import FakeEmbeddingProvider, EmbeddingStrategy
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingPopulator:
    """Handles embedding population for existing opportunities"""

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize populator with database configuration

        Args:
            db_config: Database connection configuration
        """
        self.db_config = db_config
        self.embedding_strategy = None
        self.conn = None
        self._initialize_embedding_strategy()

    def _initialize_embedding_strategy(self):
        """Initialize embedding strategy using FakeEmbeddingProvider"""
        try:
            provider = FakeEmbeddingProvider(dimensions=1536)
            self.embedding_strategy = EmbeddingStrategy(provider)
            logger.info("✓ Initialized FakeEmbeddingProvider for embedding generation")
        except Exception as e:
            logger.error(f"Failed to initialize embedding strategy: {e}")
            raise

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("✓ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Disconnected from database")

    def get_opportunities_without_embeddings(self) -> List[Dict[str, Any]]:
        """
        Fetch opportunities that don't have embeddings yet

        Returns:
            List of opportunity dictionaries
        """
        query = """
        SELECT
            id,
            reddit_title,
            problem_statement,
            app_concept,
            subreddit,
            market_demand,
            pain_intensity,
            monetization_potential,
            confidence_score,
            created_at,
            updated_at
        FROM opportunities
        WHERE embedding_vector IS NULL
        ORDER BY created_at DESC
        """

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                opportunities = cursor.fetchall()
                logger.info(f"Found {len(opportunities)} opportunities without embeddings")
                return opportunities
        except Exception as e:
            logger.error(f"Failed to fetch opportunities: {e}")
            raise

    def generate_embedding_text(self, opportunity: Dict[str, Any]) -> str:
        """
        Generate comprehensive text for embedding creation

        Args:
            opportunity: Opportunity data dictionary

        Returns:
            Combined text string for embedding generation
        """
        text_parts = [
            f"Title: {opportunity['reddit_title'] or ''}",
            f"Problem: {opportunity['problem_statement'] or ''}",
            f"Concept: {opportunity['app_concept'] or ''}",
            f"Subreddit: {opportunity['subreddit'] or ''}",
            f"Market Demand: {opportunity['market_demand'] or 0:.1f}",
            f"Pain Intensity: {opportunity['pain_intensity'] or 0:.1f}",
            f"Monetization Potential: {opportunity['monetization_potential'] or 0:.1f}",
            f"Confidence: {opportunity['confidence_score'] or 0:.1f}%"
        ]

        return " | ".join(text_parts)

    def generate_embedding_for_opportunity(self, opportunity: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding vector for a single opportunity

        Args:
            opportunity: Opportunity data dictionary

        Returns:
            Embedding vector or None if generation fails
        """
        try:
            # Prepare text for embedding
            embedding_text = self.generate_embedding_text(opportunity)

            # Generate embedding with metadata
            embedding_vector, embedding_metadata = self.embedding_strategy.generate_embedding(
                embedding_text,
                metadata={
                    'opportunity_id': opportunity['id'],
                    'subreddit': opportunity['subreddit'] or '',
                    'market_demand': opportunity['market_demand'] or 0,
                    'pain_intensity': opportunity['pain_intensity'] or 0,
                    'monetization_potential': opportunity['monetization_potential'] or 0,
                    'confidence_score': opportunity['confidence_score'] or 0,
                    'generated_at': datetime.now().isoformat()
                }
            )

            logger.debug(f"Generated {len(embedding_vector)}-dimensional embedding for opportunity {opportunity['id']}")
            return embedding_vector

        except Exception as e:
            logger.error(f"Failed to generate embedding for opportunity {opportunity['id']}: {e}")
            return None

    def update_opportunity_embedding(self, opportunity_id: str, embedding_vector: List[float]) -> bool:
        """
        Update opportunity with embedding vector

        Args:
            opportunity_id: ID of opportunity to update
            embedding_vector: Embedding vector to store

        Returns:
            True if successful, False otherwise
        """
        query = """
        UPDATE opportunities
        SET embedding_vector = %s, updated_at = %s
        WHERE id = %s
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (embedding_vector, datetime.now(), opportunity_id))
                self.conn.commit()
                logger.debug(f"✓ Updated embedding for opportunity {opportunity_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update embedding for opportunity {opportunity_id}: {e}")
            self.conn.rollback()
            return False

    def populate_embeddings(self) -> Dict[str, Any]:
        """
        Main method to populate embeddings for all opportunities

        Returns:
            Summary dictionary with results
        """
        results = {
            'total_opportunities': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'errors': []
        }

        try:
            # Connect to database
            self.connect()

            # Get opportunities without embeddings
            opportunities = self.get_opportunities_without_embeddings()
            results['total_opportunities'] = len(opportunities)

            if not opportunities:
                logger.info("✓ All opportunities already have embeddings")
                return results

            logger.info(f"Starting embedding generation for {len(opportunities)} opportunities")

            # Process each opportunity
            for i, opportunity in enumerate(opportunities, 1):
                logger.info(f"Processing opportunity {i}/{len(opportunities)}: {opportunity['id']}")

                try:
                    # Generate embedding
                    embedding_vector = self.generate_embedding_for_opportunity(opportunity)

                    if embedding_vector:
                        # Update database
                        success = self.update_opportunity_embedding(opportunity['id'], embedding_vector)
                        if success:
                            results['successful_updates'] += 1
                        else:
                            results['failed_updates'] += 1
                            results['errors'].append(f"Failed to update embedding for opportunity {opportunity['id']}")
                    else:
                        results['failed_updates'] += 1
                        results['errors'].append(f"Failed to generate embedding for opportunity {opportunity['id']}")

                except Exception as e:
                    results['failed_updates'] += 1
                    error_msg = f"Error processing opportunity {opportunity['id']}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)

            logger.info(f"Embedding population completed: {results['successful_updates']} successful, {results['failed_updates']} failed")

        except Exception as e:
            logger.error(f"Embedding population failed: {e}")
            results['errors'].append(f"Population failed: {str(e)}")
        finally:
            self.disconnect()

        return results


def main():
    """Main function to run the embedding population script"""
    # Database configuration - adjust as needed for your environment
    db_config = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', 54322)),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }

    logger.info("Starting embedding population for existing opportunities")

    # Create populator and run
    populator = EmbeddingPopulator(db_config)
    results = populator.populate_embeddings()

    # Print summary
    print("\n" + "="*50)
    print("EMBEDDING POPULATION SUMMARY")
    print("="*50)
    print(f"Total opportunities processed: {results['total_opportunities']}")
    print(f"Successful updates: {results['successful_updates']}")
    print(f"Failed updates: {results['failed_updates']}")

    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")

    print("="*50)

    # Exit with appropriate code
    if results['failed_updates'] > 0:
        logger.warning("Some embeddings failed to populate")
        sys.exit(1)
    else:
        logger.info("All embeddings populated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()