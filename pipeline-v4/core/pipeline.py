"""
Pipeline orchestrator
Coordinates Reddit extraction, LLM analysis, and database storage
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Union

from extract.reddit_client import RedditClient
from transform.analyzer import OpportunityAnalyzer
from load.loader_factory import BaseLoader, get_loader
from core.staging import StagingLayer
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PipelineResults:
    """Pipeline execution results"""
    total_time: float
    submissions_fetched: int
    analyses_completed: int
    analyses_saved: int
    analyses_skipped: int
    errors: int


class Pipeline:
    """
    Simple 3-stage pipeline orchestrator
    Extract → Transform → Load
    """

    def __init__(
        self,
        reddit_client: RedditClient | None = None,
        analyzer: OpportunityAnalyzer | None = None,
        loader: BaseLoader | None = None,
        staging: StagingLayer | None = None,
        settings = None
    ):
        """Initialize with dependency injection"""
        self.settings = settings or get_settings()

        # Initialize components (or use provided)
        self.reddit = reddit_client or RedditClient()
        self.analyzer = analyzer or OpportunityAnalyzer(self.settings)

        # Initialize loader using factory pattern
        self.loader = get_loader(self.settings, loader)

        self.staging = staging or StagingLayer()

        logger.info(f"Database loader: {'SQLModel' if self.settings.use_sqlmodel_loader else 'psycopg2'}")

    def run(
        self,
        subreddits: List[str] | None = None,
        limit: int | None = None
    ) -> PipelineResults:
        """
        Run the complete pipeline

        Args:
            subreddits: List of subreddit names (uses default if None)
            limit: Number of submissions per subreddit (uses default if None)

        Returns:
            Pipeline execution results
        """
        start_time = time.time()

        # Use defaults if not provided
        subreddits = subreddits or self.settings.default_subreddits
        limit = limit or self.settings.default_limit

        logger.info(f"Starting pipeline: {subreddits}, limit={limit}")

        # Counters
        fetched = 0
        analyzed = 0
        saved = 0
        skipped = 0
        errors = 0

        try:
            # STAGE 1: Extract from Reddit
            logger.info("Stage 1: Extracting from Reddit...")
            submissions = self.reddit.fetch_submissions(
                subreddits=subreddits,
                limit=limit,
                sort_by="hot"
            )
            fetched = len(submissions)
            logger.info(f"✓ Extracted {fetched} submissions")

            # STAGE 2: Transform with LLM
            logger.info("Stage 2: Analyzing with LLM...")
            analyses: List[AnalysisResult] = []

            for submission in submissions:
                # Check deduplication
                if self.staging.is_duplicate(submission):
                    logger.info(f"⊘ Skipping duplicate: {submission.id}")
                    skipped += 1
                    continue

                try:
                    # Analyze
                    analysis = self.analyzer.analyze(submission)
                    analyses.append(analysis)
                    analyzed += 1

                    # Checkpoint
                    self.staging.checkpoint([submission])

                    # Extract WTP score from market metrics (monetization_potential is closest)
                    wtp_score = analysis.market_metrics.monetization_potential

                    logger.info(
                        f"✓ Analyzed {submission.id}: "
                        f"WTP={wtp_score:.1f}, "
                        f"Score={analysis.final_score:.1f}"
                    )

                except Exception as e:
                    logger.error(f"Analysis failed for {submission.id}: {e}")
                    errors += 1

            # STAGE 3: Load to PostgreSQL
            logger.info("Stage 3: Loading to database...")
            for analysis in analyses:
                try:
                    if self.loader.save_analysis(analysis):
                        saved += 1
                except Exception as e:
                    logger.error(f"Save failed for {analysis.submission_id}: {e}")
                    errors += 1

            logger.info(f"✓ Saved {saved} analyses to database")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

        finally:
            total_time = time.time() - start_time

            # Results
            results = PipelineResults(
                total_time=total_time,
                submissions_fetched=fetched,
                analyses_completed=analyzed,
                analyses_saved=saved,
                analyses_skipped=skipped,
                errors=errors
            )

            # Summary
            logger.info("=" * 50)
            logger.info("PIPELINE COMPLETE")
            logger.info(f"Total Time: {total_time:.2f}s")
            logger.info(f"Fetched: {fetched}")
            logger.info(f"Analyzed: {analyzed}")
            logger.info(f"Saved: {saved}")
            logger.info(f"Skipped: {skipped}")
            logger.info(f"Errors: {errors}")
            logger.info("=" * 50)

            return results