"""
Repository pattern implementation for database operations with clean separation of concerns
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models import AnalysisResult, Opportunity

logger = logging.getLogger(__name__)


class OpportunityRepository(ABC):
    """Abstract repository for Opportunity data operations"""

    @abstractmethod
    def save(self, opportunity: Opportunity) -> bool:
        """Save a single opportunity"""
        pass

    @abstractmethod
    def save_batch(self, opportunities: List[Opportunity]) -> Dict[str, int]:
        """Save multiple opportunities and return statistics"""
        pass

    @abstractmethod
    def find_by_submission_id(self, submission_id: str) -> Optional[Opportunity]:
        """Find opportunity by submission ID"""
        pass

    @abstractmethod
    def find_all(
        self,
        limit: int = 100,
        min_score: float = 0.0,
        trust_levels: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None
    ) -> List[Opportunity]:
        """Find opportunities with filtering"""
        pass

    @abstractmethod
    def find_similar(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> List[Opportunity]:
        """Find opportunities similar to given embedding"""
        pass

    @abstractmethod
    def count_by_filters(self, filters: Dict[str, Any]) -> int:
        """Count opportunities by filters"""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass


class SQLAlchemyOpportunityRepository(OpportunityRepository):
    """SQLAlchemy implementation of Opportunity repository"""

    def __init__(self, session_factory):
        """
        Initialize repository with session factory

        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory

    def save(self, opportunity: Opportunity) -> bool:
        """
        Save a single opportunity

        Args:
            opportunity: Opportunity to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.session_factory() as session:
                # Check for existing submission
                existing = session.query(Opportunity).filter_by(
                    submission_id=opportunity.submission_id
                ).first()

                if existing:
                    logger.debug(f"Skipping duplicate submission: {opportunity.submission_id}")
                    return False

                session.add(opportunity)
                session.commit()
                logger.debug(f"Saved opportunity: {opportunity.submission_id}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to save opportunity {opportunity.submission_id}: {e}")
            session.rollback()
            return False

    def save_batch(self, opportunities: List[Opportunity]) -> Dict[str, int]:
        """
        Save multiple opportunities in a transaction

        Args:
            opportunities: List of opportunities to save

        Returns:
            Dictionary with storage statistics
        """
        stats = {"stored": 0, "skipped": 0, "errors": 0}

        if not opportunities:
            logger.warning("No opportunities to save")
            return stats

        with self.session_factory() as session:
            try:
                session.begin()

                for opportunity in opportunities:
                    try:
                        # Check for existing submission
                        existing = session.query(Opportunity).filter_by(
                            submission_id=opportunity.submission_id
                        ).first()

                        if existing:
                            logger.debug(f"Skipping duplicate submission: {opportunity.submission_id}")
                            stats["skipped"] += 1
                            continue

                        session.add(opportunity)
                        stats["stored"] += 1

                    except Exception as e:
                        logger.error(f"Failed to save opportunity {opportunity.submission_id}: {e}")
                        stats["errors"] += 1
                        continue

                session.commit()
                logger.info(f"✓ Saved {stats['stored']} opportunities to database")

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Database transaction failed: {e}")
                stats["errors"] += len(opportunities) - stats["stored"] - stats["skipped"]
                raise RuntimeError(f"Batch save failed: {e}")

        return stats

    def find_by_submission_id(self, submission_id: str) -> Optional[Opportunity]:
        """
        Find opportunity by submission ID

        Args:
            submission_id: Submission ID to search for

        Returns:
            Opportunity if found, None otherwise
        """
        try:
            with self.session_factory() as session:
                opportunity = session.query(Opportunity).filter_by(
                    submission_id=submission_id
                ).first()
                return opportunity

        except SQLAlchemyError as e:
            logger.error(f"Failed to find opportunity by submission ID {submission_id}: {e}")
            return None

    def find_all(
        self,
        limit: int = 100,
        min_score: float = 0.0,
        trust_levels: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None
    ) -> List[Opportunity]:
        """
        Find opportunities with filtering

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

    def find_similar(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> List[Opportunity]:
        """
        Find opportunities similar to the given embedding using cosine similarity

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
                # Get all opportunities with embeddings
                all_opportunities = session.query(Opportunity).filter(
                    Opportunity.embedding.isnot(None)
                ).all()

                similar_opportunities = []

                for opportunity in all_opportunities:
                    if opportunity.embedding:
                        # Calculate cosine similarity
                        similarity = self._calculate_cosine_similarity(embedding, opportunity.embedding)

                        if similarity >= similarity_threshold:
                            similar_opportunities.append(opportunity)

                # Sort by similarity score (descending)
                similar_opportunities.sort(
                    key=lambda opp: self._calculate_cosine_similarity(embedding, opp.embedding),
                    reverse=True
                )

                # Limit results
                result = similar_opportunities[:limit]

                logger.info(f"✓ Found {len(result)} similar opportunities")
                return result

        except SQLAlchemyError as e:
            logger.error(f"Failed to find similar opportunities: {e}")
            raise RuntimeError(f"Similarity search failed: {e}")

    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            return 0.0

        try:
            import numpy as np

            # Convert to numpy arrays for efficient calculation
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)

            # Calculate cosine similarity
            dot_product = np.dot(vec1_array, vec2_array)
            magnitude1 = np.linalg.norm(vec1_array)
            magnitude2 = np.linalg.norm(vec2_array)

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return float(dot_product / (magnitude1 * magnitude2))

        except ImportError:
            # Fallback to pure Python calculation
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)

    def count_by_filters(self, filters: Dict[str, Any]) -> int:
        """
        Count opportunities by filters

        Args:
            filters: Dictionary of filter criteria

        Returns:
            Count of matching opportunities
        """
        try:
            with self.session_factory() as session:
                query = session.query(Opportunity)

                # Apply filters
                if 'min_score' in filters:
                    query = query.filter(Opportunity.final_score >= filters['min_score'])

                if 'trust_levels' in filters:
                    query = query.filter(Opportunity.trust_level.in_(filters['trust_levels']))

                if 'subreddits' in filters:
                    query = query.filter(Opportunity.subreddit.in_(filters['subreddits']))

                return query.count()

        except SQLAlchemyError as e:
            logger.error(f"Failed to count opportunities: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics and summary metrics

        Returns:
            Dictionary with database statistics
        """
        try:
            with self.session_factory() as session:
                from sqlalchemy import func

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