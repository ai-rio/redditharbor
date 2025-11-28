"""
Database loading module with transaction safety and pgvector support
"""

import logging
from datetime import datetime
from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    create_engine, Column, DateTime, Float, Index, Integer, JSON,
    String, Text, func, text
)
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import expression

from config import get_settings
from models import AnalysisResult, Opportunity, OpportunityCreate

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Database loader with transaction safety and pgvector support
    """

    def __init__(self):
        """Initialize database loader with settings"""
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None

    @property
    def engine(self):
        """Lazy initialization of database engine"""
        if self._engine is None:
            try:
                self._engine = create_engine(
                    self.settings.database_url,
                    echo=False,  # Set to True for SQL debugging
                    pool_pre_ping=True,  # Test connections for liveness
                    pool_recycle=3600,  # Recycle connections after 1 hour
                )
                logger.info(f"✓ Database engine initialized: {self.settings.database_url}")

            except Exception as e:
                logger.error(f"Failed to initialize database engine: {e}")
                raise RuntimeError(f"Database initialization failed: {e}")

        return self._engine

    @property
    def session_factory(self):
        """Lazy initialization of session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def create_tables(self) -> None:
        """
        Create database tables and indexes
        """
        logger.info("Creating database tables and indexes")

        try:
            # Enable pgvector extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()

            # Create tables
            Opportunity.metadata.create_all(self.engine)
            logger.info("✓ Database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise RuntimeError(f"Table creation failed: {e}")

    def store_analyses(self, analyses: List[AnalysisResult]) -> dict:
        """
        Store multiple analysis results with transaction safety

        Args:
            analyses: List of AnalysisResult objects to store

        Returns:
            Dictionary with storage statistics

        Raises:
            RuntimeError: If database operation fails
        """
        logger.info(f"Storing {len(analyses)} analyses to database")

        if not analyses:
            logger.warning("No analyses to store")
            return {"stored": 0, "skipped": 0, "errors": 0}

        stats = {"stored": 0, "skipped": 0, "errors": 0}

        with self.session_factory() as session:
            try:
                # Begin transaction
                session.begin()

                for analysis in analyses:
                    try:
                        # Check for existing submission
                        existing = session.query(Opportunity).filter_by(
                            submission_id=analysis.submission_id
                        ).first()

                        if existing:
                            logger.debug(f"Skipping duplicate submission: {analysis.submission_id}")
                            stats["skipped"] += 1
                            continue

                        # Create opportunity record
                        opportunity = self._convert_to_opportunity(analysis)
                        session.add(opportunity)
                        stats["stored"] += 1

                    except Exception as e:
                        logger.error(f"Failed to store analysis {analysis.submission_id}: {e}")
                        stats["errors"] += 1
                        continue

                # Commit transaction
                session.commit()
                logger.info(f"✓ Stored {stats['stored']} analyses to database")

            except SQLAlchemyError as e:
                # Rollback on any database error
                session.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise RuntimeError(f"Database storage failed: {e}")

            except Exception as e:
                session.rollback()
                logger.error(f"Unexpected error during storage: {e}")
                raise RuntimeError(f"Storage failed: {e}")

        return stats

    def _convert_to_opportunity(self, analysis: AnalysisResult) -> Opportunity:
        """
        Convert AnalysisResult to Opportunity database model

        Args:
            analysis: AnalysisResult to convert

        Returns:
            Opportunity database model
        """
        # Extract Reddit data from analysis (would need to be passed separately in real implementation)
        # For now, using placeholder data - in production, this would come from the original Reddit submission

        return Opportunity(
            # Source Reddit data (placeholder - would get from original submission)
            submission_id=analysis.submission_id,
            reddit_title="Reddit Submission",  # Would get from original submission
            reddit_url=f"https://reddit.com/r/test/{analysis.submission_id}",
            subreddit="test",  # Would get from original submission
            reddit_author=None,  # Would get from original submission
            reddit_upvotes=0,  # Would get from original submission
            reddit_comments_count=0,  # Would get from original submission
            reddit_created_at=datetime.utcnow(),  # Would get from original submission

            # App idea analysis
            app_title=analysis.app_idea.title,
            app_concept=analysis.app_idea.app_concept,
            problem_statement=analysis.app_idea.problem_statement,
            target_audience=analysis.app_idea.target_audience,
            core_functions=analysis.app_idea.core_functions,

            # Market metrics
            market_demand=analysis.market_metrics.market_demand,
            pain_intensity=analysis.market_metrics.pain_intensity,
            monetization_potential=analysis.market_metrics.monetization_potential,
            competition_level=analysis.market_metrics.competition_level,
            technical_feasibility=analysis.market_metrics.technical_feasibility,

            # Overall scoring
            final_score=analysis.final_score,
            confidence_score=analysis.confidence_score,
            trust_level=analysis.trust_level,

            # Semantic search
            embedding=analysis.embedding,

            # Metadata
            analyzed_at=analysis.analyzed_at,
        )

    def get_opportunities(
        self,
        limit: int = 100,
        min_score: float = 0.0,
        trust_levels: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None
    ) -> List[Opportunity]:
        """
        Retrieve opportunities with filtering

        Args:
            limit: Maximum number of opportunities to return
            min_score: Minimum final score filter
            trust_levels: List of trust levels to include
            subreddits: List of subreddits to include

        Returns:
            List of Opportunity objects
        """
        logger.info(f"Retrieving opportunities (limit={limit}, min_score={min_score})")

        try:
            with self.session_factory() as session:
                query = session.query(Opportunity)

                # Apply filters
                if min_score > 0:
                    query = query.filter(Opportunity.final_score >= min_score)

                if trust_levels:
                    query = query.filter(Opportunity.trust_level.in_(trust_levels))

                if subreddits:
                    query = query.filter(Opportunity.subreddit.in_(subreddits))

                # Order by score and limit
                opportunities = query.order_by(Opportunity.final_score.desc()).limit(limit).all()

                logger.info(f"✓ Retrieved {len(opportunities)} opportunities")
                return opportunities

        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve opportunities: {e}")
            raise RuntimeError(f"Database query failed: {e}")

    def find_similar_opportunities(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> List[Opportunity]:
        """
        Find opportunities similar to the given embedding using pgvector

        Args:
            embedding: Query embedding vector
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum number of results

        Returns:
            List of similar opportunities
        """
        logger.info(f"Finding similar opportunities (threshold={similarity_threshold}, limit={limit})")

        try:
            with self.session_factory() as session:
                # Use pgvector cosine similarity
                query = session.query(Opportunity).filter(
                    Opportunity.embedding.isnot(None)
                ).order_by(
                    Opportunity.embedding.cosine_distance(embedding)
                ).limit(limit)

                # Filter by similarity threshold
                similar_opportunities = []
                for opp in query:
                    # Calculate similarity manually for threshold filtering
                    similarity = 1 - opp.embedding.cosine_distance(embedding)
                    if similarity >= similarity_threshold:
                        similar_opportunities.append(opp)

                logger.info(f"✓ Found {len(similar_opportunities)} similar opportunities")
                return similar_opportunities

        except SQLAlchemyError as e:
            logger.error(f"Failed to find similar opportunities: {e}")
            raise RuntimeError(f"Similarity search failed: {e}")

    def get_statistics(self) -> dict:
        """
        Get database statistics and summary metrics

        Returns:
            Dictionary with database statistics
        """
        try:
            with self.session_factory() as session:
                # Total opportunities
                total_count = session.query(func.count(Opportunity.id)).scalar()

                # Score distribution
                avg_score = session.query(func.avg(Opportunity.final_score)).scalar() or 0
                high_score_count = session.query(func.count(Opportunity.id)).filter(
                    Opportunity.final_score >= 70
                ).scalar()

                # Trust level distribution
                trust_distribution = {}
                for trust_level in ['HIGH', 'MEDIUM', 'LOW']:
                    count = session.query(func.count(Opportunity.id)).filter(
                        Opportunity.trust_level == trust_level
                    ).scalar()
                    trust_distribution[trust_level] = count

                # Subreddit distribution
                subreddit_count = session.query(func.count(func.distinct(Opportunity.subreddit))).scalar()

                # Recent activity
                recent_count = session.query(func.count(Opportunity.id)).filter(
                    Opportunity.analyzed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                ).scalar()

                return {
                    "total_opportunities": total_count,
                    "average_score": float(avg_score),
                    "high_score_count": high_score_count,
                    "high_score_percentage": (high_score_count / total_count * 100) if total_count > 0 else 0,
                    "trust_distribution": trust_distribution,
                    "unique_subreddits": subreddit_count,
                    "recent_opportunities": recent_count,
                }

        except SQLAlchemyError as e:
            logger.error(f"Failed to get database statistics: {e}")
            raise RuntimeError(f"Statistics query failed: {e}")

    def test_connection(self) -> bool:
        """
        Test database connection and basic operations

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test basic query
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()

            if test_value == 1:
                logger.info("✓ Database connection test successful")
                return True
            else:
                logger.error(f"Database connection test failed: unexpected result {test_value}")
                return False

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False