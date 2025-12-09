"""
Direct PostgreSQL loader using psycopg2
No ORM, no abstraction layers
"""

import logging
from typing import Any
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import Json
from models.analysis import AnalysisResult
from config.settings import get_settings

logger = logging.getLogger(__name__)


class PostgresLoader:
    """
    Direct PostgreSQL loader with connection pooling
    """

    def __init__(self, settings=None):
        """Initialize with connection pool"""
        self.settings = settings or get_settings()

        # Create connection pool
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=self.settings.database_url
        )

        logger.info("✓ PostgreSQL connection pool initialized")

    def save_analysis(self, analysis: AnalysisResult) -> bool:
        """
        Save analysis result to opportunities table

        Args:
            analysis: Analysis result to save

        Returns:
            True if saved, False if duplicate skipped

        Raises:
            RuntimeError: If database operation fails
        """
        conn = None
        try:
            conn = self.pool.getconn()

            with conn.cursor() as cur:
                # Insert or skip on conflict
                cur.execute(
                    """
                    INSERT INTO opportunities (
                        submission_id,
                        subreddit,
                        title,
                        wtp_score,
                        final_score,
                        confidence_score,
                        core_functions,
                        pricing_strategy,
                        target_segment,
                        pain_points,
                        trust_level
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (submission_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        analysis.submission_id,
                        analysis.subreddit,
                        analysis.title,
                        analysis.wtp_score,
                        analysis.final_score,
                        analysis.confidence_score,
                        Json(analysis.core_functions),
                        Json(analysis.pricing_strategy),
                        analysis.target_segment,
                        Json(analysis.pain_points),
                        analysis.trust_level
                    )
                )

                result = cur.fetchone()
                conn.commit()

                if result:
                    logger.info(f"✓ Saved analysis for {analysis.submission_id}")
                    return True
                else:
                    logger.info(f"⊘ Skipped duplicate {analysis.submission_id}")
                    return False

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save analysis: {e}")
            raise RuntimeError(f"Database save failed: {e}")
        finally:
            if conn:
                self.pool.putconn(conn)

    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connections closed")