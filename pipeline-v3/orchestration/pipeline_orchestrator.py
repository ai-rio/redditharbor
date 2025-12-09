"""
Pipeline orchestration with dependency injection and clean separation of concerns
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

from config import get_settings
from extract import RedditClient
from load import DatabaseLoader
from models.analysis import AnalysisResult
from models.reddit import RedditSubmission
from monitoring.metrics_collector import get_collector
from staging import StagingConfig, StagingLayer
from transform import AnalysisValidator
from transform.analyzer_factory import create_analyzer

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfiguration:
    """Configuration for pipeline execution"""
    subreddits: list[str] | None = None
    limit: int = 10
    sort_by: str = "hot"
    time_filter: str = "week"
    min_score: float = 0.0
    min_confidence: float = 40.0
    batch_size: int | None = None
    test_mode: bool = False
    dry_run: bool = False
    validate_quality: bool = False
    enable_staging: bool = True
    staging_batch_size: int = 50
    enable_deduplication: bool = True
    enable_checkpoints: bool = True
    checkpoint_interval: int = 25


@dataclass
class PipelineResults:
    """Results from pipeline execution"""
    # Execution metrics
    total_execution_time: float
    extraction_time: float
    analysis_time: float
    validation_time: float
    storage_time: float

    # Data metrics
    submissions_extracted: int
    analyses_generated: int
    high_quality_analyses: int
    analyses_stored: int
    analyses_skipped: int
    analysis_errors: int

    # Quality metrics (with defaults)
    staging_time: float = 0.0
    validation_rate: float = 0.0
    high_score_rate: float = 0.0
    average_score: float = 0.0
    trust_distribution: dict[str, int] = None

    # Database statistics
    database_stats: dict[str, Any] | None = None


class PipelineOrchestrator:
    """
    Orchestrates the complete Reddit opportunity analysis pipeline
    with dependency injection and clean separation of concerns
    """

    def __init__(
        self,
        reddit_client: RedditClient | None = None,
        analyzer_factory=None,
        database_loader: DatabaseLoader | None = None,
        validator: AnalysisValidator | None = None,
        staging_layer: StagingLayer | None = None,
        settings=None
    ):
        """
        Initialize pipeline orchestrator with dependency injection

        Args:
            reddit_client: Reddit API client (will create default if None)
            analyzer_factory: Factory for creating analyzers (will use default if None)
            database_loader: Database loader (will create default if None)
            validator: Analysis validator (will create default if None)
            staging_layer: Staging layer for extract→transform buffer (will create default if None)
            settings: Application settings
        """
        self.settings = settings or get_settings()

        # Initialize components with dependency injection
        self.reddit_client = reddit_client or RedditClient()
        self.database_loader = database_loader
        self.validator = validator or AnalysisValidator()

        # Analyzer factory for creating appropriate analyzers
        self.analyzer_factory = analyzer_factory

        # Initialize staging layer
        self.staging_layer = staging_layer

        # Pipeline state
        self._current_analyzer = None

    def initialize_connections(self, config: PipelineConfiguration) -> None:
        """
        Initialize and test connections to external services

        Args:
            config: Pipeline configuration

        Raises:
            RuntimeError: If any critical connection fails
        """
        logger.info("Initializing pipeline connections")

        # Test Reddit connection
        if not config.test_mode:
            if not self.reddit_client.test_connection():
                raise RuntimeError("Reddit API connection failed")
            logger.info("✓ Reddit API connection successful")

        # Initialize analyzer
        if config.test_mode:
            factory_type = 'test'
        elif os.environ.get('AGNO_ANALYZER_ENABLED', '').lower() == 'true':
            factory_type = 'agno'
        else:
            factory_type = 'production'

        analyzer_config = {}
        if not config.test_mode:
            analyzer_config.update({
                'batch_size': config.batch_size or self.settings.batch_size
            })

        self._current_analyzer = create_analyzer(
            factory_type=factory_type,
            config=analyzer_config
        )

        # Test analyzer connection
        if hasattr(self._current_analyzer, 'test_connection'):
            if not self._current_analyzer.test_connection():
                if config.test_mode:
                    logger.warning("Test mode analyzer connection test failed, continuing anyway")
                else:
                    raise RuntimeError("Analyzer connection failed")
        else:
            logger.info("Analyzer does not have test_connection method, skipping test")

        logger.info("✓ Analyzer connection successful")

        # Test database connection if not in dry run
        if not config.dry_run and self.database_loader:
            if not self.database_loader.test_connection():
                raise RuntimeError("Database connection failed")
            logger.info("✓ Database connection successful")

        logger.info("✓ All connections initialized successfully")

    def execute_pipeline(self, config: PipelineConfiguration) -> PipelineResults:
        """
        Execute the complete pipeline with the given configuration

        Args:
            config: Pipeline configuration

        Returns:
            PipelineResults with execution metrics and statistics

        Raises:
            RuntimeError: If pipeline execution fails
        """
        pipeline_start_time = time.time()

        logger.info("=" * 80)
        logger.info("PIPELINE V3 - Reddit Opportunity Analysis")
        logger.info("=" * 80)
        logger.info("Configuration:")
        logger.info(f"  - Subreddits: {config.subreddits or self.settings.default_subreddits}")
        logger.info(f"  - Limit: {config.limit}")
        logger.info(f"  - Sort by: {config.sort_by}")
        logger.info(f"  - Min score: {config.min_score}")
        logger.info(f"  - Min confidence: {config.min_confidence}")
        logger.info(f"  - Test mode: {config.test_mode}")
        logger.info(f"  - Dry run: {config.dry_run}")
        logger.info(f"  - Staging enabled: {config.enable_staging}")
        if config.enable_staging:
            logger.info(f"  - Staging batch size: {config.staging_batch_size}")
            logger.info(f"  - Deduplication: {config.enable_deduplication}")
            logger.info(f"  - Checkpoints: {config.enable_checkpoints}")
        logger.info("")

        try:
            # Initialize staging layer if enabled
            if config.enable_staging and not self.staging_layer:
                from pathlib import Path
                staging_dir = Path("pipeline_staging")
                staging_config = StagingConfig(
                    staging_directory=str(staging_dir),
                    max_batch_size=config.staging_batch_size,
                    deduplication_enabled=config.enable_deduplication,
                    checkpoint_interval=config.checkpoint_interval if config.enable_checkpoints else 0
                )
                self.staging_layer = StagingLayer(staging_config)
                logger.info("✓ Staging layer initialized")

            # Initialize connections
            self.initialize_connections(config)

            # Step 1: Extract Reddit submissions
            submissions, extraction_time = self._extract_submissions(config)

            # Step 1.5: Stage submissions (if staging enabled)
            if config.enable_staging and self.staging_layer:
                submissions, staging_time = self._stage_submissions(submissions, config)
            else:
                staging_time = 0.0

            if not submissions:
                logger.warning("No submissions found, ending pipeline")
                return self._create_empty_results(pipeline_start_time)

            # Step 2: Analyze submissions with individual opportunity tracking
            analyses, analysis_time = self._analyze_submissions_with_tracking(submissions, config)

            # Step 3: Validate and filter results
            high_quality_analyses, validation_time = self._validate_analyses(analyses, config)

            # Step 4: Store to database
            storage_stats, storage_time = self._store_analyses(
                high_quality_analyses, submissions, config
            )

            # Create results
            results = self._create_results(
                pipeline_start_time, extraction_time, staging_time, analysis_time,
                validation_time, storage_time, submissions, analyses,
                high_quality_analyses, storage_stats, config
            )

            # Log completion summary
            self._log_completion_summary(results, config)

            return results

        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
            raise

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise RuntimeError(f"Pipeline execution failed: {e}")

    def _extract_submissions(self, config: PipelineConfiguration) -> tuple[list[RedditSubmission], float]:
        """Extract Reddit submissions"""
        logger.info("STEP 1: Extracting Reddit submissions")

        # Get metrics collector
        metrics = get_collector()

        # Track extraction phase
        with metrics.track("extract") as context:
            extract_start = time.time()

            subreddits = config.subreddits or self.settings.default_subreddits
            submissions = self.reddit_client.fetch_submissions(
                subreddits=subreddits,
                limit=config.limit,
                sort_by=config.sort_by,
                time_filter=config.time_filter
            )

            extraction_time = time.time() - extract_start

            # Add metadata to context
            context["metadata"] = {
                "subreddits": subreddits,
                "limit": config.limit,
                "extracted_count": len(submissions),
                "sort_by": config.sort_by,
                "time_filter": config.time_filter
            }

            logger.info(f"✓ Extracted {len(submissions)} submissions in {extraction_time:.2f}s")

            return submissions, extraction_time

    def _stage_submissions(self, submissions: list[RedditSubmission], config: PipelineConfiguration) -> tuple[list[RedditSubmission], float]:
        """
        Stage submissions with deduplication and checkpointing

        Args:
            submissions: List of extracted Reddit submissions
            config: Pipeline configuration

        Returns:
            Tuple of (staged submissions, staging time)
        """
        logger.info("STEP 1.5: Staging submissions with deduplication")
        staging_start = time.time()

        if not self.staging_layer:
            logger.warning("Staging layer not initialized, returning original submissions")
            return submissions, 0.0

        # Store submissions in staging layer
        batch_ids = self.staging_layer.store_submissions(submissions)

        # Retrieve deduplicated submissions from staging
        staged_submissions = []
        if isinstance(batch_ids, str):
            batch_ids = [batch_ids]

        for batch_id in batch_ids:
            batch_submissions = self.staging_layer.get_batch(batch_id)
            staged_submissions.extend(batch_submissions)

        staging_time = time.time() - staging_start
        logger.info(f"✓ Staged {len(staged_submissions)} unique submissions in {staging_time:.2f}s")

        # Log staging statistics
        if hasattr(self.staging_layer, 'get_statistics'):
            stats = self.staging_layer.get_statistics()
            logger.info(f"  - Processed submissions: {stats['processed_submissions']}")
            logger.info(f"  - Deduplication rate: {((len(submissions) - len(staged_submissions)) / len(submissions) * 100):.1f}%")

        return staged_submissions, staging_time

    def _analyze_submissions_with_tracking(
        self, submissions: list[RedditSubmission], config: PipelineConfiguration
    ) -> tuple[list[AnalysisResult], float]:
        """Analyze submissions with individual opportunity tracking"""
        logger.info("STEP 2: Analyzing submissions with LLM (with individual tracking)")

        # Get metrics collector
        metrics = get_collector()
        transform_start = time.time()
        analyses = []

        # Process each submission individually to track opportunities
        for i, submission in enumerate(submissions):
            opportunity_id = f"opp-{getattr(submission, 'id', f'unknown-{i}')}"

            # Track individual submission analysis
            with metrics.track("transform", opportunity_id=opportunity_id) as context:
                try:
                    # Analyze single submission
                    result = self._current_analyzer.analyze_submission(submission)
                    analyses.append(result)

                    # Add opportunity-specific metadata
                    context["metadata"] = {
                        "submission_title": getattr(submission, 'title', '')[:100],
                        "subreddit": getattr(submission, 'subreddit', ''),
                        "final_score": getattr(result, 'final_score', 0.0),
                        "trust_level": getattr(result, 'trust_level', 'UNKNOWN'),
                        "is_spam": getattr(result, 'is_spam', False),
                        "batch_position": i + 1,
                        "total_batch_size": len(submissions)
                    }

                    logger.debug(f"✓ Analyzed opportunity {opportunity_id} with score {getattr(result, 'final_score', 0.0):.1f}")

                except Exception as e:
                    logger.error(f"Failed to analyze opportunity {opportunity_id}: {e}")
                    # Continue with next submission
                    continue

        transform_time = time.time() - transform_start

        # Log completion summary
        logger.info(f"✓ Analyzed {len(analyses)}/{len(submissions)} submissions in {transform_time:.2f}s")

        # Calculate success rate
        success_rate = (len(analyses) / len(submissions) * 100) if submissions else 0
        logger.info(f"  Success rate: {success_rate:.1f}%")

        return analyses, transform_time

    def _analyze_submissions(
        self, submissions: list[RedditSubmission], config: PipelineConfiguration
    ) -> tuple[list[AnalysisResult], float]:
        """Analyze submissions with LLM (legacy method for backward compatibility)"""
        logger.info("STEP 2: Analyzing submissions with LLM")

        # Get metrics collector
        metrics = get_collector()

        # Track transform phase with overall context
        with metrics.track("transform", agent_name="pipeline_orchestrator") as context:
            transform_start = time.time()

            batch_size = config.batch_size or self.settings.batch_size
            analyses = self._current_analyzer.analyze_batch(submissions, batch_size=batch_size)

            transform_time = time.time() - transform_start

            # Add metadata to context
            context["metadata"] = {
                "input_count": len(submissions),
                "output_count": len(analyses),
                "batch_size": batch_size,
                "analyzer_type": type(self._current_analyzer).__name__,
                "opportunity_ids": [f"opp-{getattr(s, 'id', 'unknown')}" for s in submissions]
            }

            logger.info(f"✓ Analyzed {len(analyses)} submissions in {transform_time:.2f}s")

            return analyses, transform_time

    def _validate_analyses(
        self, analyses: list[AnalysisResult], config: PipelineConfiguration
    ) -> tuple[list[AnalysisResult], float]:
        """Validate and filter analysis results with comprehensive quality filtering"""
        logger.info("STEP 3: Validating analysis quality")
        validate_start = time.time()

        # Apply comprehensive quality filtering
        filter_result = self._filter_by_quality(analyses, config)
        filtered_analyses = filter_result['filtered_analyses']
        filtering_stats = filter_result['statistics']

        # Additional validation if enabled
        if config.validate_quality and self.validator:
            # Apply additional validation from AnalysisValidator
            validated_analyses = []
            validation_errors = 0

            for analysis in filtered_analyses:
                try:
                    if self.validator.validate_analysis(analysis):
                        validated_analyses.append(analysis)
                    else:
                        validation_errors += 1
                        logger.debug(f"Analysis failed validation: {analysis.submission_id}")
                except Exception as e:
                    validation_errors += 1
                    logger.warning(f"Error validating analysis {analysis.submission_id}: {e}")

            # Log additional validation results
            if validation_errors > 0:
                logger.info(f"Additional validation filtered {validation_errors} more analyses")
                high_quality_analyses = validated_analyses
            else:
                high_quality_analyses = filtered_analyses
                logger.info("All quality-filtered analyses passed additional validation")
        else:
            # No additional validation - use quality filtering results
            high_quality_analyses = filtered_analyses
            logger.info("Skipping additional validation (validate_quality=False)")

        validation_time = time.time() - validate_start

        # Enhanced completion logging
        logger.info("✓ Quality filtering and validation complete:")
        logger.info(f"  - Input analyses: {len(analyses)}")
        logger.info(f"  - After quality filtering: {len(filtered_analyses)}")
        logger.info(f"  - After additional validation: {len(high_quality_analyses)}")
        logger.info(f"  - Total filtering time: {validation_time:.2f}s")

        if filtering_stats.get('filtering_percentages'):
            logger.info(f"  - Quality filter pass rate: {filtering_stats['filtering_percentages']['pass_rate_percentage']}%")

        return high_quality_analyses, validation_time

    def _store_analyses(
        self,
        analyses: list[AnalysisResult],
        submissions: list[RedditSubmission],
        config: PipelineConfiguration
    ) -> tuple[dict[str, int], float]:
        """Store analyses to database"""
        storage_stats = {"stored": 0, "skipped": 0, "errors": 0}
        storage_time = 0.0

        if not config.dry_run and analyses and self.database_loader:
            logger.info("STEP 4: Storing analyses to database")

            # Get metrics collector
            metrics = get_collector()

            # Track load phase with agent name
            with metrics.track("load") as context:
                load_start = time.time()

                # Create tables if needed
                self.database_loader.create_tables()

                # Store analyses with original Reddit data
                storage_stats = self.database_loader.store_analyses(analyses, submissions)

                storage_time = time.time() - load_start

                # Add metadata to context
                context["metadata"] = {
                    "analyses_count": len(analyses),
                    "stored_count": storage_stats['stored'],
                    "skipped_count": storage_stats['skipped'],
                    "error_count": storage_stats['errors'],
                    "dry_run": config.dry_run,
                    "opportunity_ids": [f"opp-{a.submission_id}" for a in analyses]
                }

                logger.info(f"✓ Stored {storage_stats['stored']} analyses in {storage_time:.2f}s")

        return storage_stats, storage_time

    def _filter_by_quality(self, analyses: list[AnalysisResult], config: PipelineConfiguration) -> dict[str, Any]:
        """
        Filter analyses by quality criteria with comprehensive logging and statistics

        Args:
            analyses: List of analysis results to filter
            config: Pipeline configuration with filtering thresholds

        Returns:
            Dictionary containing filtered analyses and filtering statistics
        """
        logger.info(f"Starting quality filtering for {len(analyses)} analyses")
        logger.info(f"Filtering criteria: min_score={config.min_score}, min_confidence={config.min_confidence}, quality_threshold=40")

        # Initialize comprehensive statistics
        stats = {
            'total_input': len(analyses),
            'spam_filtered': 0,
            'low_quality_filtered': 0,
            'below_min_score_filtered': 0,
            'below_min_confidence_filtered': 0,
            'total_filtered': 0,
            'final_count': 0,
            'filtering_criteria': {
                'min_score': config.min_score,
                'min_confidence': config.min_confidence,
                'content_quality_threshold': 40,
                'spam_detection_enabled': True
            }
        }

        # Track filtering reasons for detailed analysis
        filtering_reasons = {
            'spam': [],
            'low_quality': [],
            'below_score': [],
            'below_confidence': []
        }

        filtered_analyses = []

        for analysis in analyses:
            original_score = analysis.final_score
            original_confidence = analysis.confidence_score
            original_quality = analysis.content_quality_score

            # Check if spam first (highest priority filter)
            if analysis.is_spam:
                stats['spam_filtered'] += 1
                filtering_reasons['spam'].append({
                    'submission_id': analysis.submission_id,
                    'app_title': getattr(analysis.app_idea, 'title', 'Unknown'),
                    'spam_indicators': analysis.spam_indicators,
                    'final_score': original_score,
                    'confidence': original_confidence
                })
                logger.debug(f"Filtered spam: {analysis.submission_id} - {analysis.spam_indicators}")
                continue

            # Check content quality score
            if analysis.content_quality_score < 40:
                stats['low_quality_filtered'] += 1
                filtering_reasons['low_quality'].append({
                    'submission_id': analysis.submission_id,
                    'app_title': getattr(analysis.app_idea, 'title', 'Unknown'),
                    'content_quality_score': original_quality,
                    'final_score': original_score,
                    'confidence': original_confidence
                })
                logger.debug(f"Filtered low quality: {analysis.submission_id} - quality_score={original_quality}")
                continue

            # Check min_score threshold
            if analysis.final_score < config.min_score:
                stats['below_min_score_filtered'] += 1
                filtering_reasons['below_score'].append({
                    'submission_id': analysis.submission_id,
                    'app_title': getattr(analysis.app_idea, 'title', 'Unknown'),
                    'final_score': original_score,
                    'min_score_threshold': config.min_score,
                    'confidence': original_confidence
                })
                logger.debug(f"Filtered low score: {analysis.submission_id} - score={original_score} < {config.min_score}")
                continue

            # Check min_confidence threshold
            if analysis.confidence_score < config.min_confidence:
                stats['below_min_confidence_filtered'] += 1
                filtering_reasons['below_confidence'].append({
                    'submission_id': analysis.submission_id,
                    'app_title': getattr(analysis.app_idea, 'title', 'Unknown'),
                    'confidence_score': original_confidence,
                    'min_confidence_threshold': config.min_confidence,
                    'final_score': original_score
                })
                logger.debug(f"Filtered low confidence: {analysis.submission_id} - confidence={original_confidence} < {config.min_confidence}")
                continue

            # Passed all filters - add to results
            filtered_analyses.append(analysis)
            logger.debug(f"Approved analysis: {analysis.submission_id} - score={original_score}, confidence={original_confidence}")

        # Calculate total filtered
        stats['total_filtered'] = (
            stats['spam_filtered'] +
            stats['low_quality_filtered'] +
            stats['below_min_score_filtered'] +
            stats['below_min_confidence_filtered']
        )
        stats['final_count'] = len(filtered_analyses)

        # Calculate filtering percentages
        if stats['total_input'] > 0:
            stats['filtering_percentages'] = {
                'spam_percentage': round((stats['spam_filtered'] / stats['total_input']) * 100, 1),
                'low_quality_percentage': round((stats['low_quality_filtered'] / stats['total_input']) * 100, 1),
                'below_score_percentage': round((stats['below_min_score_filtered'] / stats['total_input']) * 100, 1),
                'below_confidence_percentage': round((stats['below_min_confidence_filtered'] / stats['total_input']) * 100, 1),
                'pass_rate_percentage': round((stats['final_count'] / stats['total_input']) * 100, 1)
            }

        # Add filtering reasons for debugging
        stats['filtered_items'] = filtering_reasons

        # Comprehensive logging
        logger.info("Quality filtering complete:")
        logger.info(f"  Input: {stats['total_input']} analyses")
        logger.info(f"  Output: {stats['final_count']} analyses")
        logger.info(f"  Pass rate: {stats['filtering_percentages']['pass_rate_percentage'] if 'filtering_percentages' in stats else 0}%")
        logger.info("  Filtered breakdown:")
        logger.info(f"    - Spam: {stats['spam_filtered']} ({stats['filtering_percentages']['spam_percentage'] if 'filtering_percentages' in stats else 0}%)")
        logger.info(f"    - Low quality: {stats['low_quality_filtered']} ({stats['filtering_percentages']['low_quality_percentage'] if 'filtering_percentages' in stats else 0}%)")
        logger.info(f"    - Below min_score ({config.min_score}): {stats['below_min_score_filtered']} ({stats['filtering_percentages']['below_score_percentage'] if 'filtering_percentages' in stats else 0}%)")
        logger.info(f"    - Below min_confidence ({config.min_confidence}): {stats['below_min_confidence_filtered']} ({stats['filtering_percentages']['below_confidence_percentage'] if 'filtering_percentages' in stats else 0}%)")

        # Log approved analyses summary
        if filtered_analyses:
            avg_score = sum(a.final_score for a in filtered_analyses) / len(filtered_analyses)
            avg_confidence = sum(a.confidence_score for a in filtered_analyses) / len(filtered_analyses)

            # Count trust levels
            trust_counts = {}
            for analysis in filtered_analyses:
                trust_counts[analysis.trust_level] = trust_counts.get(analysis.trust_level, 0) + 1

            logger.info("  Approved analyses summary:")
            logger.info(f"    - Average score: {avg_score:.1f}")
            logger.info(f"    - Average confidence: {avg_confidence:.1f}")
            logger.info(f"    - Trust levels: {trust_counts}")

        return {
            'filtered_analyses': filtered_analyses,
            'statistics': stats
        }

    def _create_results(
        self,
        pipeline_start_time: float,
        extraction_time: float,
        staging_time: float,
        analysis_time: float,
        validation_time: float,
        storage_time: float,
        submissions: list[RedditSubmission],
        analyses: list[AnalysisResult],
        high_quality_analyses: list[AnalysisResult],
        storage_stats: dict[str, int],
        config: PipelineConfiguration
    ) -> PipelineResults:
        """Create pipeline results object"""
        total_time = time.time() - pipeline_start_time

        # Calculate quality metrics
        quality_metrics = self.validator.get_quality_summary(analyses) if analyses else {}

        # Get database statistics if available
        database_stats = None
        if not config.dry_run and self.database_loader:
            try:
                database_stats = self.database_loader.get_statistics()
            except Exception as e:
                logger.warning(f"Failed to get database statistics: {e}")

        return PipelineResults(
            # Execution metrics
            total_execution_time=total_time,
            extraction_time=extraction_time,
            staging_time=staging_time,
            analysis_time=analysis_time,
            validation_time=validation_time,
            storage_time=storage_time,

            # Data metrics
            submissions_extracted=len(submissions),
            analyses_generated=len(analyses),
            high_quality_analyses=len(high_quality_analyses),
            analyses_stored=storage_stats["stored"],
            analyses_skipped=storage_stats["skipped"],
            analysis_errors=storage_stats["errors"],

            # Quality metrics
            validation_rate=quality_metrics.get('validation_rate', 0.0),
            high_score_rate=quality_metrics.get('high_score_rate', 0.0),
            average_score=quality_metrics.get('avg_final_score', 0.0),
            trust_distribution=quality_metrics.get('trust_distribution', {}),

            # Database statistics
            database_stats=database_stats
        )

    def _create_empty_results(self, pipeline_start_time: float) -> PipelineResults:
        """Create empty results when no submissions found"""
        total_time = time.time() - pipeline_start_time

        return PipelineResults(
            total_execution_time=total_time,
            extraction_time=0.0,
            staging_time=0.0,
            analysis_time=0.0,
            validation_time=0.0,
            storage_time=0.0,
            submissions_extracted=0,
            analyses_generated=0,
            high_quality_analyses=0,
            analyses_stored=0,
            analyses_skipped=0,
            analysis_errors=0
        )

    def _log_completion_summary(self, results: PipelineResults, config: PipelineConfiguration) -> None:
        """Log pipeline completion summary"""
        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total execution time: {results.total_execution_time:.2f}s")
        logger.info("")
        logger.info("Step Results:")
        logger.info(f"  1. Extract: {results.submissions_extracted} submissions")
        logger.info(f"  2. Analyze: {results.analyses_generated} analyses")
        logger.info(f"  3. Filter: {results.high_quality_analyses} high-quality")
        logger.info(f"  4. Store: {results.analyses_stored} stored, {results.analyses_skipped} skipped, {results.analysis_errors} errors")
        logger.info("")

        # Performance metrics
        if results.extraction_time > 0:
            throughput = results.submissions_extracted / results.extraction_time
            logger.info("Performance:")
            logger.info(f"  - Reddit extraction: {throughput:.1f} submissions/second")

        if results.analysis_time > 0:
            analysis_rate = results.analyses_generated / results.analysis_time
            logger.info(f"  - LLM analysis: {analysis_rate:.2f} analyses/second")

        if results.total_execution_time > 0:
            overall_rate = results.submissions_extracted / results.total_execution_time
            logger.info(f"  - Overall pipeline: {overall_rate:.2f} submissions/second")

        logger.info("")

        # Quality metrics
        if results.analyses_generated > 0:
            logger.info("Quality Metrics:")
            logger.info(f"  - Validation rate: {results.validation_rate:.1f}%")
            logger.info(f"  - High score rate: {results.high_score_rate:.1f}%")
            logger.info(f"  - Average score: {results.average_score:.1f}")
            logger.info(f"  - Trust distribution: {results.trust_distribution}")

        # Database statistics
        if results.database_stats and not config.dry_run:
            logger.info("")
            logger.info("Database Statistics:")
            logger.info(f"  - Total opportunities: {results.database_stats['total_opportunities']}")
            logger.info(f"  - Average score: {results.database_stats['average_score']:.1f}")
            logger.info(f"  - High score percentage: {results.database_stats['high_score_percentage']:.1f}%")

        logger.info("✓ Pipeline completed successfully")
