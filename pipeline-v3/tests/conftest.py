"""
Pytest configuration and shared fixtures for comprehensive pipeline testing
"""

import pytest
import logging
import sys
import os
from unittest.mock import Mock
from datetime import datetime, timezone

# Add the pipeline root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission


def pytest_configure(config):
    """Configure pytest with custom markers and logging"""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests (may be slow)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "quality_filtering: marks tests as quality filtering specific"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (run with --run-slow)"
    )


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for tests"""
    # Set up logging to capture test output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_output.log')
        ]
    )

    # Reduce noise from some loggers during testing
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


@pytest.fixture
def sample_reddit_submission():
    """Create a sample Reddit submission for testing"""
    return RedditSubmission(
        id="test_123",
        title="Looking for a better task management solution",
        text="I've been struggling with organizing my daily tasks efficiently. I've tried several apps but they're either too complex or too simple. I need something that balances powerful features with ease of use. What do you all use for task management?",
        author="productivity_user",
        upvotes=45,
        score=45,
        comments_count=23,
        subreddit="productivity",
        created_utc=datetime.now(timezone.utc),
        permalink="https://reddit.com/r/productivity/test_123"
    )


@pytest.fixture
def high_quality_analysis():
    """Create a high-quality analysis result for testing"""
    return AnalysisResult.model_construct(
        submission_id="high_quality_1",
        analyzed_at=datetime.now(timezone.utc),
        app_idea=AppIdea.model_construct(
            title="Task Manager Pro",
            app_concept="A smart task management app that prioritizes work automatically based on deadlines, importance, and user energy levels",
            problem_statement="Professionals struggle with managing competing priorities and maintaining productivity throughout the workday while balancing multiple projects and deadlines",
            core_functions=["AI-powered prioritization", "Smart deadline tracking", "Energy-based scheduling"],
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
def medium_quality_analysis():
    """Create a medium-quality analysis result for testing"""
    return AnalysisResult.model_construct(
        submission_id="medium_quality_1",
        analyzed_at=datetime.now(timezone.utc),
        app_idea=AppIdea.model_construct(
            title="Task Organizer",
            app_concept="A task organization app with basic features",
            problem_statement="People need help organizing their tasks",
            core_functions=["Task tracking", "Reminder system"],
            target_audience="Students and professionals"
        ),
        market_metrics=MarketMetrics.model_construct(
            market_demand=60.0,
            pain_intensity=65.0,
            monetization_potential=55.0,
            competition_level=60.0,
            technical_feasibility=70.0
        ),
        final_score=62.0,
        content_quality_score=68.0,
        is_spam=False,
        spam_indicators=[],
        confidence_score=65.0,
        trust_level="MEDIUM"
    )


@pytest.fixture
def low_quality_analysis():
    """Create a low-quality analysis result for testing"""
    return AnalysisResult.model_construct(
        submission_id="low_quality_1",
        analyzed_at=datetime.now(timezone.utc),
        app_idea=AppIdea.model_construct(
            title="Simple App",
            app_concept="An app that does stuff",
            problem_statement="Some problem exists",
            core_functions=["Basic function"],
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
def spam_analysis():
    """Create a spam analysis result for testing"""
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


@pytest.fixture
def sample_analysis_dataset():
    """Create a mixed dataset of analyses for testing"""
    return [
        # High quality
        AnalysisResult.model_construct(
            submission_id="high_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Professional Task Manager",
                app_concept="Advanced task management for professionals",
                problem_statement="Professionals need better task organization",
                core_functions=["Smart scheduling", "Team collaboration"],
                target_audience="Business professionals"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=85.0, pain_intensity=80.0, monetization_potential=75.0,
                competition_level=35.0, technical_feasibility=85.0
            ),
            final_score=82.0,
            content_quality_score=88.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=85.0,
            trust_level="HIGH"
        ),
        # Medium quality
        AnalysisResult.model_construct(
            submission_id="medium_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Task Helper",
                app_concept="Basic task assistance app",
                problem_statement="People need task help",
                core_functions=["Task tracking"],
                target_audience="General users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=55.0, pain_intensity=60.0, monetization_potential=50.0,
                competition_level=65.0, technical_feasibility=70.0
            ),
            final_score=58.0,
            content_quality_score=62.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=60.0,
            trust_level="MEDIUM"
        ),
        # Low quality
        AnalysisResult.model_construct(
            submission_id="low_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="App",
                app_concept="Does something",
                problem_statement="Problem",
                core_functions=["Function"],
                target_audience="People"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=20.0, pain_intensity=15.0, monetization_potential=10.0,
                competition_level=90.0, technical_feasibility=25.0
            ),
            final_score=18.0,
            content_quality_score=25.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=30.0,
            trust_level="LOW"
        ),
        # Spam
        AnalysisResult.model_construct(
            submission_id="spam_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="MONEY NOW!!!",
                app_concept="Get instant money",
                problem_statement="Need money fast",
                core_functions=["Quick cash"],
                target_audience="Everyone"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=90.0, pain_intensity=85.0, monetization_potential=95.0,
                competition_level=5.0, technical_feasibility=90.0
            ),
            final_score=92.0,
            content_quality_score=10.0,
            is_spam=True,
            spam_indicators=["clickbait", "all caps", "unrealistic"],
            confidence_score=25.0,
            trust_level="LOW"
        ),
        # Borderline quality (exactly at threshold)
        AnalysisResult.model_construct(
            submission_id="borderline_1",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title="Borderline App",
                app_concept="An app that barely meets standards",
                problem_statement="Minor but real problem",
                core_functions=["Basic function"],
                target_audience="Specific users"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=45.0, pain_intensity=42.0, monetization_potential=40.0,
                competition_level=60.0, technical_feasibility=50.0
            ),
            final_score=45.0,
            content_quality_score=40.0,  # Exactly at quality threshold
            is_spam=False,
            spam_indicators=[],
            confidence_score=45.0,
            trust_level="MEDIUM"
        )
    ]


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    settings = Mock()
    settings.default_subreddits = ["test", "productivity", "technology"]
    settings.batch_size = 50
    settings.api_timeout = 30
    settings.max_retries = 3
    settings.reddit_client_id = "test_client_id"
    settings.reddit_client_secret = "test_client_secret"
    settings.reddit_user_agent = "test_agent"
    return settings


@pytest.fixture
def temp_analysis_results():
    """Create temporary analysis results for testing that can be modified"""
    results = []

    # Create results with different quality levels
    quality_configs = [
        ("high", 85.0, 90.0, "HIGH", False, []),
        ("medium", 60.0, 65.0, "MEDIUM", False, []),
        ("low", 30.0, 35.0, "LOW", False, []),
        ("spam", 80.0, 15.0, "LOW", True, ["spam", "clickbait"])
    ]

    for i, (level, final_score, quality_score, trust_level, is_spam, spam_indicators) in enumerate(quality_configs):
        analysis = AnalysisResult.model_construct(
            submission_id=f"temp_{level}_{i}",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title=f"{level.title()} Quality App {i}",
                app_concept=f"App concept for {level} quality testing",
                problem_statement=f"Problem statement for {level} quality testing",
                core_functions=["Function 1", "Function 2"][:2 if level != "low" else 1],
                target_audience=f"Target audience for {level} quality testing"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=final_score,
                pain_intensity=final_score + 5,
                monetization_potential=final_score - 5,
                competition_level=max(0, 100 - final_score),
                technical_feasibility=final_score
            ),
            final_score=final_score,
            content_quality_score=quality_score,
            is_spam=is_spam,
            spam_indicators=spam_indicators,
            confidence_score=final_score - 5,
            trust_level=trust_level
        )
        results.append(analysis)

    return results


# Performance testing utilities
class PerformanceTracker:
    """Utility class for tracking performance during tests"""

    def __init__(self):
        self.measurements = []
        self.start_time = None

    def start(self):
        """Start timing"""
        self.start_time = time.time()

    def measure(self, operation_name):
        """Measure and record operation time"""
        if self.start_time is None:
            raise ValueError("Must call start() before measuring")

        elapsed = time.time() - self.start_time
        self.measurements.append({
            'operation': operation_name,
            'time': elapsed,
            'timestamp': datetime.now(timezone.utc)
        })
        self.start_time = None
        return elapsed

    def get_average_time(self, operation_name):
        """Get average time for a specific operation"""
        times = [m['time'] for m in self.measurements if m['operation'] == operation_name]
        return sum(times) / len(times) if times else 0

    def get_total_time(self, operation_name):
        """Get total time for a specific operation"""
        times = [m['time'] for m in self.measurements if m['operation'] == operation_name]
        return sum(times)


@pytest.fixture
def performance_tracker():
    """Create a performance tracker for tests"""
    return PerformanceTracker()


# Custom pytest markers for test organization
def pytest_collection_modifyitems(config, items):
    """Add custom markers to tests based on their names and locations"""
    for item in items:
        # Add performance marker to performance tests
        if "performance" in item.nodeid or "load" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Add quality_filtering marker to quality filtering tests
        if "quality" in item.nodeid or "filtering" in item.nodeid:
            item.add_marker(pytest.mark.quality_filtering)

        # Add slow marker to slow tests
        if "large_dataset" in item.nodeid or "5000" in item.nodeid:
            item.add_marker(pytest.mark.slow)


# Helper functions for test data generation
def generate_analysis_results(count, quality_distribution=None):
    """Generate a specified number of analysis results with given quality distribution"""
    if quality_distribution is None:
        quality_distribution = {
            'high': 0.2,    # 20% high quality
            'medium': 0.5,  # 50% medium quality
            'low': 0.2,     # 20% low quality
            'spam': 0.1     # 10% spam
        }

    results = []
    quality_configs = {
        'high': (85.0, 90.0, "HIGH", False, []),
        'medium': (60.0, 65.0, "MEDIUM", False, []),
        'low': (30.0, 35.0, "LOW", False, []),
        'spam': (80.0, 15.0, "LOW", True, ["spam"])
    }

    for i in range(count):
        # Select quality level based on distribution
        rand = random.random()
        cumulative = 0
        selected_quality = 'medium'  # default

        for quality, probability in quality_distribution.items():
            cumulative += probability
            if rand <= cumulative:
                selected_quality = quality
                break

        final_score, quality_score, trust_level, is_spam, spam_indicators = quality_configs[selected_quality]

        # Add some variation
        final_score += random.uniform(-10, 10)
        quality_score += random.uniform(-5, 5)
        final_score = max(0, min(100, final_score))
        quality_score = max(0, min(100, quality_score))

        analysis = AnalysisResult.model_construct(
            submission_id=f"generated_{selected_quality}_{i:04d}",
            analyzed_at=datetime.now(timezone.utc),
            app_idea=AppIdea.model_construct(
                title=f"{selected_quality.title()} App {i}",
                app_concept=f"Concept for {selected_quality} app {i}",
                problem_statement=f"Problem for {selected_quality} app {i}",
                core_functions=["Function 1", "Function 2"][:random.randint(1, 3)],
                target_audience=f"Users for {selected_quality} app {i}"
            ),
            market_metrics=MarketMetrics.model_construct(
                market_demand=final_score,
                pain_intensity=final_score + random.uniform(-5, 5),
                monetization_potential=final_score + random.uniform(-5, 5),
                competition_level=max(0, min(100, 100 - final_score + random.uniform(-10, 10))),
                technical_feasibility=final_score + random.uniform(-5, 5)
            ),
            final_score=final_score,
            content_quality_score=quality_score,
            is_spam=is_spam,
            spam_indicators=spam_indicators,
            confidence_score=final_score + random.uniform(-5, 5),
            trust_level=trust_level
        )
        results.append(analysis)

    return results


# Import required modules
import time
import random