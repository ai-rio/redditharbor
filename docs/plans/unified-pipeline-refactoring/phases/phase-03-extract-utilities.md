# Phase 3: Extract Utilities

**Timeline**: Week 2, Days 6-10  
**Duration**: 5 days  
**Risk Level**: 🟢 LOW  
**Dependencies**: Phase 2 completed (agent restructuring)

---

## Context

### What Was Completed (Phase 2)
- [x] Restructured `agent_tools/` → `core/agents/` 
- [x] Split 70KB files into manageable modules
- [x] Updated all imports across codebase
- [x] All tests passing with new structure

### Current State
Standalone utility functions are scattered across monolithic scripts:
- `map_subreddit_to_sector()` in batch_opportunity_scoring.py (100 lines)
- `format_submission_for_agent()` in batch_opportunity_scoring.py (40 lines)
- Quality scoring functions in dlt_trust_pipeline.py (75 lines)
- Trust score converters in dlt_trust_pipeline.py (50 lines)

### Why This Phase Is Critical
- Utilities have no side effects - safest extraction
- Enables immediate reuse in both pipelines
- Establishes pattern for subsequent extractions
- 100% test coverage achievable

---

## Objectives

### Primary Goals
1. **Extract** all standalone utility functions from monoliths
2. **Achieve** 100% test coverage for extracted utilities
3. **Enable** side-by-side operation with monoliths
4. **Document** usage patterns for extracted utilities

### Success Criteria
- [ ] All utilities extracted to appropriate modules
- [ ] 100% test coverage for extracted functions
- [ ] Both monoliths work with extracted utilities
- [ ] No duplicate utility code remains

### Risk Mitigation
- Keep original functions as deprecated wrappers initially
- Update imports incrementally
- Test each extraction independently

---

## Tasks

### Task 1: Extract Sector Mapping Utility (1 day)

**Source**: `scripts/core/batch_opportunity_scoring.py:188`

**Create**: `core/utils/sector_mapping.py`

```python
"""Subreddit to business sector mapping."""
from typing import Dict, Optional

# Comprehensive sector mappings
SUBREDDIT_SECTOR_MAP: Dict[str, str] = {
    # Technology & SaaS
    'SaaS': 'Technology',
    'startups': 'General Business',
    'Entrepreneur': 'General Business',
    'smallbusiness': 'Small Business',
    
    # Fitness & Health
    'fitness': 'Health & Fitness',
    'loseit': 'Health & Fitness',
    'bodyweightfitness': 'Health & Fitness',
    'running': 'Health & Fitness',
    
    # Finance & Investment
    'personalfinance': 'Finance',
    'investing': 'Finance',
    'financialindependence': 'Finance',
    
    # Productivity & Tools
    'productivity': 'Productivity Tools',
    'gtd': 'Productivity Tools',
    'notion': 'Productivity Tools',
    
    # Education & Learning
    'learnprogramming': 'Education',
    'languagelearning': 'Education',
    'GetStudying': 'Education',
    
    # E-commerce & Retail
    'ecommerce': 'E-commerce',
    'Shopify': 'E-commerce',
    'AmazonSeller': 'E-commerce',
    
    # Developer Tools
    'webdev': 'Developer Tools',
    'devops': 'Developer Tools',
    'programming': 'Developer Tools',
}

def map_subreddit_to_sector(subreddit: str) -> str:
    """
    Map a subreddit name to its business sector.
    
    Args:
        subreddit: Name of the subreddit (case-insensitive)
        
    Returns:
        str: Business sector, or 'General' if not found
        
    Examples:
        >>> map_subreddit_to_sector('SaaS')
        'Technology'
        >>> map_subreddit_to_sector('fitness')
        'Health & Fitness'
        >>> map_subreddit_to_sector('unknown')
        'General'
    """
    return SUBREDDIT_SECTOR_MAP.get(subreddit, 'General')

def get_all_sectors() -> list[str]:
    """Get list of all unique sectors."""
    return sorted(set(SUBREDDIT_SECTOR_MAP.values()))

def get_subreddits_by_sector(sector: str) -> list[str]:
    """Get all subreddits for a given sector."""
    return [
        subreddit for subreddit, s in SUBREDDIT_SECTOR_MAP.items()
        if s == sector
    ]
```

**Update monolith to use extracted version**:

```python
# In batch_opportunity_scoring.py
# OLD (lines 188-288):
# def map_subreddit_to_sector(subreddit: str) -> str:
#     ... (100 lines of mapping)

# NEW:
from core.utils.sector_mapping import map_subreddit_to_sector

# Keep deprecated wrapper for safety during transition
def map_subreddit_to_sector_DEPRECATED(subreddit: str) -> str:
    """DEPRECATED: Use core.utils.sector_mapping.map_subreddit_to_sector"""
    from core.utils.sector_mapping import map_subreddit_to_sector as new_func
    return new_func(subreddit)
```

**Create tests**:

```python
# tests/test_sector_mapping.py
import pytest
from core.utils.sector_mapping import (
    map_subreddit_to_sector,
    get_all_sectors,
    get_subreddits_by_sector,
    SUBREDDIT_SECTOR_MAP
)

def test_map_known_subreddit():
    """Test mapping of known subreddits."""
    assert map_subreddit_to_sector('SaaS') == 'Technology'
    assert map_subreddit_to_sector('fitness') == 'Health & Fitness'
    assert map_subreddit_to_sector('personalfinance') == 'Finance'

def test_map_unknown_subreddit():
    """Test mapping of unknown subreddit returns General."""
    assert map_subreddit_to_sector('unknown_sub_12345') == 'General'

def test_get_all_sectors():
    """Test getting all unique sectors."""
    sectors = get_all_sectors()
    assert 'Technology' in sectors
    assert 'Health & Fitness' in sectors
    assert len(sectors) == len(set(SUBREDDIT_SECTOR_MAP.values()))

def test_get_subreddits_by_sector():
    """Test getting subreddits for a sector."""
    tech_subs = get_subreddits_by_sector('Technology')
    assert 'SaaS' in tech_subs
    
    fitness_subs = get_subreddits_by_sector('Health & Fitness')
    assert 'fitness' in fitness_subs
    assert 'running' in fitness_subs

@pytest.mark.parametrize('subreddit', SUBREDDIT_SECTOR_MAP.keys())
def test_all_mappings_return_valid_sector(subreddit):
    """Test that all defined mappings return non-empty sectors."""
    sector = map_subreddit_to_sector(subreddit)
    assert sector
    assert isinstance(sector, str)
    assert len(sector) > 0
```

**Validation:**
- [ ] File created: `core/utils/sector_mapping.py`
- [ ] Tests pass: `pytest tests/test_sector_mapping.py -v`
- [ ] Coverage 100%: `pytest tests/test_sector_mapping.py --cov=core.utils.sector_mapping`
- [ ] Import works in monolith
- [ ] Monolith still functional

---

### Task 2: Extract Submission Formatters (1 day)

**Source**: `scripts/core/batch_opportunity_scoring.py:939`

**Create**: `core/fetchers/formatters.py`

```python
"""Submission data formatting utilities."""
from typing import Dict, Any, Optional
from datetime import datetime

def format_submission_for_agent(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format submission data for AI agent consumption.
    
    Standardizes field names, handles missing data, and adds metadata.
    
    Args:
        submission: Raw submission data from database or Reddit API
        
    Returns:
        dict: Formatted submission ready for AI analysis
        
    Examples:
        >>> raw = {'submission_id': '123', 'title': 'Test', ...}
        >>> formatted = format_submission_for_agent(raw)
        >>> assert 'submission_text' in formatted
    """
    return {
        'submission_id': submission.get('submission_id', ''),
        'submission_title': submission.get('title', ''),
        'submission_content': submission.get('content', submission.get('selftext', '')),
        'submission_text': f"{submission.get('title', '')} {submission.get('content', '')}",
        'subreddit': submission.get('subreddit', ''),
        'author': submission.get('author', '[deleted]'),
        'score': submission.get('score', 0),
        'num_comments': submission.get('num_comments', 0),
        'created_utc': submission.get('created_utc', 0),
        'url': submission.get('url', ''),
        'permalink': submission.get('permalink', ''),
        # Metadata
        'formatted_at': datetime.utcnow().isoformat(),
        'has_content': bool(submission.get('content') or submission.get('selftext')),
    }

def format_batch_submissions(submissions: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Format multiple submissions."""
    return [format_submission_for_agent(sub) for sub in submissions]

def extract_problem_statement(submission: Dict[str, Any]) -> str:
    """
    Extract the core problem statement from submission.
    
    Combines title and content into a concise problem description.
    """
    title = submission.get('title', '').strip()
    content = submission.get('content', submission.get('selftext', '')).strip()
    
    # Combine title and first 500 chars of content
    if content:
        content_preview = content[:500] + ('...' if len(content) > 500 else '')
        return f"{title}\n\n{content_preview}"
    return title

def validate_submission_completeness(submission: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate submission has all required fields.
    
    Returns:
        tuple: (is_valid, list of missing fields)
    """
    required_fields = ['submission_id', 'title', 'subreddit']
    missing = [field for field in required_fields if not submission.get(field)]
    return len(missing) == 0, missing
```

**Create tests**:

```python
# tests/test_formatters.py
import pytest
from core.fetchers.formatters import (
    format_submission_for_agent,
    format_batch_submissions,
    extract_problem_statement,
    validate_submission_completeness
)

@pytest.fixture
def raw_submission():
    return {
        'submission_id': 'test123',
        'title': 'I need a fitness app',
        'content': 'Looking for an app that helps me track workouts',
        'subreddit': 'fitness',
        'author': 'test_user',
        'score': 42,
        'num_comments': 5,
        'created_utc': 1700000000,
        'url': 'https://reddit.com/test123',
        'permalink': '/r/fitness/test123'
    }

def test_format_submission_for_agent(raw_submission):
    """Test basic submission formatting."""
    formatted = format_submission_for_agent(raw_submission)
    
    assert formatted['submission_id'] == 'test123'
    assert formatted['submission_title'] == 'I need a fitness app'
    assert formatted['submission_content'] == 'Looking for an app that helps me track workouts'
    assert 'submission_text' in formatted
    assert formatted['has_content'] is True
    assert 'formatted_at' in formatted

def test_format_submission_missing_content():
    """Test formatting submission with missing content."""
    submission = {'submission_id': 'test', 'title': 'Test', 'subreddit': 'test'}
    formatted = format_submission_for_agent(submission)
    
    assert formatted['submission_content'] == ''
    assert formatted['has_content'] is False
    assert formatted['author'] == '[deleted]'
    assert formatted['score'] == 0

def test_format_batch_submissions(raw_submission):
    """Test batch formatting."""
    submissions = [raw_submission, raw_submission.copy()]
    formatted = format_batch_submissions(submissions)
    
    assert len(formatted) == 2
    assert all('submission_text' in sub for sub in formatted)

def test_extract_problem_statement(raw_submission):
    """Test problem statement extraction."""
    problem = extract_problem_statement(raw_submission)
    
    assert 'I need a fitness app' in problem
    assert 'Looking for an app' in problem

def test_extract_problem_statement_long_content():
    """Test truncation of long content."""
    submission = {
        'title': 'Test',
        'content': 'x' * 1000
    }
    problem = extract_problem_statement(submission)
    
    assert len(problem) < 600  # Title + 500 chars + ellipsis
    assert problem.endswith('...')

def test_validate_submission_completeness_valid(raw_submission):
    """Test validation of complete submission."""
    is_valid, missing = validate_submission_completeness(raw_submission)
    
    assert is_valid is True
    assert len(missing) == 0

def test_validate_submission_completeness_missing_fields():
    """Test validation catches missing fields."""
    incomplete = {'submission_id': 'test'}
    is_valid, missing = validate_submission_completeness(incomplete)
    
    assert is_valid is False
    assert 'title' in missing
    assert 'subreddit' in missing
```

**Validation:**
- [ ] File created: `core/fetchers/formatters.py`
- [ ] Tests pass: `pytest tests/test_formatters.py -v --cov=core.fetchers.formatters`
- [ ] Coverage 100%
- [ ] Used in monolith successfully

---

### Task 3: Extract Quality Filters (2 days)

**Source**: `scripts/dlt/dlt_trust_pipeline.py:101,137`

**Create**: `core/quality_filters/quality_scorer.py`

```python
"""Pre-AI quality scoring for submissions."""
from typing import Dict, Any

def calculate_pre_ai_quality_score(submission: Dict[str, Any]) -> float:
    """
    Calculate quality score before AI analysis.
    
    Considers engagement, content length, and community signals.
    
    Args:
        submission: Submission data
        
    Returns:
        float: Quality score 0-100
    """
    score = 0.0
    
    # Engagement score (40 points)
    upvotes = submission.get('score', 0)
    comments = submission.get('num_comments', 0)
    
    if upvotes > 100:
        score += 20
    elif upvotes > 50:
        score += 15
    elif upvotes > 20:
        score += 10
    elif upvotes > 5:
        score += 5
    
    if comments > 50:
        score += 20
    elif comments > 20:
        score += 15
    elif comments > 10:
        score += 10
    elif comments > 3:
        score += 5
    
    # Content quality (30 points)
    content = submission.get('content', submission.get('selftext', ''))
    title = submission.get('title', '')
    
    content_length = len(content)
    if content_length > 500:
        score += 15
    elif content_length > 200:
        score += 10
    elif content_length > 50:
        score += 5
    
    if len(title) > 20:
        score += 10
    elif len(title) > 10:
        score += 5
    
    # Specificity indicators (30 points)
    problem_keywords = ['need', 'wish', 'looking for', 'want', 'struggle', 'difficult', 'problem', 'issue']
    solution_keywords = ['app', 'tool', 'service', 'software', 'platform', 'solution']
    
    text_lower = f"{title} {content}".lower()
    
    problem_count = sum(1 for keyword in problem_keywords if keyword in text_lower)
    solution_count = sum(1 for keyword in solution_keywords if keyword in text_lower)
    
    if problem_count >= 2:
        score += 15
    elif problem_count >= 1:
        score += 10
    
    if solution_count >= 1:
        score += 15
    elif solution_count >= 1:
        score += 10
    
    return min(score, 100.0)

def get_quality_breakdown(submission: Dict[str, Any]) -> Dict[str, float]:
    """Get detailed quality score breakdown."""
    # Implementation details...
    pass
```

**Create**: `core/quality_filters/pre_filter.py`

```python
"""Pre-AI filtering logic."""
from typing import Dict, Any
from .quality_scorer import calculate_pre_ai_quality_score

DEFAULT_QUALITY_THRESHOLD = 30.0

def should_analyze_with_ai(
    submission: Dict[str, Any],
    threshold: float = DEFAULT_QUALITY_THRESHOLD
) -> tuple[bool, float, str]:
    """
    Determine if submission should undergo AI analysis.
    
    Args:
        submission: Submission data
        threshold: Minimum quality score required
        
    Returns:
        tuple: (should_analyze, quality_score, reason)
    """
    quality_score = calculate_pre_ai_quality_score(submission)
    
    if quality_score < threshold:
        return False, quality_score, f"Quality score {quality_score:.1f} below threshold {threshold}"
    
    # Additional checks
    content = submission.get('content', submission.get('selftext', ''))
    if len(content) < 20:
        return False, quality_score, "Content too short"
    
    if submission.get('score', 0) < 0:
        return False, quality_score, "Negative score (downvoted)"
    
    return True, quality_score, "Passed pre-filter"

def filter_submissions_batch(
    submissions: list[Dict[str, Any]],
    threshold: float = DEFAULT_QUALITY_THRESHOLD
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    """
    Filter batch of submissions.
    
    Returns:
        tuple: (passed_submissions, filtered_out_submissions)
    """
    passed = []
    filtered = []
    
    for sub in submissions:
        should_analyze, score, reason = should_analyze_with_ai(sub, threshold)
        
        sub_with_meta = {**sub, 'quality_score': score, 'filter_reason': reason}
        
        if should_analyze:
            passed.append(sub_with_meta)
        else:
            filtered.append(sub_with_meta)
    
    return passed, filtered
```

**Create comprehensive tests** (similar pattern to previous tasks)

**Validation:**
- [ ] Both files created in `core/quality_filters/`
- [ ] Tests pass with 100% coverage
- [ ] Integrated into dlt_trust_pipeline.py
- [ ] Quality filtering working as before

---

### Task 4: Extract Trust Score Converters (1 day)

**Source**: `scripts/dlt/dlt_trust_pipeline.py:423-471`

**Create**: `core/enrichment/trust_converters.py`

```python
"""Trust score conversion utilities."""

def get_engagement_level(score: float) -> str:
    """Convert engagement score to categorical level."""
    if score >= 80:
        return "Very High"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Medium"
    elif score >= 20:
        return "Low"
    else:
        return "Very Low"

def get_problem_validity(score: float) -> str:
    """Convert problem validity score to category."""
    if score >= 80:
        return "Highly Valid"
    elif score >= 60:
        return "Valid"
    elif score >= 40:
        return "Somewhat Valid"
    else:
        return "Questionable"

def get_discussion_quality(score: float) -> str:
    """Convert discussion quality score to category."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor"

def get_ai_confidence_level(score: float) -> str:
    """Convert AI confidence score to category."""
    if score >= 90:
        return "Very High"
    elif score >= 70:
        return "High"
    elif score >= 50:
        return "Medium"
    elif score >= 30:
        return "Low"
    else:
        return "Very Low"

def convert_all_trust_scores(trust_data: dict) -> dict:
    """Convert all numeric trust scores to categorical levels."""
    return {
        'engagement_level': get_engagement_level(trust_data.get('engagement_score', 0)),
        'problem_validity': get_problem_validity(trust_data.get('problem_validity_score', 0)),
        'discussion_quality': get_discussion_quality(trust_data.get('discussion_quality_score', 0)),
        'ai_confidence': get_ai_confidence_level(trust_data.get('ai_confidence_score', 0)),
        # Preserve original scores
        **trust_data
    }
```

**Create tests** (similar pattern)

**Validation:**
- [ ] File created
- [ ] Tests pass with 100% coverage
- [ ] Used in trust service

---

## Full Validation Checklist

### Extraction Validation
- [ ] All utilities extracted from monoliths
- [ ] No duplicate utility code remains in monoliths
- [ ] Imports updated to use new modules
- [ ] Deprecated wrappers in place (optional safety)

### Testing Validation
- [ ] 100% test coverage for all extracted utilities
- [ ] All parametrized tests pass
- [ ] Edge cases covered
- [ ] pytest runs clean: `pytest tests/test_*_util*.py -v`

### Integration Validation
- [ ] Both monoliths work with extracted utilities
- [ ] No functionality regression
- [ ] Side-by-side operation confirmed
- [ ] Performance unchanged

### Documentation Validation
- [ ] Module docstrings complete
- [ ] Function docstrings with examples
- [ ] Usage patterns documented
- [ ] CLAUDE.md updated with new utils

---

## Rollback Procedure

If utilities extraction causes issues:

```bash
# Restore original utility functions in monoliths
git diff HEAD -- scripts/core/batch_opportunity_scoring.py
git checkout HEAD -- scripts/core/batch_opportunity_scoring.py

# Remove extracted utilities
rm -rf core/utils/sector_mapping.py
rm -rf core/fetchers/formatters.py
rm -rf core/quality_filters/quality_scorer.py
rm -rf core/quality_filters/pre_filter.py
rm -rf core/enrichment/trust_converters.py

# Remove tests
rm tests/test_sector_mapping.py
rm tests/test_formatters.py
rm tests/test_quality_*.py
rm tests/test_trust_converters.py

# Verify original system works
pytest tests/ -v
```

---

## Estimated Time Breakdown

| Task | Time |
|------|------|
| Task 1: Sector mapping | 1 day |
| Task 2: Formatters | 1 day |
| Task 3: Quality filters | 2 days |
| Task 4: Trust converters | 1 day |
| **Total** | **5 days** |

---

## Next Phase

→ **[Phase 4: Extract Data Fetching Layer](phase-04-extract-fetchers.md)**

Phase 4 will create abstract fetcher interface and extract database + Reddit API fetchers.

---

**Status**: ⏸️ NOT STARTED  
**Last Updated**: 2025-11-19

[← Back to Phases](../PHASES.md) | [↑ Top](#phase-3-extract-utilities)
