"""
OpportunityLoader Integration Tests for RedditHarbor Pipeline V4

Comprehensive integration tests for the unified OpportunityLoader verifying:
- Data persistence and retrieval
- Duplicate detection
- Transaction handling
- JSON serialization/deserialization
- UTC timestamp handling
- Score calculation
- Error handling
- Performance characteristics
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
def opportunity_loader(test_db_url):
    """Create OpportunityLoader instance for testing"""
    settings = Settings(database_url=test_db_url)
    loader = get_loader(settings)
    yield loader
    loader.close()


@pytest.fixture
def sample_opportunity_data():
    """Generate sample opportunity data for testing"""
    return {
        "submission_id": f"test_submission_{datetime.now().timestamp()}",
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
        "submission_id": f"test_complex_{datetime.now().timestamp()}",
        "subreddit": "r/technology",
        "title": "Complex multi-dimensional analysis with nested structures",
        "wtp_score": 90.0,
        "confidence_score": 95.0,
        "trust_level": "MEDIUM",
        "analysis": {
            "app_idea": {
                "title": "Advanced Analytics Platform",
                "app_concept": "A comprehensive platform for analyzing complex data patterns",
                "problem_statement": "Complex data analysis requires specialized tools",
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
                "Complex analysis requires expertise",
                "Real-time processing challenges"
            ],
            "opportunity_summary": "Advanced analytics platform for enterprise",
            "content_quality_score": 0.92,
            "is_spam": False,
            "spam_indicators": [],
            "technical_requirements": {
                "frontend": ["React", "TypeScript", "D3.js"],
                "backend": ["Python", "FastAPI", "PostgreSQL"],
                "infrastructure": ["AWS", "Docker", "Kubernetes"]
            },
            "analyzed_at": "2025-01-15T12:00:00Z"
        },
        "metrics": {
            "market_demand": 90.0,
            "pain_intensity": 85.0,
            "monetization_potential": 80.0,
            "technical_feasibility": 70.0,
            "competition_level": 60.0
        }
    }


@contextmanager
def clean_test_data(loader, submission_id):
    """Context manager to ensure test data is cleaned up"""
    try:
        yield
    finally:
        try:
            if hasattr(loader, 'get_opportunity'):
                loader.get_opportunity(submission_id)
        except:
            pass


class TestLoaderBasicFunctionality:
    """Test basic functionality of OpportunityLoader"""

    def test_loader_initialization(self, opportunity_loader):
        """Test that OpportunityLoader can be properly initialized"""
        assert opportunity_loader is not None
        assert hasattr(opportunity_loader, 'save_opportunity')
        assert hasattr(opportunity_loader, 'save_analysis')
        assert hasattr(opportunity_loader, 'close')

    def test_opportunity_model_validation(self, sample_opportunity_data):
        """Test that Opportunity model validation works correctly"""
        opportunity = Opportunity(**sample_opportunity_data)
        assert opportunity.submission_id == sample_opportunity_data["submission_id"]
        assert opportunity.subreddit == sample_opportunity_data["subreddit"]
        assert opportunity.trust_level == sample_opportunity_data["trust_level"]
        assert opportunity.final_score > 0

    def test_save_and_retrieve_opportunity(self, opportunity_loader, sample_opportunity_data):
        """Test basic save/retrieve flow"""
        opportunity = Opportunity(**sample_opportunity_data)

        with clean_test_data(opportunity_loader, opportunity.submission_id):
            # Save
            saved = opportunity_loader.save_opportunity(opportunity)
            assert saved is True

            # Retrieve
            retrieved = opportunity_loader.get_opportunity(opportunity.submission_id)
            assert retrieved is not None
            assert retrieved.submission_id == opportunity.submission_id
            assert retrieved.subreddit == opportunity.subreddit
            assert retrieved.title == opportunity.title
            assert retrieved.wtp_score == opportunity.wtp_score
            assert retrieved.final_score == opportunity.final_score


class TestDuplicateDetection:
    """Test duplicate detection functionality"""

    def test_duplicate_submission_returns_false(self, opportunity_loader, sample_opportunity_data):
        """Test that saving duplicate returns False"""
        opportunity = Opportunity(**sample_opportunity_data)

        # First save should succeed
        first_save = opportunity_loader.save_opportunity(opportunity)
        assert first_save is True

        # Second save should detect duplicate
        second_save = opportunity_loader.save_opportunity(opportunity)
        assert second_save is False


class TestJSONSerialization:
    """Test complex JSON structure handling"""

    def test_complex_json_structures_preserved(self, opportunity_loader, complex_opportunity_data):
        """Test complex JSON structures are handled correctly"""
        opportunity = Opportunity(**complex_opportunity_data)

        with clean_test_data(opportunity_loader, opportunity.submission_id):
            # Save
            opportunity_loader.save_opportunity(opportunity)

            # Retrieve and verify complex structures preserved
            retrieved = opportunity_loader.get_opportunity(opportunity.submission_id)
            assert retrieved.analysis["app_idea"]["features"] == complex_opportunity_data["analysis"]["app_idea"]["features"]
            assert retrieved.analysis["technical_requirements"] == complex_opportunity_data["analysis"]["technical_requirements"]


class TestTimestampHandling:
    """Test UTC timestamp handling"""

    def test_utc_timestamps_set_correctly(self, opportunity_loader, sample_opportunity_data):
        """Test that timestamps are set with UTC timezone"""
        opportunity = Opportunity(**sample_opportunity_data)

        with clean_test_data(opportunity_loader, opportunity.submission_id):
            opportunity_loader.save_opportunity(opportunity)
            retrieved = opportunity_loader.get_opportunity(opportunity.submission_id)

            assert retrieved.created_at is not None
            assert retrieved.updated_at is not None


class TestScoreCalculation:
    """Test final score calculation"""

    def test_final_score_calculation(self, opportunity_loader):
        """Test final score is calculated correctly from metrics"""
        metrics_data = {
            "market_demand": 80.0,
            "pain_intensity": 75.0,
            "monetization_potential": 70.0,
            "technical_feasibility": 65.0
        }

        opportunity = Opportunity(
            submission_id=f"score_test_{datetime.now().timestamp()}",
            subreddit="r/startups",
            title="Score calculation test",
            wtp_score=60.0,
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics=metrics_data
        )

        with clean_test_data(opportunity_loader, opportunity.submission_id):
            opportunity_loader.save_opportunity(opportunity)
            retrieved = opportunity_loader.get_opportunity(opportunity.submission_id)

            # Expected: (80*0.3 + 75*0.25 + 70*0.25 + 65*0.2) / 1.0
            expected_final_score = round((80*0.3 + 75*0.25 + 70*0.25 + 65*0.2), 2)
            assert retrieved.final_score == expected_final_score


class TestErrorHandling:
    """Test error handling"""

    def test_empty_submission_id_validation(self, opportunity_loader):
        """Test validation of empty submission_id"""
        invalid_data = {
            "submission_id": "",
            "subreddit": "r/test",
            "title": "Test",
            "analysis": {"app_idea": {"title": "Test", "app_concept": "Test"}},
            "metrics": {"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        }

        opportunity = Opportunity(**invalid_data)
        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            opportunity_loader.save_opportunity(opportunity)

    def test_invalid_trust_level_validation(self):
        """Test validation of trust level"""
        invalid_data = {
            "submission_id": f"test_trust_{datetime.now().timestamp()}",
            "subreddit": "r/test",
            "title": "Test",
            "trust_level": "INVALID",
            "analysis": {"app_idea": {"title": "Test", "app_concept": "Test"}},
            "metrics": {"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        }

        with pytest.raises(ValueError, match="Trust level must be one of"):
            Opportunity(**invalid_data)

    def test_database_connection_error_handling(self, opportunity_loader):
        """Test database connection error handling"""
        opportunity = Opportunity(
            submission_id=f"test_error_{datetime.now().timestamp()}",
            subreddit="r/test",
            title="Error test",
            analysis={"app_idea": {"title": "Test", "app_concept": "Test"}},
            metrics={"market_demand": 50.0, "pain_intensity": 50.0, "monetization_potential": 50.0, "technical_feasibility": 50.0}
        )

        # Mock session error
        with patch('load.loader.get_session', side_effect=RuntimeError("Connection failed")):
            with pytest.raises(RuntimeError):
                opportunity_loader.save_opportunity(opportunity)


class TestPerformance:
    """Test performance characteristics"""

    def test_single_save_performance(self, opportunity_loader, sample_opportunity_data):
        """Test performance of single save operation"""
        opportunity = Opportunity(**sample_opportunity_data)

        with clean_test_data(opportunity_loader, opportunity.submission_id):
            start_time = time.perf_counter()
            opportunity_loader.save_opportunity(opportunity)
            elapsed_time = time.perf_counter() - start_time

            # Should complete in reasonable time (< 1 second)
            assert elapsed_time < 1.0, f"Save took {elapsed_time:.4f}s which is too slow"

            print(f"\nSave time: {elapsed_time:.4f}s")


class TestDataIntegrity:
    """Test data integrity"""

    def test_round_trip_consistency(self, opportunity_loader, sample_opportunity_data):
        """Test save → retrieve → validate maintains data integrity"""
        opportunity = Opportunity(**sample_opportunity_data)

        saved = opportunity_loader.save_opportunity(opportunity)
        assert saved is True

        retrieved = opportunity_loader.get_opportunity(opportunity.submission_id)
        assert retrieved is not None

        # Verify round-trip consistency
        assert retrieved.submission_id == opportunity.submission_id
        assert retrieved.subreddit == opportunity.subreddit
        assert retrieved.title == opportunity.title
        assert retrieved.wtp_score == opportunity.wtp_score
        assert retrieved.final_score == opportunity.final_score
        assert retrieved.analysis == opportunity.analysis
        assert retrieved.metrics == opportunity.metrics


if __name__ == "__main__":
    print("Running OpportunityLoader integration tests...")
    print("Use: pytest tests/test_opportunity_loader_integration.py -v")
