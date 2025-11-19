/**
 * Opportunity Analysis API Route
 * Proxy to FastAPI backend for AI Profiler analysis
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

    // Forward request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/v1/profiler/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Forwarded-For': request.ip || 'unknown',
        'X-Real-IP': request.ip || 'unknown',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        {
          success: false,
          message: errorData.message || 'Profiler analysis failed',
          error_code: errorData.error_code || 'PROFILER_ERROR',
          details: errorData.details
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error('Opportunity analysis API error:', error);
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

    // Get search params from URL
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '100';
    const offset = searchParams.get('offset') || '0';
    const subreddit = searchParams.get('subreddit');
    const minScore = searchParams.get('min_score');

    // Build query string for backend
    const backendParams = new URLSearchParams({
      limit,
      offset,
      ...(subreddit && { subreddit }),
      ...(minScore && { min_score: minScore }),
    });

    // Forward request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/v1/data/fetch?${backendParams.toString()}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        table_name: 'opportunities_unified',
        filters: {
          ...(subreddit && { subreddit }),
          ...(minScore && { final_score: { gte: parseFloat(minScore) } }),
        },
        limit: parseInt(limit),
        offset: parseInt(offset),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        {
          success: false,
          message: errorData.message || 'Failed to fetch opportunities',
          error_code: errorData.error_code || 'FETCH_ERROR'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error('Opportunities fetch API error:', error);
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