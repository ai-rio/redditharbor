# API Endpoints Specification

**Purpose**: Define all REST endpoints for the RedditHarbor unified pipeline, ensuring complete coverage of pipeline functionality with proper request/response models and error handling.

---

## Core Design Principles

### RESTful Design
- Use standard HTTP verbs (GET, POST, PUT, DELETE)
- Resource-based URL structure
- Consistent response format
- Proper HTTP status codes

### RedditHarbor Integration
- All endpoints must integrate with `core.pipeline.orchestrator.OpportunityPipeline`
- Respect existing configuration system
- Maintain PII anonymization settings
- Use established error handling patterns

### Request/Response Standards
- Pydantic models for validation
- Consistent error response format
- Pagination for list endpoints
- Field selection and filtering support

---

## Endpoint Categories

### 1. Pipeline Management Endpoints

#### POST /api/v1/pipeline/run
Execute the complete opportunity discovery pipeline.

**Purpose**: Trigger pipeline execution with configurable parameters.

**Request Model**:
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class PipelineRunRequest(BaseModel):
    """Request model for pipeline execution."""
    source: str = Field(
        default="database",
        description="Data source: 'database', 'reddit', 'file'"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of submissions to process"
    )
    subreddits: Optional[List[str]] = Field(
        default=None,
        description="Specific subreddits to process (null for all)"
    )
    time_range: Optional[dict] = Field(
        default=None,
        description="Time range filter: {start_date, end_date}"
    )
    config: Optional[dict] = Field(
        default=None,
        description="Additional pipeline configuration"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "source": "database",
                "limit": 500,
                "subreddits": ["Entrepreneur", "SideProject"],
                "time_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                },
                "config": {
                    "enable_pii_anonymization": True
                }
            }
        }
    }
```

**Response Model**:
```python
class PipelineRunResponse(BaseModel):
    """Response model for pipeline execution."""
    success: bool = Field(description="Whether pipeline completed successfully")
    pipeline_id: str = Field(description="Unique identifier for this execution")
    stats: dict = Field(description="Execution statistics and metrics")
    summary: dict = Field(description="Results summary")
    warnings: Optional[List[str]] = Field(default=None, description="Any warnings encountered")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "pipeline_id": "pipeline_1737278400_abc123",
                "stats": {
                    "submissions_processed": 500,
                    "opportunities_found": 12,
                    "processing_time_seconds": 245.7,
                    "api_calls_saved": 1200,
                    "cost_savings_usd": 2.40
                },
                "summary": {
                    "total_opportunities": 12,
                    "high_confidence": 8,
                    "medium_confidence": 3,
                    "low_confidence": 1,
                    "categories": {
                        "SaaS": 5,
                        "Content": 3,
                        "Marketplace": 2,
                        "Service": 2
                    }
                }
            }
        }
    }
```

**Implementation**:
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from api.core.auth import verify_api_key
from core.pipeline.orchestrator import OpportunityPipeline
from core.pipeline.config import PipelineConfig
import uuid
import logging

router = APIRouter(prefix="/api/v1", tags=["pipeline"])
logger = logging.getLogger(__name__)

@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute the complete opportunity discovery pipeline.

    This endpoint triggers the full pipeline including:
    - Data fetching from specified source
    - PII anonymization (if enabled)
    - AI enrichment (profiler, opportunity scoring, etc.)
    - Trust and market validation
    - Results storage in Supabase

    **Rate Limit**: 5 requests per minute per API key
    **Timeout**: 10 minutes maximum execution time
    """
    try:
        # Generate unique pipeline ID
        pipeline_id = f"pipeline_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Create pipeline configuration
        config = PipelineConfig(
            data_source=request.source,
            limit=request.limit,
            subreddits=request.subreddits,
            time_range=request.time_range,
            **(request.config or {})
        )

        # Initialize pipeline
        pipeline = OpportunityPipeline(config)

        # Run pipeline (with timeout)
        result = await asyncio.wait_for(
            pipeline.run(subreddits=request.subreddits),
            timeout=600.0  # 10 minutes
        )

        return PipelineRunResponse(
            success=True,
            pipeline_id=pipeline_id,
            stats=result['stats'],
            summary=result['summary'],
            warnings=result.get('warnings')
        )

    except asyncio.TimeoutError:
        logger.error(f"Pipeline {pipeline_id} timed out after 10 minutes")
        raise HTTPException(
            status_code=408,
            detail="Pipeline execution timed out"
        )
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )
```

#### GET /api/v1/pipeline/status/{pipeline_id}
Check the status of a running pipeline.

**Response Model**:
```python
class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status."""
    pipeline_id: str
    status: str  # 'running', 'completed', 'failed', 'cancelled'
    progress: Optional[float] = None  # 0.0 to 1.0
    current_stage: Optional[str] = None
    stats: Optional[dict] = None
    error: Optional[str] = None
    estimated_completion: Optional[str] = None
```

---

### 2. Enrichment Service Endpoints

#### POST /api/v1/profiler/analyze
Analyze a single submission using the AI profiler.

**Purpose**: Get detailed analysis of a submission's potential without running the full pipeline.

**Request Model**:
```python
class ProfilerRequest(BaseModel):
    """Request model for submission profiling."""
    submission_id: str = Field(description="Reddit submission ID")
    submission_title: str = Field(description="Submission title")
    submission_content: str = Field(description="Submission content/text")
    subreddit: str = Field(description="Subreddit name")
    author: Optional[str] = Field(default=None, description="Author username")
    score: Optional[int] = Field(default=None, description="Submission score")
    comment_count: Optional[int] = Field(default=None, description="Number of comments")

    model_config = {
        "json_schema_extra": {
            "example": {
                "submission_id": "1abc123",
                "submission_title": "I built a tool that analyzes Reddit comments for business ideas",
                "submission_content": "After months of research...",
                "subreddit": "Entrepreneur",
                "author": "tech_entrepreneur",
                "score": 1250,
                "comment_count": 89
            }
        }
    }
```

**Response Model**:
```python
class ProfilerResponse(BaseModel):
    """Response model for submission profiling."""
    success: bool
    submission_id: str
    analysis: dict = Field(description="AI analysis results")
    potential_score: float = Field(ge=0.0, le=1.0, description="Overall potential score")
    key_insights: List[str] = Field(description="Key business insights")
    suggested_categories: List[str] = Field(description="Potential business categories")
    confidence_level: str = Field(description="Analysis confidence: high/medium/low")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "submission_id": "1abc123",
                "analysis": {
                    "business_model": "SaaS",
                    "target_audience": "Content creators",
                    "market_size": "Medium",
                    "technical_complexity": "Medium",
                    "time_to_mvp": "3-6 months"
                },
                "potential_score": 0.78,
                "key_insights": [
                    "Clear pain point in content analysis",
                    "Existing tools are expensive",
                    "Reddit community shows interest"
                ],
                "suggested_categories": ["SaaS", "Content Tools", "Analytics"],
                "confidence_level": "high"
            }
        }
    }
```

**Implementation**:
```python
@router.post("/profiler/analyze", response_model=ProfilerResponse)
async def analyze_with_profiler(
    request: ProfilerRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze a single submission using the AI profiler.

    This endpoint provides detailed AI analysis of a submission's
    business potential without running the full pipeline.

    **Rate Limit**: 20 requests per minute per API key
    **Processing Time**: Typically 5-15 seconds
    """
    try:
        # Import here to avoid circular imports
        from core.enrichment.profiler_service import ProfilerService

        # Initialize profiler service
        profiler_service = ProfilerService()

        # Prepare submission data
        submission_data = {
            'submission_id': request.submission_id,
            'title': request.submission_title,
            'content': request.submission_content,
            'subreddit': request.subreddit,
            'author': request.author,
            'score': request.score,
            'comment_count': request.comment_count
        }

        # Run analysis
        result = await profiler_service.enrich(submission_data)

        # Extract key information
        analysis = result.get('analysis', {})
        insights = result.get('insights', [])

        return ProfilerResponse(
            success=True,
            submission_id=request.submission_id,
            analysis=analysis,
            potential_score=result.get('potential_score', 0.0),
            key_insights=insights,
            suggested_categories=result.get('categories', []),
            confidence_level=result.get('confidence', 'medium')
        )

    except Exception as e:
        logger.error(f"Profiler analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Profiler analysis failed: {str(e)}"
        )
```

#### POST /api/v1/opportunities/score
Score opportunities using the opportunity detection service.

#### POST /api/v1/monetization/analyze
Analyze monetization potential for opportunities.

#### POST /api/v1/trust/validate
Validate trustworthiness of opportunities.

#### POST /api/v1/market/validate
Validate market demand for opportunities.

---

### 3. Data Management Endpoints

#### GET /api/v1/opportunities
Retrieve discovered opportunities with filtering and pagination.

**Query Parameters**:
```python
class OpportunityListParams(BaseModel):
    """Parameters for opportunity listing."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    category: Optional[str] = Field(default=None, description="Filter by category")
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum score")
    date_from: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order: asc/desc")
```

**Response Model**:
```python
class OpportunityListResponse(BaseModel):
    """Response model for opportunity listing."""
    opportunities: List[dict]
    pagination: dict
    filters: dict
    total_count: int
```

---

### 4. Monitoring & Metrics Endpoints

#### GET /api/v1/health
Health check endpoint.

**Response Model**:
```python
class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "2.0.0"
    timestamp: str
    services: dict
    uptime_seconds: float
```

**Implementation**:
```python
@router.get("/health", response_model=HealthResponse, tags=["monitoring"])
async def health_check():
    """
    Health check endpoint.

    Returns the current health status of the API and all dependent services.
    This endpoint does not require authentication.
    """
    try:
        # Check database connection
        db_status = await check_database_health()

        # Check Redis connection
        redis_status = await check_redis_health()

        # Check AI services
        ai_status = await check_ai_services_health()

        overall_status = "healthy"
        if not all([db_status, redis_status, ai_status]):
            overall_status = "degraded"

        return HealthResponse(
            status=overall_status,
            version=settings.APP_VERSION,
            timestamp=datetime.utcnow().isoformat(),
            services={
                "database": "healthy" if db_status else "unhealthy",
                "redis": "healthy" if redis_status else "unhealthy",
                "ai_services": "healthy" if ai_status else "unhealthy"
            },
            uptime_seconds=time.time() - start_time
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.APP_VERSION,
            timestamp=datetime.utcnow().isoformat(),
            services={"error": str(e)},
            uptime_seconds=0.0
        )
```

#### GET /api/v1/metrics
Get application metrics and statistics.

**Response Model**:
```python
class MetricsResponse(BaseModel):
    """Application metrics response."""
    cost_savings_ytd: float
    total_analyzed: int
    api_calls_saved: int
    processing_time_avg: float
    uptime_percentage: float
    pipeline_runs_today: int
    error_rate_24h: float
    active_users: int
    redis_hits: int
    redis_misses: int
```

---

## Error Handling Standards

### Standard Error Response
```python
class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: str
    request_id: str
```

### HTTP Status Code Guidelines
- `200`: Success
- `201`: Resource created
- `400`: Bad request (validation error)
- `401`: Unauthorized (invalid API key)
- `403`: Forbidden (insufficient permissions)
- `404`: Resource not found
- `408`: Request timeout
- `429`: Rate limit exceeded
- `500`: Internal server error
- `503`: Service unavailable

---

## Integration Examples

### Python Client Example
```python
import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Run Pipeline
def run_pipeline():
    url = f"{BASE_URL}/api/v1/pipeline/run"
    data = {
        "source": "database",
        "limit": 100,
        "subreddits": ["Entrepreneur", "SideProject"]
    }

    response = requests.post(url, headers=HEADERS, json=data)
    return response.json()

# Analyze Single Submission
def analyze_submission(submission_data):
    url = f"{BASE_URL}/api/v1/profiler/analyze"

    response = requests.post(url, headers=HEADERS, json=submission_data)
    return response.json()

# Get Opportunities
def get_opportunities(category="SaaS", min_score=0.7):
    url = f"{BASE_URL}/api/v1/opportunities"
    params = {
        "category": category,
        "min_score": min_score,
        "limit": 50
    }

    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()
```

### JavaScript/TypeScript Client Example
```typescript
interface PipelineRunRequest {
  source?: string;
  limit?: number;
  subreddits?: string[];
}

interface PipelineRunResponse {
  success: boolean;
  pipeline_id: string;
  stats: Record<string, any>;
  summary: Record<string, any>;
}

class RedditHarborAPI {
  private baseURL: string;
  private apiKey: string;

  constructor(baseURL: string, apiKey: string) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async runPipeline(request: PipelineRunRequest): Promise<PipelineRunResponse> {
    return this.request<PipelineRunResponse>('/api/v1/pipeline/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

// Usage
const api = new RedditHarborAPI('http://localhost:8000', 'your-api-key');

const result = await api.runPipeline({
  source: 'database',
  limit: 100,
  subreddits: ['Entrepreneur']
});
```

---

## Testing Strategy

### Unit Testing
```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_pipeline_run_success():
    """Test successful pipeline execution."""
    response = client.post(
        "/api/v1/pipeline/run",
        headers={"X-API-Key": "test-key"},
        json={"source": "database", "limit": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pipeline_id" in data
    assert "stats" in data

def test_pipeline_run_invalid_api_key():
    """Test pipeline execution with invalid API key."""
    response = client.post(
        "/api/v1/pipeline/run",
        headers={"X-API-Key": "invalid-key"},
        json={"source": "database", "limit": 10}
    )

    assert response.status_code == 401
```

### Integration Testing
```python
import asyncio
from api.routers.pipeline import run_pipeline
from api.models.requests import PipelineRunRequest

@pytest.mark.asyncio
async def test_pipeline_integration():
    """Test pipeline integration with real services."""
    request = PipelineRunRequest(
        source="database",
        limit=5
    )

    # This test requires actual services to be running
    # Use test database and Redis instances
    result = await run_pipeline(request, background_tasks=None, api_key="test-key")

    assert result.success is True
    assert result.stats["submissions_processed"] <= 5
```

### Load Testing
```python
from locust import HttpUser, task, between

class RedditHarborAPIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup API key for all requests."""
        self.client.headers.update({"X-API-Key": "test-key"})

    @task(3)
    def health_check(self):
        """Test health endpoint."""
        self.client.get("/api/v1/health")

    @task(2)
    def get_metrics(self):
        """Test metrics endpoint."""
        self.client.get("/api/v1/metrics")

    @task(1)
    def run_small_pipeline(self):
        """Test small pipeline execution."""
        self.client.post(
            "/api/v1/pipeline/run",
            json={"source": "database", "limit": 5}
        )
```

---

## Performance Considerations

### Response Time Targets
- Health check: <50ms
- Metrics: <100ms
- Opportunity listing: <200ms
- Single submission analysis: <15s
- Pipeline execution: <5min (depending on data size)

### Optimization Strategies
1. **Database Query Optimization**: Use proper indexing
2. **Caching**: Cache frequent API responses in Redis
3. **Pagination**: Implement efficient pagination for large datasets
4. **Background Processing**: Use async tasks for long-running operations
5. **Connection Pooling**: Reuse database and Redis connections

### Monitoring Metrics
- Response times by endpoint
- Error rates by endpoint
- Database query performance
- Redis hit/miss ratios
- Memory usage patterns
- CPU utilization