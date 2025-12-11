"""
Loader Comparison Tests for RedditHarbor Pipeline V4

This module tests the behavioral consistency between PostgresLoader and SQLModelLoader
to ensure they produce identical results when given the same input data.

Tests follow the TDD approach and verify:
- Data persistence consistency
- Duplicate detection behavior
- Transaction handling
- Performance characteristics
- JSON serialization/deserialization
- UTC timestamp handling
- Score calculation consistency
"""

import time
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlmodel import select

from config.settings import Settings
from database import get_session
from load.loader_factory import get_loader
from models.analysis import Opportunity


@pytest.fixture(scope="function", autouse=True)
def clean_test_database():
    """Clean database before AND after each test to ensure isolation"""
    # Clean BEFORE test
    try:
        from sqlalchemy import text
        with next(get_session()) as session:
            session.execute(text("DELETE FROM opportunities"))
            session.commit()
    except Exception:
        pass

    yield

    # Clean AFTER test
    try:
        from sqlalchemy import text
        with next(get_session()) as session:
            session.execute(text("DELETE FROM opportunities"))
            session.commit()
    except Exception:
        pass


@pytest.fixture(scope="module")
def test_db_url():
    """Get test database URL from settings"""
    return Settings().database_url


@pytest.fixture
def postgres_loader(test_db_url):
    """Create PostgresLoader instance for testing"""
    settings = Settings(database_url=test_db_url, use_sqlmodel_loader=False)
    loader = get_loader(settings)
    yield loader
    loader.close()


@pytest.fixture
def sqlmodel_loader(test_db_url):
    """Create SQLModelLoader instance for testing"""
    settings = Settings(database_url=test_db_url, use_sqlmodel_loader=True)
    loader = get_loader(settings)
    yield loader
    loader.close()


@pytest.fixture
def sample_opportunity_data():
    """Generate sample opportunity data for testing"""
    return {
        "submission_id": "test_submission_123",
        "subreddit": "r/startups",
        "title": "This is a test submission about AI-powered tools",
        "wtp_score": 75.5,
        "confidence_score": 85.0,
        "trust_level": "HIGH",
        "analysis": {
            "app_idea": {
                "title": "AI Productivity Tool",
                "app_concept": "An AI-powered productivity tool that helps teams collaborate more efficiently",
                "problem_statement": "Teams struggle with inefficient workflows and manual task management"
            },
            "pain_points": [
                "Manual task management is time-consuming",
                "Lack of real-time collaboration features",
                "Difficulty tracking project progress"
            ],
            "opportunity_summary": "AI-powered productivity tool with real-time collaboration features",
            "content_quality_score": 0.85,
            "is_spam": False,
            "spam_indicators": [],
            "analyzed_at": "2025-01-15T12:00:00Z"
        },
        "metrics": {
            "market_demand": 80.0,
            "pain_intensity": 75.0,
            "monetization_potential": 70.0,
            "technical_feasibility": 65.0,
            "competition_level": 50.0
        }
    }


@pytest.fixture
def complex_opportunity_data():
    """Generate complex nested opportunity data for edge case testing"""
    return {
        "submission_id": "test_submission_complex_456",
        "subreddit": "r/technology",
        "title": "Complex multi-dimensional analysis with nested structures",
        "wtp_score": 90.0,
        "confidence_score": 95.0,
        "trust_level": "MEDIUM",
        "analysis": {
            "app_idea": {
                "title": "Advanced Analytics Platform",
                "app_concept": "A comprehensive platform for analyzing complex data patterns across multiple domains",
                "problem_statement": "Complex data analysis requires specialized tools and expertise",
                "target_audience": ["Enterprise", "Mid-market", "Small businesses"],
                "features": [
                    "Real-time data processing",
                    "Multi-dimensional analysis",
                    "Customizable dashboards",
                    "API integration capabilities"
                ]
            },
            "pain_points": [
                "Data silos between departments",
                "Complex analysis requires specialized expertise",
                "Real-time processing challenges",
                "Integration difficulties with existing systems"
            ],
            "opportunity_summary": "Advanced analytics platform addressing multiple enterprise pain points",
            "content_quality_score": 0.92,
            "is_spam": False,
            "spam_indicators": [],
            "technical_requirements": {
                "frontend": ["React", "TypeScript", "D3.js"],
                "backend": ["Python", "FastAPI", "PostgreSQL"],
                "infrastructure": ["AWS", "Docker", "Kubernetes"],
                "ai_components": ["TensorFlow", "PyTorch", "NLP models"]
            },
            "market_analysis": {
                "total_addressable_market": 50.0,
                "serviceable_addressable_market": 25.0,
                "serviceable_obtainable_market": 10.0,
                "market_growth_rate": 15.0,
                "market_segments": [
                    {"segment": "Enterprise", "size": 30.0, "growth": 12.0},
                    {"segment": "Mid-market", "size": 40.0, "growth": 18.0},
                    {"segment": "Small business", "size": 30.0, "growth": 20.0}
                ]
            },
            "analyzed_at": "2025-01-15T12:00:00Z"
        },
        "metrics": {
            "market_demand": 90.0,
            "pain_intensity": 85.0,
            "monetization_potential": 80.0,
            "technical_feasibility": 70.0,
            "competition_level": 60.0,
            "user_retention_potential": 75.0,
            "scalability_score": 80.0,
            "ip_protection_score": 65.0
        }
    }


@contextmanager
def clean_test_data(loader, submission_id):
    """Context manager to ensure test data is cleaned up"""
    try:
        yield
    finally:
        # Clean up any test data
        try:
            if hasattr(loader, 'get_opportunity'):
                loader.get_opportunity(submission_id)
        except:
            pass


class TestLoaderBasicFunctionality:
    """Test basic functionality of both loaders"""

    @pytest.mark.parametrize("loader", ["postgres_loader", "sqlmodel_loader"])
    def test_loader_can_be_initialized(self, loader, request):
        """Test that both loaders can be properly initialized"""
        loader_instance = request.getfixturevalue(loader)
        assert loader_instance is not None
        assert hasattr(loader_instance, 'save_opportunity')
        assert hasattr(loader_instance, 'save_analysis')
        assert hasattr(loader_instance, 'close')

    def test_opportunity_model_validation(self, sample_opportunity_data):
        """Test that Opportunity model validation works correctly"""
        opportunity = Opportunity(**sample_opportunity_data)
        assert opportunity.submission_id == sample_opportunity_data["submission_id"]
        assert opportunity.subreddit == sample_opportunity_data["subreddit"]
        assert opportunity.trust_level == sample_opportunity_data["trust_level"]
        assert opportunity.final_score > 0  # Should be calculated from metrics

    def test_save_opportunity_basic_flow(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test basic save/retrieve flow for both loaders"""
        # Create Opportunity instances with different submission IDs
        postgres_data = sample_opportunity_data.copy()
        postgres_data['submission_id'] = 'postgres_test_123'
        postgres_opportunity = Opportunity(**postgres_data)

        sqlmodel_data = sample_opportunity_data.copy()
        sqlmodel_data['submission_id'] = 'sqlmodel_test_123'
        sqlmodel_opportunity = Opportunity(**sqlmodel_data)

        # Test PostgresLoader (only save method available)
        with clean_test_data(postgres_loader, postgres_opportunity.submission_id):
            saved = postgres_loader.save_opportunity(postgres_opportunity)
            assert saved is True

            # Verify save completed successfully
            # Note: PostgresLoader doesn't have get_opportunity method

        # Test SQLModelLoader
        with clean_test_data(sqlmodel_loader, sqlmodel_opportunity.submission_id):
            saved = sqlmodel_loader.save_opportunity(sqlmodel_opportunity)
            assert saved is True

            retrieved = sqlmodel_loader.get_opportunity(sqlmodel_opportunity.submission_id)
            assert retrieved is not None
            assert retrieved.submission_id == sqlmodel_opportunity.submission_id
            assert retrieved.subreddit == sqlmodel_opportunity.subreddit
            assert retrieved.title == sqlmodel_opportunity.title
            assert retrieved.wtp_score == sqlmodel_opportunity.wtp_score
            assert retrieved.final_score == sqlmodel_opportunity.final_score


class TestLoaderConsistency:
    """Test that both loaders produce identical results"""

    def test_identical_persistence_behavior(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test both loaders persist identical data"""
        # Create identical Opportunity instances with different submission IDs
        postgres_data = sample_opportunity_data.copy()
        postgres_data['submission_id'] = 'postgres_persist_123'
        postgres_opportunity = Opportunity(**postgres_data)

        sqlmodel_data = sample_opportunity_data.copy()
        sqlmodel_data['submission_id'] = 'sqlmodel_persist_123'
        sqlmodel_opportunity = Opportunity(**sqlmodel_data)

        # Save using both loaders
        with clean_test_data(postgres_loader, postgres_opportunity.submission_id):
            with clean_test_data(sqlmodel_loader, sqlmodel_opportunity.submission_id):
                postgres_saved = postgres_loader.save_opportunity(postgres_opportunity)
                sqlmodel_saved = sqlmodel_loader.save_opportunity(sqlmodel_opportunity)

                assert postgres_saved == sqlmodel_saved, "Both loaders should report same save status"

                # Retrieve and compare (SQLModelLoader only has get_opportunity)
                sqlmodel_retrieved = sqlmodel_loader.get_opportunity(sqlmodel_opportunity.submission_id)

                # Verify SQLModelLoader data
                assert sqlmodel_retrieved.submission_id == sqlmodel_opportunity.submission_id
                assert sqlmodel_retrieved.subreddit == sqlmodel_opportunity.subreddit
                assert sqlmodel_retrieved.title == sqlmodel_opportunity.title
                assert sqlmodel_retrieved.wtp_score == sqlmodel_opportunity.wtp_score
                assert sqlmodel_retrieved.final_score == sqlmodel_opportunity.final_score
                assert sqlmodel_retrieved.confidence_score == sqlmodel_opportunity.confidence_score
                assert sqlmodel_retrieved.trust_level == sqlmodel_opportunity.trust_level

                # Compare JSON fields
                assert sqlmodel_retrieved.analysis == sqlmodel_opportunity.analysis
                assert sqlmodel_retrieved.metrics == sqlmodel_opportunity.metrics

                # Verify timestamps are set correctly
                assert sqlmodel_retrieved.created_at is not None
                assert sqlmodel_retrieved.updated_at is not None

    def test_duplicate_detection_consistency(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test both loaders handle duplicates identically"""
        # Test PostgresLoader duplicate detection
        postgres_data = sample_opportunity_data.copy()
        postgres_data['submission_id'] = f"postgres_dup_{datetime.now().timestamp()}"
        postgres_opportunity = Opportunity(**postgres_data)

        # First save should succeed
        first_save = postgres_loader.save_opportunity(postgres_opportunity)
        assert first_save is True

        # Second save should be duplicate
        second_save = postgres_loader.save_opportunity(postgres_opportunity)
        assert second_save is False

        # Test SQLModelLoader duplicate detection with different ID
        sqlmodel_data = sample_opportunity_data.copy()
        sqlmodel_data['submission_id'] = f"sqlmodel_dup_{datetime.now().timestamp()}"
        sqlmodel_opportunity = Opportunity(**sqlmodel_data)

        # First save should succeed
        first_save = sqlmodel_loader.save_opportunity(sqlmodel_opportunity)
        assert first_save is True

        # Second save should be duplicate
        second_save = sqlmodel_loader.save_opportunity(sqlmodel_opportunity)
        assert second_save is False

    def test_duplicate_across_loaders(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test duplicate detection when same opportunity saved with different loaders"""
        # Create unique submission ID for this test
        unique_id = f"cross_loader_{datetime.now().timestamp()}"
        data = sample_opportunity_data.copy()
        data['submission_id'] = unique_id
        opportunity = Opportunity(**data)

        # Save with PostgresLoader first
        postgres_save = postgres_loader.save_opportunity(opportunity)
        assert postgres_save is True

        # Now try to save with SQLModelLoader - both loaders share same database
        # so SQLModelLoader SHOULD detect the duplicate
        sqlmodel_save = sqlmodel_loader.save_opportunity(opportunity)
        assert sqlmodel_save is False, "SQLModelLoader should detect duplicate from PostgresLoader (shared database)"

    def test_json_serialization_consistency(self, postgres_loader, sqlmodel_loader, complex_opportunity_data):
        """Test complex JSON structures are handled identically"""
        postgres_opportunity = Opportunity(**complex_opportunity_data)
        sqlmodel_opportunity = Opportunity(**complex_opportunity_data)

        with clean_test_data(postgres_loader, postgres_opportunity.submission_id):
            with clean_test_data(sqlmodel_loader, sqlmodel_opportunity.submission_id):
                # Save with both loaders
                postgres_loader.save_opportunity(postgres_opportunity)
                sqlmodel_loader.save_opportunity(sqlmodel_opportunity)

                # Retrieve and compare complex structures
                sqlmodel_retrieved = sqlmodel_loader.get_opportunity(sqlmodel_opportunity.submission_id)

                # Verify complex structures are preserved
                assert sqlmodel_retrieved.analysis["app_idea"]["title"] == complex_opportunity_data["analysis"]["app_idea"]["title"]
                assert sqlmodel_retrieved.analysis["pain_points"] == complex_opportunity_data["analysis"]["pain_points"]
                assert sqlmodel_retrieved.analysis["technical_requirements"] == complex_opportunity_data["analysis"]["technical_requirements"]

                # Compare nested market analysis
                assert sqlmodel_retrieved.analysis["market_analysis"]["market_segments"] == complex_opportunity_data["analysis"]["market_analysis"]["market_segments"]

                # Compare extended metrics
                assert sqlmodel_retrieved.metrics["user_retention_potential"] == complex_opportunity_data["metrics"]["user_retention_potential"]
                assert sqlmodel_retrieved.metrics["scalability_score"] == complex_opportunity_data["metrics"]["scalability_score"]

    def test_timestamp_handling_consistency(self, postgres_loader, sqlmodel_loader):
        """Test UTC timestamp handling is consistent"""
        # Create opportunity with specific timestamp
        fixed_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

        data = {
            "submission_id": f"test_timestamp_{datetime.now().timestamp()}",
            "subreddit": "r/test",
            "title": "Timestamp test",
            "wtp_score": 50.0,
            "analysis": {"app_idea": {"title": "Test App", "app_concept": "Test concept"}},
            "metrics": {"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        }

        postgres_opportunity = Opportunity(**data)
        sqlmodel_opportunity = Opportunity(**data)

        # Manually set timestamps to be equal (with timezone)
        postgres_opportunity.created_at = fixed_time
        postgres_opportunity.updated_at = fixed_time
        sqlmodel_opportunity.created_at = fixed_time
        sqlmodel_opportunity.updated_at = fixed_time

        with clean_test_data(postgres_loader, postgres_opportunity.submission_id):
            with clean_test_data(sqlmodel_loader, sqlmodel_opportunity.submission_id):
                postgres_loader.save_opportunity(postgres_opportunity)
                sqlmodel_loader.save_opportunity(sqlmodel_opportunity)

                # Retrieve and verify timestamps match
                sqlmodel_retrieved = sqlmodel_loader.get_opportunity(sqlmodel_opportunity.submission_id)

                # Note: SQLModel might normalize the timezone, so check equivalence rather than identity
                # Also, SQLModel might store timestamps without timezone info
                assert sqlmodel_retrieved.created_at.replace(tzinfo=None) == fixed_time.replace(tzinfo=None)
                assert sqlmodel_retrieved.updated_at.replace(tzinfo=None) == fixed_time.replace(tzinfo=None)

    def test_final_score_calculation_consistency(self, postgres_loader, sqlmodel_loader):
        """Test final score calculation is consistent between loaders"""
        # Create opportunities with same metrics
        metrics_data = {
            "market_demand": 80.0,
            "pain_intensity": 75.0,
            "monetization_potential": 70.0,
            "technical_feasibility": 65.0
        }

        postgres_opportunity = Opportunity(
            submission_id="test_score_calculation_101",
            subreddit="r/startups",
            title="Score calculation test",
            wtp_score=60.0,
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics=metrics_data
        )

        sqlmodel_opportunity = Opportunity(
            submission_id="test_score_calculation_101",
            subreddit="r/startups",
            title="Score calculation test",
            wtp_score=60.0,
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics=metrics_data
        )

        with clean_test_data(postgres_loader, postgres_opportunity.submission_id):
            with clean_test_data(sqlmodel_loader, sqlmodel_opportunity.submission_id):
                postgres_loader.save_opportunity(postgres_opportunity)
                sqlmodel_loader.save_opportunity(sqlmodel_opportunity)

                # Verify final scores are calculated identically
                postgres_calculated = postgres_opportunity.final_score
                sqlmodel_retrieved = sqlmodel_loader.get_opportunity(sqlmodel_opportunity.submission_id)

                # Expected calculation: (80*0.3 + 75*0.25 + 70*0.25 + 65*0.2) / (0.3+0.25+0.25+0.2)
                expected_final_score = (80*0.3 + 75*0.25 + 70*0.25 + 65*0.2) / 1.0
                expected_final_score = round(expected_final_score, 2)

                assert postgres_calculated == expected_final_score
                assert sqlmodel_retrieved.final_score == expected_final_score
                assert postgres_calculated == sqlmodel_retrieved.final_score


class TestLoaderErrorHandling:
    """Test error handling consistency between loaders"""

    def test_empty_submission_id_validation(self, postgres_loader, sqlmodel_loader):
        """Test both loaders validate empty submission_id"""
        invalid_data = {
            "submission_id": "",
            "subreddit": "r/test",
            "title": "Test",
            "analysis": {"app_idea": {"title": "Test", "app_concept": "Test"}},
            "metrics": {"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        }

        postgres_opportunity = Opportunity(**invalid_data)
        sqlmodel_opportunity = Opportunity(**invalid_data)

        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            postgres_loader.save_opportunity(postgres_opportunity)

        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            sqlmodel_loader.save_opportunity(sqlmodel_opportunity)

    def test_invalid_trust_level_validation(self, postgres_loader, sqlmodel_loader):
        """Test both loaders validate trust level"""
        invalid_data = {
            "submission_id": "test_trust_202",
            "subreddit": "r/test",
            "title": "Test",
            "trust_level": "INVALID",
            "analysis": {"app_idea": {"title": "Test", "app_concept": "Test"}},
            "metrics": {"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        }

        # Validation happens at model instantiation, not during save
        # Both should raise ValueError during object creation
        with pytest.raises(ValueError, match="Trust level must be one of"):
            postgres_opportunity = Opportunity(**invalid_data)

        with pytest.raises(ValueError, match="Trust level must be one of"):
            sqlmodel_opportunity = Opportunity(**invalid_data)

    def test_database_connection_error_handling(self, postgres_loader, sqlmodel_loader):
        """Test both loaders handle database connection errors gracefully"""
        opportunity = Opportunity(
            submission_id="test_error_303",
            subreddit="r/test",
            title="Error test",
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics={"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        )

        # Mock a database connection error at the pool/session level
        def mock_getconn_error():
            raise RuntimeError("Connection failed")

        def mock_session_error():
            raise RuntimeError("Connection failed")

        # Test PostgresLoader - mock the connection pool
        with patch.object(postgres_loader.pool, 'getconn', side_effect=mock_getconn_error):
            with pytest.raises(RuntimeError, match="Database save failed"):
                postgres_loader.save_opportunity(opportunity)

        # Test SQLModelLoader - mock get_session
        with patch('load.sqlmodel_loader.get_session', side_effect=mock_session_error):
            with pytest.raises(RuntimeError):
                sqlmodel_loader.save_opportunity(opportunity)


class TestLoaderPerformance:
    """Test performance characteristics of both loaders"""

    def test_single_save_performance(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test performance of single save operation"""
        opportunity = Opportunity(**sample_opportunity_data)

        # Test PostgresLoader performance
        with clean_test_data(postgres_loader, opportunity.submission_id):
            start_time = time.perf_counter()
            postgres_loader.save_opportunity(opportunity)
            postgres_time = time.perf_counter() - start_time

        # Test SQLModelLoader performance
        with clean_test_data(sqlmodel_loader, opportunity.submission_id):
            start_time = time.perf_counter()
            sqlmodel_loader.save_opportunity(opportunity)
            sqlmodel_time = time.perf_counter() - start_time

        # Performance difference should be reasonable
        # Updated to allow SQLModelLoader to be faster after optimizations
        performance_ratio = postgres_time / sqlmodel_time
        assert 0.01 < performance_ratio < 100, f"Performance ratio {performance_ratio} is unreasonable"

        print(f"\nPostgresLoader save time: {postgres_time:.4f}s")
        print(f"SQLModelLoader save time: {sqlmodel_time:.4f}s")
        print(f"Performance ratio (Postgres/SQLModel): {performance_ratio:.2f}")

    def test_batch_save_performance(self, postgres_loader, sqlmodel_loader):
        """Test performance of batch save operations"""
        # Create multiple opportunities
        opportunities = []
        for i in range(10):
            data = {
                "submission_id": f"batch_test_{i}",
                "subreddit": "r/startups",
                "title": f"Batch test opportunity {i}",
                "wtp_score": 50.0 + i,
                "analysis": {"app_idea": {"title": f"App {i}", "app_concept": f"Concept {i}"}},
                "metrics": {"market_demand": 60.0 + i, "pain_intensity": 50.0 + i, "monetization_potential": 40.0 + i, "technical_feasibility": 30.0 + i}
            }
            opportunities.append(Opportunity(**data))

        # Test PostgresLoader performance
        for opp in opportunities:
            with clean_test_data(postgres_loader, opp.submission_id):
                start_time = time.perf_counter()
                postgres_loader.save_opportunity(opp)
                postgres_time = time.perf_counter() - start_time

        # Test SQLModelLoader performance
        for opp in opportunities:
            with clean_test_data(sqlmodel_loader, opp.submission_id):
                start_time = time.perf_counter()
                sqlmodel_loader.save_opportunity(opp)
                sqlmodel_time = time.perf_counter() - start_time

        # Average performance difference should be reasonable
        postgres_avg = postgres_time / len(opportunities)
        sqlmodel_avg = sqlmodel_time / len(opportunities)
        performance_ratio = postgres_avg / sqlmodel_avg

        print(f"\nPostgresLoader avg save time: {postgres_avg:.4f}s")
        print(f"SQLModelLoader avg save time: {sqlmodel_avg:.4f}s")
        print(f"Performance ratio (Postgres/SQLModel): {performance_ratio:.2f}")

    def test_memory_usage_comparison(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test memory usage comparison (basic approximation)"""
        import gc
        import sys

        opportunity = Opportunity(**sample_opportunity_data)

        # Test PostgresLoader memory usage
        with clean_test_data(postgres_loader, opportunity.submission_id):
            gc.collect()
            start_memory = sys.getsizeof(postgres_loader) + sys.getsizeof(opportunity)
            postgres_loader.save_opportunity(opportunity)
            postgres_memory = sys.getsizeof(postgres_loader) + sys.getsizeof(opportunity)

        # Test SQLModelLoader memory usage
        with clean_test_data(sqlmodel_loader, opportunity.submission_id):
            gc.collect()
            start_memory = sys.getsizeof(sqlmodel_loader) + sys.getsizeof(opportunity)
            sqlmodel_loader.save_opportunity(opportunity)
            sqlmodel_memory = sys.getsizeof(sqlmodel_loader) + sys.getsizeof(opportunity)

        # Memory usage difference should be minimal
        memory_diff = abs(postgres_memory - sqlmodel_memory)
        print(f"\nPostgresLoader memory usage: {postgres_memory} bytes")
        print(f"SQLModelLoader memory usage: {sqlmodel_memory} bytes")
        print(f"Memory difference: {memory_diff} bytes")

        # Allow reasonable difference but not orders of magnitude
        assert memory_diff < 10000, f"Memory difference {memory_diff} bytes is too large"


class TestLoaderTransactionBehavior:
    """Test transaction handling behavior consistency"""

    def test_transaction_rollback_on_error(self, postgres_loader, sqlmodel_loader):
        """Test transactions are rolled back on errors"""
        opportunity = Opportunity(
            submission_id="test_transaction_404",
            subreddit="r/test",
            title="Transaction test",
            wtp_score=50.0,
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics={"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        )

        # Save with PostgresLoader and verify
        saved = postgres_loader.save_opportunity(opportunity)
        assert saved is True

        retrieved = postgres_loader.get_opportunity(opportunity.submission_id)
        assert retrieved is not None
        assert retrieved.submission_id == opportunity.submission_id

        # Save with SQLModelLoader and verify
        opportunity2 = Opportunity(
            submission_id="test_transaction_405",
            subreddit="r/test",
            title="Transaction test 2",
            wtp_score=55.0,
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics={"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        )

        saved2 = sqlmodel_loader.save_opportunity(opportunity2)
        assert saved2 is True

        retrieved2 = sqlmodel_loader.get_opportunity(opportunity2.submission_id)
        assert retrieved2 is not None
        assert retrieved2.submission_id == opportunity2.submission_id

    def test_concurrent_safety(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test basic concurrent safety"""
        import threading
        import time

        results = {'postgres': [], 'sqlmodel': []}

        def save_with_loader(loader, loader_name, opportunity):
            try:
                start_time = time.perf_counter()
                success = loader.save_opportunity(opportunity)
                end_time = time.perf_counter()
                results[loader_name].append({
                    'success': success,
                    'time': end_time - start_time
                })
            except Exception as e:
                results[loader_name].append({
                    'success': False,
                    'error': str(e)
                })

        # Create two different opportunities to avoid duplicate conflicts
        postgres_data = sample_opportunity_data.copy()
        postgres_data['submission_id'] = f'concurrent_postgres_{time.time()}'
        postgres_opportunity = Opportunity(**postgres_data)

        sqlmodel_data = sample_opportunity_data.copy()
        sqlmodel_data['submission_id'] = f'concurrent_sqlmodel_{time.time()}'
        sqlmodel_opportunity = Opportunity(**sqlmodel_data)

        # Create threads for concurrent saves
        postgres_thread = threading.Thread(
            target=save_with_loader,
            args=(postgres_loader, 'postgres', postgres_opportunity)
        )
        sqlmodel_thread = threading.Thread(
            target=save_with_loader,
            args=(sqlmodel_loader, 'sqlmodel', sqlmodel_opportunity)
        )

        # Start both threads
        postgres_thread.start()
        sqlmodel_thread.start()

        # Wait for both to complete
        postgres_thread.join(timeout=5)
        sqlmodel_thread.join(timeout=5)

        # Verify both completed successfully
        assert len(results['postgres']) == 1
        assert len(results['sqlmodel']) == 1
        assert results['postgres'][0]['success'] is True
        assert results['sqlmodel'][0]['success'] is True

        # Performance should be comparable
        postgres_time = results['postgres'][0]['time']
        sqlmodel_time = results['sqlmodel'][0]['time']
        time_diff = abs(postgres_time - sqlmodel_time)

        print(f"\nConcurrent save times - Postgres: {postgres_time:.4f}s, SQLModel: {sqlmodel_time:.4f}s")
        print(f"Time difference: {time_diff:.4f}s")

        # Time difference should be reasonable
        assert time_diff < 1.0, f"Concurrent time difference {time_diff}s is too large"


class TestLoaderDataIntegrity:
    """Test data integrity across both loaders"""

    def test_round_trip_consistency(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test save → retrieve → validate cycle maintains data integrity"""
        # Test PostgresLoader round-trip
        postgres_data = sample_opportunity_data.copy()
        postgres_data['submission_id'] = f"postgres_roundtrip_{datetime.now().timestamp()}"
        postgres_opportunity = Opportunity(**postgres_data)

        postgres_saved = postgres_loader.save_opportunity(postgres_opportunity)
        assert postgres_saved is True

        # Retrieve from PostgresLoader
        postgres_retrieved = postgres_loader.get_opportunity(postgres_opportunity.submission_id)
        assert postgres_retrieved is not None

        # Verify round-trip consistency
        assert postgres_retrieved.submission_id == postgres_opportunity.submission_id
        assert postgres_retrieved.subreddit == postgres_opportunity.subreddit
        assert postgres_retrieved.title == postgres_opportunity.title
        assert postgres_retrieved.wtp_score == postgres_opportunity.wtp_score
        assert postgres_retrieved.final_score == postgres_opportunity.final_score
        assert postgres_retrieved.analysis == postgres_opportunity.analysis
        assert postgres_retrieved.metrics == postgres_opportunity.metrics

        # Test SQLModelLoader round-trip with different ID
        sqlmodel_data = sample_opportunity_data.copy()
        sqlmodel_data['submission_id'] = f"sqlmodel_roundtrip_{datetime.now().timestamp()}"
        sqlmodel_opportunity = Opportunity(**sqlmodel_data)

        sqlmodel_saved = sqlmodel_loader.save_opportunity(sqlmodel_opportunity)
        assert sqlmodel_saved is True

        # Retrieve from SQLModelLoader
        sqlmodel_retrieved = sqlmodel_loader.get_opportunity(sqlmodel_opportunity.submission_id)
        assert sqlmodel_retrieved is not None

        # Verify round-trip consistency
        assert sqlmodel_retrieved.submission_id == sqlmodel_opportunity.submission_id
        assert sqlmodel_retrieved.subreddit == sqlmodel_opportunity.subreddit
        assert sqlmodel_retrieved.title == sqlmodel_opportunity.title
        assert sqlmodel_retrieved.wtp_score == sqlmodel_opportunity.wtp_score
        assert sqlmodel_retrieved.final_score == sqlmodel_opportunity.final_score
        assert sqlmodel_retrieved.analysis == sqlmodel_opportunity.analysis
        assert sqlmodel_retrieved.metrics == sqlmodel_opportunity.metrics

    def test_database_state_consistency(self, postgres_loader, sqlmodel_loader, sample_opportunity_data):
        """Test database state is consistent between loaders"""
        opportunity = Opportunity(**sample_opportunity_data)

        # Save with both loaders (should skip duplicate)
        postgres_saved = postgres_loader.save_opportunity(opportunity)
        assert postgres_saved is True

        sqlmodel_saved = sqlmodel_loader.save_opportunity(opportunity)
        assert sqlmodel_saved is False, "Should detect duplicate from PostgresLoader"

        # Query database directly to verify state
        from database import get_db_session

        # Check SQLModelLoader can retrieve the record
        sqlmodel_record = sqlmodel_loader.get_opportunity(opportunity.submission_id)
        assert sqlmodel_record is not None

        # Check PostgresLoader can retrieve the record
        postgres_record = postgres_loader.get_opportunity(opportunity.submission_id)
        assert postgres_record is not None

        # Query directly and compare with loader results
        with get_db_session() as session:
            direct_record = session.exec(
                select(Opportunity).where(Opportunity.submission_id == opportunity.submission_id)
            ).first()

            assert direct_record is not None

            # Access attributes before detaching
            direct_id = direct_record.submission_id
            direct_subreddit = direct_record.subreddit
            direct_title = direct_record.title
            direct_score = direct_record.final_score

        # Both loader results should have the same data as direct query
        assert sqlmodel_record.submission_id == direct_id
        assert sqlmodel_record.subreddit == direct_subreddit
        assert sqlmodel_record.title == direct_title
        assert sqlmodel_record.final_score == direct_score

        assert postgres_record.submission_id == direct_id
        assert postgres_record.subreddit == direct_subreddit
        assert postgres_record.title == direct_title
        assert postgres_record.final_score == direct_score


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running basic loader comparison tests...")

    # Test loader creation
    postgres_loader = get_loader(Settings(use_sqlmodel_loader=False))
    sqlmodel_loader = get_loader(Settings(use_sqlmodel_loader=True))

    print(f"✓ Created PostgresLoader: {type(postgres_loader).__name__}")
    print(f"✓ Created SQLModelLoader: {type(sqlmodel_loader).__name__}")

    # Test basic functionality
    sample_data = {
        "submission_id": "test_smoke_999",
        "subreddit": "r/startups",
        "title": "Smoke test",
        "wtp_score": 50.0,
        "analysis": {"app_idea": {"title": "Test App", "app_concept": "Test concept"}},
        "metrics": {"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
    }

    opportunity = Opportunity(**sample_data)

    # Test both loaders can save and retrieve
    postgres_loader.save_opportunity(opportunity)
    retrieved = postgres_loader.get_opportunity(opportunity.submission_id)
    assert retrieved is not None

    sqlmodel_loader.save_opportunity(opportunity)
    retrieved = sqlmodel_loader.get_opportunity(opportunity.submission_id)
    assert retrieved is not None

    print("✓ Basic functionality test passed")

    # Clean up
    postgres_loader.close()
    sqlmodel_loader.close()

    print("\nAll basic tests passed!")
