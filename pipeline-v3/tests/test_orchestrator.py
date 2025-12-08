"""
Tests for PipelineOrchestrator with TDD approach for quality filtering functionality
"""

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
)


class TestPipelineOrchestratorQualityFiltering:
    """Test suite for _filter_by_quality method following TDD methodology"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock PipelineOrchestrator for testing"""
        # Mock all dependencies
        mock_reddit_client = Mock()
        mock_analyzer_factory = Mock()
        mock_database_loader = Mock()
        mock_validator = Mock()
        mock_staging_layer = Mock()
        mock_settings = Mock()

        # Create orchestrator with mocked dependencies
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
    def sample_analysis_results(self) -> list[AnalysisResult]:
        """Create sample analysis results for testing using construct to bypass validation"""
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
            content_quality_score=20.0,  # Low quality but high score (suspicious)
            is_spam=True,  # This should cause filtering
            spam_indicators=["clickbait", "unrealistic promises"],
            confidence_score=60.0,
            trust_level="LOW"
        )
        results.append(spam_analysis)

        # Low quality analysis (should be filtered out by content_quality_score)
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

        # Below min_score threshold (should be filtered out)
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
            confidence_score=45.0,  # Below default min_confidence of 50.0
            trust_level="MEDIUM"
        )
        results.append(low_score)

        # Below min_confidence threshold (should be filtered out)
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

        return results

    def test_filter_by_quality_method_exists(self, mock_orchestrator):
        """GREEN TEST: Verify that _filter_by_quality method exists and can be called"""
        # Method should exist now (GREEN phase)
        assert hasattr(mock_orchestrator, '_filter_by_quality'), \
            "Method _filter_by_quality should exist now (GREEN phase)"

        # Method should be callable
        assert callable(mock_orchestrator._filter_by_quality)

        # Method call should work without raising AttributeError
        try:
            result = mock_orchestrator._filter_by_quality([], PipelineConfiguration())
            # Should return expected structure
            assert isinstance(result, dict)
            assert 'filtered_analyses' in result
            assert 'statistics' in result
        except Exception as e:
            pytest.fail(f"Method call failed unexpectedly: {type(e).__name__}: {e}")

    def test_filter_by_quality_basic_functionality(self, mock_orchestrator, sample_analysis_results):
        """GREEN TEST: Test basic quality filtering functionality"""
        config = PipelineConfiguration(
            min_score=50.0,
            min_confidence=50.0
        )

        # Method should work now (GREEN phase)
        result = mock_orchestrator._filter_by_quality(sample_analysis_results, config)

        # Should return:
        # - Only 1 high quality analysis (the rest should be filtered out)
        # - Statistics about filtering
        assert len(result['filtered_analyses']) == 1
        assert result['filtered_analyses'][0].submission_id == "high_quality_1"
        assert result['statistics']['total_input'] == 5
        assert result['statistics']['spam_filtered'] == 1
        assert result['statistics']['low_quality_filtered'] == 1
        assert result['statistics']['below_min_score_filtered'] == 1
        assert result['statistics']['below_min_confidence_filtered'] == 1
        assert result['statistics']['total_filtered'] == 4
        assert result['statistics']['final_count'] == 1

    def test_filter_by_quality_empty_input(self, mock_orchestrator):
        """GREEN TEST: Test filtering with empty input list"""
        config = PipelineConfiguration()

        result = mock_orchestrator._filter_by_quality([], config)

        # Should handle empty input gracefully
        assert result['filtered_analyses'] == []
        assert result['statistics']['total_input'] == 0
        assert result['statistics']['final_count'] == 0

    def test_filter_by_quality_all_spam(self, mock_orchestrator):
        """GREEN TEST: Test filtering when all analyses are spam"""
        spam_analyses = []
        for i in range(3):
            spam_analysis = AnalysisResult.model_construct(
                submission_id=f"spam_{i}",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"Spam App Number {i}",
                    app_concept="Spam concept application system",
                    problem_statement="Fake problem statement exists",
                    core_functions=["Spam function"],
                    target_audience="Everyone looking for spam"
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

        # Should filter out all spam
        assert len(result['filtered_analyses']) == 0
        assert result['statistics']['total_input'] == 3
        assert result['statistics']['spam_filtered'] == 3
        assert result['statistics']['final_count'] == 0

    def test_filter_by_quality_custom_thresholds(self, mock_orchestrator, sample_analysis_results):
        """GREEN TEST: Test filtering with custom min_score and min_confidence thresholds"""
        config = PipelineConfiguration(
            min_score=70.0,  # Higher threshold
            min_confidence=70.0  # Higher threshold
        )

        result = mock_orchestrator._filter_by_quality(sample_analysis_results, config)

        # Should filter out more analyses due to higher thresholds
        assert len(result['filtered_analyses']) == 1
        assert result['filtered_analyses'][0].submission_id == "high_quality_1"
        assert result['statistics']['below_min_score_filtered'] >= 1
        # Note: The high_quality analysis has confidence_score=85.0, so only the spam
        # analysis (confidence_score=60.0) and low_confidence (35.0) should be filtered
        # by confidence. The low_confidence analysis already gets filtered by min_score.

    def test_filter_by_quality_no_filters_needed(self, mock_orchestrator):
        """GREEN TEST: Test filtering when no analyses need to be filtered"""
        # Create only high-quality analyses
        high_quality_analyses = []
        for i in range(3):
            high_quality = AnalysisResult.model_construct(
                submission_id=f"high_quality_{i}",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"Quality App Number {i}",
                    app_concept="High quality concept system",
                    problem_statement="Real problem statement exists",
                    core_functions=["Quality function"],
                    target_audience="Specific target audience"
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

        config = PipelineConfiguration(
            min_score=50.0,
            min_confidence=50.0
        )

        result = mock_orchestrator._filter_by_quality(high_quality_analyses, config)

        # Should pass all analyses through
        assert len(result['filtered_analyses']) == 3
        assert result['statistics']['total_input'] == 3
        assert result['statistics']['final_count'] == 3
        assert result['statistics']['total_filtered'] == 0

    def test_filter_by_quality_return_structure(self, mock_orchestrator, sample_analysis_results):
        """GREEN TEST: Test that the return value has the correct structure"""
        config = PipelineConfiguration()

        result = mock_orchestrator._filter_by_quality(sample_analysis_results, config)

        # Should return a dictionary with expected keys
        assert isinstance(result, dict)
        assert 'filtered_analyses' in result
        assert 'statistics' in result
        assert isinstance(result['filtered_analyses'], list)
        assert isinstance(result['statistics'], dict)

        # Check expected statistics keys
        expected_stat_keys = [
            'total_input',
            'spam_filtered',
            'low_quality_filtered',
            'below_min_score_filtered',
            'below_min_confidence_filtered',
            'total_filtered',
            'final_count'
        ]
        for key in expected_stat_keys:
            assert key in result['statistics']
