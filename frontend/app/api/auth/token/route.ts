/**
 * Authentication Token API Route
 * Proxy to FastAPI backend for token authentication
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        {
          success: false,
          message: errorData.message || 'Authentication failed',
          error_code: errorData.error_code || 'AUTH_ERROR'
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Set HTTP-only cookie with token for secure storage
    const token = data.access_token;
    const responseHeaders = new Headers(response.headers);

    if (token) {
      responseHeaders.set(
        'Set-Cookie',
        `token=${token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=${data.expires_in || 3600}`
      );
    }

    return NextResponse.json(data, {
      status: response.status,
      headers: responseHeaders,
    });

  } catch (error) {
    console.error('Token API error:', error);
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