# API Endpoint Documentation

<div align="center">

**Pipeline v3 Internal and External API Interfaces**

*Complete documentation of all API endpoints, request/response formats, and error handling*

</div>

## 📋 Table of Contents

- [🔗 API Overview](#-api-overview)
- [🏗️ Internal Pipeline APIs](#️-internal-pipeline-apis)
- [🌐 External Service Integrations](#-external-service-integrations)
- [📝 Request/Response Formats](#-requestresponse-formats)
- [⚠️ Error Codes and Handling](#️-error-codes-and-handling)
- [🔐 Authentication and Security](#-authentication-and-security)
- [📊 API Rate Limiting](#-api-rate-limiting)
- [🧪 API Testing and Examples](#-api-testing-and-examples)

---

## 🔗 API Overview

### Architecture Summary

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Client]
        B[Mobile Client]
        C[CLI Tool]
        D[External API Consumer]
    end

    subgraph "API Gateway"
        E[Authentication]
        F[Rate Limiting]
        G[Request Validation]
        H[Response Formatting]
    end

    subgraph "Pipeline APIs"
        I[Pipeline Management API]
        J[Data Processing API]
        K[Results Query API]
        L[Health Check API]
        M[Configuration API]
    end

    subgraph "External Services"
        N[Reddit API]
        O[OpenRouter LLM API]
        P[Supabase API]
    end

    A --> E
    B --> E
    C --> E
    D --> E

    E --> F
    F --> G
    G --> H

    H --> I
    H --> J
    H --> K
    H --> L
    H --> M

    I --> N
    I --> O
    I --> P
```

### API Categories

| Category | Purpose | Authentication | Rate Limit |
|----------|---------|----------------|-------------|
| **Management** | Pipeline control and configuration | Required | 100 req/hr |
| **Processing** | Data processing and analysis | Required | 1000 req/hr |
| **Querying** | Results retrieval and search | Optional | 5000 req/hr |
| **Health** | System health and monitoring | None | Unlimited |
| **External** | Third-party service integration | Required | Service-specific |

---

## 🏗️ Internal Pipeline APIs

### 1. Pipeline Management API

#### Start Pipeline

```http
POST /api/v1/pipeline/start
Content-Type: application/json
Authorization: Bearer <token>

{
  "config": {
    "subreddits": ["productivity", "tools"],
    "limit": 50,
    "sort_by": "hot",
    "time_filter": "week",
    "min_score": 10,
    "enable_llm_analysis": true,
    "batch_size": 10
  },
  "options": {
    "dry_run": false,
    "validate_quality": true,
    "enable_logging": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "pipeline_id": "pipeline_123456",
  "status": "started",
  "estimated_duration": "15-30 minutes",
  "message": "Pipeline started successfully",
  "config": {
    "subreddits": ["productivity", "tools"],
    "limit": 50
  }
}
```

#### Get Pipeline Status

```http
GET /api/v1/pipeline/{pipeline_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "pipeline_id": "pipeline_123456",
  "status": "processing",
  "progress": {
    "current_stage": "transform",
    "stage_progress": 65,
    "overall_progress": 45,
    "estimated_remaining": "8 minutes"
  },
  "metrics": {
    "extracted_submissions": 50,
    "analyzed_submissions": 32,
    "stored_results": 28,
    "errors": 0,
    "start_time": "2025-12-01T10:30:00Z",
    "current_time": "2025-12-01T10:35:30Z"
  },
  "stages": {
    "extract": {
      "status": "completed",
      "duration": "2m 15s",
      "items_processed": 50
    },
    "transform": {
      "status": "processing",
      "duration": "3m 30s",
      "items_processed": 32,
      "items_remaining": 18
    },
    "load": {
      "status": "pending",
      "duration": null,
      "items_processed": 0
    }
  }
}
```

#### Stop Pipeline

```http
POST /api/v1/pipeline/{pipeline_id}/stop
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Pipeline stop initiated",
  "pipeline_id": "pipeline_123456",
  "status": "stopping",
  "graceful_shutdown": true
}
```

### 2. Data Processing API

#### Process Single Submission

```http
POST /api/v1/process/submission
Content-Type: application/json
Authorization: Bearer <token>

{
  "submission": {
    "id": "abc123",
    "title": "Need help with time management",
    "text": "I struggle to manage my time effectively...",
    "author": "user123",
    "subreddit": "productivity",
    "upvotes": 25,
    "comments_count": 12
  },
  "options": {
    "enable_quality_validation": true,
    "min_confidence": 0.7,
    "skip_existing": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "submission_id": "abc123",
    "analysis_id": "analysis_789",
    "app_idea": {
      "title": "Time Management Assistant",
      "app_concept": "AI-powered time management and productivity app",
      "problem_statement": "People struggle with effective time management",
      "target_audience": "Busy professionals and students",
      "core_functions": ["Smart scheduling", "Time tracking", "Productivity insights"]
    },
    "market_metrics": {
      "market_demand": 78.5,
      "pain_intensity": 82.3,
      "monetization_potential": 71.2,
      "competition_level": 55.8,
      "technical_feasibility": 85.1,
      "final_score": 76.5
    },
    "confidence_score": 0.87,
    "trust_level": "HIGH",
    "processing_time": "2.3s"
  }
}
```

#### Batch Process Submissions

```http
POST /api/v1/process/batch
Content-Type: application/json
Authorization: Bearer <token>

{
  "submissions": [
    {
      "id": "abc123",
      "title": "Need help with time management",
      "text": "I struggle to manage my time..."
    },
    {
      "id": "def456",
      "title": "Looking for task management app",
      "text": "Need a better way to track tasks..."
    }
  ],
  "options": {
    "batch_size": 5,
    "parallel_processing": true,
    "continue_on_error": true,
    "enable_quality_validation": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "batch_id": "batch_456789",
  "total_submissions": 2,
  "results": [
    {
      "submission_id": "abc123",
      "success": true,
      "analysis_id": "analysis_789",
      "processing_time": "2.1s"
    },
    {
      "submission_id": "def456",
      "success": true,
      "analysis_id": "analysis_790",
      "processing_time": "1.8s"
    }
  ],
  "summary": {
    "successful": 2,
    "failed": 0,
    "total_processing_time": "3.9s",
    "average_processing_time": "1.95s"
  }
}
```

### 3. Results Query API

#### Get Analysis Results

```http
GET /api/v1/results/opportunities?page=1&limit=20&min_score=50&trust_level=HIGH
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "opportunities": [
      {
        "id": "analysis_789",
        "app_title": "Time Management Assistant",
        "app_concept": "AI-powered time management app",
        "problem_statement": "People struggle with time management",
        "target_audience": "Busy professionals",
        "core_functions": ["Smart scheduling", "Time tracking"],
        "final_score": 76.5,
        "confidence_score": 0.87,
        "trust_level": "HIGH",
        "submission_id": "abc123",
        "subreddit": "productivity",
        "created_at": "2025-12-01T10:35:15Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_count": 156,
      "total_pages": 8,
      "has_next": true,
      "has_previous": false
    }
  },
  "filters_applied": {
    "min_score": 50,
    "trust_level": "HIGH"
  }
}
```

#### Search Opportunities

```http
POST /api/v1/results/search
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "time management productivity",
  "filters": {
    "subreddits": ["productivity", "tools"],
    "score_range": [60, 100],
    "trust_levels": ["HIGH", "MEDIUM"],
    "date_range": {
      "start": "2025-11-01",
      "end": "2025-12-01"
    }
  },
  "sort": {
    "field": "final_score",
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "limit": 25
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "opportunities": [...],
    "search_metadata": {
      "query": "time management productivity",
      "total_matches": 23,
      "search_time": "0.05s",
      "filters_applied": ["subreddits", "score_range", "trust_levels", "date_range"]
    },
    "pagination": {
      "page": 1,
      "limit": 25,
      "total_count": 23,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  }
}
```

#### Get Similar Opportunities

```http
POST /api/v1/results/similar
Content-Type: application/json
Authorization: Bearer <token>

{
  "reference_id": "analysis_789",
  "similarity_threshold": 0.8,
  "limit": 10,
  "include_details": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "reference_opportunity": {
      "id": "analysis_789",
      "app_title": "Time Management Assistant",
      "final_score": 76.5
    },
    "similar_opportunities": [
      {
        "id": "analysis_456",
        "app_title": "Productivity Planner",
        "similarity_score": 0.92,
        "final_score": 71.3,
        "trust_level": "MEDIUM",
        "shared_aspects": ["time management", "productivity", "scheduling"],
        "differences": ["focus on planning vs. automation"]
      }
    ],
    "summary": {
      "total_found": 5,
      "average_similarity": 0.85,
      "search_time": "0.12s"
    }
  }
}
```

### 4. Health Check API

#### System Health

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-01T10:40:00Z",
  "version": "3.0.0",
  "uptime": "2d 14h 32m",
  "components": {
    "database": {
      "status": "healthy",
      "response_time": "5ms",
      "connection_pool": {
        "active": 3,
        "idle": 17,
        "total": 20
      }
    },
    "reddit_api": {
      "status": "healthy",
      "response_time": "145ms",
      "rate_limit_remaining": 45,
      "last_request": "2025-12-01T10:39:45Z"
    },
    "llm_service": {
      "status": "healthy",
      "response_time": "2.3s",
      "model": "claude-3.5-sonnet",
      "queue_size": 0
    },
    "cache": {
      "status": "healthy",
      "hit_rate": "87.3%",
      "memory_usage": "245MB"
    }
  },
  "metrics": {
    "requests_per_minute": 12,
    "error_rate": "0.1%",
    "memory_usage": "512MB",
    "cpu_usage": "23.5%"
  }
}
```

#### Detailed Component Health

```http
GET /api/v1/health/components/{component_name}
```

**Response for `reddit_api`:**
```json
{
  "component": "reddit_api",
  "status": "healthy",
  "timestamp": "2025-12-01T10:40:00Z",
  "configuration": {
    "rate_limit_rpm": 60,
    "burst_allowance": 5,
    "timeout": "30s"
  },
  "current_state": {
    "requests_remaining": 45,
    "reset_time": "2025-12-01T10:41:00Z",
    "last_successful_request": "2025-12-01T10:39:45Z",
    "consecutive_failures": 0
  },
  "performance": {
    "average_response_time": "145ms",
    "p95_response_time": "280ms",
    "success_rate": "99.8%",
    "requests_today": 1234
  },
  "recent_errors": []
}
```

---

## 🌐 External Service Integrations

### 1. Reddit API Integration

#### Submission Extraction

**Internal Request:**
```json
{
  "service": "reddit_api",
  "method": "extract_submissions",
  "params": {
    "subreddit": "productivity",
    "limit": 50,
    "sort": "hot",
    "time_filter": "week",
    "min_score": 10
  }
}
```

**External API Call:**
```http
GET https://oauth.reddit.com/r/productivity/hot.json?limit=50&t=week
Authorization: Bearer <reddit_token>
User-Agent: RedditHarbor Pipeline v3/1.0
```

**Response Processing:**
```json
{
  "success": true,
  "data": [
    {
      "id": "abc123",
      "title": "Need help with time management",
      "selftext": "I struggle to manage my time effectively...",
      "author": "user123",
      "score": 25,
      "num_comments": 12,
      "created_utc": 1701427200.0,
      "permalink": "/r/productivity/comments/abc123/need_help_with_time_management/",
      "subreddit": "productivity"
    }
  ],
  "metadata": {
    "extracted_count": 47,
    "filtered_count": 3,
    "api_calls_made": 5,
    "rate_limit_remaining": 55
  }
}
```

### 2. OpenRouter LLM Integration

#### Analysis Request

**Internal Request:**
```json
{
  "service": "openrouter",
  "method": "analyze_submission",
  "params": {
    "model": "claude-3.5-sonnet",
    "submission": {
      "title": "Need help with time management",
      "text": "I struggle to manage my time effectively...",
      "subreddit": "productivity"
    },
    "response_format": {
      "type": "json_schema",
      "schema": "AnalysisResult"
    },
    "options": {
      "temperature": 0.3,
      "max_tokens": 1000
    }
  }
}
```

**External API Call:**
```http
POST https://openrouter.ai/api/v1/chat/completions
Authorization: Bearer <openrouter_api_key>
Content-Type: application/json

{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert app analyst..."
    },
    {
      "role": "user",
      "content": "Analyze this Reddit post for app opportunities..."
    }
  ],
  "temperature": 0.3,
  "max_tokens": 1000,
  "response_format": {
    "type": "json_object"
  }
}
```

**Response Processing:**
```json
{
  "success": true,
  "data": {
    "app_idea": {
      "title": "Time Management Assistant",
      "app_concept": "AI-powered time management app...",
      "problem_statement": "People struggle with time management...",
      "target_audience": "Busy professionals and students...",
      "core_functions": ["Smart scheduling", "Time tracking", "Productivity insights"]
    },
    "market_metrics": {
      "market_demand": 78.5,
      "pain_intensity": 82.3,
      "monetization_potential": 71.2,
      "competition_level": 55.8,
      "technical_feasibility": 85.1
    },
    "final_score": 76.5,
    "confidence_score": 0.87
  },
  "metadata": {
    "model_used": "claude-3.5-sonnet",
    "tokens_used": 847,
    "processing_time": "2.3s",
    "cost": 0.00254
  }
}
```

### 3. Supabase Integration

#### Data Storage

**Internal Request:**
```json
{
  "service": "supabase",
  "method": "store_analysis",
  "params": {
    "table": "opportunities",
    "data": {
      "submission_id": "abc123",
      "app_title": "Time Management Assistant",
      "app_concept": "AI-powered time management app...",
      "final_score": 76.5,
      "confidence_score": 0.87,
      "trust_level": "HIGH",
      "embedding": [0.1, 0.2, 0.3, ...]
    }
  }
}
```

**External API Call:**
```http
POST https://your-project.supabase.co/rest/v1/opportunities
Authorization: Bearer <supabase_anon_key>
Content-Type: application/json
Prefer: return=representation

{
  "submission_id": "abc123",
  "app_title": "Time Management Assistant",
  "app_concept": "AI-powered time management app...",
  "final_score": 76.5,
  "confidence_score": 0.87,
  "trust_level": "HIGH",
  "embedding": [0.1, 0.2, 0.3, ...]
}
```

**Response Processing:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "submission_id": "abc123",
    "app_title": "Time Management Assistant",
    "created_at": "2025-12-01T10:35:15.123Z"
  },
  "metadata": {
    "operation": "insert",
    "rows_affected": 1,
    "processing_time": "45ms"
  }
}
```

---

## 📝 Request/Response Formats

### Standard Response Format

All API responses follow a consistent format:

```json
{
  "success": boolean,
  "data": object | array | null,
  "message": string | null,
  "errors": array | null,
  "metadata": object | null,
  "timestamp": "ISO 8601 datetime"
}
```

### Pagination Format

```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_count": 156,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false,
    "next_page_url": "/api/v1/results/opportunities?page=2&limit=20",
    "previous_page_url": null
  }
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "limit",
        "message": "limit must be between 1 and 100",
        "value": 150
      }
    ],
    "request_id": "req_123456",
    "timestamp": "2025-12-01T10:40:00Z"
  }
}
```

### Bulk Operation Format

```json
{
  "success": true,
  "bulk_operation": {
    "operation_id": "bulk_789",
    "total_items": 50,
    "successful_items": 47,
    "failed_items": 3,
    "processing_time": "45.2s",
    "results": [
      {
        "item_id": "item_1",
        "success": true,
        "result": { ... }
      },
      {
        "item_id": "item_2",
        "success": false,
        "error": {
          "code": "VALIDATION_ERROR",
          "message": "Invalid data format"
        }
      }
    ]
  }
}
```

---

## ⚠️ Error Codes and Handling

### HTTP Status Codes

| Status Code | Category | Meaning |
|-------------|----------|---------|
| 200 | Success | Request completed successfully |
| 201 | Success | Resource created successfully |
| 202 | Success | Request accepted for processing |
| 400 | Client Error | Bad request - validation failed |
| 401 | Client Error | Authentication required |
| 403 | Client Error | Access forbidden |
| 404 | Client Error | Resource not found |
| 409 | Client Error | Resource conflict |
| 422 | Client Error | Unprocessable entity |
| 429 | Client Error | Rate limit exceeded |
| 500 | Server Error | Internal server error |
| 502 | Server Error | Bad gateway |
| 503 | Server Error | Service unavailable |
| 504 | Server Error | Gateway timeout |

### Application Error Codes

#### Validation Errors (400/422)

| Code | Description | Fields |
|------|-------------|--------|
| `MISSING_REQUIRED_FIELD` | Required field is missing | field_name |
| `INVALID_FIELD_FORMAT` | Field format is invalid | field_name, expected_format |
| `FIELD_OUT_OF_RANGE` | Field value is out of allowed range | field_name, min_value, max_value |
| `INVALID_ENUM_VALUE` | Invalid enum value provided | field_name, allowed_values |
| `DUPLICATE_RESOURCE` | Resource already exists | resource_type, identifier |

#### Authentication Errors (401/403)

| Code | Description | Details |
|------|-------------|---------|
| `AUTHENTICATION_REQUIRED` | API token required | auth_type |
| `INVALID_TOKEN` | Provided token is invalid | token_type |
| `EXPIRED_TOKEN` | Token has expired | expires_at |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions | required_permission |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded | reset_time, limit |

#### Processing Errors (500/503)

| Code | Description | Details |
|------|-------------|---------|
| `EXTERNAL_SERVICE_ERROR` | Third-party service error | service_name, error_code |
| `DATABASE_ERROR` | Database operation failed | operation, error_details |
| `PROCESSING_TIMEOUT` | Operation timed out | timeout_duration |
| `RESOURCE_EXHAUSTED` | System resources exhausted | resource_type |
| `PIPELINE_ERROR` | Pipeline processing failed | stage, error_details |

#### Business Logic Errors (409/422)

| Code | Description | Details |
|------|-------------|---------|
| `INVALID_PIPELINE_STATE` | Pipeline not in expected state | current_state, required_state |
| `INSUFFICIENT_DATA_QUALITY` | Data doesn't meet quality standards | quality_score, threshold |
| `DUPLICATE_ANALYSIS` | Analysis already exists | submission_id, analysis_id |
| `CIRCUIT_BREAKER_OPEN` | Service circuit breaker is open | service_name, retry_after |

### Error Handling Patterns

#### Client-Side Error Handling

```javascript
// Example JavaScript error handling
async function callAPI(endpoint, data) {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (!result.success) {
      handleAPIError(result.error);
      return null;
    }

    return result.data;

  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

function handleAPIError(error) {
  switch (error.code) {
    case 'AUTHENTICATION_REQUIRED':
      redirectToLogin();
      break;
    case 'RATE_LIMIT_EXCEEDED':
      showRateLimitWarning(error.reset_time);
      break;
    case 'VALIDATION_ERROR':
      showValidationErrors(error.details);
      break;
    default:
      showGenericError(error.message);
  }
}
```

#### Retry Logic

```python
# Example Python retry logic
import asyncio
import time
from typing import Callable, Any

class APIRetryHandler:
    def __init__(self, max_retries=3, base_delay=1.0, backoff_factor=2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor

    async def retry_call(self, func: Callable, *args, **kwargs) -> Any:
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except Exception as error:
                last_error = error

                if not self._should_retry(error, attempt):
                    raise error

                delay = self.base_delay * (self.backoff_factor ** attempt)
                await asyncio.sleep(delay)

        raise last_error

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False

        # Retry on network and timeout errors
        retryable_errors = [
            'timeout', 'connection', 'rate_limit', 'service_unavailable'
        ]

        error_str = str(error).lower()
        return any(retry_error in error_str for retry_error in retryable_errors)
```

---

## 🔐 Authentication and Security

### API Token Authentication

#### Token Generation

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password",
  "grant_type": "password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_token": "def50200...",
    "scope": "read write process"
  }
}
```

#### Token Refresh

```http
POST /api/v1/auth/refresh
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "refresh_token": "def50200..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600
  }
}
```

#### Token Usage

```http
GET /api/v1/results/opportunities
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key Authentication

For service-to-service authentication:

```http
GET /api/v1/health
X-API-Key: sk_live_1234567890abcdef
```

### Security Headers

All API responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

---

## 📊 API Rate Limiting

### Rate Limit Tiers

| Tier | Requests/Hour | Burst | Features |
|------|---------------|-------|----------|
| **Free** | 100 | 10 | Basic endpoints |
| **Professional** | 1,000 | 50 | All endpoints, batch processing |
| **Enterprise** | 10,000 | 200 | Priority support, custom limits |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1701427200
X-RateLimit-Retry-After: 45
```

### Rate Limit Response (429)

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_time": "2025-12-01T11:00:00Z",
      "retry_after": 1200
    }
  }
}
```

### Client-Side Rate Limiting

```javascript
class RateLimiter {
  constructor(maxRequests, timeWindowMs) {
    this.maxRequests = maxRequests;
    this.timeWindowMs = timeWindowMs;
    this.requests = [];
  }

  async makeRequest(apiCall) {
    // Clean old requests
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.timeWindowMs);

    // Check rate limit
    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = Math.min(...this.requests);
      const waitTime = this.timeWindowMs - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    // Make request
    this.requests.push(now);
    return apiCall();
  }
}

// Usage
const rateLimiter = new RateLimiter(100, 3600000); // 100 requests per hour

async function getOpportunities() {
  return rateLimiter.makeRequest(() =>
    fetch('/api/v1/results/opportunities', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
  );
}
```

---

## 🧪 API Testing and Examples

### Using curl

#### Start Pipeline

```bash
curl -X POST "https://api.redditharbor.com/v1/pipeline/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "config": {
      "subreddits": ["productivity"],
      "limit": 25,
      "enable_llm_analysis": true
    }
  }'
```

#### Get Results

```bash
curl -X GET "https://api.redditharbor.com/v1/results/opportunities?page=1&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python (requests)

```python
import requests
import json

class PipelineAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def start_pipeline(self, config):
        response = requests.post(
            f'{self.base_url}/v1/pipeline/start',
            headers=self.headers,
            json={'config': config}
        )
        return response.json()

    def get_opportunities(self, page=1, limit=20, filters=None):
        params = {'page': page, 'limit': limit}
        if filters:
            params.update(filters)

        response = requests.get(
            f'{self.base_url}/v1/results/opportunities',
            headers=self.headers,
            params=params
        )
        return response.json()

    def process_submission(self, submission_data):
        response = requests.post(
            f'{self.base_url}/v1/process/submission',
            headers=self.headers,
            json={'submission': submission_data}
        )
        return response.json()

# Usage
api = PipelineAPI('https://api.redditharbor.com', 'YOUR_TOKEN')

# Start pipeline
result = api.start_pipeline({
    'subreddits': ['productivity', 'tools'],
    'limit': 50,
    'enable_llm_analysis': True
})

print(f"Pipeline started with ID: {result['pipeline_id']}")

# Get results
opportunities = api.get_opportunities(
    page=1,
    limit=10,
    filters={'min_score': 70, 'trust_level': 'HIGH'}
)

print(f"Found {len(opportunities['data']['opportunities'])} high-quality opportunities")
```

### Using JavaScript (fetch)

```javascript
class PipelineAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    }

    async startPipeline(config) {
        const response = await fetch(`${this.baseUrl}/v1/pipeline/start`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ config })
        });
        return response.json();
    }

    async getOpportunities(options = {}) {
        const params = new URLSearchParams(options);
        const response = await fetch(
            `${this.baseUrl}/v1/results/opportunities?${params}`,
            { headers: this.headers }
        );
        return response.json();
    }

    async processSubmission(submissionData) {
        const response = await fetch(`${this.baseUrl}/v1/process/submission`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ submission: submissionData })
        });
        return response.json();
    }
}

// Usage
const api = new PipelineAPI('https://api.redditharbor.com', 'YOUR_TOKEN');

// Start pipeline
const pipelineResult = await api.startPipeline({
    subreddits: ['productivity'],
    limit: 25,
    enable_llm_analysis: true
});

console.log(`Pipeline started: ${pipelineResult.pipeline_id}`);

// Get results
const opportunities = await api.getOpportunities({
    page: 1,
    limit: 10,
    min_score: 60
});

console.log(`Found ${opportunities.data.opportunities.length} opportunities`);
```

---

<div align="center">

**🔗 Complete API Documentation for Production Integration**

*These endpoints provide comprehensive access to Pipeline v3 functionality for building applications and services*

</div>