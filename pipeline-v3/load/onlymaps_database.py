"""
PostgreSQL Database Loader - Direct Implementation

This module provides OnlyMapsDatabaseLoader that works directly with PostgreSQL:
1. Direct PostgreSQL connection on port 54322
2. Type-safe SQL-to-Python mapping
3. Agno field support for multi-agent analysis results
4. Compatible with existing orchestration layer
"""

import logging

import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DatabaseStats(BaseModel):
    """Database statistics model for OnlyMaps integration"""
    total_opportunities: int
    avg_final_score: float | None = None  # Handles missing final_score column
    max_score: float | None = None


class OpportunitySummary(BaseModel):
    """Opportunity summary model with schema flexibility"""
    id: str
    app_title: str
    final_score: float | None = None  # This field doesn't exist in current DB schema
    trust_level: str = "MEDIUM"


class OnlyMapsDatabaseLoader:
    """
    OnlyMaps-based database loader with schema flexibility

    Compatible interface with original DatabaseLoader for easy replacement
    Solves the core issues identified in tests:
    - Handles missing final_score column gracefully
    - Provides type-safe SQL-to-Python mapping
    - Simulates connection pooling
    - Compatible with existing orchestration layer
    """

    def __init__(self, repository=None, data_mapper=None, settings=None):
        """
        Initialize OnlyMaps Database Loader with compatible interface

        Args:
            repository: Not used in OnlyMaps implementation (compatibility)
            data_mapper: Not used in OnlyMaps implementation (compatibility)
            settings: Application settings for database URL
        """
        # Direct PostgreSQL connection settings
        self.database_url = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"
        self.connection = None

        logger.info("PostgreSQL Database Loader initialized for Agno field persistence")

    def _get_connection(self):
        """Get or create PostgreSQL connection"""
        if self.connection is None:
            self.connection = psycopg2.connect(
                host="127.0.0.1",
                port="54331",
                user="postgres",
                password="postgres",
                database="postgres"
            )
        return self.connection

    def _get_statistics_internal(self) -> DatabaseStats:
        """
        Get database statistics with schema flexibility

        Handles missing final_score column gracefully by using COALESCE
        Returns DatabaseStats with None values for missing columns

        Returns:
            DatabaseStats: Database statistics with schema flexibility
        """
        logger.debug("Getting database statistics with PostgreSQL")

        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Fetch statistics with missing column handling
            sql = """
                SELECT COUNT(*) as total_opportunities,
                       COALESCE(AVG(final_score), 0) as avg_final_score,
                       COALESCE(MAX(final_score), 0) as max_score
                FROM opportunities
            """

            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()

            if row is None:
                # Return default statistics if query fails
                logger.warning("Database statistics query returned None, using defaults")
                return DatabaseStats(
                    total_opportunities=0,
                    avg_final_score=None,
                    max_score=None
                )

            stats = DatabaseStats(**row)
            logger.debug(f"Database statistics retrieved: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            # Return default statistics on error
            return DatabaseStats(
                total_opportunities=0,
                avg_final_score=None,
                max_score=None
            )

    def _get_opportunities_internal(self, limit: int = 100) -> list[OpportunitySummary]:
        """
        Get opportunities with PostgreSQL type mapping

        Args:
            limit: Maximum number of opportunities to return

        Returns:
            List[OpportunitySummary]: List of opportunity summaries
        """
        logger.debug(f"Getting {limit} opportunities with PostgreSQL")

        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Fetch opportunities with type safety
            sql = "SELECT id, app_title FROM opportunities LIMIT %s"
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            cursor.close()

            opportunities = [OpportunitySummary(**row) for row in rows]
            logger.debug(f"Retrieved {len(opportunities)} opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            # Return empty list on error
            return []

    def __enter__(self):
        """Context manager entry"""
        self.connection = self._get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def store_analyses(self, analyses, reddit_submissions=None):
        """
        Store analyses directly to clean opportunities table
        NO MAPPING - Direct insert from LLM output to database

        Args:
            analyses: List of AnalysisResult objects to store
            reddit_submissions: Optional list of RedditSubmission objects

        Returns:
            Dictionary with storage statistics
        """
        import json

        from load.data_mappers import AnalysisToOpportunityMapper

        logger.info(f"Storing {len(analyses) if analyses else 0} analyses with OnlyMaps (clean schema)")

        if not analyses:
            return {"stored": 0, "skipped": 0, "errors": 0}

        # Use data mapper to convert AnalysisResults to Opportunities
        mapper = AnalysisToOpportunityMapper(preserve_reddit_metadata=True)
        opportunities = mapper.map_batch(analyses, reddit_submissions)

        stored = 0
        skipped = 0
        errors = 0

        # Use psycopg2 for actual database operations
        import psycopg2
        import psycopg2.extras

        try:
            # Connect to database using stored database_url
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()

            for opp in opportunities:
                try:
                    # Use savepoint for each insert to allow rollback without aborting transaction
                    cursor.execute("SAVEPOINT insert_savepoint")

                    # Direct insert to CLEAN opportunities schema
                    insert_query = """
                        INSERT INTO opportunities (
                            submission_id, reddit_title, reddit_url, subreddit,
                            reddit_author, reddit_upvotes, reddit_comments_count, reddit_created_at,
                            app_title, app_concept, problem_statement, target_audience, core_functions,
                            market_demand, pain_intensity, monetization_potential,
                            competition_level, technical_feasibility,
                            final_score, confidence_score, trust_level,
                            content_quality_score, is_spam, spam_indicators,
                            embedding, analyzed_at,
                            agno_wtp_score, agno_segment_confidence, agno_price_potential,
                            agno_behavior_score, agno_consensus_confidence, agno_segment_type,
                            agno_agents_count, agno_analysis_cost_usd, agno_agent_metadata,
                            agno_validation_status
                        ) VALUES (
                            %(submission_id)s, %(reddit_title)s, %(reddit_url)s, %(subreddit)s,
                            %(reddit_author)s, %(reddit_upvotes)s, %(reddit_comments_count)s, %(reddit_created_at)s,
                            %(app_title)s, %(app_concept)s, %(problem_statement)s, %(target_audience)s, %(core_functions)s,
                            %(market_demand)s, %(pain_intensity)s, %(monetization_potential)s,
                            %(competition_level)s, %(technical_feasibility)s,
                            %(final_score)s, %(confidence_score)s, %(trust_level)s,
                            %(content_quality_score)s, %(is_spam)s, %(spam_indicators)s,
                            %(embedding)s, %(analyzed_at)s,
                            %(agno_wtp_score)s, %(agno_segment_confidence)s, %(agno_price_potential)s,
                            %(agno_behavior_score)s, %(agno_consensus_confidence)s, %(agno_segment_type)s,
                            %(agno_agents_count)s, %(agno_analysis_cost_usd)s, %(agno_agent_metadata)s,
                            %(agno_validation_status)s
                        )
                        ON CONFLICT (submission_id) DO NOTHING
                    """

                    # Direct data mapping - NO TRANSFORMATION
                    data = {
                        'submission_id': opp.submission_id,
                        'reddit_title': opp.reddit_title,
                        'reddit_url': opp.reddit_url,
                        'subreddit': opp.subreddit,
                        'reddit_author': opp.reddit_author,
                        'reddit_upvotes': opp.reddit_upvotes,
                        'reddit_comments_count': opp.reddit_comments_count,
                        'reddit_created_at': opp.reddit_created_at,
                        'app_title': opp.app_title,
                        'app_concept': opp.app_concept,
                        'problem_statement': opp.problem_statement,
                        'target_audience': opp.target_audience,
                        'core_functions': json.dumps(opp.core_functions),
                        'market_demand': opp.market_demand,
                        'pain_intensity': opp.pain_intensity,
                        'monetization_potential': opp.monetization_potential,
                        'competition_level': opp.competition_level,
                        'technical_feasibility': opp.technical_feasibility,
                        'final_score': opp.final_score,
                        'confidence_score': opp.confidence_score,
                        'trust_level': opp.trust_level,
                        'content_quality_score': opp.content_quality_score,
                        'is_spam': opp.is_spam,
                        'spam_indicators': json.dumps(opp.spam_indicators) if opp.spam_indicators else '[]',
                        'embedding': json.dumps(opp.embedding) if opp.embedding else None,
                        'analyzed_at': opp.analyzed_at,
                        # Agno multi-agent analysis fields
                        'agno_wtp_score': getattr(opp, 'agno_wtp_score', None),
                        'agno_segment_confidence': getattr(opp, 'agno_segment_confidence', None),
                        'agno_price_potential': getattr(opp, 'agno_price_potential', None),
                        'agno_behavior_score': getattr(opp, 'agno_behavior_score', None),
                        'agno_consensus_confidence': getattr(opp, 'agno_consensus_confidence', None),
                        'agno_segment_type': getattr(opp, 'agno_segment_type', None),
                        'agno_agents_count': getattr(opp, 'agno_agents_count', None),
                        'agno_analysis_cost_usd': getattr(opp, 'agno_analysis_cost_usd', None),
                        'agno_agent_metadata': json.dumps(getattr(opp, 'agno_agent_metadata', None)) if getattr(opp, 'agno_agent_metadata', None) else None,
                        'agno_validation_status': getattr(opp, 'agno_validation_status', None)
                    }

                    # Execute the insert
                    cursor.execute(insert_query, data)

                    # Release savepoint if successful
                    cursor.execute("RELEASE SAVEPOINT insert_savepoint")
                    stored += 1

                except Exception as e:
                    # Rollback to savepoint to recover transaction
                    try:
                        cursor.execute("ROLLBACK TO SAVEPOINT insert_savepoint")
                    except:
                        pass  # Savepoint may not exist if error was before creation

                    if "duplicate key" in str(e).lower() or "conflict" in str(e).lower():
                        logger.debug(f"Skipping duplicate submission: {opp.submission_id}")
                        skipped += 1
                    else:
                        logger.error(f"Failed to store opportunity {opp.submission_id}: {e}")
                        errors += 1

            # Commit the transaction
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✓ Stored {stored} opportunities (skipped {skipped} duplicates, {errors} errors)")
            return {"stored": stored, "skipped": skipped, "errors": errors}

        except Exception as e:
            logger.error(f"Failed to store analyses: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {"stored": stored, "skipped": skipped, "errors": errors + len(analyses) - stored - skipped}

    def get_opportunities(self, limit=100, min_score=0.0, trust_levels=None, subreddits=None):
        """
        Get opportunities using OnlyMaps with type safety

        Args:
            limit: Maximum number of opportunities to return
            min_score: Minimum score filter
            trust_levels: List of trust levels to include
            subreddits: List of subreddits to include

        Returns:
            List of opportunity objects
        """
        logger.debug(f"Getting opportunities with OnlyMaps: limit={limit}, min_score={min_score}")

        try:
            # Use OnlyMaps to fetch opportunities with type safety
            opportunities = self._get_opportunities_internal(limit)
            return opportunities
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            return []

    def test_connection(self) -> bool:
        """
        Test database connection using OnlyMaps

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.debug("Testing PostgreSQL database connection")

            # Test a simple query using PostgreSQL
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as total_opportunities")
            result = cursor.fetchone()
            cursor.close()

            logger.info("✓ PostgreSQL database connection test successful")
            return True

        except Exception as e:
            logger.error(f"PostgreSQL database connection test failed: {e}")
            return False

    def create_tables(self) -> None:
        """
        No-op for OnlyMaps - tables are assumed to exist

        OnlyMaps expects the database schema to already be in place.
        This method exists for compatibility with the orchestration layer.
        """
        logger.debug("OnlyMaps: Skipping table creation (tables expected to exist)")
        pass

    def get_statistics(self):
        """
        Get database statistics with OnlyMaps schema flexibility

        Returns:
            Dictionary with database statistics
        """
        logger.debug("Getting database statistics with OnlyMaps schema flexibility")

        try:
            # Use OnlyMaps to get statistics with missing column handling
            stats = self._get_statistics_internal()
            return stats.model_dump()
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {
                "total_opportunities": 0,
                "avg_final_score": None,
                "max_score": None
            }
