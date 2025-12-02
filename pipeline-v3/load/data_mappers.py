"""
Data mapping layer for converting between domain models and database entities
"""

from datetime import datetime
from typing import Optional
import logging

from models import AnalysisResult, Opportunity, RedditSubmission

logger = logging.getLogger(__name__)


class AnalysisToOpportunityMapper:
    """
    Mapper for converting AnalysisResult to Opportunity database entities
    Handles the mapping logic separately from database operations
    """

    def __init__(self, preserve_reddit_metadata: bool = True):
        """
        Initialize mapper with configuration

        Args:
            preserve_reddit_metadata: Whether to preserve original Reddit metadata
        """
        self.preserve_reddit_metadata = preserve_reddit_metadata

    def map_single(
        self,
        analysis: AnalysisResult,
        reddit_submission: Optional[RedditSubmission] = None
    ) -> Opportunity:
        """
        Convert a single AnalysisResult to Opportunity

        Args:
            analysis: AnalysisResult to convert
            reddit_submission: Optional RedditSubmission with original metadata

        Returns:
            Opportunity database entity
        """
        if self.preserve_reddit_metadata and reddit_submission is not None:
            return self._map_with_original_metadata(analysis, reddit_submission)
        else:
            return self._map_with_placeholder_metadata(analysis)

    def map_batch(
        self,
        analyses: list[AnalysisResult],
        reddit_submissions: Optional[list[RedditSubmission]] = None
    ) -> list[Opportunity]:
        """
        Convert multiple AnalysisResults to Opportunities

        Args:
            analyses: List of AnalysisResults to convert
            reddit_submissions: Optional list of RedditSubmissions with original metadata

        Returns:
            List of Opportunity database entities
        """
        opportunities = []

        # Create submission lookup if reddit_submissions provided
        submission_lookup = {}
        if reddit_submissions:
            for submission in reddit_submissions:
                submission_lookup[submission.id] = submission

        for analysis in analyses:
            reddit_submission = submission_lookup.get(analysis.submission_id)
            opportunity = self.map_single(analysis, reddit_submission)
            opportunities.append(opportunity)

        return opportunities

    def _map_with_original_metadata(
        self,
        analysis: AnalysisResult,
        reddit_submission: RedditSubmission
    ) -> Opportunity:
        """
        Convert AnalysisResult to Opportunity preserving original Reddit metadata

        Args:
            analysis: AnalysisResult to convert
            reddit_submission: RedditSubmission with original metadata

        Returns:
            Opportunity database entity with preserved metadata
        """
        logger.debug(f"Mapping analysis {analysis.submission_id} with preserved Reddit metadata")

        return Opportunity(
            # Source Reddit data (preserved from original)
            submission_id=analysis.submission_id,
            reddit_title=reddit_submission.title,
            reddit_url=self._build_reddit_url(reddit_submission),
            subreddit=reddit_submission.subreddit,
            reddit_author=reddit_submission.author,
            reddit_upvotes=reddit_submission.upvotes,
            reddit_comments_count=reddit_submission.comments_count,
            reddit_created_at=reddit_submission.created_utc,

            # App idea analysis
            app_title=analysis.app_idea.title,
            app_concept=analysis.app_idea.app_concept,
            problem_statement=analysis.app_idea.problem_statement,
            target_audience=analysis.app_idea.target_audience,
            core_functions=analysis.app_idea.core_functions,

            # Market metrics
            market_demand=analysis.market_metrics.market_demand,
            pain_intensity=analysis.market_metrics.pain_intensity,
            monetization_potential=analysis.market_metrics.monetization_potential,
            competition_level=analysis.market_metrics.competition_level,
            technical_feasibility=analysis.market_metrics.technical_feasibility,

            # Overall scoring
            final_score=analysis.final_score,
            confidence_score=analysis.confidence_score,
            trust_level=analysis.trust_level,

            # AI Quality Assessment
            content_quality_score=analysis.content_quality_score,
            is_spam=analysis.is_spam,
            spam_indicators=analysis.spam_indicators,

            # Semantic search
            embedding=analysis.embedding,

            # Metadata
            analyzed_at=analysis.analyzed_at,
        )

    def _map_with_placeholder_metadata(self, analysis: AnalysisResult) -> Opportunity:
        """
        Convert AnalysisResult to Opportunity with placeholder metadata

        Args:
            analysis: AnalysisResult to convert

        Returns:
            Opportunity database entity with placeholder metadata
        """
        logger.debug(f"Mapping analysis {analysis.submission_id} with placeholder metadata")

        return Opportunity(
            # Source Reddit data (placeholder behavior)
            submission_id=analysis.submission_id,
            reddit_title="Reddit Submission",
            reddit_url=f"https://reddit.com/r/test/{analysis.submission_id}",
            subreddit="test",
            reddit_author=None,
            reddit_upvotes=0,
            reddit_comments_count=0,
            reddit_created_at=datetime.utcnow(),

            # App idea analysis
            app_title=analysis.app_idea.title,
            app_concept=analysis.app_idea.app_concept,
            problem_statement=analysis.app_idea.problem_statement,
            target_audience=analysis.app_idea.target_audience,
            core_functions=analysis.app_idea.core_functions,

            # Market metrics
            market_demand=analysis.market_metrics.market_demand,
            pain_intensity=analysis.market_metrics.pain_intensity,
            monetization_potential=analysis.market_metrics.monetization_potential,
            competition_level=analysis.market_metrics.competition_level,
            technical_feasibility=analysis.market_metrics.technical_feasibility,

            # Overall scoring
            final_score=analysis.final_score,
            confidence_score=analysis.confidence_score,
            trust_level=analysis.trust_level,

            # AI Quality Assessment
            content_quality_score=analysis.content_quality_score,
            is_spam=analysis.is_spam,
            spam_indicators=analysis.spam_indicators,

            # Semantic search
            embedding=analysis.embedding,

            # Metadata
            analyzed_at=analysis.analyzed_at,
        )

    def _build_reddit_url(self, reddit_submission: RedditSubmission) -> str:
        """
        Build Reddit URL from submission data

        Args:
            reddit_submission: RedditSubmission with URL components

        Returns:
            Full Reddit URL
        """
        # Prefer existing permalink if available and complete
        if reddit_submission.permalink and 'reddit.com' in reddit_submission.permalink:
            return reddit_submission.permalink

        # Build URL from components - using format expected by tests
        if reddit_submission.id:
            return f"https://reddit.com/r/{reddit_submission.subreddit}/{reddit_submission.id}"
        else:
            return f"https://reddit.com/r/{reddit_submission.subreddit}/unknown"


class OpportunityAnalysisMapper:
    """
    Mapper for converting Opportunity entities back to AnalysisResult domain objects
    Useful for read operations and data export
    """

    def map_single(self, opportunity: Opportunity) -> AnalysisResult:
        """
        Convert a single Opportunity to AnalysisResult

        Args:
            opportunity: Opportunity to convert

        Returns:
            AnalysisResult domain object
        """
        from models.analysis import AppIdea, MarketMetrics

        # Reconstruct domain objects
        app_idea = AppIdea(
            title=opportunity.app_title,
            app_concept=opportunity.app_concept,
            problem_statement=opportunity.problem_statement,
            target_audience=opportunity.target_audience,
            core_functions=opportunity.core_functions
        )

        market_metrics = MarketMetrics(
            market_demand=opportunity.market_demand,
            pain_intensity=opportunity.pain_intensity,
            monetization_potential=opportunity.monetization_potential,
            competition_level=opportunity.competition_level,
            technical_feasibility=opportunity.technical_feasibility
        )

        return AnalysisResult(
            submission_id=opportunity.submission_id,
            analyzed_at=opportunity.analyzed_at,
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=opportunity.final_score,
            confidence_score=opportunity.confidence_score,
            trust_level=opportunity.trust_level,
            embedding=opportunity.embedding,
            embedding_metadata={}  # Would need to be stored separately if needed
        )

    def map_batch(self, opportunities: list[Opportunity]) -> list[AnalysisResult]:
        """
        Convert multiple Opportunities to AnalysisResults

        Args:
            opportunities: List of Opportunities to convert

        Returns:
            List of AnalysisResult domain objects
        """
        return [self.map_single(opp) for opp in opportunities]