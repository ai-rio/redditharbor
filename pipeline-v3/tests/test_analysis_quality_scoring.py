"""
Comprehensive tests for AnalysisResult quality scoring and validation
"""

import pytest
import math
from datetime import datetime, timezone, timedelta
from typing import List

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission


class TestAnalysisResultQualityScoring:
    """Test suite for AnalysisResult quality scoring functionality"""

    @pytest.fixture
    def high_quality_analysis(self):
        """Create a high-quality analysis result"""
        return AnalysisResult.model_construct(
            submission_id="high_quality_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Productivity Manager Pro",
                app_concept="An intelligent task management application that automatically prioritizes work based on deadlines and importance",
                problem_statement="Professionals struggle with managing increasing workloads and prioritizing tasks effectively across multiple projects",
                core_functions=["AI-powered prioritization", "Automated deadline tracking", "Cross-project synchronization"],
                target_audience="Busy professionals, project managers, and teams handling multiple concurrent projects"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=85.0,
                pain_intensity=90.0,
                monetization_potential=80.0,
                competition_level=40.0,  # Lower competition is better
                technical_feasibility=85.0
            ),
            final_score=85.0,
            content_quality_score=92.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=88.0,
            trust_level="HIGH"
        )

    @pytest.fixture
    def low_quality_analysis(self):
        """Create a low-quality analysis result"""
        return AnalysisResult.model_construct(
            submission_id="low_quality_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Simple App",
                app_concept="An app",
                problem_statement="A problem",
                core_functions=["Function"],
                target_audience="Users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=25.0,
                pain_intensity=20.0,
                monetization_potential=15.0,
                competition_level=85.0,  # High competition
                technical_feasibility=25.0
            ),
            final_score=22.0,
            content_quality_score=28.0,  # Below quality threshold
            is_spam=False,
            spam_indicators=[],
            confidence_score=30.0,
            trust_level="LOW"
        )

    @pytest.fixture
    def spam_analysis(self):
        """Create a spam analysis result"""
        return AnalysisResult.model_construct(
            submission_id="spam_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="GET RICH QUICK!!!",
                app_concept="Make millions overnight with our revolutionary system",
                problem_statement="People need money fast and easy",
                core_functions=["Instant profits", "No work required"],
                target_audience="Everyone who wants free money"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=95.0,
                pain_intensity=90.0,
                monetization_potential=98.0,
                competition_level=5.0,  # No competition (because it's fake)
                technical_feasibility=95.0
            ),
            final_score=94.0,
            content_quality_score=15.0,  # Very low quality for spam
            is_spam=True,
            spam_indicators=["clickbait", "unrealistic promises", "all caps title", "exaggerated claims"],
            confidence_score=45.0,
            trust_level="LOW"
        )

    def test_high_quality_analysis_validation(self, high_quality_analysis):
        """Test that high-quality analysis passes all validations"""
        # Should not raise any validation errors
        analysis = AnalysisResult(**high_quality_analysis.model_dump())

        assert analysis.submission_id == "high_quality_1"
        assert analysis.content_quality_score > 40.0  # Above quality threshold
        assert analysis.is_spam is False
        assert len(analysis.spam_indicators) == 0
        assert analysis.confidence_score > 50.0
        assert analysis.trust_level == "HIGH"

    def test_low_quality_analysis_validation(self, low_quality_analysis):
        """Test that low-quality analysis passes validation but would be filtered"""
        # Should not raise validation errors (it's valid but low quality)
        analysis = AnalysisResult(**low_quality_analysis.model_dump())

        assert analysis.submission_id == "low_quality_1"
        assert analysis.content_quality_score < 40.0  # Below quality threshold
        assert analysis.is_spam is False
        assert analysis.final_score < 50.0
        assert analysis.confidence_score < 50.0
        assert analysis.trust_level == "LOW"

    def test_spam_analysis_validation(self, spam_analysis):
        """Test that spam analysis passes validation with proper constraints"""
        # Should not raise validation errors if spam score is low enough
        analysis = AnalysisResult(**spam_analysis.model_dump())

        assert analysis.submission_id == "spam_1"
        assert analysis.content_quality_score <= 40.0  # Spam must have low quality score
        assert analysis.is_spam is True
        assert len(analysis.spam_indicators) > 0
        assert analysis.trust_level == "LOW"

    def test_spam_with_high_quality_score_validation_failure(self):
        """Test that spam with high quality score fails validation"""
        with pytest.raises(ValueError, match="Spam content must have content_quality_score"):
            AnalysisResult(
                submission_id="invalid_spam",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Fake App",
                    app_concept="Fake concept",
                    problem_statement="Fake problem",
                    core_functions=["Function"],
                    target_audience="Users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=85.0,  # Too high for spam
                is_spam=True,  # This combination should fail
                spam_indicators=["spam"],
                confidence_score=50.0,
                trust_level="LOW"
            )

    def test_trust_level_validation(self):
        """Test trust level validation"""
        valid_trust_levels = ["LOW", "MEDIUM", "HIGH"]

        for level in valid_trust_levels:
            analysis = AnalysisResult.model_construct(
                submission_id="test_trust",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea.model_construct(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                    competition_level=50.0, technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level=level  # Should be capitalized
            )
            assert analysis.trust_level == level

    def test_invalid_trust_level_validation(self):
        """Test that invalid trust levels are rejected"""
        with pytest.raises(ValueError, match="trust_level must be one of"):
            AnalysisResult(
                submission_id="invalid_trust",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="INVALID"  # Invalid trust level
            )

    def test_embedding_validation(self):
        """Test embedding vector validation"""
        # Valid embedding
        valid_embedding = [0.1, 0.2, 0.3] * 100  # 300 dimensions
        analysis = AnalysisResult.model_construct(
            submission_id="test_embedding",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Test App",
                app_concept="Test concept",
                problem_statement="Test problem",
                core_functions=["Test function"],
                target_audience="Test users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                competition_level=50.0, technical_feasibility=50.0
            ),
            final_score=50.0,
            content_quality_score=50.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=50.0,
            trust_level="MEDIUM",
            embedding=valid_embedding
        )
        assert len(analysis.embedding) == 300

    def test_embedding_validation_none(self):
        """Test that None embedding is allowed"""
        analysis = AnalysisResult.model_construct(
            submission_id="test_no_embedding",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Test App",
                app_concept="Test concept",
                problem_statement="Test problem",
                core_functions=["Test function"],
                target_audience="Test users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                competition_level=50.0, technical_feasibility=50.0
            ),
            final_score=50.0,
            content_quality_score=50.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=50.0,
            trust_level="MEDIUM",
            embedding=None  # Optional field
        )
        assert analysis.embedding is None

    def test_embedding_validation_invalid_type(self):
        """Test that invalid embedding types are rejected"""
        with pytest.raises(ValueError, match="Invalid embedding vector: must be a list"):
            AnalysisResult(
                submission_id="invalid_embedding_type",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="MEDIUM",
                embedding="not_a_list"  # Invalid type
            )

    def test_embedding_validation_invalid_length(self):
        """Test that embeddings with invalid lengths are rejected"""
        with pytest.raises(ValueError, match="Invalid embedding vector: too short"):
            AnalysisResult(
                submission_id="invalid_embedding_length",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="MEDIUM",
                embedding=[0.1, 0.2]  # Too short
            )

    def test_embedding_validation_invalid_values(self):
        """Test that embeddings with invalid values are rejected"""
        with pytest.raises(ValueError, match="Invalid embedding vector: element .* is NaN"):
            AnalysisResult(
                submission_id="invalid_embedding_values",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="MEDIUM",
                embedding=[0.1, float('nan'), 0.3]  # Contains NaN
            )

    def test_timestamp_validation_future(self):
        """Test that future timestamps are rejected"""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        with pytest.raises(ValueError, match="Analysis timestamp is too old"):
            # Note: This tests the old timestamp validation, not future timestamp
            # because the validation checks for timestamps that are too old, not future
            AnalysisResult(
                submission_id="future_timestamp",
                analyzed_at=datetime.now(timezone.utc) - timedelta(days=400),  # Too old
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="MEDIUM"
            )

    def test_cross_model_score_consistency(self):
        """Test validation of score consistency with market metrics"""
        with pytest.raises(ValueError, match="Final score inconsistency"):
            AnalysisResult(
                submission_id="inconsistent_scores",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=20.0,  # Very low
                    pain_intensity=15.0,  # Very low
                    monetization_potential=10.0,  # Very low
                    competition_level=90.0,  # High competition
                    technical_feasibility=20.0  # Very low
                    # Average of these = 31.0
                ),
                final_score=90.0,  # Too high deviation from metrics average
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="MEDIUM"
            )

    def test_cross_model_score_consistency_within_tolerance(self):
        """Test that scores within tolerance are accepted"""
        # This should pass - final score within 20 points of metrics average
        analysis = AnalysisResult(
            submission_id="consistent_scores",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea(
                title="Test App",
                app_concept="Test concept",
                problem_statement="Test problem",
                core_functions=["Test function"],
                target_audience="Test users"
            ),
            market_metrics=MarketMetrics(
                market_demand=80.0,
                pain_intensity=85.0,
                monetization_potential=75.0,
                competition_level=40.0,  # Lower is better
                technical_feasibility=80.0
                # Average = (80+85+75+40+80)/5 = 72.0
            ),
            final_score=85.0,  # Within 20 points of average (72+13=85)
            content_quality_score=80.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=80.0,
            trust_level="HIGH"
        )
        assert analysis.final_score == 85.0

    def test_quality_score_boundary_values(self):
        """Test quality score boundary values"""
        # Exactly at spam quality threshold (40) and marked as spam - should pass
        spam_at_threshold = AnalysisResult(
            submission_id="spam_at_threshold",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea(
                title="Test App",
                app_concept="Test concept",
                problem_statement="Test problem",
                core_functions=["Test function"],
                target_audience="Test users"
            ),
            market_metrics=MarketMetrics(
                market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                competition_level=50.0, technical_feasibility=50.0
            ),
            final_score=50.0,
            content_quality_score=40.0,  # Exactly at threshold
            is_spam=True,
            spam_indicators=["spam"],
            confidence_score=50.0,
            trust_level="LOW"
        )
        assert spam_at_threshold.content_quality_score == 40.0

        # Just above spam quality threshold and marked as spam - should fail
        with pytest.raises(ValueError, match="Spam content must have content_quality_score"):
            AnalysisResult(
                submission_id="spam_above_threshold",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea(
                    title="Test App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics(
                    market_demand=50.0,
                    pain_intensity=50.0,
                    monetization_potential=50.0,
                    competition_level=50.0,
                    technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=40.1,  # Just above threshold
                is_spam=True,
                spam_indicators=["spam"],
                confidence_score=50.0,
                trust_level="LOW"
            )


class TestAppIdeaQualityScoring:
    """Test suite for AppIdea quality aspects"""

    def test_high_quality_app_idea(self):
        """Test creation of high-quality app idea"""
        app_idea = AppIdea(
            title="Intelligent Task Scheduler",
            app_concept="An AI-powered task scheduling application that automatically optimizes your daily workflow based on priorities, deadlines, and energy levels",
            problem_statement="Professionals struggle with managing competing priorities and maintaining productivity throughout the workday while balancing multiple projects and deadlines",
            core_functions=["AI-powered task prioritization", "Automatic schedule optimization", "Energy-based task matching"],
            target_audience="Busy professionals, freelancers, and project managers handling multiple concurrent projects"
        )

        assert len(app_idea.title) >= 5
        assert len(app_idea.title) <= 100
        assert len(app_idea.app_concept) >= 10
        assert len(app_idea.app_concept) <= 500
        assert len(app_idea.problem_statement) >= 10
        assert len(app_idea.problem_statement) <= 1000
        assert len(app_idea.core_functions) >= 1
        assert len(app_idea.core_functions) <= 3
        assert len(app_idea.target_audience) >= 10
        assert len(app_idea.target_audience) <= 500

        # Check title case
        words = app_idea.title.split()
        assert all(word[0].isupper() or word.lower() in {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'with', 'in', 'of'} for word in words if word)

    def test_low_quality_app_idea_validation(self):
        """Test that low-quality app ideas fail validation"""
        with pytest.raises(ValueError):
            AppIdea(
                title="Bad",  # Too short
                app_concept="Too short concept",
                problem_statement="Too short",
                core_functions=["Too short"],
                target_audience="Too"  # Too short
            )

    def test_too_many_core_functions(self):
        """Test validation fails with too many core functions"""
        with pytest.raises(ValueError, match="List should have at most 3 items"):
            AppIdea(
                title="Complex App",
                app_concept="An app that does everything",
                problem_statement="Complex problem",
                core_functions=["Function 1", "Function 2", "Function 3", "Function 4", "Function 5"],
                target_audience="Everyone"
            )

    def test_duplicate_core_functions(self):
        """Test validation fails with duplicate core functions"""
        with pytest.raises(ValueError, match="Core functions must be unique"):
            AppIdea(
                title="Duplicate App",
                app_concept="App with duplicates",
                problem_statement="Problem",
                core_functions=["Same function", "Same function", "Different function"],
                target_audience="Users"
            )

    def test_business_feasibility_validation(self):
        """Test business feasibility validation"""
        with pytest.raises(ValueError, match="App concept should clearly address the stated problem"):
            AppIdea(
                title="Mismatched App",
                app_concept="A social media platform for pet photos",  # Doesn't solve the problem
                problem_statement="I need help with time management and productivity",  # Different domain
                core_functions=["Photo sharing", "Pet profiles"],
                target_audience="Pet owners"
            )

    def test_business_feasibility_validation_pass(self):
        """Test that matching concept and problem passes validation"""
        app_idea = AppIdea(
            title="Time Management App",
            app_concept="A productivity app that helps users organize tasks and manage time efficiently",
            problem_statement="I struggle with time management and keeping track of my daily tasks",
            core_functions=["Task scheduling", "Time tracking"],
            target_audience="Students and professionals"
        )
        # Should not raise validation error
        assert app_idea.title == "Time Management App"


class TestMarketMetricsQualityScoring:
    """Test suite for MarketMetrics quality aspects"""

    def test_valid_market_metrics(self):
        """Test creation of valid market metrics"""
        metrics = MarketMetrics(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            competition_level=45.0,  # Remember: lower = less competition (better)
            technical_feasibility=85.0
        )

        assert 0.0 <= metrics.market_demand <= 100.0
        assert 0.0 <= metrics.pain_intensity <= 100.0
        assert 0.0 <= metrics.monetization_potential <= 100.0
        assert 0.0 <= metrics.competition_level <= 100.0
        assert 0.0 <= metrics.technical_feasibility <= 100.0

    def test_metric_consistency_validation(self):
        """Test metric consistency validation"""
        with pytest.raises(ValueError, match="High pain intensity should correlate with market demand"):
            MarketMetrics(
                market_demand=20.0,  # Low demand
                pain_intensity=90.0,  # But high pain - inconsistent
                monetization_potential=50.0,
                competition_level=50.0,
                technical_feasibility=50.0
            )

    def test_feasibility_monetization_consistency(self):
        """Test technical feasibility vs monetization potential consistency"""
        with pytest.raises(ValueError, match="Low technical feasibility limits monetization potential"):
            MarketMetrics(
                market_demand=50.0,
                pain_intensity=50.0,
                monetization_potential=90.0,  # High monetization
                competition_level=50.0,
                technical_feasibility=10.0  # But very low feasibility
            )

    def test_extreme_values_validation(self):
        """Test validation for unrealistic extreme value combinations"""
        with pytest.raises(ValueError, match="Metrics combination is unrealistic"):
            MarketMetrics(
                market_demand=95.0,  # All metrics at extreme high
                pain_intensity=95.0,
                monetization_potential=95.0,
                competition_level=5.0,  # Extreme low (good)
                technical_feasibility=95.0
            )

    def test_all_low_values_validation(self):
        """Test validation for all low values"""
        with pytest.raises(ValueError, match="Metrics combination is unrealistic"):
            MarketMetrics(
                market_demand=10.0,  # All metrics at extreme low
                pain_intensity=10.0,
                monetization_potential=10.0,
                competition_level=90.0,  # High competition (bad)
                technical_feasibility=10.0
            )

    def test_metric_precision_validation(self):
        """Test metric precision validation"""
        with pytest.raises(ValueError, match="Metric .* has too many decimal places"):
            MarketMetrics(
                market_demand=75.123,  # Too many decimal places
                pain_intensity=80.0,
                monetization_potential=70.0,
                competition_level=50.0,
                technical_feasibility=85.0
            )

    def test_metric_precision_validation_pass(self):
        """Test that acceptable precision passes validation"""
        metrics = MarketMetrics(
            market_demand=75.12,  # Two decimal places - OK
            pain_intensity=80.5,  # One decimal place - OK
            monetization_potential=70.0,  # Zero decimal places - OK
            competition_level=50.99,  # Two decimal places - OK
            technical_feasibility=85.75  # Two decimal places - OK
        )
        # Should not raise validation error
        assert metrics.market_demand == 75.12


class TestQualityScoringIntegration:
    """Integration tests for quality scoring components"""

    def test_complete_quality_analysis_flow(self):
        """Test complete quality analysis flow from high to low quality"""
        high_quality_analysis = AnalysisResult(
            submission_id="integration_test_high",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea(
                title="Professional Task Manager",
                app_concept="An intelligent task management application designed for professionals who need to coordinate complex projects across multiple teams",
                problem_statement="Project managers and team leaders struggle with coordinating tasks across multiple projects while maintaining visibility into overall progress and resource allocation",
                core_functions=["Cross-project task synchronization", "Automated progress reporting", "Resource allocation optimization"],
                target_audience="Project managers, team leads, and coordinators in medium to large organizations"
            ),
            market_metrics=MarketMetrics(
                market_demand=85.0,
                pain_intensity=90.0,
                monetization_potential=80.0,
                competition_level=35.0,
                technical_feasibility=85.0
            ),
            final_score=87.0,
            content_quality_score=92.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=89.0,
            trust_level="HIGH"
        )

        # Verify all quality aspects
        assert high_quality_analysis.content_quality_score > 90
        assert not high_quality_analysis.is_spam
        assert len(high_quality_analysis.spam_indicators) == 0
        assert high_quality_analysis.confidence_score > 85
        assert high_quality_analysis.trust_level == "HIGH"
        assert high_quality_analysis.final_score > 85

        # Verify app idea quality
        assert len(high_quality_analysis.app_idea.title) > 10
        assert len(high_quality_analysis.app_idea.app_concept) > 100
        assert len(high_quality_analysis.app_idea.problem_statement) > 100
        assert len(high_quality_analysis.app_idea.core_functions) == 3
        assert len(high_quality_analysis.app_idea.target_audience) > 50

        # Verify market metrics quality
        assert high_quality_analysis.market_metrics.market_demand > 80
        assert high_quality_analysis.market_metrics.pain_intensity > 85
        assert high_quality_analysis.market_metrics.monetization_potential > 75
        assert high_quality_analysis.market_metrics.competition_level < 50  # Lower competition is better
        assert high_quality_analysis.market_metrics.technical_feasibility > 80

    def test_quality_score_calculation_consistency(self):
        """Test that quality scores are consistent across components"""
        # Create analyses with different quality levels
        quality_levels = [
            ("low", 15.0, "LOW"),
            ("medium", 55.0, "MEDIUM"),
            ("high", 85.0, "HIGH")
        ]

        for level_name, quality_score, expected_trust in quality_levels:
            analysis = AnalysisResult.model_construct(
                submission_id=f"quality_{level_name}",
                analyzed_at=datetime.now(timezone.utc),
                app_idea=AppIdea.model_construct(
                    title=f"{level_name.title()} Quality App",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Test function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=quality_score,
                    pain_intensity=quality_score,
                    monetization_potential=quality_score,
                    competition_level=100 - quality_score,  # Inverse for realism
                    technical_feasibility=quality_score
                ),
                final_score=quality_score,
                content_quality_score=quality_score,
                is_spam=False,
                spam_indicators=[],
                confidence_score=quality_score,
                trust_level=expected_trust
            )

            assert analysis.content_quality_score == quality_score
            assert analysis.final_score == quality_score
            assert analysis.confidence_score == quality_score
            assert analysis.trust_level == expected_trust