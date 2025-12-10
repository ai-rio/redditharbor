"""
SQLModel Loader for RedditHarbor Pipeline V4
SQLModel-based database loader for Opportunity records

Provides the same interface as PostgresLoader while using SQLModel
ORM for type safety and maintainability.
"""

import logging
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any

from sqlmodel import Session, select
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError
)

from models.analysis import Opportunity
from database import get_db_session, get_engine, get_session
from config.settings import get_settings
from load.loader_factory import BaseLoader

logger = logging.getLogger(__name__)


class SQLModelLoader(BaseLoader):
    """
    SQLModel-based database loader for Opportunity records.

    Provides the same interface as PostgresLoader while using SQLModel
    ORM for type safety and maintainability.
    """

    def __init__(self, settings=None):
        """Initialize the loader with database session management."""
        self.settings = settings or get_settings()
        self.engine = get_engine()
        # Create session factory for tests that expect it
        from sqlalchemy.orm import sessionmaker
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)
        # Add logger attribute for tests
        self.logger = logger
        logger.info("✓ SQLModel Loader initialized")

    def _get_session(self):
        """Get a new database session. Added for test compatibility."""
        return next(get_session())

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

        # Validate trust_level (Opportunity model already does this in __init__)
        # But we need to check again in case of direct instantiation
        valid_levels = ['LOW', 'MEDIUM', 'HIGH']
        if opportunity.trust_level not in valid_levels:
            raise ValueError(f"Trust level must be one of {valid_levels}")

        # Validate nested analysis structure (if present)
        if opportunity.analysis and not isinstance(opportunity.analysis, dict):
            raise ValueError("analysis field must be a dictionary")

        # Check for required app_idea structure (if analysis is present)
        if opportunity.analysis and "app_idea" in opportunity.analysis:
            app_idea = opportunity.analysis["app_idea"]
            if not isinstance(app_idea, dict):
                raise ValueError("analysis['app_idea'] must be a dictionary")

        # Validate metrics structure (if present)
        if opportunity.metrics and not isinstance(opportunity.metrics, dict):
            raise ValueError("metrics field must be a dictionary")

    def _handle_database_error(self, error: SQLAlchemyError, operation: str, submission_id: str = None) -> None:
        """Centralized error handling with specific error types."""

        context = f" in {operation}"
        if submission_id:
            context += f" for {submission_id}"

        if isinstance(error, IntegrityError):
            if "unique" in str(error).lower():
                logger.warning(f"Integrity error{context}: {error}")
            else:
                logger.error(f"Integrity constraint violation{context}: {error}")

        elif isinstance(error, OperationalError):
            if "connection" in str(error).lower():
                logger.error(f"Database connection error{context}: {error}")
            elif "pool" in str(error).lower():
                logger.error(f"Connection pool error{context}: {error}")
            else:
                logger.error(f"Database operation error{context}: {error}")

        else:
            logger.error(f"Unexpected database error{context}: {type(error).__name__}: {error}")

    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Save an opportunity to the database.

        Args:
            opportunity: Opportunity instance to save

        Returns:
            bool: True if saved, False if duplicate skipped

        Raises:
            ValueError: If opportunity is invalid
            RuntimeError: If database operation fails
        """
        # Validate the opportunity
        self._validate_opportunity(opportunity)

        # Set timestamps if not already set
        if not opportunity.created_at:
            opportunity.created_at = datetime.now(UTC)
        opportunity.updated_at = datetime.now(UTC)

        try:
            with get_db_session() as session:
                # Check for duplicate
                self.logger.debug(f"Checking for duplicate: {opportunity.submission_id}")
                existing = session.exec(
                    select(Opportunity)
                    .where(Opportunity.submission_id == opportunity.submission_id)
                ).first()

                if existing:
                    self.logger.warning(f"⊘ Skipped duplicate {opportunity.submission_id}")
                    return False

                # Save new record
                session.add(opportunity)
                session.flush()  # Get ID without committing

                # Detach object from session so we can access it after
                session.expunge(opportunity)

                self.logger.info(f"✓ Saved opportunity {opportunity.submission_id} (ID: {opportunity.id})")
                return True

        except IntegrityError as e:
            # Re-raise IntegrityError for tests
            self._handle_database_error(e, "save_opportunity", opportunity.submission_id)
            raise
        except SQLAlchemyError as e:
            self._handle_database_error(e, "save_opportunity", opportunity.submission_id)
            raise RuntimeError(f"Failed to save opportunity {opportunity.submission_id}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error saving opportunity {opportunity.submission_id}: {e}")
            raise

    def save_opportunities(self, opportunities: List[Opportunity]) -> int:
        """
        Save multiple opportunities in a single transaction.

        Args:
            opportunities: List of opportunities to save

        Returns:
            int: Number of records actually saved (excludes duplicates)

        Raises:
            RuntimeError: If database operation fails
        """
        if not opportunities:
            return 0

        saved_count = 0
        submission_ids = [opp.submission_id for opp in opportunities]

        try:
            with get_db_session() as session:
                # Check all submission_ids at once
                existing = session.exec(
                    select(Opportunity)
                    .where(Opportunity.submission_id.in_(submission_ids))
                ).all()

                existing_ids = {opp.submission_id for opp in existing}

                # Filter out duplicates
                new_opportunities = [
                    opp for opp in opportunities
                    if opp.submission_id not in existing_ids
                ]

                if new_opportunities:
                    # Set timestamps for new opportunities
                    for opp in new_opportunities:
                        if not opp.created_at:
                            opp.created_at = datetime.now(UTC)
                        opp.updated_at = datetime.now(UTC)

                    session.add_all(new_opportunities)
                    session.flush()  # Get IDs

                    # Detach all opportunities so we can access them after session closes
                    for opp in new_opportunities:
                        session.expunge(opp)
                        logger.debug(f"Saved opportunity {opp.submission_id} (ID: {opp.id})")

                    saved_count = len(new_opportunities)
                    logger.info(f"✓ Batch saved {saved_count}/{len(opportunities)} opportunities")
                else:
                    logger.info("All opportunities were duplicates, none saved")

                return saved_count

        except SQLAlchemyError as e:
            self._handle_database_error(e, "save_opportunities")
            raise RuntimeError(f"Failed to save opportunities: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in batch save: {e}")
            raise

    def get_opportunity(self, submission_id: str) -> Optional[Opportunity]:
        """
        Retrieve an opportunity by submission_id.

        Args:
            submission_id: Reddit submission ID

        Returns:
            Optional[Opportunity]: Found record or None
        """
        try:
            with get_db_session() as session:
                opportunity = session.exec(
                    select(Opportunity)
                    .where(Opportunity.submission_id == submission_id)
                ).first()

                # Detach from session so it can be used outside
                if opportunity:
                    session.expunge(opportunity)

                return opportunity

        except SQLAlchemyError as e:
            self._handle_database_error(e, "get_opportunity", submission_id)
            raise RuntimeError(f"Failed to retrieve opportunity {submission_id}: {e}")

    def get_opportunities_by_subreddit(self, subreddit: str) -> List[Opportunity]:
        """
        Get all opportunities for a specific subreddit.

        Args:
            subreddit: Subreddit name

        Returns:
            List[Opportunity]: List of opportunities
        """
        try:
            with get_db_session() as session:
                opportunities = session.exec(
                    select(Opportunity)
                    .where(Opportunity.subreddit == subreddit)
                    .order_by(Opportunity.created_at.desc())
                ).all()

                # Detach all opportunities from session
                for opp in opportunities:
                    session.expunge(opp)

                return list(opportunities)

        except SQLAlchemyError as e:
            self._handle_database_error(e, "get_opportunities_by_subreddit", subreddit)
            raise RuntimeError(f"Failed to retrieve opportunities for {subreddit}: {e}")

    def update_opportunity(self, submission_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an opportunity with new values.

        Args:
            submission_id: Reddit submission ID
            updates: Dictionary of fields to update

        Returns:
            bool: True if updated, False if not found
        """
        try:
            with get_db_session() as session:
                opportunity = session.exec(
                    select(Opportunity)
                    .where(Opportunity.submission_id == submission_id)
                ).first()

                if not opportunity:
                    return False

                # Update fields
                for key, value in updates.items():
                    if hasattr(opportunity, key):
                        setattr(opportunity, key, value)

                opportunity.updated_at = datetime.now(UTC)

                logger.info(f"✓ Updated opportunity {submission_id}")
                return True

        except SQLAlchemyError as e:
            self._handle_database_error(e, "update_opportunity", submission_id)
            raise RuntimeError(f"Failed to update opportunity {submission_id}: {e}")

    def delete_opportunity(self, submission_id: str) -> bool:
        """
        Delete an opportunity by submission_id.

        Args:
            submission_id: Reddit submission ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            with get_db_session() as session:
                opportunity = session.exec(
                    select(Opportunity)
                    .where(Opportunity.submission_id == submission_id)
                ).first()

                if not opportunity:
                    return False

                session.delete(opportunity)
                logger.info(f"✓ Deleted opportunity {submission_id}")
                return True

        except SQLAlchemyError as e:
            self._handle_database_error(e, "delete_opportunity", submission_id)
            raise RuntimeError(f"Failed to delete opportunity {submission_id}: {e}")

    def get_opportunities_by_score_range(
        self, min_score: float = 0.0, max_score: float = 100.0, limit: int = 100
    ) -> List[Opportunity]:
        """
        Get opportunities within a score range.

        Args:
            min_score: Minimum final score
            max_score: Maximum final score
            limit: Maximum number of results

        Returns:
            List[Opportunity]: List of opportunities
        """
        try:
            with get_db_session() as session:
                opportunities = session.exec(
                    select(Opportunity)
                    .where(Opportunity.final_score >= min_score)
                    .where(Opportunity.final_score <= max_score)
                    .order_by(Opportunity.final_score.desc())
                    .limit(limit)
                ).all()

                # Detach all opportunities from session
                for opp in opportunities:
                    session.expunge(opp)

                return list(opportunities)

        except SQLAlchemyError as e:
            self._handle_database_error(e, "get_opportunities_by_score_range")
            raise RuntimeError(f"Failed to retrieve opportunities by score range: {e}")

    def count_opportunities(self) -> int:
        """
        Get total count of opportunities.

        Returns:
            int: Total number of opportunities
        """
        try:
            with get_db_session() as session:
                from sqlmodel import func
                count = session.exec(select(func.count(Opportunity.id))).scalar()
                return count or 0

        except SQLAlchemyError as e:
            self._handle_database_error(e, "count_opportunities")
            raise RuntimeError(f"Failed to count opportunities: {e}")

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
        """Close any resources (placeholder for consistency)."""
        # No resources to clean up - sessions are managed by context managers
        logger.info("SQLModel Loader closed")