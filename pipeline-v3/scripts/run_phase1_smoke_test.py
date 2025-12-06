#!/usr/bin/env python3
"""
Phase 1 Smoke Test Execution Script
Executes the pipeline to process 100 opportunities for smoke testing
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestration.pipeline_orchestrator import PipelineOrchestrator, PipelineConfiguration
from load import DatabaseLoader


def setup_logging():
    """Setup logging for smoke test"""
    log_file = project_root / "logs" / f"phase1_smoke_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.parent.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Execute Phase 1 smoke test"""
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("PHASE 1 SMOKE TEST EXECUTION")
    logger.info("=" * 80)
    logger.info("Processing 100 opportunities for smoke testing...")
    logger.info("")

    # Create pipeline configuration for Phase 1
    config = PipelineConfiguration(
        subreddits=["productivity", "tools", "selfimprovement", "getdisciplined", "Todoist"],
        limit=100,  # Process 100 submissions
        sort_by="hot",
        time_filter="week",
        min_score=0.0,  # Accept all scores for smoke test
        min_confidence=0.0,  # Accept all confidence for smoke test
        batch_size=10,  # Process in batches of 10
        test_mode=True,  # Use test mode for smoke test
        dry_run=False,  # Store in database
        validate_quality=True,
        enable_staging=True,
        staging_batch_size=50,
        enable_deduplication=True,
        enable_checkpoints=True,
        checkpoint_interval=25
    )

    # Initialize orchestrator
    try:
        orchestrator = PipelineOrchestrator()

        # Initialize database loader
        database_loader = DatabaseLoader()
        orchestrator.database_loader = database_loader

        # Execute pipeline
        results = orchestrator.execute_pipeline(config)

        # Log results
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 1 SMOKE TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total execution time: {results.total_execution_time:.2f}s")
        logger.info(f"Submissions extracted: {results.submissions_extracted}")
        logger.info(f"Analyses generated: {results.analyses_generated}")
        logger.info(f"High-quality analyses: {results.high_quality_analyses}")
        logger.info(f"Analyses stored: {results.analyses_stored}")
        logger.info(f"Analyses skipped: {results.analyses_skipped}")
        logger.info(f"Analysis errors: {results.analysis_errors}")

        # Check if we processed enough opportunities
        if results.analyses_stored >= 100:
            logger.info("")
            logger.info("✅ SUCCESS: Processed 100+ opportunities")
            logger.info("You can now run the validation script:")
            logger.info("  python scripts/validate_smoke_test.py")
            return 0
        else:
            logger.error("")
            logger.error(f"❌ FAILED: Only processed {results.analyses_stored} opportunities (< 100)")
            return 1

    except Exception as e:
        logger.error(f"Phase 1 smoke test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())