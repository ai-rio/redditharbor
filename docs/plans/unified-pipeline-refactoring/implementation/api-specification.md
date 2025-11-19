# API Specification

**Version**: 2.0.0  
**Base URL**: `http://localhost:8000` (development)  
**Production URL**: TBD  

This document consolidates the complete API specification from Phase 9 and the existing Next.js API integration guide.

---

## Authentication

All endpoints (except `/health`) require API key authentication.

**Header**: `X-API-Key: your_api_key_here`

**Example**:
```bash
curl -H "X-API-Key: secret123" http://localhost:8000/api/v1/health
```

---

## Core Endpoints

### POST /api/v1/pipeline/run
Run complete opportunity discovery pipeline.

**Request**:
```json
{
  "source": "database",
  "limit": 100,
  "subreddits": ["startups", "SaaS"],
  "config": {
    "enable_profiler": true,
    "enable_opportunity_scoring": true,
    "enable_monetization": true,
    "enable_trust": false,
    "enable_market_validation": false
  }
}
```

**Response**:
```json
{
  "success": true,
  "pipeline_id": "uuid-here",
  "stats": {
    "fetched": 100,
    "analyzed": 85,
    "stored": 85,
    "errors": 0
  },
  "summary": {
    "total_fetched": 100,
    "total_analyzed": 85,
    "success_rate": 85.0
  }
}
```

**Rate Limit**: 5 requests/minute

---

### POST /api/v1/profiler/analyze
Analyze single submission with AI profiler.

**Request**:
```json
{
  "submission_id": "abc123",
  "submission_title": "I need a fitness tracking app",
  "submission_content": "Looking for an app that...",
  "subreddit": "fitness"
}
```

**Response**:
```json
{
  "success": true,
  "result": {
    "app_name": "FitTrack Pro",
    "core_functions": ["Track workouts", "Set goals", "View progress"],
    "value_proposition": "Simple fitness tracking",
    "target_audience": "Busy professionals"
  }
}
```

**Rate Limit**: 20 requests/minute

---

### POST /api/v1/opportunities/score
Score opportunity potential.

**Request**: Similar to profiler  
**Response**: Opportunity scores (final_score, market_demand, etc.)  
**Rate Limit**: 20 requests/minute

---

### POST /api/v1/monetization/analyze
Analyze monetization potential.

**Rate Limit**: 15 requests/minute

---

### POST /api/v1/trust/validate
Validate with trust layer.

**Rate Limit**: 20 requests/minute

---

### POST /api/v1/market/validate
Perform market validation.

**Rate Limit**: 10 requests/minute

---

### GET /api/v1/health
Health check (no authentication required).

**Response**:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

**Rate Limit**: 100 requests/minute

---

### GET /api/v1/metrics
Get application metrics (requires authentication).

**Response**:
```json
{
  "cost_savings_ytd": 2800.00,
  "total_analyzed": 5420,
  "uptime": "99.9%"
}
```

**Rate Limit**: 30 requests/minute

---

## Error Responses

All errors return:
```json
{
  "detail": "Error message here",
  "status_code": 400/401/403/500
}
```

**Common Error Codes**:
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid API key)
- `403` - Forbidden (insufficient permissions)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

---

## Rate Limiting

Rate limits are per API key, per endpoint.

**Headers returned**:
- `X-RateLimit-Limit`: Requests allowed per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp of window reset

---

## WebSocket Support (Future)

Planned for real-time pipeline updates:

```
ws://localhost:8000/ws/pipeline/{pipeline_id}
```

Messages:
```json
{
  "type": "pipeline_status",
  "pipeline_id": "uuid",
  "progress": 45,
  "current_step": "enrichment"
}
```

---

For complete details, see [Phase 9: Build FastAPI Backend](../phases/phase-09-fastapi-backend.md)
