"""Business Concept Deduplication Module.

This module provides the core deduplication logic that saves ~$3,000/year by
preventing redundant AI analyses for duplicate business concepts.

Architecture:
    When a Reddit submission is processed, the system checks if it's semantically
    similar to a previously analyzed submission (a "business concept"). If so,
    instead of running expensive AI analyses (~$0.10 for Agno, ~$0.005 for Profiler),
    we copy results from the primary submission.

Cost Savings Breakdown:
    - Baseline: 10,000 posts/month
    - Deduplication rate: 70%
    - Agno cost: $0.10/call → $700/month saved
    - Profiler cost: $0.005/call → $35/month saved
    - Total savings: ~$735/month (~$8,820/year)
    - Conservative estimate: ~$3,000/year (accounting for variance)

Data Integrity:
    - Prevents semantic fragmentation of core_functions arrays
    - Ensures consistent business categorization across duplicates
    - Maintains reliable analytics and aggregations

Key Functions:
    - should_run_agno_analysis: Check if monetization analysis should run
    - should_run_profiler_analysis: Check if AI profiling should run
    - copy_agno_from_primary: Copy Agno results for duplicates
    - copy_profiler_from_primary: Copy AI profiles for duplicates
    - update_concept_agno_stats: Update concept after Agno analysis
    - update_concept_profiler_stats: Update concept after profiling

Usage Example:
    >>> from pipeline_v2.deduplication import (
    ...     should_run_agno_analysis,
    ...     copy_agno_from_primary,
    ...     update_concept_agno_stats,
    ... )
    >>>
    >>> # Check if we should run analysis
    >>> should_run, concept_id = should_run_agno_analysis(submission, supabase)
    >>>
    >>> if not should_run:
    ...     # Duplicate detected - copy from primary (saves $0.10)
    ...     analysis = copy_agno_from_primary(submission, concept_id, supabase)
    ... else:
    ...     # Unique submission - run analysis
    ...     analysis = run_agno_analysis(submission)
    ...     if concept_id:
    ...         # Mark concept as analyzed for future duplicates
    ...         update_concept_agno_stats(concept_id, analysis, supabase)

Database Schema:
    business_concepts table:
        - id: Unique concept identifier
        - primary_opportunity_id: First submission for this concept
        - has_agno_analysis: Boolean flag for Agno deduplication
        - has_profiler_analysis: Boolean flag for Profiler deduplication
        - submission_count: Number of duplicate submissions

    opportunities_unified table:
        - submission_id: Reddit submission ID
        - business_concept_id: Link to business_concepts table

    llm_monetization_analysis table:
        - business_concept_id: Link to concept
        - copied_from_primary: Boolean flag for audit trail
        - primary_opportunity_id: Original submission reference

    workflow_results table:
        - business_concept_id: Link to concept
        - copied_from_primary: Boolean flag for audit trail
        - core_functions: Array that must remain consistent

Extracted from:
    scripts/core/batch_opportunity_scoring.py (lines 222-776)

Related Modules:
    core/deduplication/agno_skip_logic.py - OOP wrapper for Agno deduplication
    core/deduplication/profiler_skip_logic.py - OOP wrapper for Profiler deduplication
    core/deduplication/concept_manager.py - Business concept management
"""

from .concept_tracker import (
    copy_agno_from_primary,
    copy_profiler_from_primary,
    should_run_agno_analysis,
    should_run_profiler_analysis,
    update_concept_agno_stats,
    update_concept_profiler_stats,
)

__all__ = [
    # Agno (Monetization) Analysis Deduplication
    "should_run_agno_analysis",  # Check if analysis needed
    "copy_agno_from_primary",  # Copy results for duplicates
    "update_concept_agno_stats",  # Mark concept as analyzed
    # AI Profiler Deduplication
    "should_run_profiler_analysis",  # Check if profiling needed
    "copy_profiler_from_primary",  # Copy profile for duplicates
    "update_concept_profiler_stats",  # Mark concept as profiled
]
