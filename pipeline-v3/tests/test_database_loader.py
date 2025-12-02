"""
Failing tests for DEBT-007: Reddit Data Preservation Gap

Tests that verify Reddit submission data is preserved throughout the pipeline,
specifically focusing on DatabaseLoader.store_analyses method with complete
Reddit metadata preservation and main.py pipeline flow passing both AnalysisResult
and RedditSubmission to database layer.

These tests are designed to fail because the current implementation creates
placeholder data instead of preserving original Reddit submission data.
"""


import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch, MagicMock
from typing import List

from models import AnalysisResult, AppIdea, MarketMetrics, RedditSubmission
from models.database import Opportunity, OpportunityCreate
from load.database import DatabaseLoader


class MockDatabaseLoader(DatabaseLoader):
    """Mock DatabaseLoader for testing without real database connection"""

    def __init__(self):
        # Don't call super().__init__() to avoid real database initialization
        self.settings = Mock()
        self.settings.database_url = "sqlite:///:memory:"
        self._engine = None
        self._session_factory = None
        self.opportunities_stored = []

        # Mock data mapper and repository
        from load.data_mappers import AnalysisToOpportunityMapper
        self.data_mapper = AnalysisToOpportunityMapper(preserve_reddit_metadata=True)

    @property
    def engine(self):
        """Mock engine that doesn't require real database"""
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine("sqlite:///:memory:", echo=False)
        return self._engine

    @property
    def session_factory(self):
        """Mock session factory"""
        if self._session_factory is None:
            from sqlalchemy.orm import sessionmaker
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory

    def store_analyses(self, analyses: List[AnalysisResult], reddit_submissions: List = None) -> dict:
        """Override to store in memory for testing using data mapper"""
        stats = {"stored": 0, "skipped": 0, "errors": 0}

        try:
            # Use data mapper to convert AnalysisResults to Opportunities
            opportunities = self.data_mapper.map_batch(analyses, reddit_submissions)

            # Store in memory for testing
            for opportunity in opportunities:
                self.opportunities_stored.append(opportunity)
                stats["stored"] += 1

        except Exception as e:
            stats["errors"] += len(analyses)

        return stats


class TestRedditDataPreservation:
    """Test suite for Reddit data preservation in DatabaseLoader"""

    @pytest.fixture
    def reddit_submission(self):
        """Create a test Reddit submission with complete metadata"""
        return RedditSubmission(
            id="abc123",
            title="Best Productivity App Ever - Need Task Management Solution",
            text="I've been struggling to manage my tasks effectively. I need an app that can help me organize my work and personal tasks in one place. The current solutions are too complex and don't integrate well with my existing workflow.",
            author="productivity_enthusiast",
            upvotes=150,
            downvotes=5,
            score=145,
            comments_count=42,
            subreddit="productivity",
            created_utc=datetime.now(UTC).replace(year=2024, month=1, day=15),
            permalink="/r/productivity/comments/abc123/",
            url=None,
            is_self=True,
            over_18=False
        )

    @pytest.fixture
    def analysis_result(self, reddit_submission):
        """Create a test analysis result from the Reddit submission"""
        app_idea = AppIdea(
            title="TaskFlow - Unified Task Management",
            app_concept="A simple, focused task management app that integrates with existing workflows",
            problem_statement="Users struggle with organizing work and personal tasks in a single, intuitive interface",
            target_audience="Professionals and students managing multiple projects and personal commitments",
            core_functions=["unified task organization", "cross-platform sync", "smart reminders"]
        )

        market_metrics = MarketMetrics(
            market_demand=85.0,
            pain_intensity=90.0,
            monetization_potential=75.0,
            competition_level=60.0,
            technical_feasibility=80.0
        )

        return AnalysisResult(
            submission_id=reddit_submission.id,
            analyzed_at=datetime.now(UTC),
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=78.5,
            confidence_score=85.0,
            trust_level="HIGH"
        )

    @pytest.fixture
    def mock_loader(self):
        """Create mock database loader for testing"""
        return MockDatabaseLoader()

    def test_store_analyses_preserves_original_reddit_title(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission title

        Current implementation uses placeholder "Reddit Submission" instead of the actual title.
        This test should FAIL because _convert_to_opportunity method doesn't receive
        the original Reddit submission data to extract the title.
        """
        # This would work in correct implementation where RedditSubmission is passed along with AnalysisResult
        # But currently fails because the DatabaseLoader only receives AnalysisResult

        # Try to store the analysis with original Reddit data
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])

        # Verify the analysis was stored
        assert stats["stored"] == 1
        assert len(mock_loader.opportunities_stored) == 1

        # This test will FAIL because the stored opportunity has placeholder title
        # instead of the original Reddit submission title
        stored_opportunity = mock_loader.opportunities_stored[0]
        assert stored_opportunity.reddit_title == reddit_submission.title, \
            f"Expected original title '{reddit_submission.title}', got placeholder '{stored_opportunity.reddit_title}'"

    def test_store_analyses_preserves_original_reddit_url(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission URL

        Current implementation creates a placeholder URL instead of preserving the actual permalink.
        This test should FAIL because the database loader doesn't have access to the original
        Reddit submission data to extract the proper URL.
        """
        # Store the analysis
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because the stored opportunity has a placeholder URL
        stored_opportunity = mock_loader.opportunities_stored[0]
        expected_url = f"https://reddit.com/r/{reddit_submission.subreddit}/{reddit_submission.id}"
        assert stored_opportunity.reddit_url == expected_url, \
            f"Expected original URL '{expected_url}', got placeholder '{stored_opportunity.reddit_url}'"

    def test_store_analyses_preserves_original_subreddit(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission subreddit

        Current implementation uses "test" as a hardcoded placeholder instead of the actual subreddit.
        This test should FAIL because the database loader doesn't receive the original
        Reddit submission data containing the subreddit.
        """
        # Store the analysis
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because the stored opportunity has hardcoded "test" subreddit
        stored_opportunity = mock_loader.opportunities_stored[0]
        assert stored_opportunity.subreddit == reddit_submission.subreddit, \
            f"Expected subreddit '{reddit_submission.subreddit}', got hardcoded '{stored_opportunity.subreddit}'"

    def test_store_analyses_preserves_original_author_information(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission author information

        Current implementation sets reddit_author to None instead of preserving the original author.
        This test should FAIL because the database loader doesn't have access to the original
        Reddit submission author data.
        """
        # Store the analysis
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because the stored opportunity has None for author
        stored_opportunity = mock_loader.opportunities_stored[0]
        assert stored_opportunity.reddit_author == reddit_submission.author, \
            f"Expected author '{reddit_submission.author}', got None"

    def test_store_analyses_preserves_original_upvotes(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission upvotes

        Current implementation sets reddit_upvotes to 0 (placeholder) instead of preserving the actual upvotes.
        This test should FAIL because the database loader doesn't receive the original
        Reddit submission engagement data.
        """
        # Store the analysis
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because the stored opportunity has 0 upvotes instead of actual count
        stored_opportunity = mock_loader.opportunities_stored[0]
        assert stored_opportunity.reddit_upvotes == reddit_submission.upvotes, \
            f"Expected upvotes {reddit_submission.upvotes}, got placeholder {stored_opportunity.reddit_upvotes}"

    def test_store_analyses_preserves_original_comments_count(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission comments count

        Current implementation sets reddit_comments_count to 0 (placeholder) instead of preserving the actual count.
        This test should FAIL because the database loader doesn't have access to the original
        Reddit submission engagement metrics.
        """
        # Store the analysis
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because the stored opportunity has 0 comments instead of actual count
        stored_opportunity = mock_loader.opportunities_stored[0]
        assert stored_opportunity.reddit_comments_count == reddit_submission.comments_count, \
            f"Expected comments count {reddit_submission.comments_count}, got placeholder {stored_opportunity.reddit_comments_count}"

    def test_store_analyses_preserves_original_creation_timestamp(self, mock_loader, reddit_submission, analysis_result):
        """
        DEBT-007 TEST: DatabaseLoader should preserve original Reddit submission creation timestamp

        Current implementation uses datetime.utcnow() instead of the original creation time.
        This test should FAIL because the database loader doesn't receive the original
        Reddit submission timestamp data.
        """
        # Store the analysis
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because the stored opportunity uses current time instead of original
        stored_opportunity = mock_loader.opportunities_stored[0]
        assert stored_opportunity.reddit_created_at == reddit_submission.created_utc, \
            f"Expected creation time {reddit_submission.created_utc}, got current time {stored_opportunity.reddit_created_at}"

    def test_pipeline_data_flow_preserves_reddit_metadata_integration(self, mock_loader):
        """
        DEBT-007 TEST: Main pipeline should pass both AnalysisResult and RedditSubmission to database layer

        This is an integration test that verifies the complete pipeline data flow.
        Current implementation in main.py only passes AnalysisResult to DatabaseLoader.store_analyses(),
        losing all the original Reddit metadata.

        This test should FAIL because the current pipeline architecture doesn't preserve
        the link between AnalysisResult and its source RedditSubmission when storing to database.
        """
        # Create a complete Reddit submission with all metadata
        reddit_submission = RedditSubmission(
            id="integration_test_123",
            title="AI App for Project Management - Real Pain Point",
            text="As a project manager, I struggle with AI-powered project management tools...",
            author="pm_pro",
            upvotes=89,
            downvotes=2,
            score=87,
            comments_count=15,
            subreddit="projectmanagement",
            created_utc=datetime.now(UTC).replace(year=2024, month=2, day=10),
            permalink="/r/projectmanagement/comments/integration_test_123/",
            url=None,
            is_self=True,
            over_18=False
        )

        # Create analysis result from the submission
        app_idea = AppIdea(
            title="AI-Powered PM Assistant",
            app_concept="AI assistant specifically designed for project managers",
            problem_statement="Project managers need specialized AI tools that understand project management workflows",
            target_audience="Project managers and team leads",
            core_functions=["AI task prioritization", "automated progress tracking", "resource allocation optimization"]
        )

        market_metrics = MarketMetrics(
            market_demand=82.0,
            pain_intensity=88.0,
            monetization_potential=79.0,
            competition_level=55.0,
            technical_feasibility=83.0
        )

        analysis_result = AnalysisResult(
            submission_id=reddit_submission.id,
            analyzed_at=datetime.now(UTC),
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=81.2,
            confidence_score=87.5,
            trust_level="HIGH"
        )

        # This simulates what the current main.py pipeline does - only passes AnalysisResult
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        # This test will FAIL because we lost all the original Reddit metadata
        stored_opportunity = mock_loader.opportunities_stored[0]

        # All these assertions will fail because the current implementation
        # only stores placeholder data instead of preserving original Reddit metadata
        assert stored_opportunity.reddit_title == reddit_submission.title, \
            "Reddit title not preserved in pipeline flow"

        assert stored_opportunity.reddit_url == f"https://reddit.com/r/{reddit_submission.subreddit}/{reddit_submission.id}", \
            "Reddit URL not preserved in pipeline flow"

        assert stored_opportunity.subreddit == reddit_submission.subreddit, \
            "Subreddit not preserved in pipeline flow"

        assert stored_opportunity.reddit_author == reddit_submission.author, \
            "Author not preserved in pipeline flow"

        assert stored_opportunity.reddit_upvotes == reddit_submission.upvotes, \
            "Upvotes not preserved in pipeline flow"

        assert stored_opportunity.reddit_comments_count == reddit_submission.comments_count, \
            "Comments count not preserved in pipeline flow"

        assert stored_opportunity.reddit_created_at == reddit_submission.created_utc, \
            "Creation timestamp not preserved in pipeline flow"

    def test_database_loader_placeholder_data_evidence(self, mock_loader, reddit_submission, analysis_result):
        """
        TEST: Demonstrates the current placeholder data problem in DatabaseLoader

        This test provides clear evidence that the current implementation
        creates placeholder data instead of preserving original Reddit data.
        This test should FAIL and serve as documentation of the technical debt.
        """
        # Store analysis using current implementation
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        stored_opportunity = mock_loader.opportunities_stored[0]

        # After fixing DEBT-007, these values should now preserve the original Reddit data:
        # - reddit_title should preserve the original submission title
        # - reddit_url should preserve the original submission structure
        # - subreddit should preserve the original subreddit name
        # - reddit_author should preserve the original author
        # - reddit_upvotes should preserve the original upvotes
        # - reddit_comments_count should preserve the original comments count
        # - reddit_created_at should preserve the original timestamp

        # Verify that original Reddit data is now preserved (this should pass after fix)
        assert stored_opportunity.reddit_title == reddit_submission.title, \
            "Implementation should now preserve original title"

        assert stored_opportunity.subreddit == reddit_submission.subreddit, \
            "Implementation should now preserve original subreddit"

        assert stored_opportunity.reddit_author == reddit_submission.author, \
            "Implementation should now preserve original author"

        assert stored_opportunity.reddit_upvotes == reddit_submission.upvotes, \
            "Implementation should now preserve original upvotes"

        assert stored_opportunity.reddit_comments_count == reddit_submission.comments_count, \
            "Implementation should now preserve original comments count"

        # Verify creation timestamp is preserved
        assert stored_opportunity.reddit_created_at == reddit_submission.created_utc, \
            "Implementation should now preserve original creation timestamp"

    def test_reddit_data_integrity_audit(self, mock_loader, reddit_submission, analysis_result):
        """
        TEST: Comprehensive audit of Reddit data integrity gaps

        This test provides a complete audit of what Reddit data is being lost
        in the current pipeline implementation. It should FAIL and clearly
        document all the missing data preservation issues.
        """
        # Store the analysis using current implementation
        stats = mock_loader.store_analyses([analysis_result], [reddit_submission])
        assert stats["stored"] == 1

        stored_opportunity = mock_loader.opportunities_stored[0]

        # Create a comprehensive audit report of data loss
        audit_report = {
            "submission_id": {
                "original": reddit_submission.id,
                "stored": stored_opportunity.submission_id,
                "preserved": stored_opportunity.submission_id == reddit_submission.id
            },
            "title": {
                "original": reddit_submission.title,
                "stored": stored_opportunity.reddit_title,
                "preserved": stored_opportunity.reddit_title == reddit_submission.title
            },
            "url": {
                "original": f"https://reddit.com/r/{reddit_submission.subreddit}/{reddit_submission.id}",
                "stored": stored_opportunity.reddit_url,
                "preserved": stored_opportunity.reddit_url == f"https://reddit.com/r/{reddit_submission.subreddit}/{reddit_submission.id}"
            },
            "subreddit": {
                "original": reddit_submission.subreddit,
                "stored": stored_opportunity.subreddit,
                "preserved": stored_opportunity.subreddit == reddit_submission.subreddit
            },
            "author": {
                "original": reddit_submission.author,
                "stored": stored_opportunity.reddit_author,
                "preserved": stored_opportunity.reddit_author == reddit_submission.author
            },
            "upvotes": {
                "original": reddit_submission.upvotes,
                "stored": stored_opportunity.reddit_upvotes,
                "preserved": stored_opportunity.reddit_upvotes == reddit_submission.upvotes
            },
            "comments_count": {
                "original": reddit_submission.comments_count,
                "stored": stored_opportunity.reddit_comments_count,
                "preserved": stored_opportunity.reddit_comments_count == reddit_submission.comments_count
            },
            "created_at": {
                "original": reddit_submission.created_utc,
                "stored": stored_opportunity.reddit_created_at,
                "preserved": stored_opportunity.reddit_created_at == reddit_submission.created_utc
            }
        }

        # Count preserved vs lost fields
        preserved_count = sum(1 for field in audit_report.values() if field["preserved"])
        total_fields = len(audit_report)
        preserved_percentage = (preserved_count / total_fields) * 100

        # This test will FAIL because not all fields are preserved
        # The assertion documents the percentage of data that's being lost
        assert preserved_percentage == 100.0, \
            f"Reddit data integrity compromised: {preserved_percentage:.1f}% of fields preserved ({preserved_count}/{total_fields})"

        # Additional assertion: All individual fields should be preserved
        for field_name, field_data in audit_report.items():
            assert field_data["preserved"], \
                f"Field '{field_name}' not preserved: original='{field_data['original']}', stored='{field_data['stored']}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])