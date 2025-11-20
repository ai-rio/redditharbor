# Unified Pipeline Deduplication Integration Plan

**Date**: 2025-11-20
**Status**: PLANNING
**Priority**: CRITICAL - 70% Cost Reduction Opportunity ($3,528/year savings)

---

## Executive Summary

The unified OpportunityPipeline is missing the critical **cost safeguard layer** that prevents redundant AI analysis. The monolith pipelines achieve **70% cost reduction** through deduplication logic that checks the database BEFORE calling expensive AI services.

**Current State**: AI services called on EVERY submission (no deduplication)
**Target State**: Check database first, only call AI if not already analyzed
**Expected Impact**: $3,528/year cost savings (based on 10K submissions/month)

---

## Problem Statement

### Issue 1: No Check-Before-AI Pattern

**Monolith Pattern** (`batch_opportunity_scoring.py:222-298`):
```python
# Step 1: Check database for existing analysis
should_run, concept_id = should_run_agno_analysis(submission, supabase)

if not should_run:
    # COST SAVED: Copy existing analysis ($0 spent)
    analysis = copy_agno_from_primary(submission, concept_id, supabase)
else:
    # Only call AI if no existing analysis
    analysis = agno_service.analyze(submission)  # $0.10 spent
```

**Unified Pipeline** (`orchestrator.py:150-169`):
```python
# No deduplication check - directly calls ALL services
for sub in submissions:
    result = self._enrich_submission(sub)  # ALWAYS $0.0750
    enriched.append(result)
```

**Impact**: Every re-run pays $0.0750/submission even if already enriched.

---

### Issue 2: Missing Trust Data Preservation

**Monolith Pattern** (`batch_opportunity_scoring.py:1269-1327`):
```python
# Fetch existing trust data BEFORE updating AI profile
existing = supabase.table("app_opportunities").select(
    "trust_score, trust_badge, activity_score, engagement_level, "
    "trust_level, trend_velocity, problem_validity, discussion_quality, "
    # ... 14 trust fields total
).eq("submission_id", submission_id).execute()

# Merge AI fields while PRESERVING trust
ai_profile = {
    **ai_enrichment,                        # New AI fields
    "trust_score": existing["trust_score"],  # Preserve trust
    # ... preserve all 14 trust fields
}
```

**Unified Pipeline** (`hybrid_store.py`):
```python
# Direct DLT merge - overwrites ALL fields
pipeline.run(opportunities, write_disposition="merge")
# Result: Trust data lost on update!
```

**Impact**: Trust analysis lost when AI re-enrichment occurs.

---

### Issue 3: No Concept Metadata Tracking

**Monolith Pattern** (`agno_skip_logic.py:228-291`):
```python
# Update concept metadata AFTER AI analysis
response = supabase.rpc(
    "update_agno_analysis_tracking",
    {
        "p_concept_id": int(concept_id),
        "p_has_analysis": True,  # Mark for future skip checks
        "p_wtp_score": wtp_score,
    }
).execute()
```

**Unified Pipeline**:
- No concept metadata updates
- No tracking of which submissions have been analyzed
- Future runs will re-analyze the same submissions

**Impact**: Deduplication won't work on future runs.

---

## Solution Architecture

### Three-Layer Integration

```
┌─────────────────────────────────────────────────────────────┐
│  UNIFIED PIPELINE - ENHANCED WITH DEDUPLICATION              │
└─────────────────────────────────────────────────────────────┘

1. FETCH LAYER (orchestrator.py:129-139)
   - Fetch submissions from database or Reddit API
   - No changes needed

2. DEDUPLICATION LAYER ⭐ NEW
   - Check database for existing enrichment
   - Decide: Copy OR Analyze
   - Track skipped submissions

3. ENRICHMENT LAYER (orchestrator.py:150-169)
   - Only enrich submissions that need analysis
   - Copy results for duplicates

4. STORAGE LAYER (storage/*.py)
   - Preserve trust data on updates
   - Update concept metadata
   - Store enrichment results

5. TRACKING LAYER ⭐ NEW
   - Update concept flags (has_agno_analysis, has_profiler_analysis)
   - Track copy vs analyze statistics
```

---

## Implementation Plan

### Phase 1: Integrate Deduplication Classes (2-3 hours)

**Goal**: Wire existing deduplication classes into pipeline orchestrator

#### Step 1.1: Add Deduplication Check to Orchestrator

**File**: `core/pipeline/orchestrator.py`
**Location**: Before enrichment loop (line ~150)

```python
# NEW METHOD: Check if submission needs enrichment
def _should_enrich_submission(self, submission: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Check if submission needs AI enrichment or can reuse existing.

    Returns:
        tuple: (should_run_ai, concept_id_if_exists)
    """
    submission_id = submission.get("submission_id")

    # Check each enabled service
    needs_profiler = False
    needs_monetization = False
    concept_id = None

    if self.config.enable_profiler:
        from core.deduplication import ProfilerSkipLogic
        skip_logic = ProfilerSkipLogic(self.config.supabase_client)
        needs_profiler, concept_id = skip_logic.should_run_profiler_analysis(submission)

    if self.config.enable_monetization:
        from core.deduplication import AgnoSkipLogic
        skip_logic = AgnoSkipLogic(self.config.supabase_client)
        needs_monetization, concept_id = skip_logic.should_run_agno_analysis(submission)

    # If ANY service needs to run, analyze
    should_analyze = needs_profiler or needs_monetization

    return should_analyze, concept_id
```

**Modified enrichment loop**:
```python
# MODIFIED: Add deduplication check
for sub in submissions:
    try:
        # CHECK: Should we run AI or copy existing?
        should_analyze, concept_id = self._should_enrich_submission(sub)

        if should_analyze:
            # Run AI enrichment (costs $0.0750)
            result, service_errors = self._enrich_submission_with_error_tracking(sub)
            self.stats["analyzed"] += 1
        else:
            # Copy existing analysis (costs $0)
            result = self._copy_existing_enrichment(sub, concept_id)
            self.stats["copied"] += 1  # NEW STAT
            service_errors = 0

        if result:
            enriched.append(result)
        else:
            self.stats["skipped"] += 1

        self.stats["errors"] += service_errors

    except Exception as e:
        logger.error(f"[ERROR] Enrichment error: {e}")
        self.stats["errors"] += 1
```

**Estimated Time**: 1 hour

---

#### Step 1.2: Implement Copy Logic

**File**: `core/pipeline/orchestrator.py`
**New method**:

```python
def _copy_existing_enrichment(
    self,
    submission: Dict[str, Any],
    concept_id: str
) -> Optional[Dict[str, Any]]:
    """
    Copy existing enrichment from primary concept.

    Args:
        submission: Submission data
        concept_id: Business concept ID with existing analysis

    Returns:
        Enriched submission with copied data
    """
    result = {**submission}  # Start with original

    # Copy profiler analysis if enabled
    if self.config.enable_profiler and "profiler" in self.services:
        from core.deduplication import ProfilerSkipLogic
        skip_logic = ProfilerSkipLogic(self.config.supabase_client)
        profiler_data = skip_logic.copy_profiler_analysis(
            submission_id=submission.get("submission_id"),
            concept_id=concept_id
        )
        if profiler_data:
            result.update(profiler_data)
            logger.info(f"[OK] Copied profiler analysis for {submission.get('submission_id')}")

    # Copy monetization analysis if enabled
    if self.config.enable_monetization and "monetization" in self.services:
        from core.deduplication import AgnoSkipLogic
        skip_logic = AgnoSkipLogic(self.config.supabase_client)
        agno_data = skip_logic.copy_agno_analysis(
            submission_id=submission.get("submission_id"),
            concept_id=concept_id
        )
        if agno_data:
            result.update(agno_data)
            logger.info(f"[OK] Copied monetization analysis for {submission.get('submission_id')}")

    return result
```

**Estimated Time**: 30 minutes

---

#### Step 1.3: Add Copy Statistics Tracking

**File**: `core/pipeline/orchestrator.py`
**Location**: `__init__` method (line ~81)

```python
self.stats = {
    "fetched": 0,
    "filtered": 0,
    "analyzed": 0,      # Fresh AI analysis
    "copied": 0,        # ⭐ NEW: Copied from existing
    "stored": 0,
    "errors": 0,
    "skipped": 0,
}
```

**Updated summary generation** (`_generate_summary` method):
```python
def _generate_summary(self) -> Dict[str, Any]:
    """Generate pipeline summary statistics."""
    total_fetched = self.stats["fetched"]
    total_analyzed = self.stats["analyzed"]
    total_copied = self.stats["copied"]  # ⭐ NEW
    total_processed = total_analyzed + total_copied  # ⭐ NEW
    total_stored = self.stats["stored"]

    # Calculate cost savings
    cost_saved = total_copied * 0.075  # $0.075 per copied submission

    return {
        "total_fetched": total_fetched,
        "total_filtered": self.stats["filtered"],
        "total_analyzed": total_analyzed,
        "total_copied": total_copied,  # ⭐ NEW
        "total_processed": total_processed,  # ⭐ NEW
        "total_stored": total_stored,
        "total_skipped": self.stats["skipped"],
        "total_errors": self.stats["errors"],
        "dedup_rate": round((total_copied / total_processed * 100) if total_processed > 0 else 0, 2),  # ⭐ NEW
        "cost_saved": round(cost_saved, 2),  # ⭐ NEW
        "services_used": list(self.services.keys()),
    }
```

**Estimated Time**: 30 minutes

---

### Phase 2: Trust Data Preservation (1-2 hours)

**Goal**: Preserve trust analysis when updating AI enrichment

#### Step 2.1: Pre-fetch Trust Data

**File**: `core/storage/hybrid_store.py`
**New method**:

```python
def _fetch_existing_trust_data(
    self,
    submission_ids: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Fetch existing trust data for submissions.

    Args:
        submission_ids: List of submission IDs

    Returns:
        dict: Mapping of submission_id -> trust data
    """
    from config.settings import SUPABASE_URL, SUPABASE_KEY
    from supabase import create_client

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Fetch all trust fields
    response = supabase.table("app_opportunities").select(
        "submission_id, trust_score, trust_badge, activity_score, "
        "engagement_level, trust_level, trend_velocity, problem_validity, "
        "discussion_quality, ai_confidence_level, trust_validation_timestamp, "
        "trust_validation_method, author_quality_score, response_quality_score, "
        "trust_badges"
    ).in_("submission_id", submission_ids).execute()

    # Create lookup dict
    trust_data = {}
    for record in response.data:
        trust_data[record["submission_id"]] = record

    return trust_data
```

**Estimated Time**: 30 minutes

---

#### Step 2.2: Merge Trust Data with AI Enrichment

**File**: `core/storage/hybrid_store.py`
**Modified `store` method** (around line 130):

```python
def store(self, hybrid_submissions: list[dict[str, Any]]) -> bool:
    """Store hybrid submissions with trust data preservation."""
    if not hybrid_submissions:
        logger.warning("No hybrid submissions to store")
        return False

    # ⭐ NEW: Pre-fetch existing trust data
    submission_ids = [
        sub.get("submission_id") or sub.get("reddit_id")
        for sub in hybrid_submissions
        if sub.get("submission_id") or sub.get("reddit_id")
    ]
    existing_trust = self._fetch_existing_trust_data(submission_ids)

    # Split into opportunity and profile data
    opportunities = []
    profiles = []

    for submission in hybrid_submissions:
        submission_id = submission.get("submission_id") or submission.get("reddit_id")

        if not submission_id:
            self.stats.skipped += 1
            continue

        # ⭐ NEW: Get existing trust data
        trust_data = existing_trust.get(submission_id, {})

        # Extract opportunity fields
        if submission.get("problem_description"):
            opp_data = {
                "submission_id": submission_id,
                # ... existing fields ...

                # ⭐ NEW: Preserve trust data if exists
                "trust_score": submission.get("trust_score") or trust_data.get("trust_score"),
                "trust_badge": submission.get("trust_badge") or trust_data.get("trust_badge"),
                "trust_level": submission.get("trust_level") or trust_data.get("trust_level"),
                "trust_badges": submission.get("trust_badges") or trust_data.get("trust_badges"),
                "activity_score": trust_data.get("activity_score"),
                "engagement_level": trust_data.get("engagement_level"),
                "trend_velocity": trust_data.get("trend_velocity"),
                "problem_validity": trust_data.get("problem_validity"),
                "discussion_quality": trust_data.get("discussion_quality"),
                "ai_confidence_level": trust_data.get("ai_confidence_level"),
                "trust_validation_timestamp": trust_data.get("trust_validation_timestamp"),
                "trust_validation_method": trust_data.get("trust_validation_method"),
                "author_quality_score": trust_data.get("author_quality_score"),
                "response_quality_score": trust_data.get("response_quality_score"),
            }
            opportunities.append(opp_data)

    # ... rest of storage logic ...
```

**Estimated Time**: 1 hour

---

### Phase 3: Concept Metadata Tracking (1 hour)

**Goal**: Update concept flags after AI enrichment to enable future deduplication

#### Step 3.1: Add Metadata Update After Storage

**File**: `core/pipeline/orchestrator.py`
**Modified `run` method** (after storage, line ~177):

```python
# 4. Storage
if enriched and not self.config.dry_run:
    success = self._store_results(enriched)
    if success:
        self.stats["stored"] = len(enriched)
        logger.info(f"[OK] Stored {len(enriched)} results")

        # ⭐ NEW: Update concept metadata for future deduplication
        self._update_concept_metadata(enriched)

elif self.config.dry_run:
    logger.info("[OK] Dry run mode - skipping storage")
    self.stats["stored"] = 0
```

**New method**:
```python
def _update_concept_metadata(self, enriched: list[dict[str, Any]]) -> None:
    """
    Update concept metadata after successful enrichment.

    Marks concepts as analyzed so future runs can skip AI calls.

    Args:
        enriched: List of successfully enriched submissions
    """
    if not self.config.supabase_client:
        logger.warning("No Supabase client - skipping concept metadata updates")
        return

    # Update profiler metadata
    if self.config.enable_profiler:
        from core.deduplication import ProfilerSkipLogic
        skip_logic = ProfilerSkipLogic(self.config.supabase_client)

        for submission in enriched:
            if submission.get("ai_profile"):  # Has profiler analysis
                # Get concept_id from opportunities_unified table
                concept_response = self.config.supabase_client.table("opportunities_unified").select(
                    "business_concept_id"
                ).eq("submission_id", submission.get("submission_id")).execute()

                if concept_response.data:
                    concept_id = concept_response.data[0].get("business_concept_id")
                    skip_logic.update_concept_profiler_stats(
                        concept_id=concept_id,
                        ai_profile=submission.get("ai_profile")
                    )

    # Update monetization metadata
    if self.config.enable_monetization:
        from core.deduplication import AgnoSkipLogic
        skip_logic = AgnoSkipLogic(self.config.supabase_client)

        for submission in enriched:
            if submission.get("monetization_score"):  # Has monetization analysis
                # Get concept_id
                concept_response = self.config.supabase_client.table("opportunities_unified").select(
                    "business_concept_id"
                ).eq("submission_id", submission.get("submission_id")).execute()

                if concept_response.data:
                    concept_id = concept_response.data[0].get("business_concept_id")
                    skip_logic.update_concept_agno_stats(
                        concept_id=concept_id,
                        wtp_score=submission.get("willingness_to_pay_score", 0),
                        revenue_score=submission.get("revenue_score", 0)
                    )

    logger.info(f"[OK] Updated concept metadata for {len(enriched)} submissions")
```

**Estimated Time**: 1 hour

---

### Phase 4: Testing & Validation (2-3 hours)

**Goal**: Validate deduplication logic works correctly

#### Step 4.1: Create Deduplication Test

**File**: `tests/test_pipeline_deduplication.py` (NEW)

```python
"""Test unified pipeline deduplication logic."""

import pytest
from unittest.mock import MagicMock, patch

from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource


def test_deduplication_skips_analyzed_submissions(supabase_mock):
    """Test that already-analyzed submissions are skipped."""
    # Mock: Submission already has profiler analysis
    supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"business_concept_id": "concept_123"}
    ]
    supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"has_profiler_analysis": True}  # Already analyzed!
    ]

    config = PipelineConfig(
        data_source=DataSource.DATABASE,
        limit=1,
        enable_profiler=True,
        supabase_client=supabase_mock
    )

    pipeline = OpportunityPipeline(config)
    result = pipeline.run()

    # Should have copied instead of analyzing
    assert result["stats"]["copied"] == 1
    assert result["stats"]["analyzed"] == 0
    assert result["summary"]["cost_saved"] > 0


def test_deduplication_analyzes_new_submissions(supabase_mock):
    """Test that new submissions trigger AI analysis."""
    # Mock: Submission has NO profiler analysis
    supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    config = PipelineConfig(
        data_source=DataSource.DATABASE,
        limit=1,
        enable_profiler=True,
        supabase_client=supabase_mock
    )

    pipeline = OpportunityPipeline(config)
    result = pipeline.run()

    # Should have analyzed (not copied)
    assert result["stats"]["analyzed"] == 1
    assert result["stats"]["copied"] == 0


def test_trust_data_preservation(supabase_mock):
    """Test that trust data is preserved when re-enriching."""
    # Mock: Existing record with trust data
    supabase_mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
        {
            "submission_id": "sub_123",
            "trust_score": 85.5,
            "trust_badge": "gold",
            "trust_level": "HIGH"
        }
    ]

    config = PipelineConfig(
        data_source=DataSource.DATABASE,
        limit=1,
        enable_profiler=True,
        enable_trust=False,  # Not running trust this time
        supabase_client=supabase_mock
    )

    pipeline = OpportunityPipeline(config)
    result = pipeline.run()

    # Stored data should have preserved trust fields
    stored_data = result["opportunities"][0]
    assert stored_data["trust_score"] == 85.5
    assert stored_data["trust_badge"] == "gold"
    assert stored_data["trust_level"] == "HIGH"
```

**Estimated Time**: 2 hours

---

#### Step 4.2: Integration Test with Real Database

**Test Script**: `scripts/testing/test_deduplication_integration.py` (NEW)

```python
"""Integration test for pipeline deduplication."""

from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource
from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client


def test_deduplication_real_database():
    """Test deduplication with real database."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Run 1: Fresh analysis
    config = PipelineConfig(
        data_source=DataSource.DATABASE,
        limit=5,
        enable_profiler=True,
        enable_monetization=True,
        supabase_client=supabase
    )

    pipeline = OpportunityPipeline(config)
    result1 = pipeline.run()

    print("\n=== RUN 1 (Fresh Analysis) ===")
    print(f"Analyzed: {result1['stats']['analyzed']}")
    print(f"Copied: {result1['stats']['copied']}")
    print(f"Cost saved: ${result1['summary']['cost_saved']}")

    # Run 2: Same submissions (should copy)
    pipeline2 = OpportunityPipeline(config)
    result2 = pipeline2.run()

    print("\n=== RUN 2 (Deduplication) ===")
    print(f"Analyzed: {result2['stats']['analyzed']}")
    print(f"Copied: {result2['stats']['copied']}")
    print(f"Cost saved: ${result2['summary']['cost_saved']}")

    # Validation
    assert result2['stats']['copied'] >= 4, "Should copy most submissions on second run"
    assert result2['stats']['analyzed'] <= 1, "Should analyze very few on second run"
    assert result2['summary']['cost_saved'] > 0, "Should have cost savings"

    print("\n✅ Deduplication working correctly!")
    print(f"Deduplication rate: {result2['summary']['dedup_rate']}%")


if __name__ == "__main__":
    test_deduplication_real_database()
```

**Estimated Time**: 1 hour

---

## Summary Timeline

| Phase | Task | Time | Deliverables |
|-------|------|------|--------------|
| **Phase 1** | Integrate Deduplication Classes | 2-3h | Modified orchestrator with check-before-AI |
| **Phase 2** | Trust Data Preservation | 1-2h | Modified hybrid_store with trust preservation |
| **Phase 3** | Concept Metadata Tracking | 1h | Metadata updates after enrichment |
| **Phase 4** | Testing & Validation | 2-3h | Unit tests + integration tests |
| **Total** | | **6-9 hours** | Fully integrated deduplication |

---

## Expected Results

### Cost Savings (Based on 10K submissions/month)

**Scenario 1: 50% Duplicate Rate**
- Without dedup: 10,000 × $0.075 = $750/month
- With dedup: 5,000 × $0.075 = $375/month
- **Savings: $375/month = $4,500/year**

**Scenario 2: 70% Duplicate Rate** (monolith observed)
- Without dedup: 10,000 × $0.075 = $750/month
- With dedup: 3,000 × $0.075 = $225/month
- **Savings: $525/month = $6,300/year**

### Performance Improvements

- **Faster Processing**: Copying data is ~100x faster than AI analysis
- **Reduced API Load**: Fewer calls to external AI services
- **Better Resource Utilization**: Pipeline can handle more submissions/hour

### Data Integrity

- **Trust Data Preserved**: Trust analysis not lost on re-enrichment
- **Concept Tracking**: Accurate tracking of which concepts have been analyzed
- **Audit Trail**: Clear distinction between fresh analysis and copied data

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Copy logic returns stale data | Low | Medium | Add timestamp checks, cache expiry |
| Concept ID lookup fails | Medium | Medium | Add fallback to analyze if lookup fails |
| Trust data fetch performance | Low | Low | Batch fetch with IN clause |
| Metadata update failures | Medium | Low | Make updates non-blocking, log failures |

---

## Success Criteria

✅ **Functional Requirements**:
- [ ] Pipeline checks database before calling AI services
- [ ] Existing enrichment copied instead of re-analyzed
- [ ] Trust data preserved on updates
- [ ] Concept metadata updated after enrichment
- [ ] Statistics track copied vs analyzed submissions

✅ **Performance Requirements**:
- [ ] Deduplication check adds < 100ms per submission
- [ ] Copy operation < 50ms per submission
- [ ] Trust data fetch < 200ms for batch of 50

✅ **Cost Requirements**:
- [ ] 50%+ reduction in AI costs for duplicate submissions
- [ ] Cost savings tracked and reported in summary

✅ **Testing Requirements**:
- [ ] Unit tests for deduplication logic (90%+ coverage)
- [ ] Integration tests with real database
- [ ] Test 02 (Small Batch) validates deduplication

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Begin Phase 1** implementation (orchestrator modifications)
3. **Run Test 02** to validate deduplication works
4. **Measure cost savings** in production

---

**Plan Author**: Claude Agent
**Date**: 2025-11-20
**Status**: READY FOR IMPLEMENTATION
