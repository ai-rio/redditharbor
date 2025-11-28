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
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import List

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import pipeline components
from config import get_settings
from extract import RedditClient
from transform import OpportunityAnalyzer, AnalysisValidator
from load import DatabaseLoader


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


async def run_pipeline(args: argparse.Namespace) -> int:
    """Run the complete pipeline with the given arguments"""
    settings = get_settings()
    pipeline_start_time = time.time()

    logger.info("=" * 80)
    logger.info("PIPELINE V3 - Reddit Opportunity Analysis")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Subreddits: {args.subreddits or settings.default_subreddits}")
    logger.info(f"  - Limit: {args.limit}")
    logger.info(f"  - Sort by: {args.sort_by}")
    logger.info(f"  - Min score: {args.min_score}")
    logger.info(f"  - Min confidence: {args.min_confidence}")
    logger.info(f"  - Test mode: {args.test_mode}")
    logger.info(f"  - Dry run: {args.dry_run}")
    logger.info("")

    # Initialize components
    reddit_client = None
    analyzer = None
    validator = None
    db_loader = None

    try:
        # Step 0: Initialize components
        logger.info("STEP 0: Initializing pipeline components")
        reddit_client = RedditClient()
        analyzer = OpportunityAnalyzer()
        validator = AnalysisValidator()

        if not args.dry_run:
            db_loader = DatabaseLoader()

        # Test connections
        if not args.test_mode:
            if not reddit_client.test_connection():
                raise RuntimeError("Reddit API connection failed")

            if not analyzer.test_connection():
                raise RuntimeError("LLM API connection failed")

            if db_loader and not db_loader.test_connection():
                raise RuntimeError("Database connection failed")

        logger.info("✓ All components initialized successfully")

        # Step 1: Extract Reddit submissions
        logger.info("STEP 1: Extracting Reddit submissions")
        extract_start = time.time()

        subreddits = args.subreddits or settings.default_subreddits
        submissions = reddit_client.fetch_submissions(
            subreddits=subreddits,
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

        batch_size = args.batch_size or settings.batch_size
        analyses = analyzer.analyze_batch(submissions, batch_size=batch_size)

        transform_time = time.time() - transform_start
        logger.info(f"✓ Analyzed {len(analyses)} submissions in {transform_time:.2f}s")

        # Step 3: Validate and filter results
        logger.info("STEP 3: Validating analysis quality")
        validate_start = time.time()

        if args.validate_quality:
            high_quality_analyses = validator.filter_high_quality_analyses(
                analyses,
                min_score=args.min_score,
                min_confidence=args.min_confidence
            )
        else:
            # Basic filtering by scores
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
        # Parse and validate arguments
        args = parse_arguments()
        settings = get_settings()

        validate_arguments(args, settings)

        # Setup logging
        setup_logging(args.log_level)

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