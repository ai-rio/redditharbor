"""
Comprehensive tests for PipelineOrchestrator quality filtering functionality
"""

import logging
import time
from datetime import UTC, datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission

# Import the classes we need to test
from orchestration.pipeline_orchestrator import (
    PipelineConfiguration,
    PipelineOrchestrator,
    PipelineResults,
)


class TestPipelineOrchestratorQualityFiltering:
    """Comprehensive test suite for _filter_by_quality method"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock PipelineOrchestrator for testing"""
        mock_reddit_client = Mock()
        mock_analyzer_factory = Mock()
        mock_database_loader = Mock()
        mock_validator = Mock()
        mock_staging_layer = Mock()
        mock_settings = Mock()

        orchestrator = PipelineOrchestrator(
            reddit_client=mock_reddit_client,
            analyzer_factory=mock_analyzer_factory,
            database_loader=mock_database_loader,
            validator=mock_validator,
            staging_layer=mock_staging_layer,
            settings=mock_settings
        )
        return orchestrator

    @pytest.fixture
    def sample_analyses(self) -> list[AnalysisResult]:
        """Create comprehensive sample analysis results for testing"""
        results = []

        # High quality analysis (should pass all filters)
        high_quality = AnalysisResult.model_construct(
            submission_id="high_quality_1",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Task Manager Pro",
                app_concept="A smart task management app that prioritizes work automatically",
                problem_statement="People struggle with managing their daily tasks efficiently",
                core_functions=["Automatic prioritization", "Smart reminders", "Progress tracking"],
                target_audience="Busy professionals and students"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=85.0,
                pain_intensity=90.0,
                monetization_potential=80.0,
                competition_level=40.0,
                technical_feasibility=85.0
            ),
            final_score=85.0,
            content_quality_score=90.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=85.0,
            trust_level="HIGH"
        )
        results.append(high_quality)

        # Spam analysis (should be filtered out)
        spam_analysis = AnalysisResult.model_construct(
            submission_id="spam_1",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Get Rich Quick",
                app_concept="Make money fast with our revolutionary financial system",
                problem_statement="People need more money quickly",
                core_functions=["Quick profits"],
                target_audience="Everyone looking for money"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=95.0,
                pain_intensity=85.0,
                monetization_potential=95.0,
                competition_level=10.0,
                technical_feasibility=90.0
            ),
            final_score=95.0,
            content_quality_score=20.0,
            is_spam=True,
            spam_indicators=["clickbait", "unrealistic promises"],
            confidence_score=60.0,
            trust_level="LOW"
        )
        results.append(spam_analysis)

        # Low quality content (should be filtered out)
        low_quality = AnalysisResult.model_construct(
            submission_id="low_quality_1",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Simple App",
                app_concept="An app that does stuff",
                problem_statement="Some problem exists",
                core_functions=["Basic function"],
                target_audience="Users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=30.0,
                pain_intensity=25.0,
                monetization_potential=20.0,
                competition_level=80.0,
                technical_feasibility=30.0
            ),
            final_score=25.0,
            content_quality_score=35.0,  # Below 40 threshold
            is_spam=False,
            spam_indicators=[],
            confidence_score=30.0,
            trust_level="LOW"
        )
        results.append(low_quality)

        # Below min_score threshold
        low_score = AnalysisResult.model_construct(
            submission_id="low_score_1",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Average App",
                app_concept="A mediocre app idea",
                problem_statement="Minor inconvenience",
                core_functions=["Basic feature"],
                target_audience="Small group"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=35.0,
                pain_intensity=30.0,
                monetization_potential=25.0,
                competition_level=75.0,
                technical_feasibility=40.0
            ),
            final_score=30.0,  # Below default min_score of 50.0
            content_quality_score=60.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=55.0,  # Above min_confidence
            trust_level="MEDIUM"
        )
        results.append(low_score)

        # Below min_confidence threshold
        low_confidence = AnalysisResult.model_construct(
            submission_id="low_confidence_1",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Uncertain App",
                app_concept="An app with unclear value proposition",
                problem_statement="Some unclear problem exists",
                core_functions=["Vague function"],
                target_audience="Unknown target users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=60.0,
                pain_intensity=55.0,
                monetization_potential=50.0,
                competition_level=50.0,
                technical_feasibility=60.0
            ),
            final_score=60.0,  # Above min_score
            content_quality_score=70.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=35.0,  # Below min_confidence
            trust_level="LOW"
        )
        results.append(low_confidence)

        # Borderline cases
        borderline_quality = AnalysisResult.model_construct(
            submission_id="borderline_quality",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Borderline App",
                app_concept="An app that barely meets quality standards",
                problem_statement="Minor but real problem",
                core_functions=["Basic function"],
                target_audience="Specific users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=45.0,
                pain_intensity=42.0,
                monetization_potential=40.0,
                competition_level=60.0,
                technical_feasibility=50.0
            ),
            final_score=45.0,
            content_quality_score=40.0,  # Exactly at threshold
            is_spam=False,
            spam_indicators=[],
            confidence_score=45.0,
            trust_level="MEDIUM"
        )
        results.append(borderline_quality)

        return results

    def test_filter_by_quality_comprehensive_functionality(self, mock_orchestrator, sample_analyses):
        """Test comprehensive quality filtering with all filter types"""
        config = PipelineConfiguration(
            min_score=50.0,
            min_confidence=50.0
        )

        result = mock_orchestrator._filter_by_quality(sample_analyses, config)

        # Should return only high-quality analysis
        assert len(result['filtered_analyses']) == 1
        assert result['filtered_analyses'][0].submission_id == "high_quality_1"

        # Check filtering statistics
        stats = result['statistics']
        assert stats['total_input'] == 6
        assert stats['spam_filtered'] == 1
        assert stats['low_quality_filtered'] == 1
        assert stats['below_min_score_filtered'] == 2  # low_score and borderline_quality
        assert stats['below_min_confidence_filtered'] == 1
        assert stats['total_filtered'] == 5
        assert stats['final_count'] == 1

    def test_filter_by_quality_spam_priority(self, mock_orchestrator):
        """Test that spam filtering takes priority over other filters"""
        # Create spam analysis with high scores
        spam_with_high_scores = AnalysisResult.model_construct(
            submission_id="spam_high_scores",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Amazing App",
                app_concept="Incredible solution",
                problem_statement="Urgent problem",
                core_functions=["Magic function"],
                target_audience="Everyone"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=95.0,
                pain_intensity=95.0,
                monetization_potential=95.0,
                competition_level=5.0,
                technical_feasibility=95.0
            ),
            final_score=95.0,  # High score
            content_quality_score=50.0,  # Above low quality threshold
            is_spam=True,  # But it's spam
            spam_indicators=["too good to be true"],
            confidence_score=90.0,  # High confidence
            trust_level="HIGH"
        )

        config = PipelineConfiguration(
            min_score=50.0,
            min_confidence=50.0
        )

        result = mock_orchestrator._filter_by_quality([spam_with_high_scores], config)

        # Should be filtered out due to spam, despite high scores
        assert len(result['filtered_analyses']) == 0
        assert result['statistics']['spam_filtered'] == 1
        assert result['statistics']['below_min_score_filtered'] == 0
        assert result['statistics']['below_min_confidence_filtered'] == 0

    def test_filter_by_quality_empty_input(self, mock_orchestrator):
        """Test filtering with empty input list"""
        config = PipelineConfiguration()

        result = mock_orchestrator._filter_by_quality([], config)

        assert result['filtered_analyses'] == []
        assert result['statistics']['total_input'] == 0
        assert result['statistics']['final_count'] == 0
        assert result['statistics']['total_filtered'] == 0

    def test_filter_by_quality_all_spam(self, mock_orchestrator):
        """Test filtering when all analyses are spam"""
        spam_analyses = []
        for i in range(5):
            spam_analysis = AnalysisResult.model_construct(
                submission_id=f"spam_{i}",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"Spam App {i}",
                    app_concept="Spam concept",
                    problem_statement="Fake problem",
                    core_functions=["Spam function"],
                    target_audience="Everyone"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=30.0,
                is_spam=True,
                spam_indicators=["spam"],
                confidence_score=50.0,
                trust_level="LOW"
            )
            spam_analyses.append(spam_analysis)

        config = PipelineConfiguration()
        result = mock_orchestrator._filter_by_quality(spam_analyses, config)

        assert len(result['filtered_analyses']) == 0
        assert result['statistics']['spam_filtered'] == 5
        assert result['statistics']['final_count'] == 0

    def test_filter_by_quality_all_high_quality(self, mock_orchestrator):
        """Test filtering when all analyses are high quality"""
        high_quality_analyses = []
        for i in range(5):
            high_quality = AnalysisResult.model_construct(
                submission_id=f"high_quality_{i}",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"Quality App {i}",
                    app_concept="High quality concept",
                    problem_statement="Real problem",
                    core_functions=["Quality function"],
                    target_audience="Specific audience"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=80.0,
                    pain_intensity=80.0,
                    monetization_potential=80.0,
                    competition_level=30.0,
                    technical_feasibility=80.0
                ),
                final_score=80.0,
                content_quality_score=85.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=80.0,
                trust_level="HIGH"
            )
            high_quality_analyses.append(high_quality)

        config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)
        result = mock_orchestrator._filter_by_quality(high_quality_analyses, config)

        assert len(result['filtered_analyses']) == 5
        assert result['statistics']['total_filtered'] == 0
        assert result['statistics']['final_count'] == 5

    def test_filter_by_quality_custom_thresholds(self, mock_orchestrator, sample_analyses):
        """Test filtering with custom thresholds"""
        # Very high thresholds - should filter most analyses
        config = PipelineConfiguration(
            min_score=90.0,
            min_confidence=90.0
        )

        result = mock_orchestrator._filter_by_quality(sample_analyses, config)

        # Only the spam analysis with 95 score and 90 confidence might pass
        # but it should be filtered by spam first
        assert len(result['filtered_analyses']) == 0

    def test_filter_by_quality_zero_thresholds(self, mock_orchestrator, sample_analyses):
        """Test filtering with zero thresholds (should only filter spam and low quality)"""
        config = PipelineConfiguration(
            min_score=0.0,
            min_confidence=0.0
        )

        result = mock_orchestrator._filter_by_quality(sample_analyses, config)

        # Should only filter spam and low quality (below 40)
        assert len(result['filtered_analyses']) == 4  # All except spam and low_quality
        assert result['statistics']['spam_filtered'] == 1
        assert result['statistics']['low_quality_filtered'] == 1
        assert result['statistics']['below_min_score_filtered'] == 0
        assert result['statistics']['below_min_confidence_filtered'] == 0

    def test_filter_by_quality_statistics_structure(self, mock_orchestrator, sample_analyses):
        """Test that statistics contain all expected fields"""
        config = PipelineConfiguration()
        result = mock_orchestrator._filter_by_quality(sample_analyses, config)

        stats = result['statistics']
        expected_keys = [
            'total_input',
            'spam_filtered',
            'low_quality_filtered',
            'below_min_score_filtered',
            'below_min_confidence_filtered',
            'total_filtered',
            'final_count',
            'filtering_criteria',
            'filtered_items',
            'filtering_percentages'
        ]

        for key in expected_keys:
            assert key in stats, f"Missing statistics key: {key}"

        # Check filtering criteria
        criteria = stats['filtering_criteria']
        assert criteria['min_score'] == 0.0  # Default value
        assert criteria['min_confidence'] == 40.0  # Default value
        assert criteria['content_quality_threshold'] == 40
        assert criteria['spam_detection_enabled'] is True

        # Check filtering percentages
        percentages = stats['filtering_percentages']
        assert 'pass_rate_percentage' in percentages
        assert 'spam_percentage' in percentages
        assert 'low_quality_percentage' in percentages

    def test_filter_by_quality_filtering_reasons(self, mock_orchestrator, sample_analyses):
        """Test that filtering reasons are properly tracked"""
        config = PipelineConfiguration()
        result = mock_orchestrator._filter_by_quality(sample_analyses, config)

        filtered_items = result['statistics']['filtered_items']

        # Check that we have reasons for each filtered category
        assert 'spam' in filtered_items
        assert 'low_quality' in filtered_items
        assert 'below_score' in filtered_items
        assert 'below_confidence' in filtered_items

        # Check spam filtering reasons
        spam_items = filtered_items['spam']
        assert len(spam_items) == 1
        assert spam_items[0]['submission_id'] == 'spam_1'
        assert 'spam_indicators' in spam_items[0]

        # Check low quality filtering reasons
        low_quality_items = filtered_items['low_quality']
        assert len(low_quality_items) == 1
        assert low_quality_items[0]['submission_id'] == 'low_quality_1'
        assert 'content_quality_score' in low_quality_items[0]

    def test_filter_by_quality_boundary_values(self, mock_orchestrator):
        """Test filtering with boundary values"""
        boundary_analyses = []

        # Exactly at content quality threshold (40) - should pass
        at_quality_threshold = AnalysisResult.model_construct(
            submission_id="quality_boundary",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Boundary Quality App",
                app_concept="Exactly at quality threshold",
                problem_statement="Real problem",
                core_functions=["Function"],
                target_audience="Users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=60.0,
                pain_intensity=60.0,
                monetization_potential=60.0,
                competition_level=50.0,
                technical_feasibility=60.0
            ),
            final_score=60.0,
            content_quality_score=40.0,  # Exactly at threshold
            is_spam=False,
            spam_indicators=[],
            confidence_score=60.0,
            trust_level="MEDIUM"
        )
        boundary_analyses.append(at_quality_threshold)

        # Just below content quality threshold (39.9) - should be filtered
        below_quality_threshold = AnalysisResult.model_construct(
            submission_id="below_quality_boundary",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea.model_construct(
                title="Below Quality App",
                app_concept="Just below quality threshold",
                problem_statement="Real problem",
                core_functions=["Function"],
                target_audience="Users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=60.0,
                pain_intensity=60.0,
                monetization_potential=60.0,
                competition_level=50.0,
                technical_feasibility=60.0
            ),
            final_score=60.0,
            content_quality_score=39.9,  # Just below threshold
            is_spam=False,
            spam_indicators=[],
            confidence_score=60.0,
            trust_level="MEDIUM"
        )
        boundary_analyses.append(below_quality_threshold)

        config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)
        result = mock_orchestrator._filter_by_quality(boundary_analyses, config)

        # Should only pass the analysis exactly at threshold
        assert len(result['filtered_analyses']) == 1
        assert result['filtered_analyses'][0].submission_id == "quality_boundary"
        assert result['statistics']['low_quality_filtered'] == 1

    def test_filter_by_quality_logging_behavior(self, mock_orchestrator, sample_analyses):
        """Test that appropriate logging occurs during filtering"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)
            result = mock_orchestrator._filter_by_quality(sample_analyses, config)

            # Verify that logger methods were called
            assert mock_logger.info.called
            assert mock_logger.debug.called

            # Check that comprehensive logging occurred
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]

            # Should log filtering start and completion
            assert any('Starting quality filtering' in call for call in info_calls)
            assert any('Quality filtering complete' in call for call in info_calls)

    def test_filter_by_quality_large_dataset_performance(self, mock_orchestrator):
        """Test filtering performance with large dataset"""
        # Create 1000 analyses
        large_dataset = []
        for i in range(1000):
            if i % 4 == 0:
                # 25% spam
                analysis = AnalysisResult.model_construct(
                    submission_id=f"spam_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"Spam {i}",
                        app_concept="Spam concept",
                        problem_statement="Fake problem",
                        core_functions=["Function"],
                        target_audience="Users"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                        competition_level=50.0, technical_feasibility=50.0
                    ),
                    final_score=50.0, content_quality_score=30.0, is_spam=True,
                    spam_indicators=["spam"], confidence_score=50.0, trust_level="LOW"
                )
            elif i % 4 == 1:
                # 25% low quality
                analysis = AnalysisResult.model_construct(
                    submission_id=f"low_quality_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"Low Quality {i}",
                        app_concept="Low quality concept",
                        problem_statement="Real problem",
                        core_functions=["Function"],
                        target_audience="Users"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=30.0, pain_intensity=25.0, monetization_potential=20.0,
                        competition_level=80.0, technical_feasibility=30.0
                    ),
                    final_score=25.0, content_quality_score=35.0, is_spam=False,
                    spam_indicators=[], confidence_score=30.0, trust_level="LOW"
                )
            else:
                # 50% high quality
                analysis = AnalysisResult.model_construct(
                    submission_id=f"high_quality_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"High Quality {i}",
                        app_concept="High quality concept",
                        problem_statement="Real problem",
                        core_functions=["Function"],
                        target_audience="Users"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=80.0, pain_intensity=80.0, monetization_potential=80.0,
                        competition_level=30.0, technical_feasibility=80.0
                    ),
                    final_score=80.0, content_quality_score=85.0, is_spam=False,
                    spam_indicators=[], confidence_score=80.0, trust_level="HIGH"
                )
            large_dataset.append(analysis)

        config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)

        start_time = time.time()
        result = mock_orchestrator._filter_by_quality(large_dataset, config)
        end_time = time.time()

        # Performance assertion - should complete within reasonable time
        processing_time = end_time - start_time
        assert processing_time < 5.0, f"Filtering took too long: {processing_time:.2f}s"

        # Correctness assertions
        assert result['statistics']['total_input'] == 1000
        assert result['statistics']['spam_filtered'] == 250
        assert result['statistics']['low_quality_filtered'] == 250
        assert result['statistics']['final_count'] == 500  # Only high quality analyses


class TestPipelineOrchestratorIntegration:
    """Integration tests for PipelineOrchestrator with quality filtering"""

    @pytest.fixture
    def mock_orchestrator_with_dependencies(self):
        """Create orchestrator with fully mocked dependencies"""
        mock_reddit_client = Mock()
        mock_analyzer = Mock()
        mock_analyzer_factory = Mock(return_value=mock_analyzer)
        mock_database_loader = Mock()
        mock_validator = Mock()
        mock_staging_layer = Mock()
        mock_settings = Mock()
        mock_settings.default_subreddits = ["test", "productivity"]
        mock_settings.batch_size = 10

        orchestrator = PipelineOrchestrator(
            reddit_client=mock_reddit_client,
            analyzer_factory=mock_analyzer_factory,
            database_loader=mock_database_loader,
            validator=mock_validator,
            staging_layer=mock_staging_layer,
            settings=mock_settings
        )

        # Mock the test_connection methods
        mock_reddit_client.test_connection.return_value = True
        mock_analyzer.test_connection.return_value = True
        mock_database_loader.test_connection.return_value = True

        return orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator

    @pytest.fixture
    def sample_submissions(self) -> list[RedditSubmission]:
        """Create sample Reddit submissions"""
        return [
            RedditSubmission(
                id="test_1",
                title="Need help with task management",
                text="I'm looking for a better way to manage my tasks",
                author="user1",
                upvotes=50,
                score=50,
                comments_count=20,
                subreddit="productivity",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/productivity/test_1"
            ),
            RedditSubmission(
                id="test_2",
                title="Project management software recommendations",
                text="What software do you recommend for managing projects?",
                author="user2",
                upvotes=30,
                score=30,
                comments_count=15,
                subreddit="productivity",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/productivity/test_2"
            )
        ]

    @pytest.fixture
    def sample_analyses(self) -> list[AnalysisResult]:
        """Create sample analysis results"""
        return [
            AnalysisResult.model_construct(
                submission_id="test_1",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title="Task Manager Pro",
                    app_concept="Smart task management app",
                    problem_statement="People struggle with task organization",
                    core_functions=["Task prioritization", "Smart reminders"],
                    target_audience="Professionals"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=80.0, pain_intensity=85.0, monetization_potential=75.0,
                    competition_level=40.0, technical_feasibility=80.0
                ),
                final_score=80.0,
                content_quality_score=85.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=80.0,
                trust_level="HIGH"
            ),
            AnalysisResult.model_construct(
                submission_id="test_2",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title="Project Tracker",
                    app_concept="Collaborative project management",
                    problem_statement="Teams struggle with coordination",
                    core_functions=["Team collaboration", "Progress tracking"],
                    target_audience="Teams"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=70.0, pain_intensity=75.0, monetization_potential=65.0,
                    competition_level=50.0, technical_feasibility=70.0
                ),
                final_score=70.0,
                content_quality_score=75.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=70.0,
                trust_level="MEDIUM"
            )
        ]

    def test_initialize_connections_success(self, mock_orchestrator_with_dependencies):
        """Test successful connection initialization"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        config = PipelineConfiguration(test_mode=False)

        # Should not raise any exceptions
        orchestrator.initialize_connections(config)

        # Verify connection tests were called
        mock_reddit_client.test_connection.assert_called_once()
        mock_analyzer.test_connection.assert_called_once()
        mock_database_loader.test_connection.assert_called_once()

    def test_initialize_connections_test_mode(self, mock_orchestrator_with_dependencies):
        """Test connection initialization in test mode"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        config = PipelineConfiguration(test_mode=True)

        orchestrator.initialize_connections(config)

        # Should skip Reddit connection test in test mode
        mock_reddit_client.test_connection.assert_not_called()
        mock_analyzer.test_connection.assert_called_once()

    def test_execute_pipeline_with_quality_filtering(self, mock_orchestrator_with_dependencies, sample_submissions, sample_analyses):
        """Test complete pipeline execution with quality filtering"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        # Configure mocks
        mock_reddit_client.fetch_submissions.return_value = sample_submissions
        mock_analyzer.analyze_batch.return_value = sample_analyses
        mock_database_loader.create_tables.return_value = None
        mock_database_loader.store_analyses.return_value = {"stored": 2, "skipped": 0, "errors": 0}
        mock_database_loader.get_statistics.return_value = {
            "total_opportunities": 10,
            "average_score": 75.0,
            "high_score_percentage": 80.0
        }
        mock_validator.get_quality_summary.return_value = {
            "validation_rate": 100.0,
            "high_score_rate": 100.0,
            "avg_final_score": 75.0,
            "trust_distribution": {"HIGH": 2}
        }

        config = PipelineConfiguration(
            subreddits=["productivity"],
            limit=10,
            min_score=60.0,  # Higher threshold to test filtering
            min_confidence=60.0,
            test_mode=True,
            dry_run=False
        )

        # Mock the staging layer
        orchestrator.staging_layer.store_submissions.return_value = ["batch_1"]
        orchestrator.staging_layer.get_batch.return_value = sample_submissions
        orchestrator.staging_layer.get_statistics.return_value = {
            "processed_submissions": 2,
            "deduplication_rate": 0.0
        }

        # Execute pipeline
        results = orchestrator.execute_pipeline(config)

        # Verify results
        assert isinstance(results, PipelineResults)
        assert results.submissions_extracted == 2
        assert results.analyses_generated == 2
        assert results.high_quality_analyses == 2  # Both analyses should pass quality filtering
        assert results.analyses_stored == 2

    def test_execute_pipeline_with_failed_quality_filtering(self, mock_orchestrator_with_dependencies, sample_submissions):
        """Test pipeline execution when most analyses fail quality filtering"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        # Create mostly low-quality analyses
        low_quality_analyses = [
            AnalysisResult.model_construct(
                submission_id="spam_1",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title="Bad App",
                    app_concept="Spam concept",
                    problem_statement="Fake problem",
                    core_functions=["Function"],
                    target_audience="Users"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=30.0, pain_intensity=25.0, monetization_potential=20.0,
                    competition_level=80.0, technical_feasibility=30.0
                ),
                final_score=25.0,
                content_quality_score=35.0,  # Below quality threshold
                is_spam=True,  # Marked as spam
                spam_indicators=["spam"],
                confidence_score=30.0,
                trust_level="LOW"
            ),
            AnalysisResult.model_construct(
                submission_id="test_1",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title="Good App",
                    app_concept="Good concept",
                    problem_statement="Real problem",
                    core_functions=["Function"],
                    target_audience="Users"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=80.0, pain_intensity=85.0, monetization_potential=75.0,
                    competition_level=40.0, technical_feasibility=80.0
                ),
                final_score=80.0,
                content_quality_score=85.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=80.0,
                trust_level="HIGH"
            )
        ]

        # Configure mocks
        mock_reddit_client.fetch_submissions.return_value = sample_submissions
        mock_analyzer.analyze_batch.return_value = low_quality_analyses
        mock_database_loader.create_tables.return_value = None
        mock_database_loader.store_analyses.return_value = {"stored": 1, "skipped": 0, "errors": 0}
        mock_database_loader.get_statistics.return_value = {
            "total_opportunities": 5,
            "average_score": 80.0,
            "high_score_percentage": 100.0
        }
        mock_validator.get_quality_summary.return_value = {
            "validation_rate": 50.0,  # 50% passed quality filtering
            "high_score_rate": 100.0,
            "avg_final_score": 80.0,
            "trust_distribution": {"HIGH": 1}
        }

        config = PipelineConfiguration(
            subreddits=["productivity"],
            limit=10,
            min_score=50.0,
            min_confidence=50.0,
            test_mode=True,
            dry_run=False
        )

        # Mock staging layer
        orchestrator.staging_layer.store_submissions.return_value = ["batch_1"]
        orchestrator.staging_layer.get_batch.return_value = sample_submissions
        orchestrator.staging_layer.get_statistics.return_value = {
            "processed_submissions": 2,
            "deduplication_rate": 0.0
        }

        # Execute pipeline
        results = orchestrator.execute_pipeline(config)

        # Verify quality filtering worked
        assert results.analyses_generated == 2  # Both analyses were generated
        assert results.high_quality_analyses == 1  # Only one passed quality filtering
        assert results.analyses_stored == 1  # Only one was stored
        assert results.validation_rate == 50.0  # 50% validation rate

    def test_execute_pipeline_no_submissions(self, mock_orchestrator_with_dependencies):
        """Test pipeline execution when no submissions are found"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        # Configure mocks for empty results
        mock_reddit_client.fetch_submissions.return_value = []

        config = PipelineConfiguration(
            subreddits=["empty"],
            limit=10,
            test_mode=True,
            dry_run=False
        )

        # Execute pipeline
        results = orchestrator.execute_pipeline(config)

        # Should return empty results
        assert results.submissions_extracted == 0
        assert results.analyses_generated == 0
        assert results.high_quality_analyses == 0
        assert results.analyses_stored == 0
        assert results.total_execution_time > 0

    def test_execute_pipeline_dry_run(self, mock_orchestrator_with_dependencies, sample_submissions, sample_analyses):
        """Test pipeline execution in dry run mode"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        # Configure mocks
        mock_reddit_client.fetch_submissions.return_value = sample_submissions
        mock_analyzer.analyze_batch.return_value = sample_analyses

        config = PipelineConfiguration(
            subreddits=["productivity"],
            limit=10,
            test_mode=True,
            dry_run=True  # Don't store to database
        )

        # Mock staging layer
        orchestrator.staging_layer.store_submissions.return_value = ["batch_1"]
        orchestrator.staging_layer.get_batch.return_value = sample_submissions
        orchestrator.staging_layer.get_statistics.return_value = {
            "processed_submissions": 2,
            "deduplication_rate": 0.0
        }

        # Execute pipeline
        results = orchestrator.execute_pipeline(config)

        # Should complete successfully but not store anything
        assert results.submissions_extracted == 2
        assert results.analyses_generated == 2
        assert results.high_quality_analyses == 2
        assert results.analyses_stored == 0  # Nothing stored in dry run
        assert results.analyses_skipped == 0

        # Database methods should not be called in dry run
        mock_database_loader.create_tables.assert_not_called()
        mock_database_loader.store_analyses.assert_not_called()

    def test_execute_pipeline_error_handling(self, mock_orchestrator_with_dependencies):
        """Test pipeline execution error handling"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        # Configure Reddit client to raise an exception
        mock_reddit_client.fetch_submissions.side_effect = Exception("Reddit API error")

        config = PipelineConfiguration(
            subreddits=["productivity"],
            limit=10,
            test_mode=True
        )

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Pipeline execution failed"):
            orchestrator.execute_pipeline(config)

    def test_validate_analyses_with_additional_validation(self, mock_orchestrator_with_dependencies, sample_analyses):
        """Test analysis validation with additional validation enabled"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        # Configure validator to fail one analysis
        mock_validator.validate_analysis.side_effect = [True, False]  # First passes, second fails

        config = PipelineConfiguration(
            validate_quality=True  # Enable additional validation
        )

        # Run validation
        validated_analyses, validation_time = orchestrator._validate_analyses(sample_analyses, config)

        # Should filter out one analysis due to additional validation
        assert len(validated_analyses) == 1
        assert validation_time > 0

        # Verify validator was called for both analyses
        assert mock_validator.validate_analysis.call_count == 2

    def test_validate_analyses_without_additional_validation(self, mock_orchestrator_with_dependencies, sample_analyses):
        """Test analysis validation without additional validation"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        config = PipelineConfiguration(
            validate_quality=False  # Disable additional validation
        )

        # Run validation
        validated_analyses, validation_time = orchestrator._validate_analyses(sample_analyses, config)

        # Should pass both analyses through quality filtering only
        assert len(validated_analyses) == 2
        assert validation_time > 0

        # Validator should not be called
        mock_validator.validate_analysis.assert_not_called()

    def test_stage_submissions_functionality(self, mock_orchestrator_with_dependencies, sample_submissions):
        """Test submission staging functionality"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        config = PipelineConfiguration(
            enable_staging=True,
            staging_batch_size=10
        )

        # Configure staging layer mock
        orchestrator.staging_layer.store_submissions.return_value = ["batch_1", "batch_2"]
        orchestrator.staging_layer.get_batch.side_effect = [
            [sample_submissions[0]],  # First batch
            [sample_submissions[1]]   # Second batch
        ]
        orchestrator.staging_layer.get_statistics.return_value = {
            "processed_submissions": 2,
            "deduplication_rate": 0.0
        }

        # Stage submissions
        staged_submissions, staging_time = orchestrator._stage_submissions(sample_submissions, config)

        # Verify staging worked
        assert len(staged_submissions) == 2
        assert staging_time > 0
        orchestrator.staging_layer.store_submissions.assert_called_once_with(sample_submissions)

    def test_stage_submissions_disabled(self, mock_orchestrator_with_dependencies, sample_submissions):
        """Test submission staging when disabled"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator_with_dependencies

        config = PipelineConfiguration(enable_staging=False)

        # Stage submissions
        staged_submissions, staging_time = orchestrator._stage_submissions(sample_submissions, config)

        # Should return original submissions unchanged
        assert staged_submissions == sample_submissions
        assert staging_time == 0.0
