/**
 * Pipeline Execution API Route
 * Proxy to FastAPI backend for pipeline orchestration
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// Helper function to get auth token from request
function getAuthToken(request: NextRequest): string | null {
  // Try to get token from Authorization header
  const authHeader = request.headers.get('authorization');
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  // Fallback to cookie
  const token = request.cookies.get('token')?.value;
  return token || null;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const token = getAuthToken(request);

    if (!token) {
      return NextResponse.json(
        {
          success: false,
          message: 'Authentication required',
          error_code: 'AUTH_REQUIRED'
        },
        { status: 401 }
      );
    }

    // Validate pipeline request
    if (!body.source || !['database', 'reddit'].includes(body.source)) {
      return NextResponse.json(
        {
          success: false,
          message: 'Invalid or missing source parameter',
          error_code: 'VALIDATION_ERROR'
        },
        { status: 400 }
      );
    }

    if (body.limit && (body.limit < 1 || body.limit > 1000)) {
      return NextResponse.json(
        {
          success: false,
          message: 'Limit must be between 1 and 1000',
          error_code: 'VALIDATION_ERROR'
        },
        { status: 400 }
      );
    }

    // Forward request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/v1/pipeline/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Forwarded-For': request.ip || 'unknown',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        {
          success: false,
          message: errorData.message || 'Pipeline execution failed',
          error_code: errorData.error_code || 'PIPELINE_ERROR',
          details: errorData.details
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error('Pipeline run API error:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Internal server error',
        error_code: 'INTERNAL_ERROR'
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const token = getAuthToken(request);

    if (!token) {
      return NextResponse.json(
        {
          success: false,
          message: 'Authentication required',
          error_code: 'AUTH_REQUIRED'
        },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const pipelineId = searchParams.get('pipeline_id');

    if (!pipelineId) {
      return NextResponse.json(
        {
          success: false,
          message: 'Pipeline ID required',
          error_code: 'VALIDATION_ERROR'
        },
        { status: 400 }
      );
    }

    // Check if requesting status or result
    const requestType = searchParams.get('type') || 'status';

    const endpoint = requestType === 'result'
      ? `${API_BASE_URL}/api/v1/pipeline/${pipelineId}/result`
      : `${API_BASE_URL}/api/v1/pipeline/${pipelineId}/status`;

    // Forward request to FastAPI backend
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        {
          success: false,
          message: errorData.message || 'Failed to get pipeline information',
          error_code: errorData.error_code || 'PIPELINE_FETCH_ERROR'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error('Pipeline status API error:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Internal server error',
        error_code: 'INTERNAL_ERROR'
      },
      { status: 500 }
    );
  }
}