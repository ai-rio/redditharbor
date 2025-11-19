# Phase 10: Create TypeScript SDK for Next.js

**Timeline**: Week 10  
**Duration**: 5 days  
**Risk Level**: 🟡 MEDIUM  
**Dependencies**: Phase 9 completed (FastAPI backend)

---

## Context

### What Was Completed (Phase 9)
- [x] FastAPI backend with all endpoints
- [x] Authentication and rate limiting
- [x] API documentation complete

### Current State
- API ready but no client library
- Next.js team needs TypeScript SDK
- **Next.js app lives in separate repository**
- Need clean API boundary

### Why This Phase Is Critical
- Enables Next.js development in separate repo
- Type-safe API consumption
- Clean separation of concerns
- Publishable as npm package (optional)

---

## Objectives

### Primary Goals
1. **Create** TypeScript SDK for API consumption
2. **Generate** type definitions from API
3. **Provide** integration examples
4. **Document** usage for Next.js team
5. **Package** for easy distribution

### Success Criteria
- [ ] Complete TypeScript SDK created
- [ ] All API endpoints wrapped
- [ ] Type definitions accurate
- [ ] Integration examples provided
- [ ] Ready for Next.js repo consumption

---

## Tasks

### Task 1: Generate TypeScript Types (1 day)

**Create**: `sdk/types/api.ts`

```typescript
/**
 * RedditHarbor API TypeScript Definitions
 * Generated from FastAPI OpenAPI spec
 */

// Request types
export interface PipelineRunRequest {
  source: 'database' | 'reddit';
  limit: number;
  subreddits?: string[];
  config?: PipelineConfig;
}

export interface PipelineConfig {
  enable_profiler?: boolean;
  enable_opportunity_scoring?: boolean;
  enable_monetization?: boolean;
  enable_trust?: boolean;
  enable_market_validation?: boolean;
  ai_profile_threshold?: number;
  monetization_threshold?: number;
  market_validation_threshold?: number;
}

export interface ProfilerRequest {
  submission_id: string;
  submission_title: string;
  submission_content: string;
  subreddit: string;
}

export interface OpportunityRequest {
  submission_id: string;
  title: string;
  content: string;
  subreddit: string;
}

// Response types
export interface PipelineRunResponse {
  success: boolean;
  pipeline_id: string;
  stats: PipelineStats;
  summary: PipelineSummary;
}

export interface PipelineStats {
  fetched: number;
  analyzed: number;
  stored: number;
  filtered: number;
  errors: number;
}

export interface ProfilerResponse {
  success: boolean;
  result: {
    app_name: string;
    core_functions: string[];
    value_proposition: string;
    target_audience: string;
    // ... other fields
  };
}

export interface OpportunityScoreResponse {
  success: boolean;
  result: {
    final_score: number;
    market_demand: number;
    technical_feasibility: number;
    monetization_potential: number;
    // ... other fields
  };
}

// Error types
export interface APIError {
  detail: string;
  status_code: number;
}
```

---

### Task 2: Create API Client (2 days)

**Create**: `sdk/client/reddit-harbor-client.ts`

```typescript
/**
 * RedditHarbor API Client
 * 
 * Type-safe client for RedditHarbor unified pipeline API
 */

import type {
  PipelineRunRequest,
  PipelineRunResponse,
  ProfilerRequest,
  ProfilerResponse,
  OpportunityRequest,
  OpportunityScoreResponse,
  APIError,
} from '../types/api';

export interface RedditHarborClientConfig {
  apiUrl: string;
  apiKey: string;
  timeout?: number;
}

export class RedditHarborClient {
  private apiUrl: string;
  private apiKey: string;
  private timeout: number;

  constructor(config: RedditHarborClientConfig) {
    this.apiUrl = config.apiUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000; // 30 second default
  }

  /**
   * Run complete opportunity discovery pipeline
   */
  async runPipeline(request: PipelineRunRequest): Promise<PipelineRunResponse> {
    return this.post<PipelineRunResponse>('/api/v1/pipeline/run', request);
  }

  /**
   * Analyze submission with AI profiler
   */
  async analyzeWithProfiler(request: ProfilerRequest): Promise<ProfilerResponse> {
    return this.post<ProfilerResponse>('/api/v1/profiler/analyze', request);
  }

  /**
   * Score opportunity potential
   */
  async scoreOpportunity(request: OpportunityRequest): Promise<OpportunityScoreResponse> {
    return this.post<OpportunityScoreResponse>('/api/v1/opportunities/score', request);
  }

  /**
   * Analyze monetization potential
   */
  async analyzeMonetization(request: OpportunityRequest): Promise<any> {
    return this.post('/api/v1/monetization/analyze', request);
  }

  /**
   * Validate with trust layer
   */
  async validateTrust(request: OpportunityRequest): Promise<any> {
    return this.post('/api/v1/trust/validate', request);
  }

  /**
   * Perform market validation
   */
  async validateMarket(request: any): Promise<any> {
    return this.post('/api/v1/market/validate', request);
  }

  /**
   * Get pipeline status
   */
  async getPipelineStatus(pipelineId: string): Promise<any> {
    return this.get(`/api/v1/pipeline/${pipelineId}/status`);
  }

  /**
   * Get pipeline result
   */
  async getPipelineResult(pipelineId: string): Promise<any> {
    return this.get(`/api/v1/pipeline/${pipelineId}/result`);
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.get('/api/v1/health');
  }

  /**
   * Get application metrics
   */
  async getMetrics(): Promise<any> {
    return this.get('/api/v1/metrics');
  }

  /**
   * Generic POST request
   */
  private async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.apiUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
      },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      const error: APIError = await response.json();
      throw new Error(`API Error: ${error.detail || response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generic GET request
   */
  private async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.apiUrl}${endpoint}`, {
      method: 'GET',
      headers: {
        'X-API-Key': this.apiKey,
      },
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      const error: APIError = await response.json();
      throw new Error(`API Error: ${error.detail || response.statusText}`);
    }

    return response.json();
  }
}

// Default export
export default RedditHarborClient;
```

---

### Task 3: Create Integration Examples (1 day)

**Create**: `sdk/examples/nextjs-integration.md`

```markdown
# RedditHarbor SDK - Next.js Integration Guide

## Installation

### Option 1: Local Package (Development)
```bash
# In your Next.js project
npm install file:../reddit-harbor-core-functions-fix/sdk
```

### Option 2: Git Repository (Production)
```bash
npm install git+https://github.com/your-org/reddit-harbor-sdk.git
```

### Option 3: npm Package (If published)
```bash
npm install @reddit-harbor/sdk
```

## Setup

### 1. Environment Variables

Create `.env.local` in your Next.js project:

```env
NEXT_PUBLIC_REDDIT_HARBOR_API_URL=http://localhost:8000
REDDIT_HARBOR_API_KEY=your_secret_api_key_here
```

### 2. Initialize Client

```typescript
// lib/reddit-harbor.ts
import { RedditHarborClient } from '@reddit-harbor/sdk';

export const client = new RedditHarborClient({
  apiUrl: process.env.NEXT_PUBLIC_REDDIT_HARBOR_API_URL!,
  apiKey: process.env.REDDIT_HARBOR_API_KEY!,
  timeout: 30000,
});
```

## Usage Examples

### Example 1: API Route

```typescript
// app/api/analyze/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { client } from '@/lib/reddit-harbor';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const result = await client.analyzeWithProfiler({
      submission_id: body.submission_id,
      submission_title: body.title,
      submission_content: body.content,
      subreddit: body.subreddit,
    });
    
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
```

### Example 2: Server Component

```typescript
// app/opportunities/page.tsx
import { client } from '@/lib/reddit-harbor';

export default async function OpportunitiesPage() {
  const result = await client.runPipeline({
    source: 'database',
    limit: 50,
    config: {
      enable_profiler: true,
      enable_opportunity_scoring: true,
    },
  });

  return (
    <div>
      <h1>Opportunities ({result.stats.analyzed})</h1>
      {/* Render opportunities */}
    </div>
  );
}
```

### Example 3: Client Component with React Query

```typescript
// components/OpportunityAnalyzer.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { client } from '@/lib/reddit-harbor';

export function OpportunityAnalyzer({ submissionId }: { submissionId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['opportunity', submissionId],
    queryFn: async () => {
      return client.scoreOpportunity({
        submission_id: submissionId,
        title: 'Fetched from DB',
        content: 'Fetched from DB',
        subreddit: 'startups',
      });
    },
  });

  if (isLoading) return <div>Analyzing...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Opportunity Score: {data.result.final_score}</h2>
      {/* Render detailed scores */}
    </div>
  );
}
```

## Type Safety

The SDK provides full TypeScript support:

```typescript
import type {
  ProfilerRequest,
  ProfilerResponse,
  PipelineConfig,
} from '@reddit-harbor/sdk';

const request: ProfilerRequest = {
  submission_id: '123',
  submission_title: 'My App Idea',
  submission_content: 'Looking for...',
  subreddit: 'startups',
};

const response: ProfilerResponse = await client.analyzeWithProfiler(request);
// response is fully typed ✅
```

## Error Handling

```typescript
try {
  const result = await client.runPipeline(request);
} catch (error) {
  if (error instanceof Error) {
    console.error('Pipeline error:', error.message);
    // Handle specific error cases
  }
}
```

## Best Practices

1. **Use API Routes for sensitive operations** - Keep API key server-side
2. **Cache results** - Use React Query or SWR
3. **Handle errors gracefully** - Show user-friendly messages
4. **Type everything** - Leverage TypeScript for safety
5. **Monitor API usage** - Track costs and performance

## Next Steps

- See full API reference: `/sdk/docs/api-reference.md`
- View more examples: `/sdk/examples/`
- Check troubleshooting: `/sdk/docs/troubleshooting.md`
```

---

### Task 4: Package for Distribution (1 day)

**Create**: `sdk/package.json`

```json
{
  "name": "@reddit-harbor/sdk",
  "version": "2.0.0",
  "description": "TypeScript SDK for RedditHarbor unified pipeline API",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "README.md"
  ],
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "prepublishOnly": "npm run build"
  },
  "keywords": [
    "reddit",
    "opportunity",
    "ai",
    "pipeline"
  ],
  "author": "RedditHarbor Team",
  "license": "MIT",
  "dependencies": {},
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

**Create**: `sdk/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "declaration": true,
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["client/**/*", "types/**/*"],
  "exclude": ["node_modules", "dist", "examples"]
}
```

**Create**: `sdk/README.md`

```markdown
# RedditHarbor SDK

TypeScript SDK for the RedditHarbor unified opportunity discovery pipeline.

## Installation

```bash
npm install @reddit-harbor/sdk
```

## Quick Start

```typescript
import { RedditHarborClient } from '@reddit-harbor/sdk';

const client = new RedditHarborClient({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',
});

const result = await client.analyzeWithProfiler({
  submission_id: '123',
  submission_title: 'My App Idea',
  submission_content: 'Looking for...',
  subreddit: 'startups',
});

console.log(result.result.app_name);
```

## Documentation

See [Next.js Integration Guide](examples/nextjs-integration.md) for complete examples.

## Repository Structure

This SDK is part of the RedditHarbor monorepo but designed for consumption by separate Next.js applications.

**Main Repository**: `reddit-harbor-core-functions-fix` (FastAPI + Python pipeline)
**Next.js Application**: Separate repository (consumes this SDK)

## License

MIT
```

---

## Validation Checklist

### SDK Implementation
- [ ] TypeScript types complete and accurate
- [ ] Client class implements all endpoints
- [ ] Error handling comprehensive
- [ ] Type safety validated

### Integration Validation
- [ ] Create test Next.js project
- [ ] Install SDK locally
- [ ] Test all major operations
- [ ] Verify type safety works

### Documentation Validation
- [ ] README complete
- [ ] Integration examples provided
- [ ] Type definitions documented
- [ ] Next.js team can follow guide

---

## Rollback Procedure

```bash
rm -rf sdk/
# No impact on core system
```

---

## Next Phase

→ **[Phase 11: Production Migration](phase-11-production-migration.md)**

**Status**: ⏸️ NOT STARTED

---

## Notes

**IMPORTANT**: This phase creates the SDK for Next.js consumption, NOT the Next.js application itself.

The Next.js application lives in a **separate repository** and will:
1. Install this SDK as a dependency
2. Use the TypeScript client to call the FastAPI backend
3. Implement its own UI/UX separately
4. Follow its own deployment process

This approach ensures:
- ✅ Clean separation of concerns
- ✅ Independent deployment cycles
- ✅ Clear API boundaries
- ✅ Reusable SDK for other frontends
