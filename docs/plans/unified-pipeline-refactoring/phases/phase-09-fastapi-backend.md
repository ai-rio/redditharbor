# Phase 9: Build FastAPI Backend

**Timeline**: Week 9  
**Duration**: 5 days  
**Risk Level**: 🟡 MEDIUM  
**Dependencies**: Phase 8 completed (unified orchestrator)

---

## Context

### What Was Completed (Phase 8)
- [x] Unified `OpportunityPipeline` created
- [x] Side-by-side validation passed
- [x] All services integrated

### Current State
- Pipeline only accessible via Python scripts
- No REST API for external access
- Next.js integration blocked

### Why This Phase Is Critical
- Enables web application development
- Clean boundary for separate Next.js repo
- Production-ready API infrastructure
- Foundation for Phase 10 (SDK)

---

## Objectives

### Primary Goals
1. **Create** FastAPI application with all endpoints
2. **Implement** authentication and rate limiting
3. **Add** request validation and error handling
4. **Document** API with OpenAPI/Swagger
5. **Prepare** for external consumption (separate repo)

### Success Criteria
- [ ] All services exposed as REST endpoints
- [ ] Authentication working (JWT)
- [ ] Rate limiting configured
- [ ] API documentation complete
- [ ] Load testing passes

---

## Tasks

### Task 1: Create FastAPI Application (2 days)

**Create**: `api/main.py`

```python
"""FastAPI backend for RedditHarbor unified pipeline."""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from core.pipeline.orchestrator import OpportunityPipeline
from core.pipeline.config import PipelineConfig
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="RedditHarbor API",
    description="Unified opportunity discovery pipeline API",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class PipelineRunRequest(BaseModel):
    source: str = "database"
    limit: int = 100
    subreddits: Optional[list[str]] = None
    config: Optional[dict] = None

class ProfilerRequest(BaseModel):
    submission_id: str
    submission_title: str
    submission_content: str
    subreddit: str

# Endpoints
@app.post("/api/v1/pipeline/run")
async def run_pipeline(
    request: PipelineRunRequest,
    api_key: str = Header(...)
):
    """Run complete opportunity discovery pipeline."""
    try:
        # Validate API key
        if not validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Create config
        config = PipelineConfig(
            data_source=request.source,
            limit=request.limit,
            **(request.config or {})
        )
        
        # Run pipeline
        pipeline = OpportunityPipeline(config)
        result = pipeline.run(subreddits=request.subreddits)
        
        return {
            "success": True,
            "pipeline_id": generate_pipeline_id(),
            "stats": result['stats'],
            "summary": result['summary']
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/profiler/analyze")
async def analyze_with_profiler(
    request: ProfilerRequest,
    api_key: str = Header(...)
):
    """Run AI profiler on single submission."""
    try:
        if not validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        from core.enrichment.profiler_service import ProfilerService
        
        # Initialize service
        profiler_service = get_profiler_service()
        
        # Run analysis
        result = profiler_service.enrich({
            'submission_id': request.submission_id,
            'title': request.submission_title,
            'content': request.submission_content,
            'subreddit': request.subreddit
        })
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Profiler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Similar endpoints for:
# - /api/v1/opportunities/score
# - /api/v1/monetization/analyze
# - /api/v1/trust/validate
# - /api/v1/market/validate

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}

@app.get("/api/v1/metrics")
async def get_metrics(api_key: str = Header(...)):
    """Get application metrics."""
    if not validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Return pipeline statistics, cost savings, etc.
    return {
        "cost_savings_ytd": 2800.00,
        "total_analyzed": 5420,
        "uptime": "99.9%"
    }

def validate_api_key(key: str) -> bool:
    """Validate API key."""
    # Implement proper validation
    return True  # Placeholder

def generate_pipeline_id() -> str:
    """Generate unique pipeline ID."""
    import uuid
    return str(uuid.uuid4())
```

---

### Task 2: Add Authentication & Rate Limiting (1 day)

```python
# api/auth.py
"""Authentication middleware."""
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key from header."""
    valid_key = os.getenv("REDDIT_HARBOR_API_KEY")
    
    if api_key != valid_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return api_key

# api/rate_limit.py
"""Rate limiting middleware."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to app:
# @app.post("/api/v1/pipeline/run")
# @limiter.limit("5/minute")
# async def run_pipeline(...):
```

---

### Task 3: API Documentation (1 day)

- Configure OpenAPI/Swagger UI
- Add request/response examples
- Document authentication flow
- Create integration examples

**Access**: http://localhost:8000/docs

---

### Task 4: Docker Deployment (1 day)

**Create**: `api/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Create**: `docker-compose.yml`

```yaml
version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - REDDIT_HARBOR_API_KEY=${API_KEY}
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Validation Checklist

### Implementation Validation
- [ ] All endpoints created and tested
- [ ] Authentication working
- [ ] Rate limiting functional
- [ ] Error handling comprehensive

### API Testing
- [ ] Manual testing via Swagger UI
- [ ] Automated API tests: `pytest api/tests/`
- [ ] Load testing: 100 concurrent requests
- [ ] Response times <500ms for simple operations

### Documentation Validation
- [ ] OpenAPI spec complete
- [ ] All endpoints documented
- [ ] Examples provided
- [ ] Authentication flow documented

---

## Rollback Procedure

```bash
rm -rf api/
docker-compose down
pytest tests/ -v
```

---

## Next Phase

→ **[Phase 10: Create TypeScript SDK for Next.js](phase-10-nextjs-sdk.md)**

**Status**: ⏸️ NOT STARTED
