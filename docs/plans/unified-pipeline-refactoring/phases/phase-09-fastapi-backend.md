# Phase 9: Build FastAPI Backend

**Timeline**: Week 9
**Duration**: 5 days
**Risk Level**: 🟡 MEDIUM
**Dependencies**: Phase 8 completed (unified orchestrator)

---

## Quick Start (30-Second Overview)

**Goal**: Convert the unified Python pipeline into a production-ready REST API.

**What We're Building**:
- FastAPI backend exposing all pipeline services
- Production-ready authentication & rate limiting
- Docker deployment configuration
- Complete API documentation

**Key Files**:
- `api/main.py` - FastAPI application core
- `api/core/` - Configuration, auth, rate limiting
- `docker-compose.yml` - Production deployment

**Success**: All pipeline services accessible via REST API with proper security.

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

## Implementation Decision Matrix

| Aspect | Custom Implementation | Boilerplate-Based | Decision |
|--------|----------------------|-------------------|----------|
| **Configuration** | Manual .env parsing | Pydantic Settings | ✅ **Boilerplate** - More robust |
| **Authentication** | Simple API key checks | JWT + API Key patterns | ✅ **Boilerplate** - Production ready |
| **Rate Limiting** | In-memory counters | Redis-based distributed | ✅ **Boilerplate** - Scalable |
| **App Structure** | Single file | Modular core/ router pattern | ✅ **Boilerplate** - Maintainable |
| **Deployment** | Basic Dockerfile | Multi-stage + nginx + redis | ✅ **Boilerplate** - Production ready |

**Rationale**: The extracted boilerplate provides production-ready patterns that would take weeks to implement from scratch. It's proven, tested, and follows FastAPI best practices.

---

## Implementation Roadmap

### Day 1-2: Core API Structure
**Main Document**: This orchestrator
**Sub-Document**: [API Endpoints Specification](api/endpoints.md)

Tasks:
- [ ] Create modular FastAPI application structure
- [ ] Implement all pipeline service endpoints
- [ ] Add request/response models
- [ ] Integrate with existing `OpportunityPipeline`

**Implementation Guide**: See [API Endpoints Specification](api/endpoints.md) for detailed endpoint definitions and integration patterns.

### Day 2-3: Authentication & Security
**Sub-Document**: [API Authentication Patterns](api/authentication.md)

Tasks:
- [ ] Implement API key authentication
- [ ] Add JWT token validation (optional)
- [ ] Configure request validation
- [ ] Add security headers

**Implementation Guide**: See [API Authentication Patterns](api/authentication.md) for complete security implementation using proven boilerplate patterns.

### Day 3: Rate Limiting
**Sub-Document**: [Redis Rate Limiting](api/rate-limiting.md)

Tasks:
- [ ] Set up Redis for distributed rate limiting
- [ ] Implement endpoint-specific limits
- [ ] Add rate limit headers
- [ ] Configure burst and sustained rates

**Implementation Guide**: See [Redis Rate Limiting](api/rate-limiting.md) for production-ready rate limiting implementation.

### Day 4: Documentation & Testing
**Sub-Document**: [API Testing Strategies](api/testing.md)

Tasks:
- [ ] Configure OpenAPI/Swagger documentation
- [ ] Add request/response examples
- [ ] Write comprehensive API tests
- [ ] Load testing validation

**Implementation Guide**: See [API Testing Strategies](api/testing.md) for testing patterns and validation approaches.

### Day 5: Production Deployment
**Sub-Document**: [Docker & Production Setup](api/deployment.md)

Tasks:
- [ ] Create multi-stage Docker build
- [ ] Configure nginx reverse proxy
- [ ] Set up production monitoring
- [ ] Environment configuration

**Implementation Guide**: See [Docker & Production Setup](api/deployment.md) for complete production deployment configuration.

---

## Architecture Overview

### Modular Application Structure
```
api/
├── main.py                 # FastAPI app factory
├── core/
│   ├── config.py          # Pydantic settings
│   ├── auth.py            # Authentication patterns
│   ├── rate_limit.py      # Redis rate limiting
│   └── setup.py           # App factory utilities
├── routers/
│   ├── pipeline.py        # Pipeline endpoints
│   ├── enrichment.py      # AI service endpoints
│   └── monitoring.py      # Health & metrics
├── models/
│   ├── requests.py        # Pydantic request models
│   └── responses.py       # Pydantic response models
└── tests/
    ├── test_endpoints.py
    └── test_auth.py
```

### Integration Points
- **Pipeline Integration**: `core.pipeline.orchestrator.OpportunityPipeline`
- **Database**: Supabase connection (existing config)
- **Cache**: Redis for rate limiting (Phase 5 deduplication)
- **Enrichment**: All Phase 6 services
- **Configuration**: Existing `config/settings.py` system

---

## Progress Tracking

### Phase 9 Implementation Status

#### Core API Structure
- [ ] FastAPI application factory created
- [ ] All pipeline endpoints implemented
- [ ] Request/response models defined
- [ ] Error handling standardized

#### Security & Rate Limiting
- [ ] API key authentication functional
- [ ] Redis rate limiting configured
- [ ] Request validation active
- [ ] Security headers added

#### Documentation & Testing
- [ ] OpenAPI spec complete
- [ ] API tests passing
- [ ] Load testing validated
- [ ] Swagger UI functional

#### Production Readiness
- [ ] Docker build optimized
- [ ] nginx reverse proxy configured
- [ ] Environment variables documented
- [ ] Monitoring endpoints added

---

## RedditHarbor Integration Requirements

### Essential Integration Points

#### 1. Pipeline Integration
```python
# Must integrate with existing:
from core.pipeline.orchestrator import OpportunityPipeline
from core.pipeline.config import PipelineConfig
```

#### 2. Database Connection
```python
# Use existing Supabase config
from config.settings import SUPABASE_URL, SUPABASE_KEY
```

#### 3. Redis Connection
```python
# Leverage existing Redis from Phase 5
# core/deduplication/redis_deduplicator.py
```

#### 4. Enrichment Services
```python
# All Phase 6 services must be accessible
from core.enrichment.profiler_service import ProfilerService
from core.enrichment.opportunity_service import OpportunityService
```

### Configuration Compatibility
- Must work with existing `.env` structure
- Respect `ENABLE_PII_ANONYMIZATION` setting
- Integrate with existing logging configuration
- Use existing error handling patterns

---

## Success Criteria Checklist

### Functional Requirements
- [ ] All pipeline services exposed via REST API
- [ ] Authentication and authorization working
- [ ] Rate limiting preventing abuse
- [ ] Request validation preventing bad data
- [ ] Error handling returning proper HTTP codes

### Performance Requirements
- [ ] Response times <500ms for simple operations
- [ ] Pipeline execution under existing time limits
- [ ] Rate limiting not impacting legitimate usage
- [ ] Memory usage within acceptable bounds

### Security Requirements
- [ ] API key validation working
- [ ] Rate limits enforced per endpoint
- [ ] PII anonymization respected
- [ ] CORS properly configured for production

### Documentation Requirements
- [ ] All endpoints documented in OpenAPI
- [ ] Request/response examples provided
- [ ] Authentication flow documented
- [ ] Integration examples available

### Production Readiness
- [ ] Docker build working and optimized
- [ ] Environment configuration complete
- [ ] Health endpoints functional
- [ ] Monitoring data available

---

## Templates Directory

The following templates are available for immediate use:

| Template | Purpose | Location |
|----------|---------|----------|
| `api-main.py.template` | Complete FastAPI application | [templates/api-main.py.template](../templates/api-main.py.template) |
| `docker-compose.yml.template` | Production deployment | [templates/docker-compose.yml.template](../templates/docker-compose.yml.template) |
| `nginx.conf.template` | Reverse proxy configuration | [templates/nginx.conf.template](../templates/nginx.conf.template) |
| `requirements.txt.template` | Python dependencies | [templates/requirements.txt.template](../templates/requirements.txt.template) |

All templates include RedditHarbor-specific integration points and are ready for customization.

---

## Testing & Validation

### Manual Testing Checklist
```bash
# 1. Start services
docker-compose up -d

# 2. Test authentication
curl -H "X-API-Key: $REDDIT_HARBOR_API_KEY" http://localhost:8000/api/v1/health

# 3. Test pipeline endpoint
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $REDDIT_HARBOR_API_KEY" \
  -d '{"source": "database", "limit": 10}'

# 4. Test rate limiting
for i in {1..10}; do
  curl -s http://localhost:8000/api/v1/metrics -H "X-API-Key: $REDDIT_HARBOR_API_KEY"
done
```

### Automated Testing
```bash
# Run all API tests
pytest api/tests/ -v

# Load testing
locust -f api/tests/load_test.py --host=http://localhost:8000

# Documentation validation
curl http://localhost:8000/docs
```

---

## Rollback Procedure

If implementation fails at any point:

```bash
# 1. Remove API directory
rm -rf api/

# 2. Stop containers
docker-compose down -v

# 3. Validate existing pipeline still works
pytest tests/ -v
python -m core.pipeline.orchestrator

# 4. Restore from git if needed
git checkout HEAD -- .
```

---

## Related Documentation

### Implementation Guides
- [API Endpoints Specification](api/endpoints.md) - Detailed endpoint definitions
- [API Authentication Patterns](api/authentication.md) - Security implementation
- [Redis Rate Limiting](api/rate-limiting.md) - Rate limiting configuration
- [Docker & Production Setup](api/deployment.md) - Production deployment
- [API Testing Strategies](api/testing.md) - Testing patterns

### Templates
- [FastAPI Main Application](../templates/api-main.py.template)
- [Docker Compose Configuration](../templates/docker-compose.yml.template)
- [Nginx Reverse Proxy](../templates/nginx.conf.template)
- [Python Dependencies](../templates/requirements.txt.template)

---

## Next Phase

→ **[Phase 10: Create TypeScript SDK for Next.js](phase-10-nextjs-sdk.md)**

**Dependencies**: Phase 9 API must be fully functional and documented.

**Status**: ⏸️ NOT STARTED

---

## Quick Reference

### Essential Commands
```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production
docker-compose up -d

# Testing
pytest api/tests/ -v
```

### Key URLs
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- OpenAPI Spec: http://localhost:8000/openapi.json

### Environment Variables
```bash
REDDIT_HARBOR_API_KEY=your-api-key-here
REDIS_URL=redis://localhost:6379
CORS_ORIGINS=http://localhost:3000
```