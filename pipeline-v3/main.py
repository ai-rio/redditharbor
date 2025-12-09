#!/usr/bin/env python3
"""
Pipeline v3 - Clean Reddit Data Processing Pipeline

A minimal, type-safe Reddit data extraction and analysis pipeline following ELT pattern:
Extract → Transform → Load

Usage:
    python -m pipeline_v3 --limit 25 --subreddits productivity tools
    python -m pipeline_v3 --test-mode --limit 5
    python -m pipeline_v3 --score-threshold 70.0 --min-confidence 60.0
"""

import argparse
import logging
import sys

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import pipeline components
from config import get_settings
from extract import RedditClient
from load import DatabaseLoader
from orchestration import PipelineConfiguration, PipelineOrchestrator
from transform import AnalysisValidator


def setup_logging(log_level: str = "INFO") -> None:
    """Set up comprehensive logging for the pipeline"""
    settings = get_settings()

    # Create logs directory if it doesn't exist
    log_path = settings.project_root / "logs"
    log_path.mkdir(exist_ok=True)

    # Configure logger
    logger.setLevel(getattr(logging, log_level.upper()))

    # Add file handler
    file_handler = logging.FileHandler(log_path / settings.log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for the pipeline"""
    parser = argparse.ArgumentParser(
        description="Pipeline v3 - Reddit Opportunity Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --limit 25 --subreddits productivity tools
  %(prog)s --test-mode --limit 5
  %(prog)s --score-threshold 70.0 --min-confidence 60.0 --sort-by top
        """
    )

    # Reddit extraction options
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of Reddit submissions to process (default: 10)"
    )

    parser.add_argument(
        "--subreddits",
        type=str,
        nargs="+",
        help="List of subreddits to fetch from (default: from settings)"
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
        default=0.0,
        help="Minimum opportunity score to store (default: 0.0)"
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=40.0,
        help="Minimum confidence score to store (default: 40.0)"
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
        help="Batch size for LLM processing (default: from settings)"
    )

    parser.add_argument(
        "--test-mode",
        action="store_true",
        default=False,
        help="Enable test mode with mocked data"
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


def validate_arguments(args: argparse.Namespace, settings) -> None:
    """Validate command line arguments"""
    if args.limit <= 0:
        raise ValueError("--limit must be a positive integer")

    if not 0.0 <= args.min_score <= 100.0:
        raise ValueError("--min-score must be between 0.0 and 100.0")

    if not 0.0 <= args.min_confidence <= 100.0:
        raise ValueError("--min-confidence must be between 0.0 and 100.0")

    if args.sort_by == "top" and not args.time_filter:
        raise ValueError("--time-filter is required when --sort-by is 'top'")


def run_pipeline(args: argparse.Namespace) -> int:
    """Run the complete pipeline using the orchestrator"""
    settings = get_settings()

    try:
        # Create pipeline configuration from arguments
        config = PipelineConfiguration(
            subreddits=args.subreddits or settings.default_subreddits,
            limit=args.limit,
            sort_by=args.sort_by,
            time_filter=args.time_filter,
            min_score=args.min_score,
            min_confidence=args.min_confidence,
            batch_size=args.batch_size,
            test_mode=args.test_mode,
            dry_run=args.dry_run,
            validate_quality=args.validate_quality
        )

        # Initialize components with dependency injection
        reddit_client = RedditClient()
        validator = AnalysisValidator()
        # Use OnlyMaps integration to fix database schema issues
        if args.dry_run:
            db_loader = None
        else:
            try:
                from load.onlymaps_database import OnlyMapsDatabaseLoader
                db_loader = OnlyMapsDatabaseLoader()
                print("✓ Using OnlyMaps DatabaseLoader with schema flexibility")
            except ImportError:
                # Fallback to original DatabaseLoader if OnlyMaps not available
                db_loader = DatabaseLoader()
                print("⚠️ Falling back to SQLAlchemy DatabaseLoader")

        # Create orchestrator with injected dependencies
        orchestrator = PipelineOrchestrator(
            reddit_client=reddit_client,
            validator=validator,
            database_loader=db_loader,
            settings=settings
        )

        # Execute pipeline
        results = orchestrator.execute_pipeline(config)

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
        # Parse and validate arguments
        args = parse_arguments()
        settings = get_settings()

        validate_arguments(args, settings)

        # Setup logging
        setup_logging(args.log_level)

        # Run the pipeline
        return run_pipeline(args)

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Pipeline initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
