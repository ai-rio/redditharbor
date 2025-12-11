"""
Direct PostgreSQL loader using psycopg2
No ORM, no abstraction layers
"""

import logging

import psycopg2
import psycopg2.pool
from load.loader_factory import BaseLoader
from psycopg2.extras import Json

from config.settings import get_settings
from models.analysis import Opportunity

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

    def _validate_opportunity(self, opportunity: Opportunity) -> None:
        """
        Validate opportunity before saving.

        Args:
            opportunity: Opportunity instance to validate

        Raises:
            ValueError: If opportunity is invalid
        """
        # Check for empty/None submission_id
        if opportunity.submission_id is None or opportunity.submission_id.strip() == "":
            raise ValueError("submission_id cannot be empty")

        # Validate trust_level
        valid_levels = ['LOW', 'MEDIUM', 'HIGH']
        if opportunity.trust_level not in valid_levels:
            raise ValueError(f"Trust level must be one of {valid_levels}")

    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Save Opportunity object to opportunities table

        Args:
            opportunity: Opportunity object to save

        Returns:
            True if saved, False if duplicate skipped

        Raises:
            ValueError: If opportunity is invalid
            RuntimeError: If database operation fails
        """
        # Validate the opportunity
        self._validate_opportunity(opportunity)

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

    def get_opportunity(self, submission_id: str):
        """
        Retrieve an opportunity by submission_id.

        Args:
            submission_id: Reddit submission ID

        Returns:
            Optional[Opportunity]: Found record or None

        Raises:
            RuntimeError: If database operation fails
        """
        conn = None
        try:
            conn = self.pool.getconn()

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id, submission_id, subreddit, title, wtp_score,
                        final_score, confidence_score, trust_level,
                        analysis, metrics, created_at, updated_at
                    FROM opportunities
                    WHERE submission_id = %s
                    """,
                    (submission_id,)
                )

                result = cur.fetchone()

                if result:
                    # Unpack the result
                    (id, submission_id, subreddit, title, wtp_score,
                     final_score, confidence_score, trust_level,
                     analysis, metrics, created_at, updated_at) = result

                    # Create Opportunity object from database row
                    opportunity = Opportunity(
                        submission_id=submission_id,
                        subreddit=subreddit,
                        title=title,
                        wtp_score=wtp_score,
                        final_score=final_score,
                        confidence_score=confidence_score,
                        trust_level=trust_level,
                        analysis=analysis,
                        metrics=metrics
                    )
                    opportunity.id = id
                    opportunity.created_at = created_at
                    opportunity.updated_at = updated_at

                    return opportunity
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to retrieve opportunity: {e}")
            raise RuntimeError(f"Database retrieval failed: {e}")
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
