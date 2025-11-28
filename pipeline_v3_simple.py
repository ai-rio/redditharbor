#!/usr/bin/env python3
"""
Pipeline v3 - Simple Version (No pgvector) - Clean Reddit Data Processing Pipeline Entry Point

A minimal, type-safe Reddit data extraction and analysis pipeline following ELT pattern:
Extract → Transform → Load

Usage:
    python pipeline_v3_simple.py --limit 25 --subreddits productivity tools
    python pipeline_v3_simple.py --test-mode --limit 5
    python pipeline_v3_simple.py --score-threshold 70.0 --min-confidence 60.0
"""

import argparse
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import List

# Add pipeline-v3 to Python path
pipeline_v3_path = Path(__file__).parent / "pipeline-v3"
sys.path.insert(0, str(pipeline_v3_path))

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check if dependencies are available
try:
    from config import get_settings
    from models.reddit import RedditSubmission
    from models.analysis import AnalysisResult
    logger.info("✓ Core models imported successfully")
except ImportError as e:
    logger.error(f"Failed to import core models: {e}")
    logger.info("Using simplified built-in models for testing")

    # Simplified models for testing
    from datetime import datetime, UTC
    from typing import List, Optional

    class RedditSubmission:
        def __init__(self, id, title, text, author, upvotes, score, comments_count, subreddit, created_utc, permalink):
            self.id = id
            self.title = title
            self.text = text
            self.author = author
            self.upvotes = upvotes
            self.score = score
            self.comments_count = comments_count
            self.subreddit = subreddit
            self.created_utc = created_utc
            self.permalink = permalink

    class AppIdea:
        def __init__(self, title, app_concept, problem_statement, target_audience, core_functions):
            self.title = title
            self.app_concept = app_concept
            self.problem_statement = problem_statement
            self.target_audience = target_audience
            self.core_functions = core_functions

    class MarketMetrics:
        def __init__(self, market_demand, pain_intensity, monetization_potential, competition_level, technical_feasibility):
            self.market_demand = market_demand
            self.pain_intensity = pain_intensity
            self.monetization_potential = monetization_potential
            self.competition_level = competition_level
            self.technical_feasibility = technical_feasibility

    class AnalysisResult:
        def __init__(self, submission_id, app_idea, market_metrics, final_score, confidence_score, trust_level, embedding=None):
            self.submission_id = submission_id
            self.app_idea = app_idea
            self.market_metrics = market_metrics
            self.final_score = final_score
            self.confidence_score = confidence_score
            self.trust_level = trust_level
            self.embedding = embedding

    logger.info("✓ Using built-in simplified models")

# Mock implementations for testing
class MockRedditClient:
    """Mock Reddit client for testing"""

    def test_connection(self) -> bool:
        logger.info("✓ Mock Reddit API connection test successful")
        return True

    def fetch_submissions(self, subreddits: List[str], limit: int, sort_by: str = "hot", time_filter: str = "week") -> List[RedditSubmission]:
        """Generate mock Reddit submissions for testing"""
        mock_submissions = []
        for i in range(min(limit, 5)):  # Limit to 5 for testing
            submission = RedditSubmission(
                id=f"test{i:123}",
                title=f"Test Productivity Post {i+1}",
                text=f"This is a test Reddit post about productivity tools and workflow optimization. It discusses common pain points and desired features.",
                author=f"testuser{i}",
                upvotes=100 + i * 25,
                score=100 + i * 25,
                comments_count=50 + i * 10,
                subreddit=subreddits[0] if subreddits else "productivity",
                created_utc=datetime.now(UTC),
                permalink=f"https://reddit.com/r/{subreddits[0] if subreddits else 'productivity'}/test{i}/"
            )
            mock_submissions.append(submission)

        logger.info(f"Generated {len(mock_submissions)} mock submissions")
        return mock_submissions


class MockAnalyzer:
    """Mock LLM analyzer for testing"""

    def test_connection(self) -> bool:
        logger.info("✓ Mock LLM API connection test successful")
        return True

    def get_model_info(self) -> dict:
        return {
            "model": "mock-gpt-4o-mini",
            "provider": "Mock Provider",
            "base_url": "https://mock-api.com/v1",
            "max_tokens": 1000,
            "temperature": 0.3,
            "is_configured": True
        }

    def analyze_batch(self, submissions: List[RedditSubmission], batch_size: int = None) -> List[AnalysisResult]:
        """Generate mock analysis results"""
        mock_analyses = []

        for i, submission in enumerate(submissions):
            from models.analysis import AppIdea, MarketMetrics

            app_idea = AppIdea(
                title=f"Productivity Helper App {i+1}",
                app_concept="A simple productivity tool that helps users track tasks and deadlines",
                problem_statement="Users struggle with task organization and deadline tracking",
                target_audience="Students and professionals who need better time management",
                core_functions=["task tracking", "deadline reminders"] if i % 2 == 0 else ["task tracking"]
            )

            market_metrics = MarketMetrics(
                market_demand=70.0 + (i * 5),
                pain_intensity=75.0 + (i * 3),
                monetization_potential=80.0 + (i * 2),
                competition_level=60.0 + (i * 4),
                technical_feasibility=85.0 + (i * 2)
            )

            analysis = AnalysisResult(
                submission_id=submission.id,
                app_idea=app_idea,
                market_metrics=market_metrics,
                final_score=75.0 + (i * 3),
                confidence_score=80.0 + (i * 2),
                trust_level="HIGH" if i % 3 == 0 else "MEDIUM",
                embedding=None  # No pgvector in simple version
            )

            mock_analyses.append(analysis)

        logger.info(f"Generated {len(mock_analyses)} mock analyses")
        return mock_analyses


class MockValidator:
    """Mock analysis validator"""

    def validate_analysis(self, analysis: AnalysisResult) -> bool:
        return True

    def get_quality_summary(self, analyses: List[AnalysisResult]) -> dict:
        if not analyses:
            return {"total": 0}

        return {
            "total": len(analyses),
            "validation_rate": 100.0,
            "high_score_rate": 80.0,
            "avg_final_score": sum(a.final_score for a in analyses) / len(analyses),
            "trust_distribution": {"HIGH": 60, "MEDIUM": 40, "LOW": 0}
        }


class MockDatabaseLoader:
    """Mock database loader"""

    def test_connection(self) -> bool:
        logger.info("✓ Mock database connection test successful")
        return True

    def create_tables(self) -> None:
        logger.info("✓ Mock database tables created")

    def store_analyses(self, analyses: List[AnalysisResult]) -> dict:
        logger.info(f"✓ Mock stored {len(analyses)} analyses to database")
        return {"stored": len(analyses), "skipped": 0, "errors": 0}

    def get_statistics(self) -> dict:
        return {
            "total_opportunities": 50,
            "average_score": 78.5,
            "high_score_percentage": 65.0
        }


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the pipeline"""
    parser = argparse.ArgumentParser(
        description="Pipeline v3 Simple - Reddit Opportunity Analysis (Mock Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --limit 5 --subreddits productivity tools
  %(prog)s --test-mode --limit 3
  %(prog)s --score-threshold 70.0 --min-confidence 60.0
        """
    )

    # Reddit extraction options
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of Reddit submissions to process (default: 5)"
    )

    parser.add_argument(
        "--subreddits",
        type=str,
        nargs="+",
        default=["productivity"],
        help="List of subreddits to fetch from (default: productivity)"
    )

    parser.add_argument(
        "--sort-by",
        type=str,
        choices=["hot", "top", "new"],
        default="hot",
        help="Reddit sorting method (default: hot)"
    )

    parser.add_argument(
        "--time-filter",
        type=str,
        choices=["hour", "day", "week", "month", "year", "all"],
        default="week",
        help="Time filter for 'top' sorting (default: week)"
    )

    # Quality filtering options
    parser.add_argument(
        "--min-score",
        type=float,
        default=70.0,
        help="Minimum opportunity score to store (default: 70.0)"
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=60.0,
        help="Minimum confidence score to store (default: 60.0)"
    )

    parser.add_argument(
        "--validate-quality",
        action="store_true",
        default=False,
        help="Enable additional quality validation filtering"
    )

    # Processing options
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Batch size for LLM processing (default: 3)"
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        default=True,
        help="Enable test mode with mocked data (always enabled in simple version)"
    )

    # Database options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Process data but don't store to database"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    return parser.parse_args()


async def run_pipeline(args: argparse.Namespace) -> int:
    """Run the complete pipeline with the given arguments"""
    pipeline_start_time = time.time()

    logger.info("=" * 80)
    logger.info("PIPELINE V3 SIMPLE - Reddit Opportunity Analysis (Mock Mode)")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Subreddits: {args.subreddits}")
    logger.info(f"  - Limit: {args.limit}")
    logger.info(f"  - Sort by: {args.sort_by}")
    logger.info(f"  - Min score: {args.min_score}")
    logger.info(f"  - Min confidence: {args.min_confidence}")
    logger.info(f"  - Test mode: {args.test_mode}")
    logger.info(f"  - Dry run: {args.dry_run}")
    logger.info("")

    try:
        # Step 0: Initialize components
        logger.info("STEP 0: Initializing pipeline components")
        reddit_client = MockRedditClient()
        analyzer = MockAnalyzer()
        validator = MockValidator()

        db_loader = None if args.dry_run else MockDatabaseLoader()

        # Test connections
        reddit_client.test_connection()
        analyzer.test_connection()

        model_info = analyzer.get_model_info()
        logger.info(f"✓ Using {model_info['provider']} model: {model_info['model']}")

        if db_loader:
            db_loader.test_connection()

        logger.info("✓ All components initialized successfully")

        # Step 1: Extract Reddit submissions
        logger.info("STEP 1: Extracting Reddit submissions")
        extract_start = time.time()

        submissions = reddit_client.fetch_submissions(
            subreddits=args.subreddits,
            limit=args.limit,
            sort_by=args.sort_by,
            time_filter=args.time_filter
        )

        extract_time = time.time() - extract_start
        logger.info(f"✓ Extracted {len(submissions)} submissions in {extract_time:.2f}s")

        if not submissions:
            logger.warning("No submissions found, ending pipeline")
            return 0

        # Step 2: Transform with LLM analysis
        logger.info("STEP 2: Analyzing submissions with LLM")
        transform_start = time.time()

        analyses = analyzer.analyze_batch(submissions, batch_size=args.batch_size)

        transform_time = time.time() - transform_start
        logger.info(f"✓ Analyzed {len(analyses)} submissions in {transform_time:.2f}s")

        # Step 3: Validate and filter results
        logger.info("STEP 3: Validating analysis quality")
        validate_start = time.time()

        # Filter by scores
        high_quality_analyses = [
            a for a in analyses
            if (a.final_score >= args.min_score and
                a.confidence_score >= args.min_confidence and
                validator.validate_analysis(a))
        ]

        validate_time = time.time() - validate_start
        logger.info(f"✓ Filtered to {len(high_quality_analyses)} high-quality analyses in {validate_time:.2f}s")

        # Step 4: Load to database
        load_stats = {"stored": 0, "skipped": 0, "errors": 0}
        if not args.dry_run and high_quality_analyses:
            logger.info("STEP 4: Storing analyses to database")
            load_start = time.time()

            # Create tables if needed
            db_loader.create_tables()

            # Store analyses
            load_stats = db_loader.store_analyses(high_quality_analyses)

            load_time = time.time() - load_start
            logger.info(f"✓ Stored {load_stats['stored']} analyses in {load_time:.2f}s")

        # Pipeline completion
        pipeline_time = time.time() - pipeline_start_time

        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total execution time: {pipeline_time:.2f}s")
        logger.info("")
        logger.info("Step Results:")
        logger.info(f"  1. Extract: {len(submissions)} submissions")
        logger.info(f"  2. Analyze: {len(analyses)} analyses")
        logger.info(f"  3. Filter: {len(high_quality_analyses)} high-quality")
        logger.info(f"  4. Store: {load_stats['stored']} stored, {load_stats['skipped']} skipped, {load_stats['errors']} errors")
        logger.info("")

        # Performance metrics
        throughput = len(submissions) / extract_time if extract_time > 0 else 0
        analysis_rate = len(analyses) / transform_time if transform_time > 0 else 0

        logger.info("Performance:")
        logger.info(f"  - Reddit extraction: {throughput:.1f} submissions/second")
        logger.info(f"  - LLM analysis: {analysis_rate:.2f} analyses/second")
        logger.info(f"  - Overall pipeline: {len(submissions) / pipeline_time:.2f} submissions/second")
        logger.info("")

        # Quality metrics
        if analyses:
            quality_summary = validator.get_quality_summary(analyses)
            logger.info("Quality Metrics:")
            logger.info(f"  - Validation rate: {quality_summary['validation_rate']:.1f}%")
            logger.info(f"  - High score rate: {quality_summary['high_score_rate']:.1f}%")
            logger.info(f"  - Average score: {quality_summary['avg_final_score']:.1f}")
            logger.info(f"  - Trust distribution: {quality_summary['trust_distribution']}")

        # Database statistics
        if not args.dry_run and db_loader:
            db_stats = db_loader.get_statistics()
            logger.info("")
            logger.info("Database Statistics:")
            logger.info(f"  - Total opportunities: {db_stats['total_opportunities']}")
            logger.info(f"  - Average score: {db_stats['average_score']:.1f}")
            logger.info(f"  - High score percentage: {db_stats['high_score_percentage']:.1f}%")

        logger.info("✓ Pipeline completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.debug("Exception details:", exc_info=True)
        return 1


def main() -> int:
    """Main entry point for the pipeline"""
    try:
        # Parse arguments
        args = parse_arguments()

        # Setup logging
        logger.setLevel(getattr(logging, args.log_level))

        # Run the pipeline
        import asyncio
        return asyncio.run(run_pipeline(args))

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Pipeline initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())