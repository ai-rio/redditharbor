# AI Enrichment Services

Unified service wrappers for AI analysis components in the RedditHarbor pipeline.

## Overview

This module provides standardized service interfaces for enriching Reddit submissions with AI-powered analysis. Each service wraps an underlying AI component and integrates with the deduplication system to prevent redundant API calls and preserve cost savings.

All services extend `BaseEnrichmentService`, providing:
- Consistent `enrich()` interface for all AI analyses
- Built-in statistics tracking (analyzed, skipped, copied, errors)
- Input validation with standardized error handling
- Deduplication integration where applicable

## Modules

| Module | Description |
|--------|-------------|
| `base_service.py` | Abstract base class defining the enrichment service interface with statistics tracking, input validation, and error handling |
| `profiler_service.py` | Wraps `EnhancedLLMProfiler` to generate app profiles (app name, core functions, value proposition) with deduplication support |
| `opportunity_service.py` | Wraps `OpportunityAnalyzerAgent` for 5-dimensional opportunity scoring (market demand, pain intensity, monetization, market gap, technical feasibility) |
| `monetization_service.py` | Wraps `MonetizationAgnoAnalyzer` to analyze willingness-to-pay, revenue potential, and customer segments with deduplication support |
| `trust_service.py` | Wraps `TrustValidationService` for multi-dimensional trust assessment (activity, engagement, community health, problem validity) |
| `market_validation_service.py` | Wraps `MarketDataValidator` to validate opportunities using real market data (competitor pricing, market size, similar launches) |
| `trust_converters.py` | Utility functions to convert numeric trust scores to categorical levels (engagement, problem validity, discussion quality, AI confidence) |
| `activity_validation.py` | Subreddit activity scoring using PRAW with multi-factor weighted scoring (comments, engagement, subscribers, active users) |
| `lead_extractor.py` | Extracts sales leads from Reddit posts using regex and keyword matching (budget signals, competitor mentions, team size, buying intent) |

## Usage Examples

### Basic Service Usage

```python
from supabase import create_client
from core.agents.profiler import EnhancedLLMProfiler
from core.deduplication.profiler_skip_logic import ProfilerSkipLogic
from core.enrichment.profiler_service import ProfilerService

# Initialize dependencies
client = create_client(url, key)
profiler = EnhancedLLMProfiler()
skip_logic = ProfilerSkipLogic(client)

# Create service
service = ProfilerService(profiler, skip_logic, config={
    "enable_deduplication": True
})

# Enrich a submission
submission = {
    "submission_id": "abc123",
    "title": "Need better project management tool",
    "text": "Our team struggles with coordination across timezones",
    "subreddit": "startups"
}
profile = service.enrich(submission)

# Check statistics
stats = service.get_statistics()
print(f"Analyzed: {stats['analyzed']}, Skipped: {stats['skipped']}")
```

### Opportunity Analysis

```python
from core.agents.interactive.opportunity_analyzer import OpportunityAnalyzerAgent
from core.enrichment.opportunity_service import OpportunityService

analyzer = OpportunityAnalyzerAgent()
service = OpportunityService(analyzer)

submission = {
    "submission_id": "xyz789",
    "title": "Looking for budgeting app",
    "text": "Current apps are too complicated",
    "subreddit": "personalfinance",
    "upvotes": 245,
    "num_comments": 87
}
analysis = service.enrich(submission)
# Returns: final_score, dimension_scores, priority, core_functions
```

### Trust Validation

```python
from core.trust import TrustValidationService, TrustRepositoryFactory
from core.enrichment.trust_service import TrustService

repository = TrustRepositoryFactory.create_repository(client)
validator = TrustValidationService(repository)
service = TrustService(validator)

submission = {
    "id": "test123",
    "title": "Need CRM solution",
    "text": "Evaluating options for our sales team",
    "subreddit": "sales",
    "upvotes": 150,
    "comments_count": 25,
    "created_utc": 1700000000
}
validation = service.enrich(submission)
# Returns: overall_trust_score, trust_level, trust_badges
```

### Trust Score Conversion

```python
from core.enrichment.trust_converters import convert_all_trust_scores

trust_data = {
    "engagement_score": 85.0,
    "problem_validity_score": 70.0,
    "discussion_quality_score": 55.0,
    "ai_confidence_score": 90.0
}
result = convert_all_trust_scores(trust_data)
# Returns: engagement_level='VERY_HIGH', problem_validity='POTENTIAL', etc.
```

### Activity Validation

```python
import praw
from core.enrichment.activity_validation import (
    calculate_activity_score,
    collect_activity_metrics,
    get_active_subreddits
)

reddit = praw.Reddit(client_id=..., client_secret=..., user_agent=...)

# Score a single subreddit
subreddit = reddit.subreddit("python")
score = calculate_activity_score(subreddit, time_filter="day")

# Filter active subreddits from candidates
active = get_active_subreddits(
    reddit,
    candidate_subreddits=["python", "learnprogramming", "technology"],
    time_filter="day",
    min_activity_score=50.0
)
```

### Lead Extraction

```python
from core.enrichment.lead_extractor import LeadExtractor, format_lead_for_slack

extractor = LeadExtractor()

post = {
    "id": "abc123",
    "author": "startup_founder",
    "title": "Switching from Asana - need recommendations",
    "selftext": "Team of 12, budget approved at $200/month",
    "subreddit": "projectmanagement",
    "created_utc": 1705334567
}
lead = extractor.extract_from_reddit_post(post, opportunity_score=85.0)
# Returns: LeadSignals with budget, team_size, buying_intent_stage, urgency_level

slack_message = format_lead_for_slack(lead)
```

## Architecture

```
BaseEnrichmentService (abstract)
    |
    +-- ProfilerService (with deduplication)
    +-- OpportunityService (no deduplication)
    +-- MonetizationService (with deduplication)
    +-- TrustService (no deduplication)
    +-- MarketValidationService (no deduplication, with retry logic)
```

**Deduplication Strategy:**
- `ProfilerService` and `MonetizationService` integrate skip logic to prevent redundant AI calls on semantically similar submissions
- Other services run on all submissions as their analyses are context-dependent or time-sensitive

## Related Modules

- `core/agents/` - Underlying AI agent implementations
- `core/deduplication/` - Skip logic and concept management for cost savings
- `core/trust/` - Trust validation models and repository
- `config/settings.py` - Configuration constants
