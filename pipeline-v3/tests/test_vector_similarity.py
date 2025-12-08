"""
Comprehensive tests for Vector Similarity Functionality - pgvector Integration

Tests that verify pgvector functionality for similarity-based deduplication
and semantic search in the database layer. These tests focus on:

1. pgvector storage and retrieval of embeddings
2. Similarity search functionality
3. Deduplication using vector embeddings
4. Integration with existing database models
5. Performance and accuracy of vector operations
"""


import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from load.database import DatabaseLoader
from load.repositories import SQLAlchemyOpportunityRepository
from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.database import Opportunity, OpportunityCreate
from models.reddit import RedditSubmission

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestVectorSimilarityFunctionality:
    """Comprehensive test suite for vector similarity functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing"""
        settings = Mock()
        settings.database_url = "sqlite:///:memory:"
        return settings

    @pytest.fixture
    def test_database_loader(self, mock_settings):
        """Create a test database loader with SQLite in-memory database"""
        loader = DatabaseLoader(settings=mock_settings)
        loader.create_tables()
        return loader

    @pytest.fixture
    def sample_embedding_384(self):
        """Create a sample 384-dimensional embedding for testing"""
        # Generate a deterministic 384-dimensional embedding
        base_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        return (base_values * 76 + [0.6, 0.7, 0.8, 0.9])[:384]  # 384 dimensions

    @pytest.fixture
    def sample_opportunity_data(self, sample_embedding_384):
        """Create a sample opportunity with embedding for testing"""
        return {
            "submission_id": "test_001",
            "reddit_title": "Task Management App for Remote Teams",
            "reddit_url": "https://reddit.com/r/productivity/test_001/",
            "subreddit": "productivity",
            "reddit_author": "remote_worker",
            "reddit_upvotes": 150,
            "reddit_comments_count": 45,
            "reddit_created_at": datetime.now(UTC).replace(year=2024, month=1, day=15),
            "app_title": "TeamFlow",
            "app_concept": "Collaborative task management for distributed teams",
            "problem_statement": "Remote teams struggle with task coordination and communication",
            "target_audience": "Remote team leaders and members",
            "core_functions": ["real-time task sync", "team communication", "progress tracking"],
            "market_demand": 85.0,
            "pain_intensity": 90.0,
            "monetization_potential": 78.0,
            "competition_level": 65.0,
            "technical_feasibility": 82.0,
            "final_score": 80.0,
            "confidence_score": 88.0,
            "trust_level": "HIGH",
            "embedding": sample_embedding_384,
            "analyzed_at": datetime.now(UTC)
        }

    @pytest.fixture
    def multiple_opportunity_data(self, sample_embedding_384):
        """Create multiple sample opportunities with different embeddings"""
        base_time = datetime.now(UTC).replace(year=2024, month=1, day=1)

        # Generate different embeddings
        similar_embedding = self._generate_similar_embedding(sample_embedding_384, similarity=0.9)
        different_embedding = self._generate_similar_embedding(sample_embedding_384, similarity=0.3)
        duplicate_embedding = sample_embedding_384.copy()  # Exact duplicate

        return [
            {
                "submission_id": "similar_001",
                "reddit_title": "Project Management Tool for Startups",
                "reddit_url": "https://reddit.com/r/startups/similar_001/",
                "subreddit": "startups",
                "reddit_author": "startup_founder",
                "reddit_upvotes": 200,
                "reddit_comments_count": 60,
                "reddit_created_at": base_time,
                "app_title": "StartupPM",
                "app_concept": "Simple project management for early-stage startups",
                "problem_statement": "Startups need affordable and simple project management",
                "target_audience": "Startup founders and small teams",
                "core_functions": ["milestone tracking", "budget management", "team collaboration"],
                "market_demand": 88.0,
                "pain_intensity": 92.0,
                "monetization_potential": 80.0,
                "competition_level": 70.0,
                "technical_feasibility": 85.0,
                "final_score": 83.0,
                "confidence_score": 90.0,
                "trust_level": "HIGH",
                "embedding": similar_embedding,
                "analyzed_at": datetime.now(UTC)
            },
            {
                "submission_id": "different_001",
                "reddit_title": "AI Writing Assistant Content Creation",
                "reddit_url": "https://reddit.com/r/contentcreation/different_001/",
                "subreddit": "contentcreation",
                "reddit_author": "content_writer",
                "reddit_upvotes": 120,
                "reddit_comments_count": 35,
                "reddit_created_at": base_time + timedelta(days=1),
                "app_title": "WriteAI",
                "app_concept": "AI-powered writing assistant for content creators",
                "problem_statement": "Content creators need help with writer's block and content optimization",
                "target_audience": "Bloggers, copywriters, and content marketers",
                "core_functions": ["AI content generation", "SEO optimization", "tone adjustment"],
                "market_demand": 82.0,
                "pain_intensity": 75.0,
                "monetization_potential": 85.0,
                "competition_level": 60.0,
                "technical_feasibility": 78.0,
                "final_score": 76.0,
                "confidence_score": 82.0,
                "trust_level": "MEDIUM",
                "embedding": different_embedding,
                "analyzed_at": datetime.now(UTC)
            },
            {
                "submission_id": "duplicate_001",
                "reddit_title": "Team Task Management Application",
                "reddit_url": "https://reddit.com/r/technology/duplicate_001/",
                "subreddit": "technology",
                "reddit_author": "tech_manager",
                "reddit_upvotes": 180,
                "reddit_comments_count": 55,
                "reddit_created_at": base_time + timedelta(days=2),
                "app_title": "TeamSync",
                "app_concept": "Collaborative task management solution",
                "problem_statement": "Teams need better coordination tools",
                "target_audience": "Team leaders and project managers",
                "core_functions": ["task assignment", "progress monitoring", "team communication"],
                "market_demand": 86.0,
                "pain_intensity": 88.0,
                "monetization_potential": 79.0,
                "competition_level": 68.0,
                "technical_feasibility": 84.0,
                "final_score": 81.0,
                "confidence_score": 87.0,
                "trust_level": "HIGH",
                "embedding": duplicate_embedding,
                "analyzed_at": datetime.now(UTC)
            }
        ]

    def _generate_similar_embedding(self, base_embedding: list[float], similarity: float = 0.8) -> list[float]:
        """Generate an embedding with specified similarity to base embedding"""
        # Add controlled variations to achieve desired similarity
        variation = 1.0 - similarity
        return [x + np.random.normal(0, variation) for x in base_embedding]

    def _calculate_cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")

        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(vec1_array, vec2_array)
        magnitude1 = np.linalg.norm(vec1_array)
        magnitude2 = np.linalg.norm(vec2_array)

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _store_opportunity_in_db(self, loader: DatabaseLoader, opportunity_data: dict[str, Any]) -> Opportunity:
        """Store an opportunity in the database and return the model instance"""
        with loader.session_factory() as session:
            # Create Opportunity instance
            opportunity = Opportunity(
                submission_id=opportunity_data["submission_id"],
                reddit_title=opportunity_data["reddit_title"],
                reddit_url=opportunity_data["reddit_url"],
                subreddit=opportunity_data["subreddit"],
                reddit_author=opportunity_data["reddit_author"],
                reddit_upvotes=opportunity_data["reddit_upvotes"],
                reddit_comments_count=opportunity_data["reddit_comments_count"],
                reddit_created_at=opportunity_data["reddit_created_at"],
                app_title=opportunity_data["app_title"],
                app_concept=opportunity_data["app_concept"],
                problem_statement=opportunity_data["problem_statement"],
                target_audience=opportunity_data["target_audience"],
                core_functions=opportunity_data["core_functions"],
                market_demand=opportunity_data["market_demand"],
                pain_intensity=opportunity_data["pain_intensity"],
                monetization_potential=opportunity_data["monetization_potential"],
                competition_level=opportunity_data["competition_level"],
                technical_feasibility=opportunity_data["technical_feasibility"],
                final_score=opportunity_data["final_score"],
                confidence_score=opportunity_data["confidence_score"],
                trust_level=opportunity_data["trust_level"],
                embedding=opportunity_data["embedding"],
                analyzed_at=opportunity_data["analyzed_at"]
            )

            session.add(opportunity)
            session.commit()
            session.refresh(opportunity)

            return opportunity

    def test_embedding_storage_and_retrieval(self, test_database_loader, sample_opportunity_data):
        """
        TEST: Database should store and retrieve opportunities with embeddings correctly
        """
        # Store opportunity with embedding
        stored_opportunity = self._store_opportunity_in_db(test_database_loader, sample_opportunity_data)

        # Verify storage
        assert stored_opportunity.id is not None, "Opportunity should have an ID after storage"
        assert stored_opportunity.embedding is not None, "Embedding should be stored in database"
        assert isinstance(stored_opportunity.embedding, list), "Embedding should be stored as list"
        assert len(stored_opportunity.embedding) == 384, f"Embedding should have 384 dimensions, got {len(stored_opportunity.embedding)}"
        assert all(isinstance(x, (int, float)) for x in stored_opportunity.embedding), "All embedding values should be numeric"

        # Test retrieval
        with test_database_loader.session_factory() as session:
            retrieved_opportunity = session.query(Opportunity).filter_by(
                submission_id=sample_opportunity_data["submission_id"]
            ).first()

            assert retrieved_opportunity is not None, "Opportunity should be retrievable from database"
            assert retrieved_opportunity.embedding == stored_opportunity.embedding, "Retrieved embedding should match stored embedding"
            assert retrieved_opportunity.app_title == sample_opportunity_data["app_title"], "Other fields should be preserved"

    def test_vector_similarity_search_basic(self, test_database_loader, sample_opportunity_data, multiple_opportunity_data):
        """
        TEST: Vector similarity search should find similar opportunities correctly
        """
        # Store all opportunities
        self._store_opportunity_in_db(test_database_loader, sample_opportunity_data)
        for opp_data in multiple_opportunity_data:
            self._store_opportunity_in_db(test_database_loader, opp_data)

        # Test similarity search using the repository
        query_embedding = sample_opportunity_data["embedding"]

        # Use the database loader's find_similar_opportunities method
        similar_opportunities = test_database_loader.find_similar_opportunities(
            embedding=query_embedding,
            similarity_threshold=0.7,  # Lower threshold for testing
            limit=10
        )

        # Verify results
        assert len(similar_opportunities) > 0, "Should find at least one similar opportunity"

        # Results should be Opportunity objects (not dictionaries with similarity scores)
        for opportunity in similar_opportunities:
            assert isinstance(opportunity, Opportunity), "Results should be Opportunity objects"
            assert opportunity.embedding is not None, "Similar opportunities should have embeddings"

        # Should include the original opportunity (highest similarity to itself)
        original_found = any(opp.submission_id == sample_opportunity_data["submission_id"] for opp in similar_opportunities)
        assert original_found, "Original opportunity should be found in similar results"

    def test_cosine_similarity_calculation(self, sample_embedding_384):
        """
        TEST: Cosine similarity calculations should be accurate
        """
        # Test identical vectors
        similarity_identical = self._calculate_cosine_similarity(sample_embedding_384, sample_embedding_384)
        assert abs(similarity_identical - 1.0) < 0.001, "Identical vectors should have similarity ~1.0"

        # Test orthogonal vectors
        orthogonal_vector = [0.0] * 384
        orthogonal_vector[0] = 1.0  # Make first dimension 1
        similarity_orthogonal = self._calculate_cosine_similarity(sample_embedding_384, orthogonal_vector)
        assert similarity_orthogonal < 0.5, "Orthogonal vectors should have low similarity"

        # Test similar vectors
        similar_vector = self._generate_similar_embedding(sample_embedding_384, similarity=0.9)
        similarity_similar = self._calculate_cosine_similarity(sample_embedding_384, similar_vector)
        assert 0.8 <= similarity_similar <= 1.0, f"Similar vectors should have high similarity (got {similarity_similar})"

    def test_vector_deduplication(self, test_database_loader, sample_opportunity_data, multiple_opportunity_data):
        """
        TEST: Vector-based deduplication should identify duplicate opportunities
        """
        # Store all opportunities including duplicates
        self._store_opportunity_in_db(test_database_loader, sample_opportunity_data)
        for opp_data in multiple_opportunity_data:
            self._store_opportunity_in_db(test_database_loader, opp_data)

        # Find opportunities similar to the first one
        query_embedding = sample_opportunity_data["embedding"]
        similar_opportunities = test_database_loader.find_similar_opportunities(
            embedding=query_embedding,
            similarity_threshold=0.95,  # High threshold for duplicates
            limit=10
        )

        # Should find the exact duplicate (duplicate_001)
        duplicate_found = any(opp.submission_id == "duplicate_001" for opp in similar_opportunities)
        assert duplicate_found, "Should find the duplicate opportunity with high similarity threshold"

        # Calculate similarity scores for verification
        for opportunity in similar_opportunities:
            if opportunity.submission_id == "duplicate_001":
                similarity = self._calculate_cosine_similarity(query_embedding, opportunity.embedding)
                assert similarity >= 0.95, f"Duplicate should have very high similarity (got {similarity})"

    def test_similarity_threshold_filtering(self, test_database_loader, sample_opportunity_data, multiple_opportunity_data):
        """
        TEST: Similarity thresholds should filter results appropriately
        """
        # Store all opportunities
        self._store_opportunity_in_db(test_database_loader, sample_opportunity_data)
        for opp_data in multiple_opportunity_data:
            self._store_opportunity_in_db(test_database_loader, opp_data)

        query_embedding = sample_opportunity_data["embedding"]

        # Test with different thresholds
        high_threshold_results = test_database_loader.find_similar_opportunities(
            embedding=query_embedding,
            similarity_threshold=0.9,
            limit=10
        )

        low_threshold_results = test_database_loader.find_similar_opportunities(
            embedding=query_embedding,
            similarity_threshold=0.5,
            limit=10
        )

        # Lower threshold should return >= results than higher threshold
        assert len(low_threshold_results) >= len(high_threshold_results), \
            "Lower threshold should return >= results than higher threshold"

        # Verify that high threshold results actually have high similarity
        for opportunity in high_threshold_results:
            similarity = self._calculate_cosine_similarity(query_embedding, opportunity.embedding)
            assert similarity >= 0.5, f"High threshold results should have reasonable similarity (got {similarity})"

    def test_vector_operations_performance(self, test_database_loader):
        """
        TEST: Vector operations should perform reasonably well
        """
        import time

        # Create test data with different embeddings
        test_embeddings = []
        base_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 76 + [0.6]  # 384 dimensions

        for i in range(20):  # Create 20 test opportunities
            embedding = self._generate_similar_embedding(base_embedding, similarity=0.7 + (i * 0.01))
            opportunity_data = {
                "submission_id": f"perf_test_{i}",
                "reddit_title": f"Performance Test App {i}",
                "reddit_url": f"https://reddit.com/test/perf_test_{i}/",
                "subreddit": "test",
                "reddit_author": "user",
                "reddit_upvotes": 100 + i,
                "reddit_comments_count": 20 + i // 2,
                "reddit_created_at": datetime.now(UTC),
                "app_title": f"PerfApp{i}",
                "app_concept": "Test concept for performance",
                "problem_statement": "Test problem for performance",
                "target_audience": "Test users for performance",
                "core_functions": ["func1", "func2"],
                "market_demand": 70.0,
                "pain_intensity": 75.0,
                "monetization_potential": 80.0,
                "competition_level": 65.0,
                "technical_feasibility": 85.0,
                "final_score": 75.0,
                "confidence_score": 80.0,
                "trust_level": "HIGH",
                "embedding": embedding,
                "analyzed_at": datetime.now(UTC)
            }
            self._store_opportunity_in_db(test_database_loader, opportunity_data)
            test_embeddings.append(embedding)

        # Test similarity search performance
        query_embedding = test_embeddings[0]
        start_time = time.time()

        results = test_database_loader.find_similar_opportunities(
            embedding=query_embedding,
            similarity_threshold=0.6,
            limit=10
        )

        search_time = time.time() - start_time

        # Performance assertions
        assert search_time < 2.0, f"Similarity search should complete in <2s, took {search_time:.2f}s"
        assert len(results) > 0, "Should find similar opportunities"

        # Verify results quality
        for opportunity in results:
            similarity = self._calculate_cosine_similarity(query_embedding, opportunity.embedding)
            assert similarity >= 0.5, f"Results should have reasonable similarity (got {similarity})"

    def test_embedding_validation(self, test_database_loader, sample_opportunity_data):
        """
        TEST: Embedding validation should work correctly
        """
        # Test with valid embedding
        valid_opportunity = self._store_opportunity_in_db(test_database_loader, sample_opportunity_data)
        assert valid_opportunity.embedding is not None, "Valid embedding should be stored"

        # Test with None embedding
        opportunity_data_no_embedding = sample_opportunity_data.copy()
        opportunity_data_no_embedding["submission_id"] = "test_no_embedding"
        opportunity_data_no_embedding["embedding"] = None

        opportunity_no_embedding = self._store_opportunity_in_db(test_database_loader, opportunity_data_no_embedding)
        assert opportunity_no_embedding.embedding is None, "None embedding should be stored as None"

        # Test with empty embedding
        opportunity_data_empty = sample_opportunity_data.copy()
        opportunity_data_empty["submission_id"] = "test_empty_embedding"
        opportunity_data_empty["embedding"] = []

        opportunity_empty = self._store_opportunity_in_db(test_database_loader, opportunity_data_empty)
        assert opportunity_empty.embedding == [], "Empty embedding should be stored as empty list"

    def test_edge_cases(self, test_database_loader, sample_embedding_384):
        """
        TEST: Edge cases should be handled gracefully
        """
        # Test similarity search with empty database
        results_empty = test_database_loader.find_similar_opportunities(
            embedding=sample_embedding_384,
            similarity_threshold=0.5,
            limit=10
        )
        assert len(results_empty) == 0, "Empty database should return no results"

        # Test with very high threshold
        # First store one opportunity
        single_opportunity_data = {
            "submission_id": "single_test",
            "reddit_title": "Single Test App",
            "reddit_url": "https://reddit.com/test/single_test/",
            "subreddit": "test",
            "reddit_author": "user",
            "reddit_upvotes": 100,
            "reddit_comments_count": 20,
            "reddit_created_at": datetime.now(UTC),
            "app_title": "SingleApp",
            "app_concept": "Test concept",
            "problem_statement": "Test problem",
            "target_audience": "Test users",
            "core_functions": ["func1", "func2"],
            "market_demand": 70.0,
            "pain_intensity": 75.0,
            "monetization_potential": 80.0,
            "competition_level": 65.0,
            "technical_feasibility": 85.0,
            "final_score": 75.0,
            "confidence_score": 80.0,
            "trust_level": "HIGH",
            "embedding": sample_embedding_384,
            "analyzed_at": datetime.now(UTC)
        }
        self._store_opportunity_in_db(test_database_loader, single_opportunity_data)

        # Search with very high threshold
        results_high_threshold = test_database_loader.find_similar_opportunities(
            embedding=sample_embedding_384,
            similarity_threshold=0.999,
            limit=10
        )
        # Should find the exact match
        assert len(results_high_threshold) >= 1, "Very high threshold should find exact matches"

    def test_database_connection_and_setup(self, test_database_loader):
        """
        TEST: Database connection and table creation should work correctly
        """
        # Test database connection
        connection_successful = test_database_loader.test_connection()
        assert connection_successful, "Database connection should be successful"

        # Test table creation
        try:
            with test_database_loader.session_factory() as session:
                # Try to query the opportunities table
                count = session.query(Opportunity).count()
                assert isinstance(count, int), "Table should be queryable"
        except Exception as e:
            pytest.fail(f"Database table creation failed: {e}")

    def test_repository_pattern_integration(self, test_database_loader, sample_opportunity_data):
        """
        TEST: Repository pattern should integrate correctly with vector functionality
        """
        # Store an opportunity using repository pattern
        stored_opportunity = self._store_opportunity_in_db(test_database_loader, sample_opportunity_data)

        # Test repository find_by_submission_id
        found_opportunity = test_database_loader.repository.find_by_submission_id(
            sample_opportunity_data["submission_id"]
        )
        assert found_opportunity is not None, "Repository should find opportunity by submission ID"
        assert found_opportunity.id == stored_opportunity.id, "Should find the correct opportunity"
        assert found_opportunity.embedding == stored_opportunity.embedding, "Embedding should be preserved"

        # Test repository statistics
        stats = test_database_loader.repository.get_statistics()
        assert "total_opportunities" in stats, "Statistics should include total opportunities"
        assert stats["total_opportunities"] >= 1, "Should count the stored opportunity"


if __name__ == "__main__":
    # Allow running the tests directly
    pytest.main([__file__, "-v"])
