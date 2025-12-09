"""
Pipeline V4 CLI
Usage: python main.py [--subreddits r1,r2] [--limit N] [--clear-staging]
"""

import argparse
import logging
import sys
from config.settings import get_settings
from core.pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RedditHarbor Pipeline V4"
    )

    parser.add_argument(
        '--subreddits',
        type=str,
        help='Comma-separated list of subreddits (e.g., "productivity,tools")'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Number of submissions per subreddit'
    )
    parser.add_argument(
        '--clear-staging',
        action='store_true',
        help='Clear staging state before running'
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = None
    try:
        settings = get_settings()
        pipeline = Pipeline(settings=settings)

        # Clear staging if requested
        if args.clear_staging:
            pipeline.staging.clear()
            logger.info("Staging state cleared")

        # Parse subreddits
        subreddits = None
        if args.subreddits:
            subreddits = [s.strip() for s in args.subreddits.split(',')]

        # Run pipeline
        results = pipeline.run(
            subreddits=subreddits,
            limit=args.limit
        )

        # Exit code based on success
        if results.errors > 0:
            logger.warning(f"Pipeline completed with {results.errors} errors")
            sys.exit(1)
        else:
            logger.info("Pipeline completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if pipeline:
            pipeline.loader.close()


if __name__ == "__main__":
    main()