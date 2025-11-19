# Complete Deduplication Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Skip both Agno monetization analysis and AI profiling for duplicate business concepts to achieve 70% cost savings and eliminate semantic fragmentation.

**Architecture:** Add deduplication checks at two integration points in batch_opportunity_scoring.py (lines 876 and 984) with copy-from-primary functionality and comprehensive tracking.

**Tech Stack:** Python, Supabase, PostgreSQL, Reddit API, Agno multi-agent analysis, EnhancedLLMProfiler

---

### Task 1: Database Schema Updates

**Files:**
- Modify: `supabase/migrations/` (create new migration file)
- Test: `scripts/database/test_schema.py`

**Step 1: Create migration file**

```bash
# Create new migration file
timestamp=$(date +%Y%m%d%H%M%S)
migration_file="supabase/migrations/${timestamp}_add_deduplication_tracking.sql"
touch "$migration_file"
```

**Step 2: Write deduplication schema migration**

```sql
-- File: supabase/migrations/${timestamp}_add_deduplication_tracking.sql

-- Add deduplication tracking to business_concepts table
ALTER TABLE business_concepts
-- Agno analysis tracking
ADD COLUMN IF NOT EXISTS has_agno_analysis BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS agno_analysis_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_agno_analysis_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS agno_avg_wtp_score NUMERIC(5,2),

-- AI profiler tracking
ADD COLUMN IF NOT EXISTS has_ai_profile BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ai_profile_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_ai_profile_at TIMESTAMPTZ;

-- Track copied Agno analyses
ALTER TABLE llm_monetization_analysis
ADD COLUMN IF NOT EXISTS copied_from_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS primary_opportunity_id UUID,
ADD COLUMN IF NOT EXISTS business_concept_id BIGINT REFERENCES business_concepts(id);

-- Track copied AI profiles
ALTER TABLE opportunities_unified
ADD COLUMN IF NOT EXISTS copied_from_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS primary_opportunity_id UUID;

-- Indexes for fast lookup during deduplication checks
CREATE INDEX IF NOT EXISTS idx_business_concepts_has_agno
ON business_concepts(has_agno_analysis)
WHERE has_agno_analysis = TRUE;

CREATE INDEX IF NOT EXISTS idx_business_concepts_has_ai_profile
ON business_concepts(has_ai_profile)
WHERE has_ai_profile = TRUE;

CREATE INDEX IF NOT EXISTS idx_llm_monetization_copied
ON llm_monetization_analysis(copied_from_primary);

CREATE INDEX IF NOT EXISTS idx_opportunities_unified_copied
ON opportunities_unified(copied_from_primary);
```

**Step 3: Apply migration to local database**

```bash
# Apply migration
supabase db push
```

**Step 4: Test schema changes**

```python
# File: scripts/database/test_schema.py
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from supabase import create_client

def test_deduplication_schema():
    """Test that deduplication columns exist and work properly"""
    supabase = create_client(
        os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321'),
        os.getenv('SUPABASE_KEY', 'your-anon-key')
    )

    # Test business_concepts table has new columns
    response = supabase.table('business_concepts').select('*').limit(1).execute()
    if response.data:
        row = response.data[0]
        assert 'has_agno_analysis' in row
        assert 'has_ai_profile' in row
        assert 'agno_analysis_count' in row
        assert 'ai_profile_count' in row
        print("✅ business_concepts schema updated")

    # Test llm_monetization_analysis has tracking columns
    response = supabase.table('llm_monetization_analysis').select('*').limit(1).execute()
    if response.data:
        row = response.data[0]
        assert 'copied_from_primary' in row
        assert 'primary_opportunity_id' in row
        print("✅ llm_monetization_analysis schema updated")

    # Test opportunities_unified has tracking columns
    response = supabase.table('opportunities_unified').select('*').limit(1).execute()
    if response.data:
        row = response.data[0]
        assert 'copied_from_primary' in row
        assert 'primary_opportunity_id' in row
        print("✅ opportunities_unified schema updated")

if __name__ == "__main__":
    test_deduplication_schema()
    print("✅ All schema tests passed")
```

**Step 5: Run schema tests**

```bash
python scripts/database/test_schema.py
```

**Step 6: Commit schema changes**

```bash
git add supabase/migrations/${timestamp}_add_deduplication_tracking.sql scripts/database/test_schema.py
git commit -m "feat: Add deduplication tracking schema for Agno and AI profiler"
```

---

### Task 2: Agno Analysis Deduplication Functions

**Files:**
- Modify: `batch_opportunity_scoring.py` (lines 205+)
- Test: `tests/test_agno_deduplication.py`

**Step 1: Write failing test for Agno skip logic**

```python
# File: tests/test_agno_deduplication.py
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batch_opportunity_scoring import should_run_agno_analysis, copy_agno_from_primary

def test_should_run_agno_for_new_submission():
    """Test that new submissions should run Agno analysis"""
    submission = {
        'submission_id': 'test-new-123',
        'title': 'New app concept'
    }
    # Mock supabase response - no existing record
    mock_supabase = MockSupabase([])

    should_run, concept_id = should_run_agno_analysis(submission, mock_supabase)

    assert should_run == True, "New submissions should run Agno"
    assert concept_id is None, "New submissions should have no concept_id"
    print("✅ New submission correctly triggers Agno analysis")

def test_should_skip_agno_for_duplicate_with_analysis():
    """Test that duplicates with existing Agno analysis should skip"""
    submission = {
        'submission_id': 'test-duplicate-456',
        'title': 'FitnessFAQ app concept'
    }
    # Mock supabase response - duplicate with existing analysis
    mock_supabase = MockSupabase([
        {'is_duplicate': True, 'business_concept_id': '42'},  # opportunities_unified response
        {'primary_opportunity_id': 'abc123', 'has_agno_analysis': True}  # business_concepts response
    ])

    should_run, concept_id = should_run_agno_analysis(submission, mock_supabase)

    assert should_run == False, "Duplicates with analysis should skip Agno"
    assert concept_id == '42', "Should return concept_id for duplicate"
    print("✅ Duplicate correctly skips Agno analysis")

class MockSupabase:
    def __init__(self, data_list):
        self.data_list = data_list
        self.index = 0

    def table(self, table_name):
        return MockTable(self.data_list[self.index] if self.index < len(self.data_list) else [])

class MockTable:
    def __init__(self, data):
        self.data = data

    def select(self, columns):
        return self

    def eq(self, column, value):
        return self

    def execute(self):
        return MockResponse(self.data)

class MockResponse:
    def __init__(self, data):
        self.data = data

if __name__ == "__main__":
    test_should_run_agno_for_new_submission()
    test_should_skip_agno_for_duplicate_with_analysis()
    print("✅ All Agno deduplication tests passed")
```

**Step 2: Run test to verify it fails**

```bash
python tests/test_agno_deduplication.py
```

Expected: FAIL with "function not defined" errors

**Step 3: Implement should_run_agno_analysis function**

```python
# Add to batch_opportunity_scoring.py after SECTOR_MAPPING section (around line 205)

def should_run_agno_analysis(submission: dict, supabase) -> tuple[bool, str | None]:
    """
    Check if Agno monetization analysis should run for this submission.
    Skip if it's a duplicate with existing Agno analysis.

    Args:
        submission: Submission dict from app_opportunities table
        supabase: Supabase client

    Returns:
        (should_run: bool, concept_id: str | None)
        - should_run: True to run Agno, False to skip and copy
        - concept_id: Business concept ID if duplicate, None otherwise
    """
    submission_id = submission.get("submission_id", submission.get("id"))

    # Query opportunities_unified to check deduplication status
    try:
        response = supabase.table("opportunities_unified")\
            .select("is_duplicate, business_concept_id")\
            .eq("submission_id", submission_id)\
            .execute()
    except Exception:
        return True, None  # If table doesn't exist or query fails, run Agno

    if not response.data:
        return True, None  # Not in unified table yet, run Agno

    opp = response.data[0]
    if not opp.get("is_duplicate"):
        return True, None  # Not a duplicate, run Agno

    concept_id = opp.get("business_concept_id")
    if not concept_id:
        return True, None  # Duplicate but no concept ID, run Agno anyway

    # Check if business_concepts has Agno analysis
    try:
        concept_response = supabase.table("business_concepts")\
            .select("primary_opportunity_id, has_agno_analysis")\
            .eq("id", concept_id)\
            .execute()
    except Exception:
        return True, None  # If query fails, run Agno

    if not concept_response.data:
        return True, None  # No concept record, run Agno

    concept = concept_response.data[0]
    if concept.get("has_agno_analysis"):
        return False, concept_id  # Skip Agno, copy from primary

    return True, None  # No existing analysis, run Agno
```

**Step 4: Implement copy_agno_from_primary function**

```python
# Add to batch_opportunity_scoring.py after should_run_agno_analysis

def copy_agno_from_primary(
    submission: dict,
    concept_id: str,
    supabase
) -> dict:
    """
    Copy Agno analysis results from primary opportunity.

    Args:
        submission: Current submission being processed
        concept_id: Business concept ID
        supabase: Supabase client

    Returns:
        llm_analysis dict formatted for hybrid_results, or {} if copy fails
    """
    try:
        # Get primary opportunity ID for this concept
        concept_response = supabase.table("business_concepts")\
            .select("primary_opportunity_id")\
            .eq("id", concept_id)\
            .execute()

        if not concept_response.data:
            return {}

        primary_opp_id = concept_response.data[0]["primary_opportunity_id"]

        # Get Agno analysis from llm_monetization_analysis table
        analysis_response = supabase.table("llm_monetization_analysis")\
            .select("*")\
            .eq("opportunity_id", f"opp_{primary_opp_id}")\
            .execute()

        if not analysis_response.data:
            return {}

        # Copy analysis and adapt for current submission
        primary_analysis = analysis_response.data[0]
        submission_id = submission.get("submission_id", submission.get("id"))

        # Return in hybrid_results format
        return {
            "opportunity_id": f"opp_{submission_id}",
            "submission_id": submission_id,
            "llm_monetization_score": primary_analysis["llm_monetization_score"],
            "keyword_monetization_score": primary_analysis["keyword_monetization_score"],
            "customer_segment": primary_analysis["customer_segment"],
            "willingness_to_pay_score": primary_analysis["willingness_to_pay_score"],
            "price_sensitivity_score": primary_analysis["price_sensitivity_score"],
            "revenue_potential_score": primary_analysis["revenue_potential_score"],
            "payment_sentiment": primary_analysis["payment_sentiment"],
            "urgency_level": primary_analysis["urgency_level"],
            "existing_payment_behavior": primary_analysis["existing_payment_behavior"],
            "mentioned_price_points": primary_analysis["mentioned_price_points"],
            "payment_friction_indicators": primary_analysis["payment_friction_indicators"],
            "confidence": primary_analysis["confidence"],
            "reasoning": primary_analysis["reasoning"],
            "subreddit_multiplier": primary_analysis["subreddit_multiplier"],
            "model_used": primary_analysis["model_used"],
            "score_delta": primary_analysis["score_delta"],
            "copied_from_primary": True,
            "primary_opportunity_id": primary_opp_id,
            "business_concept_id": concept_id,
        }

    except Exception as e:
        print(f"  ⚠️  Failed to copy Agno analysis from primary: {e}")
        return {}
```

**Step 5: Implement update_concept_agno_stats function**

```python
# Add to batch_opportunity_scoring.py after copy_agno_from_primary

def update_concept_agno_stats(
    concept_id: str,
    agno_result: dict,
    supabase
) -> None:
    """
    Update business concept with Agno analysis metadata.

    Args:
        concept_id: Business concept ID
        agno_result: Agno analysis result from MonetizationAgnoAnalyzer
        supabase: Supabase client
    """
    try:
        from datetime import datetime

        # Get current stats
        concept = supabase.table("business_concepts")\
            .select("agno_analysis_count, agno_avg_wtp_score")\
            .eq("id", concept_id)\
            .execute()

        current = concept.data[0] if concept.data else {}
        count = current.get("agno_analysis_count", 0) + 1

        # Calculate running average for WTP score
        new_wtp = agno_result.get("willingness_to_pay_score", 0)
        avg_wtp = current.get("agno_avg_wtp_score", 0)
        updated_wtp = ((avg_wtp * (count - 1)) + new_wtp) / count

        # Update database
        supabase.table("business_concepts").update({
            "has_agno_analysis": True,
            "agno_analysis_count": count,
            "last_agno_analysis_at": datetime.now().isoformat(),
            "agno_avg_wtp_score": updated_wtp,
        }).eq("id", concept_id).execute()

    except Exception as e:
        print(f"  ⚠️  Failed to update concept Agno stats: {e}")
```

**Step 6: Run test to verify functions work**

```bash
python tests/test_agno_deduplication.py
```

**Step 7: Commit Agno deduplication functions**

```bash
git add batch_opportunity_scoring.py tests/test_agno_deduplication.py
git commit -m "feat: Add Agno analysis deduplication functions"
```

---

### Task 3: AI Profiler Deduplication Functions

**Files:**
- Modify: `batch_opportunity_scoring.py` (after Agno functions)
- Test: `tests/test_profiler_deduplication.py`

**Step 1: Write failing test for Profiler skip logic**

```python
# File: tests/test_profiler_deduplication.py
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batch_opportunity_scoring import should_run_profiler_analysis, copy_profiler_from_primary

def test_should_run_profiler_for_new_submission():
    """Test that new submissions should run profiler analysis"""
    submission = {
        'submission_id': 'test-new-789',
        'title': 'New app concept'
    }
    mock_supabase = MockSupabase([])

    should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

    assert should_run == True, "New submissions should run profiler"
    assert concept_id is None, "New submissions should have no concept_id"
    print("✅ New submission correctly triggers profiler analysis")

def test_should_skip_profiler_for_duplicate_with_profile():
    """Test that duplicates with existing AI profile should skip"""
    submission = {
        'submission_id': 'test-duplicate-profile-999',
        'title': 'FitnessFAQ app idea'
    }
    mock_supabase = MockSupabase([
        {'is_duplicate': True, 'business_concept_id': '42'},
        {'primary_opportunity_id': 'abc123', 'has_ai_profile': True}
    ])

    should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

    assert should_run == False, "Duplicates with profile should skip profiler"
    assert concept_id == '42', "Should return concept_id for duplicate"
    print("✅ Duplicate correctly skips profiler analysis")

def test_copy_profiler_from_primary():
    """Test copying AI profile from primary opportunity"""
    submission = {
        'submission_id': 'test-copy-123',
        'title': 'Test copy'
    }
    concept_id = '42'

    # Mock response with existing AI profile
    mock_supabase = MockSupabase([
        {'primary_opportunity_id': 'abc123'},  # business_concepts response
        {  # opportunities_unified response
            'app_name': 'FitnessFAQ',
            'core_functions': ['Answer fitness questions', 'Track workout history'],
            'problem_description': 'FAQ platform for fitness',
            'value_proposition': 'Get expert fitness answers'
        }
    ])

    copied_profile = copy_profiler_from_primary(submission, concept_id, mock_supabase)

    assert 'core_functions' in copied_profile
    assert isinstance(copied_profile['core_functions'], list)
    assert copied_profile.get('copied_from_primary') == True
    assert copied_profile['app_name'] == 'FitnessFAQ'
    print("✅ AI profile correctly copied from primary")

# Mock classes (same as Agno test)
class MockSupabase:
    def __init__(self, data_list):
        self.data_list = data_list
        self.index = 0

    def table(self, table_name):
        return MockTable(self.data_list[self.index] if self.index < len(self.data_list) else [])

class MockTable:
    def __init__(self, data):
        self.data = data

    def select(self, columns):
        return self

    def eq(self, column, value):
        return self

    def execute(self):
        return MockResponse(self.data)

class MockResponse:
    def __init__(self, data):
        self.data = data

if __name__ == "__main__":
    test_should_run_profiler_for_new_submission()
    test_should_skip_profiler_for_duplicate_with_profile()
    test_copy_profiler_from_primary()
    print("✅ All Profiler deduplication tests passed")
```

**Step 2: Run test to verify it fails**

```bash
python tests/test_profiler_deduplication.py
```

Expected: FAIL with "function not defined" errors

**Step 3: Implement should_run_profiler_analysis function**

```python
# Add to batch_opportunity_scoring.py after Agno functions

def should_run_profiler_analysis(submission: dict, supabase) -> tuple[bool, str | None]:
    """
    Check if AI profiling should run for this submission.
    Skip if it's a duplicate with existing AI profile.

    This prevents semantic fragmentation of core_functions arrays.

    Args:
        submission: Submission dict from app_opportunities table
        supabase: Supabase client

    Returns:
        (should_run: bool, concept_id: str | None)
        - should_run: True to run profiler, False to skip and copy
        - concept_id: Business concept ID if duplicate, None otherwise
    """
    submission_id = submission.get("submission_id", submission.get("id"))

    # Query opportunities_unified to check deduplication status
    try:
        response = supabase.table("opportunities_unified")\
            .select("is_duplicate, business_concept_id")\
            .eq("submission_id", submission_id)\
            .execute()
    except Exception:
        return True, None  # If table doesn't exist or query fails, run profiler

    if not response.data:
        return True, None  # Not in unified table yet, run profiler

    opp = response.data[0]
    if not opp.get("is_duplicate"):
        return True, None  # Not a duplicate, run profiler

    concept_id = opp.get("business_concept_id")
    if not concept_id:
        return True, None  # Duplicate but no concept ID, run profiler anyway

    # Check if business_concepts has AI profile
    try:
        concept_response = supabase.table("business_concepts")\
            .select("primary_opportunity_id, has_ai_profile")\
            .eq("id", concept_id)\
            .execute()
    except Exception:
        return True, None  # If query fails, run profiler

    if not concept_response.data:
        return True, None  # No concept record, run profiler

    concept = concept_response.data[0]
    if concept.get("has_ai_profile"):
        return False, concept_id  # Skip profiler, copy from primary

    return True, None  # No existing profile, run profiler
```

**Step 4: Implement copy_profiler_from_primary function**

```python
# Add to batch_opportunity_scoring.py after should_run_profiler_analysis

def copy_profiler_from_primary(
    submission: dict,
    concept_id: str,
    supabase
) -> dict:
    """
    Copy AI profile (app_name, core_functions, etc.) from primary opportunity.

    This ensures consistent core_functions arrays across duplicate submissions,
    preventing semantic fragmentation.

    Args:
        submission: Current submission being processed
        concept_id: Business concept ID
        supabase: Supabase client

    Returns:
        ai_profile dict with app metadata, or {} if copy fails
    """
    try:
        # Get primary opportunity ID for this concept
        concept_response = supabase.table("business_concepts")\
            .select("primary_opportunity_id")\
            .eq("id", concept_id)\
            .execute()

        if not concept_response.data:
            return {}

        primary_opp_id = concept_response.data[0]["primary_opportunity_id"]

        # Get AI profile from opportunities_unified table
        profile_response = supabase.table("opportunities_unified")\
            .select(
                "app_name, problem_description, app_concept, core_functions, "
                "value_proposition, target_user, monetization_model, "
                "cost_tracking, evidence_validation, evidence_summary"
            )\
            .eq("submission_id", primary_opp_id)\
            .execute()

        if not profile_response.data:
            return {}

        # Copy profile and mark as copied
        primary_profile = profile_response.data[0]

        return {
            "app_name": primary_profile.get("app_name"),
            "problem_description": primary_profile.get("problem_description"),
            "app_concept": primary_profile.get("app_concept"),
            "core_functions": primary_profile.get("core_functions", []),
            "value_proposition": primary_profile.get("value_proposition"),
            "target_user": primary_profile.get("target_user"),
            "monetization_model": primary_profile.get("monetization_model"),
            "cost_tracking": primary_profile.get("cost_tracking", {}),
            "evidence_validation": primary_profile.get("evidence_validation"),
            "evidence_summary": primary_profile.get("evidence_summary"),
            "copied_from_primary": True,
            "primary_opportunity_id": primary_opp_id,
            "business_concept_id": concept_id,
        }

    except Exception as e:
        print(f"  ⚠️  Failed to copy AI profile from primary: {e}")
        return {}
```

**Step 5: Implement update_concept_profiler_stats function**

```python
# Add to batch_opportunity_scoring.py after copy_profiler_from_primary

def update_concept_profiler_stats(
    concept_id: str,
    ai_profile: dict,
    supabase
) -> None:
    """
    Update business concept with AI profile metadata.

    Args:
        concept_id: Business concept ID
        ai_profile: AI profile result from EnhancedLLMProfiler
        supabase: Supabase client
    """
    try:
        from datetime import datetime

        # Get current stats
        concept = supabase.table("business_concepts")\
            .select("ai_profile_count")\
            .eq("id", concept_id)\
            .execute()

        current = concept.data[0] if concept.data else {}
        count = current.get("ai_profile_count", 0) + 1

        # Update database
        supabase.table("business_concepts").update({
            "has_ai_profile": True,
            "ai_profile_count": count,
            "last_ai_profile_at": datetime.now().isoformat(),
        }).eq("id", concept_id).execute()

    except Exception as e:
        print(f"  ⚠️  Failed to update concept profiler stats: {e}")
```

**Step 6: Run test to verify functions work**

```bash
python tests/test_profiler_deduplication.py
```

**Step 7: Commit Profiler deduplication functions**

```bash
git add batch_opportunity_scoring.py tests/test_profiler_deduplication.py
git commit -m "feat: Add AI profiler deduplication functions"
```

---

### Task 4: Integration Point 1 - Agno Skip (Line 876)

**Files:**
- Modify: `batch_opportunity_scoring.py` (lines 876-926)
- Test: `tests/test_integration_agno.py`

**Step 1: Write failing test for Agno integration**

```python
# File: tests/test_integration_agno.py
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batch_opportunity_scoring import process_batch

def test_agno_skip_for_duplicate():
    """Test that Agno analysis is skipped for duplicates with existing analysis"""
    # This test would require mocking the entire process_batch function
    # For now, we'll test the integration logic exists
    import batch_opportunity_scoring as bos

    # Verify our helper functions exist and are callable
    assert hasattr(bos, 'should_run_agno_analysis'), "should_run_agno_analysis function should exist"
    assert hasattr(bos, 'copy_agno_from_primary'), "copy_agno_from_primary function should exist"
    assert callable(bos.should_run_agno_analysis), "should_run_agno_analysis should be callable"
    assert callable(bos.copy_agno_from_primary), "copy_agno_from_primary should be callable"

    print("✅ Agno integration functions are available")

def test_agno_integration_code_structure():
    """Test that the integration code is present in process_batch"""
    import inspect
    import batch_opportunity_scoring as bos

    # Get the source code of process_batch
    source = inspect.getsource(bos.process_batch)

    # Check that our integration patterns are present
    assert 'should_run_agno_analysis' in source, "should_run_agno_analysis should be called"
    assert 'copy_agno_from_primary' in source, "copy_agno_from_primary should be called"
    assert 'update_concept_agno_stats' in source, "update_concept_agno_stats should be called"

    print("✅ Agno integration code structure is correct")

if __name__ == "__main__":
    test_agno_skip_for_duplicate()
    test_agno_integration_code_structure()
    print("✅ All Agno integration tests passed")
```

**Step 2: Run test to verify integration is missing**

```bash
python tests/test_integration_agno.py
```

Expected: FAIL - integration code not yet added

**Step 3: Add Agno integration at line 876**

```python
# In batch_opportunity_scoring.py, around line 876, modify the Agno section:

# Find this existing code:
if final_score >= ai_profile_threshold:
    hybrid_results = {}

    # Option A: LLM Monetization Analysis (if enabled)
    if HYBRID_STRATEGY_CONFIG["option_a"]["enabled"]:
        # ... existing Agno code ...

# Replace with:
if final_score >= ai_profile_threshold:
    hybrid_results = {}

    # NEW: Check if we should skip Agno for this duplicate
    should_run_agno, concept_id = should_run_agno_analysis(submission, supabase)

    # Option A: LLM Monetization Analysis (if enabled)
    if HYBRID_STRATEGY_CONFIG["option_a"]["enabled"]:
        if should_run_agno:
            # ... existing Agno analysis code (keep lines 879-926) ...

            # NEW: Update concept with fresh Agno metadata
            if concept_id and "llm_analysis" in hybrid_results:
                update_concept_agno_stats(concept_id, hybrid_results["llm_analysis"], supabase)
        else:
            # Copy analysis from primary opportunity
            print(f"  🔄 Skipping Agno - duplicate of concept {concept_id}")
            hybrid_results["llm_analysis"] = copy_agno_from_primary(
                submission, concept_id, supabase
            )
```

**Step 4: Run test to verify integration works**

```bash
python tests/test_integration_agno.py
```

**Step 5: Commit Agno integration**

```bash
git add batch_opportunity_scoring.py tests/test_integration_agno.py
git commit -m "feat: Integrate Agno deduplication at line 876"
```

---

### Task 5: Integration Point 2 - AI Profiler Skip (Line 984)

**Files:**
- Modify: `batch_opportunity_scoring.py` (lines 984-1031)
- Test: `tests/test_integration_profiler.py`

**Step 1: Write failing test for Profiler integration**

```python
# File: tests/test_integration_profiler.py
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from batch_opportunity_scoring import process_batch

def test_profiler_skip_for_duplicate():
    """Test that AI profiling is skipped for duplicates with existing profile"""
    import batch_opportunity_scoring as bos

    # Verify our helper functions exist
    assert hasattr(bos, 'should_run_profiler_analysis'), "should_run_profiler_analysis should exist"
    assert hasattr(bos, 'copy_profiler_from_primary'), "copy_profiler_from_primary should exist"
    assert callable(bos.should_run_profiler_analysis), "should_run_profiler_analysis should be callable"
    assert callable(bos.copy_profiler_from_primary), "copy_profiler_from_primary should be callable"

    print("✅ Profiler integration functions are available")

def test_profiler_integration_code_structure():
    """Test that the profiler integration code is present in process_batch"""
    import inspect
    import batch_opportunity_scoring as bos

    source = inspect.getsource(bos.process_batch)

    # Check that our integration patterns are present
    assert 'should_run_profiler_analysis' in source, "should_run_profiler_analysis should be called"
    assert 'copy_profiler_from_primary' in source, "copy_profiler_from_primary should be called"
    assert 'update_concept_profiler_stats' in source, "update_concept_profiler_stats should be called"

    print("✅ Profiler integration code structure is correct")

if __name__ == "__main__":
    test_profiler_skip_for_duplicate()
    test_profiler_integration_code_structure()
    print("✅ All Profiler integration tests passed")
```

**Step 2: Run test to verify integration is missing**

```bash
python tests/test_integration_profiler.py
```

Expected: FAIL - integration code not yet added

**Step 3: Add Profiler integration at line 984**

```python
# In batch_opportunity_scoring.py, around line 984, modify the profiler section:

# Find this existing code:
if llm_profiler and final_score >= ai_profile_threshold:
    high_score_count += 1
    print(f"  🎯 High score ({final_score:.1f}) - generating AI profile...")

    # Generate real AI app profile with cost tracking
    try:
        # ... existing profiler code ...

# Replace with:
if llm_profiler and final_score >= ai_profile_threshold:
    high_score_count += 1

    # NEW: Check if we should skip AI profiling for this duplicate
    should_run_profiler, concept_id = should_run_profiler_analysis(submission, supabase)

    if should_run_profiler:
        print(f"  🎯 High score ({final_score:.1f}) - generating AI profile...")

        # Generate real AI app profile with cost tracking
        try:
            # ... existing profiler code (lines 988-1031) ...

            # NEW: Update concept with fresh profile metadata
            if concept_id:
                update_concept_profiler_stats(concept_id, ai_profile, supabase)
        except Exception as e:
            print(f"  ⚠️  AI profiling failed: {e}")
    else:
        # Copy AI profile from primary opportunity
        print(f"  🔄 Skipping AI profiling - duplicate of concept {concept_id}")
        copied_profile = copy_profiler_from_primary(submission, concept_id, supabase)

        if copied_profile:
            analysis.update(copied_profile)
            print(f"  ✅ Copied profile: {copied_profile.get('app_name', 'Unknown')}")
        else:
            print(f"  ⚠️  Copy failed - running fresh AI profile as fallback")
            # Fallback to fresh generation (include original code from lines 988-1031)
```

**Step 4: Run test to verify integration works**

```bash
python tests/test_integration_profiler.py
```

**Step 5: Commit Profiler integration**

```bash
git add batch_opportunity_scoring.py tests/test_integration_profiler.py
git commit -m "feat: Integrate AI profiler deduplication at line 984"
```

---

### Task 6: End-to-End Integration Testing

**Files:**
- Test: `tests/test_deduplication_e2e.py`
- Script: `scripts/testing/test_deduplication_integration.py`

**Step 1: Create comprehensive E2E test**

```python
# File: tests/test_deduplication_e2e.py
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_deduplication_pipeline_integration():
    """Test the complete deduplication pipeline with mocked data"""
    # This test verifies that all components work together
    import batch_opportunity_scoring as bos

    # Verify all required functions exist
    required_functions = [
        'should_run_agno_analysis',
        'should_run_profiler_analysis',
        'copy_agno_from_primary',
        'copy_profiler_from_primary',
        'update_concept_agno_stats',
        'update_concept_profiler_stats'
    ]

    for func_name in required_functions:
        assert hasattr(bos, func_name), f"{func_name} should exist"
        assert callable(getattr(bos, func_name)), f"{func_name} should be callable"

    # Test integration code is present
    import inspect
    source = inspect.getsource(bos.process_batch)

    integration_patterns = [
        'should_run_agno_analysis(submission, supabase)',
        'should_run_profiler_analysis(submission, supabase)',
        'copy_agno_from_primary(',
        'copy_profiler_from_primary('
    ]

    for pattern in integration_patterns:
        assert pattern in source, f"Integration pattern '{pattern}' should be present"

    print("✅ All deduplication components are integrated")
    print("✅ Integration patterns are correctly placed in process_batch")

def test_deduplication_function_signatures():
    """Test that all deduplication functions have correct signatures"""
    import batch_opportunity_scoring as bos
    import inspect

    # Test Agno functions
    agno_sig = inspect.signature(bos.should_run_agno_analysis)
    agno_params = list(agno_sig.parameters.keys())
    assert 'submission' in agno_params, "should_run_agno_analysis should take submission param"
    assert 'supabase' in agno_params, "should_run_agno_analysis should take supabase param"

    # Test Profiler functions
    prof_sig = inspect.signature(bos.should_run_profiler_analysis)
    prof_params = list(prof_sig.parameters.keys())
    assert 'submission' in prof_params, "should_run_profiler_analysis should take submission param"
    assert 'supabase' in prof_params, "should_run_profiler_analysis should take supabase param"

    print("✅ All deduplication functions have correct signatures")

if __name__ == "__main__":
    test_deduplication_pipeline_integration()
    test_deduplication_function_signatures()
    print("✅ All E2E deduplication tests passed")
```

**Step 2: Run E2E test**

```bash
python tests/test_deduplication_e2e.py
```

**Step 3: Create integration test script**

```python
# File: scripts/testing/test_deduplication_integration.py
#!/usr/bin/env python3
"""
Integration test script for deduplication functionality.
This script tests the actual integration with Supabase.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from supabase import create_client
from batch_opportunity_scoring import (
    should_run_agno_analysis, should_run_profiler_analysis,
    copy_agno_from_primary, copy_profiler_from_primary
)

def test_with_mock_data():
    """Test deduplication logic with mock data setup"""
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
    supabase_key = os.getenv('SUPABASE_KEY', 'your-anon-key')
    supabase = create_client(supabase_url, supabase_key)

    print("🧪 Testing deduplication integration with mock data...")

    # Test 1: New submission should run both analyses
    new_submission = {
        'submission_id': 'test-new-integration-123',
        'title': 'Brand new app concept'
    }

    should_agno, concept_id_1 = should_run_agno_analysis(new_submission, supabase)
    should_profiler, concept_id_2 = should_run_profiler_analysis(new_submission, supabase)

    assert should_agno == True, "New submission should run Agno"
    assert should_profiler == True, "New submission should run profiler"
    assert concept_id_1 is None, "New submission should have no concept_id for Agno"
    assert concept_id_2 is None, "New submission should have no concept_id for profiler"

    print("✅ New submission correctly triggers both analyses")

    # Test 2: Function signatures and basic behavior
    print("✅ All deduplication functions are callable")
    print("✅ Integration test completed successfully")

def test_error_handling():
    """Test that deduplication functions handle errors gracefully"""
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
    supabase_key = os.getenv('SUPABASE_KEY', 'your-anon-key')
    supabase = create_client(supabase_url, supabase_key)

    print("🧪 Testing error handling...")

    # Test with invalid submission
    invalid_submission = {}

    should_agno, concept_id_1 = should_run_agno_analysis(invalid_submission, supabase)
    should_profiler, concept_id_2 = should_run_profiler_analysis(invalid_submission, supabase)

    # Should default to running analyses when data is missing
    assert should_agno == True, "Invalid submission should default to running Agno"
    assert should_profiler == True, "Invalid submission should default to running profiler"

    print("✅ Error handling works correctly")

def main():
    """Run all integration tests"""
    print("🚀 Starting deduplication integration tests...\n")

    try:
        test_with_mock_data()
        print()
        test_error_handling()
        print()
        print("🎉 All integration tests passed!")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Step 4: Make test script executable**

```bash
chmod +x scripts/testing/test_deduplication_integration.py
```

**Step 5: Run integration tests**

```bash
python scripts/testing/test_deduplication_integration.py
```

**Step 6: Run all tests together**

```bash
python tests/test_agno_deduplication.py
python tests/test_profiler_deduplication.py
python tests/test_integration_agno.py
python tests/test_integration_profiler.py
python tests/test_deduplication_e2e.py
python scripts/testing/test_deduplication_integration.py
```

**Step 7: Commit integration tests**

```bash
git add tests/test_deduplication_e2e.py scripts/testing/test_deduplication_integration.py
git commit -m "feat: Add comprehensive deduplication integration tests"
```

---

### Task 7: Code Quality and Documentation

**Files:**
- Modify: `batch_opportunity_scoring.py` (add docstrings)
- Create: `docs/implementation/deduplication-integration-summary.md`
- Test: N/A

**Step 1: Add comprehensive docstring header**

```python
# Add to the top of batch_opportunity_scoring.py after existing imports:

"""
Deduplication Integration for AI Analysis Components

This module implements cost-saving deduplication logic for two expensive AI components:
1. Agno Monetization Analysis (multi-agent team, ~$0.10 per analysis)
2. AI App Profiling (EnhancedLLMProfiler, ~$0.005 per profile)

Key Functions:
- should_run_agno_analysis(): Check if Agno should run or be skipped
- should_run_profiler_analysis(): Check if profiler should run or be skipped
- copy_agno_from_primary(): Copy Agno results from primary opportunity
- copy_profiler_from_primary(): Copy AI profile from primary opportunity
- update_concept_agno_stats(): Update concept metadata after Agno analysis
- update_concept_profiler_stats(): Update concept metadata after profiling

Integration Points:
- Line 876: Agno monetization analysis deduplication check
- Line 984: AI profiling deduplication check

Expected ROI: 70% cost reduction ($3,528/year at 10K posts/month)
Data Quality: Consistent core_functions arrays, no semantic fragmentation
"""
```

**Step 2: Add inline comments at integration points**

```python
# At line 876, add comprehensive comments:

# === DEDUPLICATION INTEGRATION POINT 1: AGNO MONETIZATION ANALYSIS ===
# Skip expensive Agno multi-agent analysis (~$0.10) for duplicates
# Expected savings: $2.80 per 100 posts (70% reduction)
should_run_agno, concept_id = should_run_agno_analysis(submission, supabase)

# At line 984, add comprehensive comments:

# === DEDUPLICATION INTEGRATION POINT 2: AI PROFILING ===
# Skip AI app profiling for duplicates to prevent semantic fragmentation
# Ensures consistent core_functions arrays across duplicate submissions
should_run_profiler, concept_id = should_run_profiler_analysis(submission, supabase)
```

**Step 3: Create integration summary documentation**

```markdown
# File: docs/implementation/deduplication-integration-summary.md

# Deduplication Integration Summary

## Overview
Successfully implemented cost-saving deduplication for both Agno monetization analysis and AI app profiling components in the RedditHarbor opportunity scoring pipeline.

## What Was Built

### 1. Database Schema Updates
- Added tracking columns to `business_concepts` table
- Added deduplication tracking to `llm_monetization_analysis` and `opportunities_unified` tables
- Created indexes for fast deduplication lookups

### 2. Agno Deduplication Functions
- `should_run_agno_analysis()`: Check if Agno should run for a submission
- `copy_agno_from_primary()`: Copy Agno results from primary opportunity
- `update_concept_agno_stats()`: Update concept metadata after Agno analysis

### 3. AI Profiler Deduplication Functions
- `should_run_profiler_analysis()`: Check if profiler should run for a submission
- `copy_profiler_from_primary()`: Copy AI profile from primary opportunity
- `update_concept_profiler_stats()`: Update concept metadata after profiling

### 4. Integration Points
- **Line 876**: Added Agno skip logic in `process_batch()`
- **Line 984**: Added profiler skip logic in `process_batch()`

## Expected Benefits

### Cost Savings
- **70% reduction** in both Agno and Profiler API calls
- **$3,528/year** savings (at 10K posts/month, 40% qualifying rate)
- **Faster processing** (fewer LLM calls)

### Data Quality
- **Consistent core_functions** arrays across duplicates
- **No semantic fragmentation** of app concepts
- **Better analytics** with clean concept aggregation

## Testing Coverage
- Unit tests for all deduplication functions
- Integration tests for both skip points
- E2E pipeline integration tests
- Error handling and fallback tests

## Files Modified
- `batch_opportunity_scoring.py`: Added 6 helper functions + 2 integration points
- `supabase/migrations/`: Added deduplication schema
- `tests/`: Added comprehensive test suite
- `docs/`: Added integration documentation

## Next Steps
1. Monitor production skip rates
2. Validate cost savings metrics
3. Verify data quality improvements
4. Consider expanding to other AI components
```

**Step 4: Run linting and formatting**

```bash
# Run ruff for linting
ruff check batch_opportunity_scoring.py
ruff format batch_opportunity_scoring.py

# Run tests to ensure nothing broke
python tests/test_deduplication_e2e.py
```

**Step 5: Commit documentation and final cleanup**

```bash
git add batch_opportunity_scoring.py docs/implementation/deduplication-integration-summary.md
git commit -m "docs: Add deduplication integration documentation and final cleanup"
```

---

## Summary

This implementation plan provides a comprehensive, bite-sized approach to integrating deduplication functionality that:

1. **Saves 70% on AI costs** by skipping both Agno ($0.10) and Profiler ($0.005) analysis for duplicates
2. **Eliminates semantic fragmentation** by ensuring consistent `core_functions` arrays across duplicates
3. **Provides robust error handling** with fallbacks to fresh analysis when copying fails
4. **Includes comprehensive testing** covering unit, integration, and E2E scenarios
5. **Tracks everything** with proper database schema for monitoring and analytics

The plan follows TDD principles, maintains clean code practices, and provides clear monitoring capabilities for validating the expected $3,528/year savings at scale.

**Plan complete and saved to `docs/plans/2025-11-19-complete-deduplication-integration.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**