# Pipeline v3 API Documentation

<div align="center">

**External Integrations and API Interfaces**

*Documentation for third-party service integrations and external APIs*

</div>

## 📋 Table of Contents

- [🔗 Reddit API Integration](#-reddit-api-integration)
- [🤖 OpenRouter LLM API](#-openrouter-llm-api)
- [🗄️ Supabase Database API](#️-supabase-database-api)
- [📊 Internal Pipeline API](#-internal-pipeline-api)

---

## 🔗 Reddit API Integration

### Overview
RedditHarbor Pipeline v3 uses the Reddit API via the PRAW (Python Reddit API Wrapper) library for data extraction.

### Authentication
```python
import praw

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    read_only=True
)
```

### Rate Limits
- **Requests per minute**: 60
- **Burst requests**: 300 per 10 minutes
- **Automatic handling**: Built-in rate limiting in extract layer

### API Endpoints Used
- `/r/{subreddit}/hot` - Hot posts extraction
- `/r/{subreddit}/top` - Top posts extraction
- `/comments/{post_id}` - Comment thread extraction
- `/api/v1/me` - Authentication verification

### Error Handling
- `401 Unauthorized` - Invalid credentials
- `429 Too Many Requests` - Rate limit exceeded
- `503 Service Unavailable` - Reddit API downtime

*For detailed Reddit API documentation, visit: https://www.reddit.com/dev/api/*

---

## 🤖 OpenRouter LLM API

### Overview
OpenRouter API provides access to multiple language models for content analysis and opportunity detection.

### Authentication
```python
import openai

client = openai.AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)
```

### Supported Models
- `anthropic/claude-3.5-sonnet` (default)
- `openai/gpt-4o`
- `google/gemini-pro`
- `meta-llama/llama-3.1-405b-instruct`

### Rate Limits
- **Requests per minute**: 100
- **Tokens per minute**: 150,000
- **Automatic handling**: Built-in rate limiting

### Usage Example
```python
response = await client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    max_tokens=1000
)
```

*For detailed OpenRouter API documentation, visit: https://openrouter.ai/docs*

---

## 🗄️ Supabase Database API

### Overview
Supabase provides PostgreSQL database services with real-time capabilities and REST API access.

### Connection
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    echo=False
)
```

### REST API Endpoints
- `GET /rest/v1/app_opportunities` - Query opportunities
- `POST /rest/v1/app_opportunities` - Create opportunity
- `PATCH /rest/v1/app_opportunities/{id}` - Update opportunity
- `DELETE /rest/v1/app_opportunities/{id}` - Delete opportunity

### Authentication
- **Anonymous Key**: For read operations
- **Service Role Key**: For admin operations
- **Row Level Security**: Enforced for data access control

### Rate Limits
- **API Requests**: 100,000 per month (free tier)
- **Bandwidth**: 2GB per month (free tier)
- **Connections**: 60 concurrent connections

*For detailed Supabase API documentation, visit: https://supabase.com/docs/reference*

---

## 📊 Internal Pipeline API

### Overview
Pipeline v3 exposes internal APIs for data processing and pipeline management.

### Python API

#### Main Pipeline Interface
```python
from pipeline_v3.main import PipelineV3

pipeline = PipelineV3()
result = await pipeline.run_pipeline(
    subreddit="productivity",
    limit=100,
    enable_llm_analysis=True
)
```

#### Repository Interface
```python
from pipeline_v3.load.repositories import OpportunityRepository

repo = OpportunityRepository(db_session)
opportunities = await repo.find_opportunities_by_score(
    min_score=70.0,
    limit=50
)
```

#### Configuration Interface
```python
from pipeline_v3.config import get_config

config = get_config()
print(f"Batch size: {config.batch_size}")
print(f"Log level: {config.log_level}")
```

### CLI API
```bash
# Run pipeline
python -m pipeline_v3.main --subreddit productivity --limit 100

# Check database
python -m pipeline_v3.scripts.check_schema

# View opportunities
python -m pipeline_v3.scripts.view_opportunities --limit 5
```

### Error Response Format
```python
{
    "success": false,
    "error": "Error description",
    "error_type": "RedditAPIError | ValidationError | DatabaseError",
    "timestamp": "2025-12-01T10:00:00Z",
    "context": {
        "subreddit": "productivity",
        "phase": "extract"
    }
}
```

### Success Response Format
```python
{
    "success": true,
    "total_posts_extracted": 100,
    "posts_passed_quality": 75,
    "opportunities_created": 50,
    "opportunities_saved": 48,
    "duration_seconds": 120.5
}
```

---

## 🔍 API Monitoring

### Health Checks
```bash
# Reddit API health
python -m pipeline_v3.scripts.check_reddit_health

# Database health
python -m pipeline_v3.scripts.check_database_health

# LLM API health
python -m pipeline_v3.scripts.check_llm_health
```

### Monitoring Metrics
- **API Response Times**: Average latency per service
- **Success Rates**: Percentage of successful API calls
- **Rate Limit Utilization**: Current vs. allowed request rates
- **Error Rates**: Frequency of API errors by type

### Log Locations
- **API Calls**: `logs/api_calls.log`
- **API Errors**: `logs/api_errors.log`
- **Performance**: `logs/performance.log`

---

## 🛠️ Troubleshooting

### Common API Issues

#### Reddit API Authentication
```bash
# Test Reddit API connection
python -c "
import praw
reddit = praw.Reddit(
    client_id='YOUR_ID',
    client_secret='YOUR_SECRET',
    user_agent='RedditHarbor/1.0'
)
print('Reddit API OK' if reddit.read_only else 'Auth failed')
"
```

#### Database Connection
```bash
# Test database connection
python -c "
import sqlalchemy
engine = sqlalchemy.create_engine('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
with engine.connect() as conn:
    print('Database connection successful')
"
```

#### OpenRouter API
```bash
# Test OpenRouter API
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": "test"}]}'
```

---

<div align="center">

**🔗 API Documentation Complete!**

**For integration examples, see the [Implementation Guide](../implementation/elt-pipeline-implementation.md)**

</div>