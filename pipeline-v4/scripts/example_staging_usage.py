#!/usr/bin/env python3
"""
Example usage of the staging layer for deduplication
"""

import sys
from pathlib import Path
import logging
from datetime import UTC, datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.reddit import RedditSubmission
from core.staging import StagingLayer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Demonstrate staging layer usage"""
    # Initialize staging layer
    staging = StagingLayer("example_staging")

    # Create some sample submissions
    submissions = [
        RedditSubmission(
            id="abc123",
            title="Looking for productivity tools",
            text="What tools do you use to stay productive?",
            author="user1",
            upvotes=50,
            downvotes=2,
            score=48,
            comments_count=25,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/productivity/abc123"
        ),
        RedditSubmission(
            id="def456",
            title="Best project management software",
            text="Need recommendations for project management tools",
            author="user2",
            upvotes=30,
            downvotes=1,
            score=29,
            comments_count=15,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/productivity/def456"
        ),
        RedditSubmission(
            id="abc123",  # Duplicate of first submission
            title="Looking for productivity tools",
            text="What tools do you use to stay productive?",
            author="user1",
            upvotes=50,
            downvotes=2,
            score=48,
            comments_count=25,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/productivity/abc123"
        )
    ]

    # Check for duplicates before processing
    logger.info(f"Processing {len(submissions)} submissions...")

    for i, submission in enumerate(submissions, 1):
        if staging.is_duplicate(submission):
            logger.info(f"[{i}] Skipping duplicate: {submission.id}")
        else:
            logger.info(f"[{i}] Processing new submission: {submission.id} - {submission.title}")
            # Here you would do your analysis
            # After processing, checkpoint the submission
            staging.checkpoint_single(submission)

    # Show statistics
    stats = staging.get_statistics()
    logger.info(f"\nStaging Statistics:")
    logger.info(f"  Total processed: {stats['processed_count']}")
    logger.info(f"  State file: {stats['state_file']}")
    logger.info(f"  Directory: {stats['staging_directory']}")

    # Demonstrate batch checkpointing
    logger.info("\nDemonstrating batch checkpointing...")
    new_submissions = [
        RedditSubmission(
            id="ghi789",
            title=f"New submission {i}",
            text="Content",
            author="user",
            upvotes=10,
            downvotes=0,
            score=10,
            comments_count=5,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink=f"https://reddit.com/r/test/ghi789_{i}"
        )
        for i in range(3)
    ]

    staging.checkpoint(new_submissions)
    logger.info(f"Checkpointed {len(new_submissions)} new submissions")

    # Final statistics
    final_stats = staging.get_statistics()
    logger.info(f"\nFinal Statistics:")
    logger.info(f"  Total processed: {final_stats['processed_count']}")

    # Uncomment to clear the staging state
    # logger.info("\nClearing staging state...")
    # staging.clear()
    # logger.info("State cleared!")


if __name__ == "__main__":
    main()