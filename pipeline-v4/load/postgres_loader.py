"""
Direct PostgreSQL loader using psycopg2
No ORM, no abstraction layers
"""

import logging
from typing import Any
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import Json
from models.analysis import Opportunity
from config.settings import get_settings
from load.loader_factory import BaseLoader

logger = logging.getLogger(__name__)


class PostgresLoader(BaseLoader):
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

    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Save Opportunity object to opportunities table

        Args:
            opportunity: Opportunity object to save

        Returns:
            True if saved, False if duplicate skipped

        Raises:
            RuntimeError: If database operation fails
        """
        conn = None
        try:
            conn = self.pool.getconn()

            with conn.cursor() as cur:
                # Insert or skip on conflict - using Opportunity model schema
                cur.execute(
                    """
                    INSERT INTO opportunities (
                        submission_id,
                        subreddit,
                        title,
                        wtp_score,
                        final_score,
                        confidence_score,
                        trust_level,
                        analysis,
                        metrics,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (submission_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        opportunity.submission_id,
                        opportunity.subreddit,
                        opportunity.title,
                        opportunity.wtp_score,
                        opportunity.final_score,
                        opportunity.confidence_score,
                        opportunity.trust_level,
                        Json(opportunity.analysis),
                        Json(opportunity.metrics),
                        opportunity.created_at,
                        opportunity.updated_at
                    )
                )

                result = cur.fetchone()
                conn.commit()

                if result:
                    logger.info(f"✓ Saved opportunity for {opportunity.submission_id}")
                    return True
                else:
                    logger.info(f"⊘ Skipped duplicate {opportunity.submission_id}")
                    return False

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save opportunity: {e}")
            raise RuntimeError(f"Database save failed: {e}")
        finally:
            if conn:
                self.pool.putconn(conn)

    def save_analysis(self, analysis) -> bool:
        """
        Convert AnalysisResult to Opportunity and save it

        Args:
            analysis: AnalysisResult object to convert and save

        Returns:
            True if saved, False if duplicate skipped
        """
        # Convert AnalysisResult to Opportunity
        opportunity = Opportunity(
            submission_id=analysis.submission_id,
            subreddit=analysis.subreddit,
            title=analysis.title,
            wtp_score=analysis.wtp_score,
            final_score=analysis.final_score,
            confidence_score=analysis.confidence_score,
            trust_level=analysis.trust_level,
            analysis={
                "app_idea": analysis.app_idea.model_dump(),
                "pain_points": analysis.pain_points,
                "opportunity_summary": analysis.opportunity_summary,
                "content_quality_score": analysis.content_quality_score,
                "is_spam": analysis.is_spam,
                "spam_indicators": analysis.spam_indicators,
                "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None
            },
            metrics=analysis.metrics.model_dump()
        )

        # Use the existing save_opportunity method
        return self.save_opportunity(opportunity)

    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connections closed")