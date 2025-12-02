"""
Database loading module with repository pattern and clean separation of concerns
"""

import logging
from typing import List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from config import get_settings
from models import AnalysisResult, Opportunity, RedditSubmission
from .repositories import SQLAlchemyOpportunityRepository
from .data_mappers import AnalysisToOpportunityMapper

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """
    Database loader with repository pattern and dependency injection
    Clean separation between storage, data mapping, and business logic
    """

    def __init__(
        self,
        repository: Optional[SQLAlchemyOpportunityRepository] = None,
        data_mapper: Optional[AnalysisToOpportunityMapper] = None,
        settings=None
    ):
        """
        Initialize database loader with dependency injection

        Args:
            repository: Opportunity repository (will create default if None)
            data_mapper: Data mapper for AnalysisResult to Opportunity conversion
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self._engine = None
        self._session_factory = None

        # Repository will be created after session_factory is initialized
        self._repository = repository

        # Initialize data mapper with default configuration
        self.data_mapper = data_mapper or AnalysisToOpportunityMapper(
            preserve_reddit_metadata=True
        )

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

            # Update repository if it was created earlier
            if hasattr(self, 'repository') and isinstance(self.repository, SQLAlchemyOpportunityRepository):
                self.repository.session_factory = self._session_factory

        return self._session_factory

    @property
    def repository(self):
        """Lazy initialization of repository"""
        if not hasattr(self, '_initialized_repository') or self._initialized_repository is None:
            if self._repository is not None:
                self._initialized_repository = self._repository
            else:
                self._initialized_repository = SQLAlchemyOpportunityRepository(self.session_factory)
        return self._initialized_repository

    def create_tables(self) -> None:
        """
        Create database tables and indexes
        """
        logger.info("Creating database tables and indexes")

        try:
            # Enable pgvector extension if available
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                logger.debug("✓ pgvector extension enabled")
            except Exception as e:
                logger.debug(f"pgvector extension not available: {e}")

            # Create tables
            Opportunity.metadata.create_all(self.engine)
            logger.info("✓ Database tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise RuntimeError(f"Table creation failed: {e}")

    def store_analyses(
        self,
        analyses: List[AnalysisResult],
        reddit_submissions: Optional[List[RedditSubmission]] = None
    ) -> dict:
        """
        Store multiple analysis results using repository pattern

        Args:
            analyses: List of AnalysisResult objects to store
            reddit_submissions: Optional list of RedditSubmission objects with original metadata

        Returns:
            Dictionary with storage statistics

        Raises:
            RuntimeError: If database operation fails
        """
        logger.info(f"Storing {len(analyses)} analyses to database")

        if not analyses:
            logger.warning("No analyses to store")
            return {"stored": 0, "skipped": 0, "errors": 0}

        try:
            # Use data mapper to convert AnalysisResults to Opportunities
            opportunities = self.data_mapper.map_batch(analyses, reddit_submissions)

            # Use repository to store opportunities
            stats = self.repository.save_batch(opportunities)

            logger.info(f"✓ Stored {stats['stored']} analyses to database")
            return stats

        except Exception as e:
            logger.error(f"Failed to store analyses: {e}")
            raise RuntimeError(f"Database storage failed: {e}")

    def get_opportunities(
        self,
        limit: int = 100,
        min_score: float = 0.0,
        trust_levels: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None
    ) -> List[Opportunity]:
        """
        Retrieve opportunities with filtering using repository

        Args:
            limit: Maximum number of opportunities to return
            min_score: Minimum final score filter
            trust_levels: List of trust levels to include
            subreddits: List of subreddits to include

        Returns:
            List of Opportunity objects
        """
        return self.repository.find_all(limit, min_score, trust_levels, subreddits)

    def find_similar_opportunities(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> List[Opportunity]:
        """
        Find opportunities similar to the given embedding using repository

        Args:
            embedding: Query embedding vector
            similarity_threshold: Minimum similarity score (0-1)
            limit: Maximum number of results

        Returns:
            List of similar opportunities
        """
        return self.repository.find_similar(embedding, similarity_threshold, limit)

    def get_statistics(self) -> dict:
        """
        Get database statistics using repository

        Returns:
            Dictionary with database statistics
        """
        return self.repository.get_statistics()

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