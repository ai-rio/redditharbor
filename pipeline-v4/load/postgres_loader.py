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
                        reddit_title,
                        reddit_url,
                        reddit_author,
                        reddit_upvotes,
                        reddit_comments_count,
                        reddit_created_at,
                        app_title,
                        app_concept,
                        problem_statement,
                        target_audience,
                        core_functions,
                        market_demand,
                        pain_intensity,
                        monetization_potential,
                        competition_level,
                        technical_feasibility,
                        final_score,
                        confidence_score,
                        trust_level,
                        content_quality_score,
                        is_spam,
                        spam_indicators,
                        pain_points,
                        pricing_strategy,
                        wtp_score
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (submission_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        analysis.submission_id,
                        analysis.subreddit,
                        analysis.title,  # reddit_title
                        f"https://reddit.com/r/{analysis.subreddit}/comments/{analysis.submission_id.split('_')[1] if '_' in analysis.submission_id else analysis.submission_id}",  # reddit_url
                        "anonymous",  # reddit_author (PII protection)
                        0,  # reddit_upvotes
                        0,  # reddit_comments_count
                        analysis.analyzed_at,  # reddit_created_at
                        analysis.app_idea.title,  # app_title
                        analysis.app_idea.app_concept,  # app_concept
                        analysis.app_idea.problem_statement,  # problem_statement
                        analysis.app_idea.target_audience,  # target_audience
                        Json(analysis.app_idea.core_functions),  # core_functions
                        analysis.market_metrics.market_demand,  # market_demand
                        analysis.market_metrics.pain_intensity,  # pain_intensity
                        analysis.market_metrics.monetization_potential,  # monetization_potential
                        analysis.market_metrics.competition_level,  # competition_level
                        analysis.market_metrics.technical_feasibility,  # technical_feasibility
                        analysis.final_score,  # final_score
                        analysis.confidence_score,  # confidence_score
                        analysis.trust_level,  # trust_level
                        analysis.content_quality_score,  # content_quality_score
                        analysis.is_spam,  # is_spam
                        Json(analysis.spam_indicators),  # spam_indicators
                        Json([{"pain_point": "TODO"}]),  # pain_points
                        Json({"pricing_strategy": "TODO", "tier": "basic", "price": "$10/mo"}),  # pricing_strategy
                        analysis.wtp_score  # wtp_score
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