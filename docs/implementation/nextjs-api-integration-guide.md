> **📌 DEPRECATION NOTICE**
> 
> **Status**: This document has been superseded  
> **Date**: 2025-11-19  
> **Replacement**: [Unified Pipeline Refactoring Plan](unified-pipeline-refactoring/README.md)
> 
> This file is kept for historical reference only. The content has been reorganized into an executable, phase-by-phase plan with:
> - 11 detailed phase files
> - Complete implementation guides
> - Executable checklists
> - Rollback procedures
> - Progress tracking
> 
> **For current planning, see**: [docs/plans/unified-pipeline-refactoring/](unified-pipeline-refactoring/)
> 
> ---
> 
# RedditHarbor Next.js API Integration Guide

**Complete API layer for unified opportunity discovery pipeline**

## Overview

This guide provides comprehensive documentation for the Next.js API integration with the RedditHarbor unified pipeline. The integration consists of:

1. **FastAPI Backend** - Complete REST API with all AI services
2. **Next.js Frontend** - API routes and client libraries
3. **Real-time Communication** - WebSocket support for live updates
4. **Authentication & Security** - JWT-based auth with role-based access
5. **Performance & Monitoring** - Rate limiting, caching, and health checks

---

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│  Next.js App    │◄──►│  FastAPI Backend │◄──►│  Python Services │
│  (Frontend)     │    │  (REST API)     │    │  (AI Pipeline)  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐            ┌─────▼──────┐        ┌───────▼──────┐
    │ WebSocket│            │    Redis   │        │   Supabase   │
    │ (Updates)│            │   (Cache)  │        │ (Database)   │
    └─────────┘            └────────────┘        └──────────────┘
```

### Key Components

- **FastAPI Main Server** (`api/main.py`) - Central API gateway
- **Next.js API Routes** - Proxies to FastAPI backend
- **TypeScript Client** - Type-safe API client with authentication
- **WebSocket Hooks** - Real-time pipeline progress tracking
- **Docker Compose** - Complete development environment

---

## 1. FastAPI Backend

### Features

✅ **Complete AI Service Endpoints**
- `/api/v1/profiler/analyze` - AI Profiler (EnhancedLLMProfiler)
- `/api/v1/opportunities/score` - Opportunity Scoring (OpportunityAnalyzerAgent)
- `/api/v1/monetization/analyze` - Monetization Analysis (MonetizationAgnoAnalyzer)
- `/api/v1/trust/validate` - Trust Validation (TrustLayerValidator)
- `/api/v1/market/validate` - Market Validation (MarketDataValidator)

✅ **Pipeline Orchestration**
- `/api/v1/pipeline/run` - Full pipeline execution
- `/api/v1/pipeline/{id}/status` - Real-time status tracking
- `/api/v1/pipeline/{id}/result` - Pipeline results

✅ **Data Management**
- `/api/v1/data/fetch` - Query Supabase tables
- `/api/v1/files/upload` - File upload support
- `/api/v1/health` - Health check endpoint
- `/api/v1/metrics` - Application metrics

✅ **Authentication & Security**
- JWT token-based authentication
- Role-based access control
- Rate limiting per endpoint
- CORS configuration for Next.js
- Request validation with Pydantic

✅ **Performance Features**
- Redis caching for frequent requests
- Background job processing
- Response compression (GZip)
- Connection pooling
- Real-time WebSocket updates

### Setup

```bash
# Navigate to API directory
cd api

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use Docker
docker build -t reddit-harbor-api .
docker run -p 8000:8000 reddit-harbor-api
```

### Environment Variables

```bash
# Database Configuration
SUPABASE_URL="http://127.0.0.1:54321"
SUPABASE_KEY="your_service_role_key"

# Redis Configuration
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD=""

# AI Services Configuration
OPENROUTER_API_KEY="your_openrouter_key"
REDDIT_PUBLIC="your_reddit_public_key"
REDDIT_SECRET="your_reddit_secret_key"
JINA_API_KEY="your_jina_api_key"
AGENTOPS_API_KEY="your_agentops_key"
```

---

## 2. Next.js Frontend Integration

### API Routes Structure

```
frontend/app/api/
├── auth/
│   └── token/
│       └── route.ts          # Authentication
├── opportunities/
│   └── analyze/
│       └── route.ts          # Profiler + Data Fetch
├── pipeline/
│   └── run/
│       └── route.ts          # Pipeline Orchestration
├── monetization/
│   └── analyze/
│       └── route.ts          # Monetization Analysis
├── trust/
│   └── validate/
│       └── route.ts          # Trust Validation
└── market/
    └── validate/
        └── route.ts          # Market Validation
```

### TypeScript Client

```typescript
import { apiClient } from '@/lib/api/client';
import { ProfilerRequest, PipelineRequest } from '@/lib/types/api';

// AI Profiling
const result = await apiClient.analyzeWithProfiler({
  submission_id: 'abc123',
  submission_title: 'Title',
  submission_content: 'Content...',
  subreddit: 'startups'
});

// Pipeline Execution
const pipeline = await apiClient.runPipeline({
  source: 'database',
  limit: 100,
  config: {
    enable_profiler: true,
    enable_opportunity_scoring: true,
    enable_monetization: true,
    enable_trust: true,
    enable_market_validation: true,
    ai_profile_threshold: 40.0,
    monetization_threshold: 60.0,
    market_validation_threshold: 60.0
  }
});
```

### WebSocket Integration

```typescript
import { usePipelineProgress } from '@/lib/hooks/useWebSocket';

// Real-time pipeline progress
const {
  progress,
  status,
  currentStep,
  errors,
  isConnected
} = usePipelineProgress(pipelineId);

// Custom WebSocket usage
const {
  sendMessage,
  isConnected,
  lastMessage
} = useWebSocket({
  pipelineId: 'abc-123',
  onMessage: (message) => {
    console.log('Received:', message);
  }
});
```

### Environment Variables

```bash
# Next.js Frontend (.env.local)
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_SUPABASE_URL="http://localhost:54321"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your_anon_key"
```

---

## 3. Authentication Flow

### Token-Based Authentication

```typescript
// Login
const credentials = {
  username: 'user@example.com',
  password: 'password123'
};

const tokenResponse = await apiClient.authenticate(credentials);
// Token automatically stored and managed

// API calls automatically include authentication
const result = await apiClient.analyzeWithProfiler(request);
```

### Role-Based Access Control

```typescript
// Available permissions
const permissions = [
  'read',           // Read data
  'write',          // Write data
  'pipeline:run',   // Run pipelines
  'admin',          // Admin access
  'analytics'       // Access analytics
];
```

---

## 4. API Usage Examples

### Individual Service Analysis

```typescript
// 1. AI Profiling
const profile = await apiClient.analyzeWithProfiler({
  submission_id: 'abc123',
  submission_title: 'New Fitness App Idea',
  submission_content: 'I wish there was an app that...',
  subreddit: 'fitness'
});

// 2. Opportunity Scoring
const scores = await apiClient.scoreOpportunity({
  submission_id: 'abc123',
  title: 'New Fitness App Idea',
  content: 'I wish there was an app that...',
  subreddit: 'fitness'
});

// 3. Monetization Analysis
const monetization = await apiClient.analyzeMonetization({
  submission_id: 'abc123',
  title: 'New Fitness App Idea',
  content: 'I wish there was an app that...',
  subreddit: 'fitness'
});

// 4. Trust Validation
const trust = await apiClient.validateTrust({
  submission_id: 'abc123',
  title: 'New Fitness App Idea',
  content: 'I wish there was an app that...',
  subreddit: 'fitness'
});

// 5. Market Validation
const market = await apiClient.validateMarket({
  submission_id: 'abc123',
  app_concept: 'Fitness App',
  problem_description: 'Difficulty tracking workouts',
  target_competitors: ['MyFitnessPal', 'Strava']
});
```

### Pipeline Execution

```typescript
// Run full pipeline
const pipeline = await apiClient.runPipeline({
  source: 'database',          // or 'reddit'
  limit: 100,
  subreddits: ['startups', 'SaaS'],
  config: {
    enable_profiler: true,
    enable_opportunity_scoring: true,
    enable_monetization: true,
    enable_trust: true,
    enable_market_validation: true,
    ai_profile_threshold: 40.0,
    monetization_threshold: 60.0,
    market_validation_threshold: 60.0
  },
  test_mode: false
});

// Monitor pipeline progress
const status = await apiClient.getPipelineStatus(pipeline.pipeline_id);
const result = await apiClient.getPipelineResult(pipeline.pipeline_id);
```

### Data Fetching

```typescript
// Fetch opportunities with filters
const opportunities = await apiClient.fetchOpportunities({
  limit: 50,
  offset: 0,
  subreddit: 'startups',
  minScore: 60.0,
  hasAppName: true,
  sortBy: 'final_score',
  sortOrder: 'desc'
});

// Fetch business concepts
const concepts = await apiClient.fetchBusinessConcepts({
  limit: 20,
  minSubmissions: 5,
  hasAnalysis: true
});

// Custom data queries
const customData = await apiClient.fetchData({
  table_name: 'opportunities_unified',
  filters: {
    subreddit: { in: ['startups', 'SaaS'] },
    final_score: { gte: 70.0 },
    created_utc: { gte: '2024-01-01' }
  },
  limit: 100,
  offset: 0
});
```

---

## 5. Real-time Updates

### WebSocket Connection

```typescript
// Connect to pipeline updates
const {
  sendMessage,
  isConnected,
  lastMessage,
  error
} = useWebSocket({
  pipelineId: 'abc-123',
  onMessage: (message) => {
    switch (message.type) {
      case 'pipeline_started':
        console.log('Pipeline started:', message.pipeline_id);
        break;
      case 'pipeline_completed':
        console.log('Pipeline completed');
        break;
      case 'pipeline_error':
        console.error('Pipeline error:', message.error);
        break;
      case 'pipeline_status':
        console.log('Progress:', message.data?.progress);
        break;
    }
  },
  onError: (error) => {
    console.error('WebSocket error:', error);
  }
});
```

### Progress Tracking Hook

```typescript
import { usePipelineProgress } from '@/lib/hooks/useWebSocket';

function PipelineMonitor({ pipelineId }: { pipelineId: string }) {
  const {
    progress,
    status,
    currentStep,
    errors,
    isConnected,
    connectionError
  } = usePipelineProgress(pipelineId);

  return (
    <div>
      <div>Progress: {progress}%</div>
      <div>Status: {status}</div>
      <div>Current Step: {currentStep}</div>
      <div>Connected: {isConnected ? 'Yes' : 'No'}</div>
      {errors.length > 0 && (
        <div>
          <h4>Errors:</h4>
          <ul>
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## 6. Error Handling

### Standardized Error Responses

```typescript
interface ErrorResponse {
  success: false;
  message: string;
  error_code: string;
  details?: Record<string, any>;
}

// Example error handling
try {
  const result = await apiClient.analyzeWithProfiler(request);
} catch (error) {
  if (error.message.includes('Authentication')) {
    // Handle auth error
    router.push('/login');
  } else if (error.message.includes('Rate limit')) {
    // Handle rate limiting
    setError('Please wait before making another request');
  } else {
    // Handle other errors
    setError('Analysis failed. Please try again.');
  }
}
```

### Error Codes

```typescript
const ERROR_CODES = {
  // Authentication
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  AUTH_INVALID: 'AUTH_INVALID',
  PERMISSION_DENIED: 'PERMISSION_DENIED',

  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',

  // Rate Limiting
  RATE_LIMITED: 'RATE_LIMITED',

  // Service Errors
  PROFILER_ERROR: 'PROFILER_ERROR',
  PIPELINE_ERROR: 'PIPELINE_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',

  // System Errors
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  TIMEOUT: 'TIMEOUT'
} as const;
```

---

## 7. Performance Optimization

### Caching Strategy

```typescript
// Automatic caching by API client
const result = await apiClient.analyzeWithProfiler(request);
// Results cached for 24 hours by default

// Force cache refresh
const freshResult = await apiClient.analyzeWithProfiler(request, {
  cache: 'no-cache'
});
```

### Rate Limiting

- **Authentication endpoints**: 10 requests/minute
- **AI service endpoints**: 20 requests/minute
- **Pipeline endpoints**: 5 requests/minute
- **Data fetching**: 50 requests/minute
- **Health checks**: 100 requests/minute

### Batch Operations

```typescript
// Analyze multiple submissions efficiently
const submissions = [
  { submission_id: '1', ... },
  { submission_id: '2', ... },
  { submission_id: '3', ... }
];

const results = await apiClient.analyzeMultipleSubmissions(
  submissions,
  { batchSize: 5, delay: 1000 }
);
```

---

## 8. Development Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Redis
- Supabase CLI

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd reddit-harbor-core-functions-fix

# 2. Set up environment variables
cp .env.example .env.local
# Edit .env.local with your credentials

# 3. Start development stack
docker-compose up -d

# 4. Install Python dependencies
cd api
pip install -r requirements.txt

# 5. Install Node.js dependencies
cd ../frontend
npm install

# 6. Start development servers
# Terminal 1: FastAPI backend
cd ../api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Next.js frontend
cd ../frontend
npm run dev

# 7. Access applications
# FastAPI: http://localhost:8000
# Next.js: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Supabase Studio: http://localhost:54323
```

### Docker Development

```bash
# Start complete stack
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f frontend

# Stop stack
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

---

## 9. Production Deployment

### Environment Configuration

```bash
# Production environment variables
NODE_ENV=production
API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
SUPABASE_URL=https://your-project.supabase.co
REDIS_HOST=your-redis-host
```

### Docker Production

```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ ./
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Monitoring & Logging

```typescript
// Custom logging
import { logger } from '@/lib/utils/logger';

logger.info('Pipeline started', { pipelineId, userId });
logger.error('Analysis failed', { error, submissionId });

// Performance monitoring
const startTime = performance.now();
await apiClient.analyzeWithProfiler(request);
const duration = performance.now() - startTime;
logger.info('Analysis completed', { duration, submissionId });
```

---

## 10. API Reference

### Complete Endpoints List

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/v1/auth/token` | Authenticate user | 10/min |
| POST | `/api/v1/profiler/analyze` | AI Profiling | 20/min |
| POST | `/api/v1/opportunities/score` | Opportunity Scoring | 20/min |
| POST | `/api/v1/monetization/analyze` | Monetization Analysis | 15/min |
| POST | `/api/v1/trust/validate` | Trust Validation | 20/min |
| POST | `/api/v1/market/validate` | Market Validation | 10/min |
| POST | `/api/v1/pipeline/run` | Run Pipeline | 5/min |
| GET | `/api/v1/pipeline/{id}/status` | Pipeline Status | 30/min |
| GET | `/api/v1/pipeline/{id}/result` | Pipeline Result | 10/min |
| POST | `/api/v1/data/fetch` | Fetch Data | 50/min |
| POST | `/api/v1/files/upload` | Upload File | 10/min |
| GET | `/api/v1/health` | Health Check | 100/min |
| GET | `/api/v1/metrics` | Application Metrics | 30/min |
| WS | `/ws/pipeline/{id}` | Real-time Updates | N/A |

### Request/Response Examples

See the `frontend/lib/types/api.ts` file for complete TypeScript definitions of all request and response types.

---

## 11. Testing

### Unit Tests

```typescript
// API client tests
import { apiClient } from '@/lib/api/client';

describe('ApiClient', () => {
  test('should authenticate successfully', async () => {
    const result = await apiClient.authenticate({
      username: 'test@example.com',
      password: 'password'
    });
    expect(result.success).toBe(true);
    expect(result.access_token).toBeDefined();
  });

  test('should analyze with profiler', async () => {
    const result = await apiClient.analyzeWithProfiler({
      submission_id: 'test-123',
      submission_title: 'Test Title',
      submission_content: 'Test content',
      subreddit: 'test'
    });
    expect(result.success).toBe(true);
    expect(result.app_name).toBeDefined();
  });
});
```

### Integration Tests

```typescript
// Pipeline integration tests
describe('Pipeline Integration', () => {
  test('should run complete pipeline', async () => {
    const pipeline = await apiClient.runPipeline({
      source: 'database',
      limit: 10,
      config: {
        enable_profiler: true,
        enable_opportunity_scoring: true,
        enable_monetization: false,
        enable_trust: false,
        enable_market_validation: false,
        ai_profile_threshold: 40.0,
        monetization_threshold: 60.0,
        market_validation_threshold: 60.0
      },
      test_mode: true
    });

    expect(pipeline.success).toBe(true);
    expect(pipeline.pipeline_id).toBeDefined();

    // Check pipeline completion
    const status = await apiClient.getPipelineStatus(pipeline.pipeline_id);
    expect(['completed', 'running']).toContain(status.status);
  });
});
```

---

## 12. Troubleshooting

### Common Issues

**Connection Refused**
```bash
# Check if API server is running
curl http://localhost:8000/api/v1/health

# Check Docker containers
docker-compose ps
docker-compose logs api
```

**Authentication Issues**
```typescript
// Clear stored tokens and re-authenticate
localStorage.removeItem('reddit_harbor_token');
localStorage.removeItem('reddit_harbor_token_expiry');
apiClient.logout();
```

**WebSocket Connection Issues**
```typescript
// Check WebSocket support
if (typeof WebSocket !== 'undefined') {
  console.log('WebSocket supported');
} else {
  console.error('WebSocket not supported');
}

// Check connection status
const ws = useWebSocket({
  pipelineId: 'test-123',
  onError: (error) => {
    console.error('WebSocket error:', error);
  }
});
```

**Rate Limiting**
```typescript
// Implement exponential backoff
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.message.includes('Rate limit') && i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
      } else {
        throw error;
      }
    }
  }
}
```

---

## 13. Contributing

### Development Workflow

1. Create feature branch
2. Make changes with tests
3. Run linting and type checking
4. Test integration
5. Submit pull request

### Code Quality

```bash
# Python linting
cd api
ruff check .
ruff format .

# TypeScript linting
cd frontend
npm run lint
npm run type-check

# Run tests
npm run test
npm run test:coverage
```

---

## 14. Support

### Documentation

- **API Documentation**: http://localhost:8000/docs
- **Type Definitions**: `frontend/lib/types/api.ts`
- **Client Library**: `frontend/lib/api/client.ts`
- **WebSocket Hooks**: `frontend/lib/hooks/useWebSocket.ts`

### Getting Help

1. Check API documentation
2. Review example code
3. Check logs for errors
4. Create GitHub issue with details

---

## 15. License

This API integration is part of the RedditHarbor project. See the main project license for details.

---

**Created**: 2025-11-19
**Author**: RedditHarbor Development Team
**Version**: 2.0.0