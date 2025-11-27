# Trust Validation System Interface Specification

**Phase 4: Trust Validation Characterization**
**Source: scripts/dlt/dlt_trust_pipeline.py**
**Target: pipeline-v2/trust/validator.py**

## Overview

This document characterizes the existing trust validation system in `dlt_trust_pipeline.py` to understand the complete 6-dimensional trust scoring algorithm before extracting to `pipeline-v2/trust/validator.py`.

## System Architecture

### Current Implementation Structure

```
scripts/dlt/dlt_trust_pipeline.py
├── TrustLayerValidator (core/trust/legacy_layer.py)
│   ├── TrustValidationService (core/trust/validation.py)
│   ├── TrustIndicators (core/trust/models.py)
│   └── TrustRepository (core/trust/repository.py)
└── Integration Points
    ├── collect_posts_with_activity_validation()
    ├── analyze_opportunities_with_ai()
    ├── apply_trust_validation()
    └── load_trusted_opportunities_to_supabase()
```

### Target Extraction Structure

```
pipeline-v2/trust/
├── validator.py          # Main trust validation logic
├── scoring.py           # 6-dimensional scoring algorithms
├── badges.py            # Badge assignment system
├── constraints.py       # Validation constraints
└── integration.py       # Pipeline integration helpers
```

## 6-Dimensional Trust Scoring Algorithm

### 1. Subreddit Activity Scoring (25% weight)

**Purpose**: Validate community engagement and subreddit health
**Implementation**: Uses `calculate_activity_score` from `core.activity_validation`
**Normalization**: Raw score × 2 (scaled to 0-100)
**Reddit API**: Fetches subreddit data via PRAW client

```python
def _validate_subreddit_activity(request):
    # Uses Reddit API to get subreddit activity
    # Normalizes: raw_score * 2
    # Returns: 0-100 activity score
```

**Scoring Pattern**:
- Raw activity score from Reddit API
- Multiplied by 2 for normalization to 0-100 scale
- Network errors return 0.0

### 2. Post Engagement Scoring (20% weight)

**Purpose**: Measure post interaction and community response
**Components**: Upvotes (70%) + Comments (30%)
**Upvote Scaling**: Logarithmic to reward engagement growth

```python
if upvotes <= 10:
    upvote_score = upvotes * 10
elif upvotes <= 100:
    upvote_score = 100 + (upvotes - 10) * 5
else:
    upvote_score = 100 + (upvotes - 100) * 2

comment_score = min(100, comments)
engagement_score = (upvote_score * 0.7) + (comment_score * 0.3)
```

**Score Range**: 0-100+ (can exceed 100 for high engagement)

### 3. Trend Velocity Scoring (15% weight)

**Purpose**: Identify emerging vs established opportunities
**Time-based Multipliers**:
- ≤1 hour: engagement × 10 (very recent)
- ≤24 hours: engagement × 5 (recent)
- ≤1 week: engagement × 2 (establishing)
- >1 week: engagement × 1 with decay (aging)

```python
if hours_old <= 1:
    velocity_score = min(100, total_engagement * 10)
elif hours_old <= 24:
    velocity_score = min(100, total_engagement * 5)
elif hours_old <= 168:
    velocity_score = min(100, total_engagement * 2)
else:
    velocity_score = min(100, total_engagement)
    # Apply time decay for very old posts
    if hours_old > 168:
        decay_factor = max(0.1, 1.0 - (hours_old - 168) / 720)
        velocity_score *= decay_factor
```

**Decay Logic**: Linear decay over 1 month for posts older than 1 week

### 4. Problem Validity Scoring (15% weight)

**Purpose**: Validate problem clarity and AI analysis quality
**Components**: Problem keywords (60%) + Description length (40%)

```python
# Problem keyword detection
problem_keywords_found = len([kw for kw in PROBLEM_KEYWORDS if kw in text.lower()])
keyword_score = min(100, problem_keywords_found * 20)

# Length validation
length_score = min(100, len(problem_desc) / 2)

validity_score = (keyword_score * 0.6) + (length_score * 0.4)
```

**Validation Requirements**:
- `problem_description` length ≥ 20 characters
- `app_concept` length ≥ 20 characters
- Keywords from `core.collection.PROBLEM_KEYWORDS`

### 5. Discussion Quality Scoring (15% weight)

**Purpose**: Measure community discussion depth
**Scaling Logic**:
- 0 comments: 0 score
- 1-5 comments: `comments * 20` (linear)
- 6-50 comments: `100 + (comments - 5) * 2` (bonus)
- >50 comments: 100 (maximum)

```python
if comments_count == 0:
    return 0.0
elif comments_count <= 5:
    return comments_count * 20
elif comments_count <= 50:
    return 100 + (comments_count - 5) * 2
else:
    return 100
```

### 6. AI Confidence Scoring (10% weight)

**Purpose**: Validate AI analysis reliability
**Score Mapping**:
- `final_score` ≥ 70: 90.0 confidence (high)
- `final_score` ≥ 50: 70.0 confidence (medium)
- `final_score` ≥ 30: 50.0 confidence (low)
- `final_score` < 30: 30.0 confidence (very low)

```python
if final_score >= 70:
    return 90.0  # High confidence
elif final_score >= 50:
    return 70.0  # Medium confidence
elif final_score >= 30:
    return 50.0  # Low confidence
else:
    return 30.0  # Very low confidence
```

## Overall Trust Score Calculation

**Weighted Sum Formula**:
```
overall_trust_score = (
    subreddit_activity_score * 0.25 +
    post_engagement_score * 0.20 +
    trend_velocity_score * 0.15 +
    problem_validity_score * 0.15 +
    discussion_quality_score * 0.15 +
    ai_analysis_confidence * 0.10
)
```

**Trust Level Mapping**:
- `>= 85.0`: VERY_HIGH
- `>= 70.0`: HIGH
- `>= 50.0`: MEDIUM
- `< 50.0`: LOW

## Badge Assignment System

### Primary Trust Badges

```python
if overall_trust_score >= 85:
    primary_badge = "GOLD"
elif overall_trust_score >= 70:
    primary_badge = "SILVER"
elif overall_trust_score >= 50:
    primary_badge = "BRONZE"
else:
    primary_badge = "BASIC"
```

### Secondary Achievement Badges

#### Activity Badges (if `activity_constraints_met`):
- `activity_score >= 80`: "🔥 Highly Active Community"
- `activity_score >= 60`: "✅ Active Community"
- `activity_score < 60`: "⚠️ Low Activity"

#### Engagement Badges:
- `engagement_score >= 70`: "📈 High Engagement"
- `engagement_score >= 40`: "📊 Good Engagement"

#### Trend Badges:
- `trend_score >= 80`: "🚀 Trending Topic"
- `trend_score >= 50`: "📈 Emerging Trend"

#### Quality Badges:
- `quality_constraints_met`: "✅ Quality Verified"

#### AI Confidence Badges:
- `ai_confidence >= 70`: "🤖 High AI Confidence"
- `ai_confidence >= 50`: "🤖 AI Verified"

#### Trust Level Badges:
- VERY_HIGH: "🏆 Premium Quality"
- HIGH: "🌟 High Trust"
- MEDIUM: "🟡 Moderate Trust"
- LOW: "⚠️ Basic Validation"

## Validation Constraints

### Quality Constraints (`quality_constraints_met`)

**Requirements**:
1. `core_functions` count ≤ `MAX_CORE_FUNCTIONS` (3)
2. `problem_description` length ≥ `MIN_PROBLEM_DESCRIPTION_LENGTH` (20)
3. `app_concept` length ≥ `MIN_APP_CONCEPT_LENGTH` (20)

**Penalty Application**:
- Quality constraints failed: 20% confidence penalty
- Activity constraints failed: 10% confidence penalty

### Activity Constraints (`activity_constraints_met`)

**Requirement**:
- `activity_score >= activity_threshold` (default: 25.0)

## Database Field Mapping

### Input Schema (`submission_data`)
```python
{
    'submission_id': str,
    'title': str,
    'text': str,
    'subreddit': str,
    'upvotes': int,
    'comments_count': int,
    'created_utc': float | str,
    'permalink': str
}
```

### AI Analysis Schema (`ai_analysis`)
```python
{
    'final_score': float,
    'confidence_score': float,
    'market需求评估': str,
    '技术可行性': str,
    '商业模式': str,
    '竞争分析': str,
    'user_pain_point': str,
    'core_features': List[str],
    'monetization': str,
    'target_audience': str
}
```

### Output Schema (`TrustIndicators`)
```python
{
    # Core trust metrics
    'trust_score': float,
    'trust_level': str,
    'trust_badges': List[str],

    # Activity indicators
    'activity_score': float,
    'engagement_level': str,
    'trend_velocity': float,

    # Quality indicators
    'problem_validity': str,
    'discussion_quality': str,
    'ai_confidence_level': str,

    # Validation metadata
    'validation_timestamp': str,
    'validation_method': str,
    'confidence_score': float,

    # Constraint indicators
    'quality_constraints_met': bool,
    'activity_constraints_met': bool,

    # Detailed scoring components
    'subreddit_activity_score': float,
    'post_engagement_score': float,
    'community_health_score': float,
    'trend_velocity_score': float,
    'problem_validity_score': float,
    'discussion_quality_score': float,
    'ai_analysis_confidence': float,
    'overall_trust_score': float
}
```

### DLT Integration Mapping

**Database Table**: `app_opportunities`

**Field Mappings**:
```python
{
    'trust_level': 'trust_level.value',
    'trust_score': 'overall_trust_score',
    'trust_badge': 'trust_badges[0] or BASIC',
    'activity_score': 'activity_score',
    'confidence_score': 'ai_analysis_confidence',
    'engagement_level': 'engagement_level',
    'trend_velocity': 'trend_velocity',
    'problem_validity': 'problem_validity',
    'discussion_quality': 'discussion_quality',
    'ai_confidence_level': 'ai_confidence_level',
    'trust_validation_timestamp': 'validation_timestamp',
    'trust_validation_method': 'validation_method'
}
```

## Configuration Constants

### Trust Weights (`TrustWeights.DEFAULT_WEIGHTS`)
```python
{
    "subreddit_activity": 0.25,      # 25%
    "post_engagement": 0.20,        # 20%
    "trend_velocity": 0.15,         # 15%
    "problem_validity": 0.15,       # 15%
    "discussion_quality": 0.15,     # 15%
    "ai_confidence": 0.10           # 10%
}
```

### Score Thresholds
```python
TRUST_THRESHOLDS = {
    "very_high": 85.0,
    "high": 70.0,
    "medium": 50.0,
    "low": 0.0
}

DEFAULT_ACTIVITY_THRESHOLD = 25.0
```

### Badge Thresholds
```python
ACTIVITY_BADGE_THRESHOLDS = {
    "highly_active": 80.0,
    "active": 60.0
}

ENGAGEMENT_BADGE_THRESHOLDS = {
    "high": 70.0,
    "good": 40.0
}

TREND_BADGE_THRESHOLDS = {
    "trending": 80.0,
    "emerging": 50.0
}

AI_CONFIDENCE_THRESHOLDS = {
    "high": 70.0,
    "medium": 50.0
}
```

## Pipeline Integration Pattern

### Current Flow in `dlt_trust_pipeline.py`

```python
def apply_trust_validation(posts):
    """Step 3: Apply comprehensive trust layer validation"""

    # 1. Initialize trust validator
    trust_validator = TrustLayerValidator(activity_threshold=DLT_MIN_ACTIVITY_SCORE)

    # 2. Process each post
    for post in posts:
        # Prepare submission data
        submission_data = {...}
        ai_analysis = {...}

        # Apply trust validation
        trust_indicators = trust_validator.validate_opportunity_trust(
            submission_data=submission_data,
            ai_analysis=ai_analysis
        )

        # Merge trust indicators with post data
        validated_post = post.copy()
        validated_post.update({
            'trust_level': trust_indicators.trust_level,
            'trust_score': trust_indicators.overall_trust_score,
            'trust_badge': trust_indicators.trust_badges[0] if trust_indicators.trust_badges else 'BASIC',
            # ... additional field mappings
        })
```

### Expected Extraction Interface

```python
# pipeline-v2/trust/validator.py
class TrustValidator:
    def __init__(self, activity_threshold: float = 25.0):
        ...

    def validate_opportunity_trust(
        self,
        submission_data: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> TrustIndicators:
        ...

    def validate_batch_opportunities(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[TrustIndicators]:
        ...
```

## Error Handling Patterns

### Network Errors
- Reddit API failures → 0.0 activity score
- Service initialization errors → Basic trust indicators
- Timeout handling with gracefule degradation

### Data Validation Errors
- Missing required fields → Default values (0 for numeric, "" for text)
- Invalid numeric values → Clamped to valid ranges
- Malformed timestamps → Current time fallback

### Constraint Violations
- Quality constraints failed → Apply confidence penalties
- Activity constraints failed → Mark as failed constraint
- Missing AI analysis → Zero scores for AI-dependent components

## Performance Characteristics

### Processing Time
- **Single validation**: < 5 seconds (network-dependent)
- **In-memory operations**: < 100ms
- **Batch validation**: Linear scaling with progress logging

### Memory Usage
- **Service initialization**: Minimal overhead
- **Validation history**: Maintained in memory
- **Large AI analysis**: Handled efficiently without leaks

### Concurrency Safety
- Thread-safe validation processing
- Safe history updates
- Consistent results under concurrent load

## Migration Strategy

### Phase 1: Characterization (Current)
- ✅ Document existing behavior
- ✅ Create comprehensive test suite
- ✅ Define interface specification

### Phase 2: Extraction
- Extract core algorithms to `pipeline-v2/trust/`
- Maintain backward compatibility
- Implement clean service interface

### Phase 3: Integration
- Update `dlt_trust_pipeline.py` to use new interface
- Preserve existing data flow
- Add performance monitoring

### Phase 4: Validation
- Run characterization tests against extraction
- Verify behavioral equivalence
- Performance benchmarking

## Dependencies and Imports

### Current Dependencies
```python
# Core imports
from core.trust_layer import TrustLayerValidator
from core.trust.config import TrustWeights, TrustValidationConfig
from core.trust.models import TrustIndicators, TrustValidationRequest

# External dependencies
import praw  # Reddit API
import time  # Timestamp calculations
import logging  # Error handling
```

### Target Imports (After Extraction)
```python
# Pipeline-v2 imports
from pipeline_v2.trust.validator import TrustValidator
from pipeline_v2.trust.scoring import TrustScoringEngine
from pipeline_v2.trust.badges import BadgeSystem
from pipeline_v2.trust.constraints import ValidationConstraints

# Direct core imports (NEW STRATEGY)
from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
from core.agents.profiler.enhanced_profiler import EnhancedLLMProfiler

# Wrapper imports (NEW STRATEGY)
from pipeline_v2.analysis import OpportunityAnalyzer
```

## Testing Strategy

### Characterization Tests
- ✅ **Initialization tests**: Configuration and setup
- ✅ **Scoring algorithm tests**: All 6 dimensions
- ✅ **Badge assignment tests**: Threshold and logic verification
- ✅ **Integration tests**: Pipeline data flow
- ✅ **Edge case tests**: Error handling and constraints
- ✅ **Performance tests**: Timing and memory characteristics

### Validation Tests (Post-Extraction)
- Behavioral equivalence verification
- Performance regression testing
- Integration compatibility testing

---

**Status**: Characterization Complete
**Next Phase**: Trust Validation Extraction
**Target File**: `pipeline-v2/trust/validator.py`