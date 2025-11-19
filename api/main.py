"""
RedditHarbor FastAPI Backend
Comprehensive REST API for the unified opportunity discovery pipeline

This FastAPI application provides:
- Individual AI service endpoints (profiler, opportunity scoring, monetization, trust, market validation)
- Pipeline orchestration endpoints
- Real-time WebSocket progress updates
- Authentication and authorization
- Rate limiting and request validation
- Error handling and logging
- CORS configuration for Next.js
- Background job processing
- File upload/download support
- OpenAPI documentation

Author: RedditHarbor AI Team
Version: 2.0.0
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import json
import os

from fastapi import (
    FastAPI, HTTPException, Depends, status, BackgroundTasks,
    WebSocket, WebSocketDisconnect, Request, Response, UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from supabase import create_client
import httpx
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown handlers"""

    # Startup
    logger.info("🚀 Starting RedditHarbor API v2.0.0...")

    # Initialize global resources
    app.state.redis_client = await redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        password=os.getenv('REDIS_PASSWORD', None),
        decode_responses=True
    )

    app.state.supabase_client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    app.state.active_websockets: Dict[str, WebSocket] = {}

    logger.info("✅ RedditHarbor API startup complete")

    yield

    # Shutdown
    logger.info("🛑 Shutting down RedditHarbor API...")

    if hasattr(app.state, 'redis_client'):
        await app.state.redis_client.close()

    logger.info("✅ RedditHarbor API shutdown complete")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="RedditHarbor API",
    description="Unified Opportunity Discovery Pipeline API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "profiler", "description": "AI Profiler service endpoints"},
        {"name": "opportunities", "description": "Opportunity scoring endpoints"},
        {"name": "monetization", "description": "Monetization analysis endpoints"},
        {"name": "trust", "description": "Trust validation endpoints"},
        {"name": "market", "description": "Market validation endpoints"},
        {"name": "pipeline", "description": "Pipeline orchestration endpoints"},
        {"name": "data", "description": "Data fetching and storage endpoints"},
        {"name": "monitoring", "description": "Health and monitoring endpoints"},
    ]
)

# Rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "http://localhost:3001",  # Alternative Next.js port
        "https://your-nextjs-domain.com",  # Production Next.js
        "https://vercel.app",  # Vercel deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security
security = HTTPBearer()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

# Base Models
class BaseResponse(BaseModel):
    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseResponse):
    success: bool = False
    error_code: str
    details: Optional[Dict[str, Any]] = None

# Authentication Models
class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseResponse):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    permissions: List[str]

# Profiler Models
class ProfilerRequest(BaseModel):
    submission_id: str
    submission_title: str
    submission_content: str
    subreddit: str
    author: Optional[str] = None
    score: Optional[int] = 0
    num_comments: Optional[int] = 0

    @validator('submission_content')
    def validate_content_length(cls, v):
        if len(v) > 10000:
            raise ValueError('Content too long (max 10,000 characters)')
        return v

class ProfilerResponse(BaseResponse):
    submission_id: str
    app_name: Optional[str]
    app_concept: Optional[str]
    problem_description: Optional[str]
    core_functions: List[str] = []
    value_proposition: Optional[str]
    target_user: Optional[str]
    monetization_model: Optional[str]
    ai_confidence: Optional[float]
    cost_tracking: Optional[Dict[str, Any]]
    evidence_validation: Optional[Dict[str, Any]]

# Opportunity Scoring Models
class OpportunityRequest(BaseModel):
    submission_id: str
    title: str
    content: str
    subreddit: str
    author: Optional[str] = None
    score: Optional[int] = 0
    num_comments: Optional[int] = 0
    created_utc: Optional[str] = None

class OpportunityResponse(BaseResponse):
    submission_id: str
    market_demand_score: float
    pain_intensity_score: float
    monetization_potential_score: float
    market_gap_score: float
    technical_feasibility_score: float
    simplicity_score: float
    final_score: float
    reasoning: Optional[str]
    evidence_summary: Optional[Dict[str, Any]]

# Monetization Models
class MonetizationRequest(BaseModel):
    submission_id: str
    title: str
    content: str
    subreddit: str
    existing_analysis: Optional[Dict[str, Any]] = None

class MonetizationResponse(BaseResponse):
    submission_id: str
    llm_monetization_score: float
    customer_segment: Optional[str]
    willingness_to_pay_score: float
    price_sensitivity_score: float
    revenue_potential_score: float
    payment_sentiment: Optional[str]
    urgency_level: Optional[str]
    existing_payment_behavior: Optional[List[str]]
    mentioned_price_points: Optional[List[str]]
    payment_friction_indicators: Optional[List[str]]
    confidence: Optional[float]
    reasoning: Optional[str]

# Trust Validation Models
class TrustRequest(BaseModel):
    submission_id: str
    title: str
    content: str
    subreddit: str
    author: Optional[str] = None
    score: Optional[int] = 0
    num_comments: Optional[int] = 0
    created_utc: Optional[str] = None

class TrustResponse(BaseResponse):
    submission_id: str
    trust_score: float
    engagement_level: Optional[str]
    problem_validity: Optional[str]
    discussion_quality: Optional[str]
    ai_confidence_level: Optional[str]
    trust_factors: Optional[Dict[str, Any]]

# Market Validation Models
class MarketValidationRequest(BaseModel):
    submission_id: str
    app_concept: Optional[str]
    problem_description: Optional[str]
    target_competitors: Optional[List[str]] = []

class MarketValidationResponse(BaseResponse):
    submission_id: str
    market_validation_score: float
    competitor_analysis: Optional[Dict[str, Any]]
    market_evidence: Optional[Dict[str, Any]]
    validation_summary: Optional[str]
    confidence: Optional[float]

# Pipeline Models
class PipelineConfig(BaseModel):
    enable_profiler: bool = True
    enable_opportunity_scoring: bool = True
    enable_monetization: bool = True
    enable_trust: bool = True
    enable_market_validation: bool = True
    ai_profile_threshold: float = 40.0
    monetization_threshold: float = 60.0
    market_validation_threshold: float = 60.0

class PipelineRequest(BaseModel):
    source: str = Field(..., description="Data source: 'database' or 'reddit'")
    limit: int = Field(100, ge=1, le=1000, description="Number of submissions to process")
    subreddits: Optional[List[str]] = Field(None, description="Subreddits for Reddit API source")
    config: PipelineConfig = Field(default_factory=PipelineConfig)
    test_mode: bool = Field(False, description="Run in test mode without persistent storage")

class PipelineResponse(BaseResponse):
    pipeline_id: str
    status: str
    stats: Dict[str, Any]
    summary: Optional[str]
    opportunities: Optional[List[Dict[str, Any]]]

class PipelineStatusResponse(BaseResponse):
    pipeline_id: str
    status: str
    progress: float
    current_step: str
    stats: Dict[str, Any]
    errors: List[str] = []
    started_at: datetime
    estimated_completion: Optional[datetime]

# Data Models
class DataFetchRequest(BaseModel):
    table_name: str
    filters: Optional[Dict[str, Any]] = {}
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class DataFetchResponse(BaseResponse):
    table_name: str
    data: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int

class FileUploadResponse(BaseResponse):
    filename: str
    file_size: int
    upload_url: Optional[str]
    processing_status: str

# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Validate JWT token and return user information"""

    try:
        # Here you would validate the JWT token
        # For now, we'll use a simple implementation
        token = credentials.credentials

        # Check if token is in Redis cache
        cached_user = await app.state.redis_client.get(f"token:{token}")
        if cached_user:
            return json.loads(cached_user)

        # Validate token with Supabase or your auth provider
        # This is a placeholder - implement actual token validation
        if not token or token == "invalid":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Mock user data - replace with actual user lookup
        user_data = {
            "user_id": "user_123",
            "username": "demo_user",
            "permissions": ["read", "write", "pipeline:run"],
            "subscription_tier": "pro"
        }

        # Cache user data
        await app.state.redis_client.setex(
            f"token:{token}",
            timedelta(hours=1),
            json.dumps(user_data)
        )

        return user_data

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return permission_dependency

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def fetch_submission_from_db(submission_id: str) -> Optional[Dict[str, Any]]:
    """Fetch submission from database"""
    try:
        response = app.state.supabase_client.table("submissions").select(
            "*"
        ).eq("submission_id", submission_id).execute()

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        logger.error(f"Error fetching submission {submission_id}: {e}")
        return None

async def cache_result(key: str, data: Any, ttl: int = 3600):
    """Cache result in Redis"""
    try:
        await app.state.redis_client.setex(
            key,
            ttl,
            json.dumps(data, default=str)
        )
    except Exception as e:
        logger.error(f"Cache error: {e}")

async def get_cached_result(key: str) -> Optional[Any]:
    """Get cached result from Redis"""
    try:
        cached = await app.state.redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        logger.error(f"Cache error: {e}")
        return None

def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """Create standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            success=False,
            message=message,
            error_code=error_code,
            details=details
        ).dict()
    )

async def broadcast_to_websockets(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    disconnected_clients = []

    for client_id, websocket in app.state.active_websockets.items():
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected_clients.append(client_id)

    # Clean up disconnected clients
    for client_id in disconnected_clients:
        del app.state.active_websockets[client_id]

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/auth/token", response_model=TokenResponse, tags=["auth"])
@limiter.limit("10/minute")
async def authenticate_token(request: Request, token_req: TokenRequest):
    """Authenticate user and return JWT token"""
    try:
        # Implement actual authentication logic
        # This is a placeholder implementation

        if token_req.username == "demo" and token_req.password == "demo":
            # Generate mock token
            token = str(uuid.uuid4())

            user_data = {
                "user_id": "user_123",
                "username": token_req.username,
                "permissions": ["read", "write", "pipeline:run"],
                "subscription_tier": "pro"
            }

            # Cache token
            await cache_result(f"token:{token}", user_data, ttl=3600)

            return TokenResponse(
                success=True,
                message="Authentication successful",
                access_token=token,
                expires_in=3600,
                user_id=user_data["user_id"],
                permissions=user_data["permissions"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

# ============================================================================
# AI PROFILER ENDPOINTS
# ============================================================================

@app.post("/api/v1/profiler/analyze", response_model=ProfilerResponse, tags=["profiler"])
@limiter.limit("20/minute")
async def analyze_with_profiler(
    request: Request,
    profiler_req: ProfilerRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze submission with AI Profiler (EnhancedLLMProfiler)"""
    try:
        # Check cache first
        cache_key = f"profiler:{profiler_req.submission_id}"
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return ProfilerResponse(**cached_result)

        # Import and use ProfilerService
        try:
            from core.enrichment.profiler_service import ProfilerService

            profiler_service = ProfilerService(app.state.supabase_client)
            submission_data = profiler_req.dict()

            # Run profiler analysis
            result = await asyncio.to_thread(
                profiler_service.enrich,
                submission_data
            )

            response = ProfilerResponse(
                success=True,
                message="AI profiling completed successfully",
                submission_id=profiler_req.submission_id,
                app_name=result.get("app_name"),
                app_concept=result.get("app_concept"),
                problem_description=result.get("problem_description"),
                core_functions=result.get("core_functions", []),
                value_proposition=result.get("value_proposition"),
                target_user=result.get("target_user"),
                monetization_model=result.get("monetization_model"),
                ai_confidence=result.get("ai_confidence"),
                cost_tracking=result.get("cost_tracking"),
                evidence_validation=result.get("evidence_validation")
            )

            # Cache result
            await cache_result(cache_key, response.dict(), ttl=86400)

            return response

        except ImportError as e:
            logger.error(f"Profiler service import error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Profiler service not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profiler analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profiler analysis failed: {str(e)}"
        )

# ============================================================================
# OPPORTUNITY SCORING ENDPOINTS
# ============================================================================

@app.post("/api/v1/opportunities/score", response_model=OpportunityResponse, tags=["opportunities"])
@limiter.limit("20/minute")
async def score_opportunity(
    request: Request,
    opportunity_req: OpportunityRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Score opportunity with OpportunityAnalyzerAgent"""
    try:
        # Check cache first
        cache_key = f"opportunity:{opportunity_req.submission_id}"
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return OpportunityResponse(**cached_result)

        # Import and use OpportunityService
        try:
            from core.enrichment.opportunity_service import OpportunityService

            opportunity_service = OpportunityService(app.state.supabase_client)
            submission_data = opportunity_req.dict()

            # Run opportunity scoring
            result = await asyncio.to_thread(
                opportunity_service.enrich,
                submission_data
            )

            response = OpportunityResponse(
                success=True,
                message="Opportunity scoring completed successfully",
                submission_id=opportunity_req.submission_id,
                market_demand_score=result.get("market_demand_score", 0.0),
                pain_intensity_score=result.get("pain_intensity_score", 0.0),
                monetization_potential_score=result.get("monetization_potential_score", 0.0),
                market_gap_score=result.get("market_gap_score", 0.0),
                technical_feasibility_score=result.get("technical_feasibility_score", 0.0),
                simplicity_score=result.get("simplicity_score", 0.0),
                final_score=result.get("final_score", 0.0),
                reasoning=result.get("reasoning"),
                evidence_summary=result.get("evidence_summary")
            )

            # Cache result
            await cache_result(cache_key, response.dict(), ttl=86400)

            return response

        except ImportError as e:
            logger.error(f"Opportunity service import error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Opportunity service not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Opportunity scoring error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Opportunity scoring failed: {str(e)}"
        )

# ============================================================================
# MONETIZATION ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/v1/monetization/analyze", response_model=MonetizationResponse, tags=["monetization"])
@limiter.limit("15/minute")
async def analyze_monetization(
    request: Request,
    monetization_req: MonetizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze monetization potential with MonetizationAgnoAnalyzer"""
    try:
        # Check cache first
        cache_key = f"monetization:{monetization_req.submission_id}"
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return MonetizationResponse(**cached_result)

        # Import and use MonetizationService
        try:
            from core.enrichment.monetization_service import MonetizationService

            monetization_service = MonetizationService(app.state.supabase_client)
            submission_data = monetization_req.dict()

            # Run monetization analysis
            result = await asyncio.to_thread(
                monetization_service.enrich,
                submission_data
            )

            response = MonetizationResponse(
                success=True,
                message="Monetization analysis completed successfully",
                submission_id=monetization_req.submission_id,
                llm_monetization_score=result.get("llm_monetization_score", 0.0),
                customer_segment=result.get("customer_segment"),
                willingness_to_pay_score=result.get("willingness_to_pay_score", 0.0),
                price_sensitivity_score=result.get("price_sensitivity_score", 0.0),
                revenue_potential_score=result.get("revenue_potential_score", 0.0),
                payment_sentiment=result.get("payment_sentiment"),
                urgency_level=result.get("urgency_level"),
                existing_payment_behavior=result.get("existing_payment_behavior", []),
                mentioned_price_points=result.get("mentioned_price_points", []),
                payment_friction_indicators=result.get("payment_friction_indicators", []),
                confidence=result.get("confidence"),
                reasoning=result.get("reasoning")
            )

            # Cache result
            await cache_result(cache_key, response.dict(), ttl=86400)

            return response

        except ImportError as e:
            logger.error(f"Monetization service import error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Monetization service not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Monetization analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Monetization analysis failed: {str(e)}"
        )

# ============================================================================
# TRUST VALIDATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/trust/validate", response_model=TrustResponse, tags=["trust"])
@limiter.limit("20/minute")
async def validate_trust(
    request: Request,
    trust_req: TrustRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate trust with TrustLayerValidator"""
    try:
        # Check cache first
        cache_key = f"trust:{trust_req.submission_id}"
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return TrustResponse(**cached_result)

        # Import and use TrustService
        try:
            from core.enrichment.trust_service import TrustService

            trust_service = TrustService(app.state.supabase_client)
            submission_data = trust_req.dict()

            # Run trust validation
            result = await asyncio.to_thread(
                trust_service.enrich,
                submission_data
            )

            response = TrustResponse(
                success=True,
                message="Trust validation completed successfully",
                submission_id=trust_req.submission_id,
                trust_score=result.get("trust_score", 0.0),
                engagement_level=result.get("engagement_level"),
                problem_validity=result.get("problem_validity"),
                discussion_quality=result.get("discussion_quality"),
                ai_confidence_level=result.get("ai_confidence_level"),
                trust_factors=result.get("trust_factors")
            )

            # Cache result
            await cache_result(cache_key, response.dict(), ttl=86400)

            return response

        except ImportError as e:
            logger.error(f"Trust service import error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trust service not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trust validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trust validation failed: {str(e)}"
        )

# ============================================================================
# MARKET VALIDATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/market/validate", response_model=MarketValidationResponse, tags=["market"])
@limiter.limit("10/minute")
async def validate_market(
    request: Request,
    market_req: MarketValidationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate market with MarketDataValidator"""
    try:
        # Check cache first
        cache_key = f"market:{market_req.submission_id}"
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return MarketValidationResponse(**cached_result)

        # Import and use MarketValidationService
        try:
            from core.enrichment.market_validation_service import MarketValidationService

            market_service = MarketValidationService()
            submission_data = market_req.dict()

            # Run market validation
            result = await asyncio.to_thread(
                market_service.enrich,
                submission_data
            )

            response = MarketValidationResponse(
                success=True,
                message="Market validation completed successfully",
                submission_id=market_req.submission_id,
                market_validation_score=result.get("market_validation_score", 0.0),
                competitor_analysis=result.get("competitor_analysis"),
                market_evidence=result.get("market_evidence"),
                validation_summary=result.get("validation_summary"),
                confidence=result.get("confidence")
            )

            # Cache result
            await cache_result(cache_key, response.dict(), ttl=86400)

            return response

        except ImportError as e:
            logger.error(f"Market validation service import error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Market validation service not available"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Market validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market validation failed: {str(e)}"
        )

# ============================================================================
# PIPELINE ORCHESTRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/pipeline/run", response_model=PipelineResponse, tags=["pipeline"])
@limiter.limit("5/minute")
async def run_pipeline(
    request: Request,
    pipeline_req: PipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("pipeline:run"))
):
    """Run full opportunity discovery pipeline"""
    try:
        # Generate pipeline ID
        pipeline_id = str(uuid.uuid4())

        # Initialize pipeline status in Redis
        pipeline_status = {
            "pipeline_id": pipeline_id,
            "status": "initializing",
            "progress": 0.0,
            "current_step": "Setting up pipeline",
            "stats": {},
            "errors": [],
            "started_at": datetime.utcnow().isoformat(),
            "estimated_completion": None,
            "user_id": current_user["user_id"]
        }

        await cache_result(f"pipeline:{pipeline_id}", pipeline_status, ttl=3600)

        # Start pipeline in background
        background_tasks.add_task(
            run_pipeline_background,
            pipeline_id,
            pipeline_req.dict(),
            current_user
        )

        # Broadcast WebSocket notification
        await broadcast_to_websockets({
            "type": "pipeline_started",
            "pipeline_id": pipeline_id,
            "status": "initializing"
        })

        return PipelineResponse(
            success=True,
            message="Pipeline started successfully",
            pipeline_id=pipeline_id,
            status="running",
            stats={},
            summary="Pipeline execution started in background"
        )

    except Exception as e:
        logger.error(f"Pipeline start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start pipeline: {str(e)}"
        )

async def run_pipeline_background(
    pipeline_id: str,
    pipeline_config: Dict[str, Any],
    current_user: Dict[str, Any]
):
    """Background task to run pipeline"""
    try:
        # Import pipeline orchestrator
        from core.pipeline.orchestrator import OpportunityPipeline
        from core.fetchers.database_fetcher import DatabaseFetcher
        from core.fetchers.reddit_api_fetcher import RedditAPIFetcher

        # Update status
        await update_pipeline_status(pipeline_id, "setting_up", 0.1, "Initializing pipeline components")

        # Configure fetcher based on source
        if pipeline_config["source"] == "database":
            fetcher = DatabaseFetcher(app.state.supabase_client)
        elif pipeline_config["source"] == "reddit":
            fetcher = RedditAPIFetcher(
                subreddits=pipeline_config.get("subreddits", [])
            )
        else:
            raise ValueError(f"Invalid source: {pipeline_config['source']}")

        # Create pipeline
        pipeline = OpportunityPipeline(
            fetcher=fetcher,
            supabase_client=app.state.supabase_client,
            **pipeline_config["config"]
        )

        # Update status
        await update_pipeline_status(pipeline_id, "running", 0.2, "Starting data fetch")

        # Run pipeline
        result = await asyncio.to_thread(
            pipeline.run,
            limit=pipeline_config["limit"],
            test_mode=pipeline_config.get("test_mode", False)
        )

        # Update final status
        await update_pipeline_status(
            pipeline_id,
            "completed" if result["success"] else "failed",
            1.0,
            "Pipeline execution completed"
        )

        # Cache final result
        await cache_result(f"pipeline_result:{pipeline_id}", result, ttl=86400)

        # Broadcast completion
        await broadcast_to_websockets({
            "type": "pipeline_completed",
            "pipeline_id": pipeline_id,
            "status": "completed" if result["success"] else "failed",
            "result": result
        })

    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        await update_pipeline_status(
            pipeline_id,
            "failed",
            1.0,
            f"Pipeline failed: {str(e)}"
        )

        # Broadcast error
        await broadcast_to_websockets({
            "type": "pipeline_error",
            "pipeline_id": pipeline_id,
            "status": "failed",
            "error": str(e)
        })

async def update_pipeline_status(
    pipeline_id: str,
    status: str,
    progress: float,
    current_step: str,
    error: Optional[str] = None
):
    """Update pipeline status in Redis"""
    try:
        # Get existing status
        cached = await get_cached_result(f"pipeline:{pipeline_id}")
        if cached:
            pipeline_status = cached
        else:
            pipeline_status = {
                "pipeline_id": pipeline_id,
                "stats": {},
                "errors": []
            }

        # Update status
        pipeline_status.update({
            "status": status,
            "progress": progress,
            "current_step": current_step
        })

        if error:
            pipeline_status["errors"].append(error)

        # Calculate estimated completion
        if progress > 0:
            started_at = datetime.fromisoformat(pipeline_status.get("started_at", datetime.utcnow().isoformat()))
            elapsed = (datetime.utcnow() - started_at).total_seconds()
            estimated_total = elapsed / progress
            pipeline_status["estimated_completion"] = (started_at + timedelta(seconds=estimated_total)).isoformat()

        # Cache updated status
        await cache_result(f"pipeline:{pipeline_id}", pipeline_status, ttl=3600)

    except Exception as e:
        logger.error(f"Error updating pipeline status: {e}")

@app.get("/api/v1/pipeline/{pipeline_id}/status", response_model=PipelineStatusResponse, tags=["pipeline"])
@limiter.limit("30/minute")
async def get_pipeline_status(
    pipeline_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get pipeline execution status"""
    try:
        cached_status = await get_cached_result(f"pipeline:{pipeline_id}")
        if not cached_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found"
            )

        return PipelineStatusResponse(**cached_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline status: {str(e)}"
        )

@app.get("/api/v1/pipeline/{pipeline_id}/result", tags=["pipeline"])
@limiter.limit("10/minute")
async def get_pipeline_result(
    pipeline_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get pipeline execution result"""
    try:
        cached_result = await get_cached_result(f"pipeline_result:{pipeline_id}")
        if not cached_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline result not found"
            )

        return cached_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline result: {str(e)}"
        )

# ============================================================================
# WEBSOCKET ENDPOINT FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/pipeline/{pipeline_id}")
async def websocket_pipeline_updates(websocket: WebSocket, pipeline_id: str):
    """WebSocket endpoint for real-time pipeline updates"""
    await websocket.accept()

    client_id = str(uuid.uuid4())
    app.state.active_websockets[client_id] = websocket

    try:
        # Send initial status
        cached_status = await get_cached_result(f"pipeline:{pipeline_id}")
        if cached_status:
            await websocket.send_json({
                "type": "pipeline_status",
                "data": cached_status
            })

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client message with timeout
                message = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)

                # Handle client message (could be ping, unsubscribe, etc.)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "unsubscribe":
                    break

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        if client_id in app.state.active_websockets:
            del app.state.active_websockets[client_id]

# ============================================================================
# DATA FETCHING ENDPOINTS
# ============================================================================

@app.post("/api/v1/data/fetch", response_model=DataFetchResponse, tags=["data"])
@limiter.limit("50/minute")
async def fetch_data(
    request: Request,
    data_req: DataFetchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Fetch data from Supabase tables"""
    try:
        # Validate table name
        allowed_tables = [
            "submissions", "comments", "redditors",
            "opportunities_unified", "llm_monetization_analysis",
            "business_concepts", "app_opportunities"
        ]

        if data_req.table_name not in allowed_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Table {data_req.table_name} not allowed"
            )

        # Build query
        query = app.state.supabase_client.table(data_req.table_name).select("*")

        # Apply filters
        for field, value in data_req.filters.items():
            if isinstance(value, dict):
                if "gt" in value:
                    query = query.gt(field, value["gt"])
                elif "gte" in value:
                    query = query.gte(field, value["gte"])
                elif "lt" in value:
                    query = query.lt(field, value["lt"])
                elif "lte" in value:
                    query = query.lte(field, value["lte"])
                elif "in" in value:
                    query = query.in_(field, value["in"])
                elif "like" in value:
                    query = query.like(field, value["like"])
            else:
                query = query.eq(field, value)

        # Apply pagination
        query = query.range(data_req.offset, data_req.offset + data_req.limit - 1)

        # Execute query
        result = query.execute()

        # Get total count
        count_query = app.state.supabase_client.table(data_req.table_name).select("id", count="exact")
        for field, value in data_req.filters.items():
            if isinstance(value, dict):
                # Apply same filters for count
                pass
            else:
                count_query = count_query.eq(field, value)

        count_result = count_query.execute()
        total_count = count_result.count if count_result.count else len(result.data)

        return DataFetchResponse(
            success=True,
            message="Data fetched successfully",
            table_name=data_req.table_name,
            data=result.data or [],
            total_count=total_count,
            limit=data_req.limit,
            offset=data_req.offset
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data fetch failed: {str(e)}"
        )

# ============================================================================
# FILE UPLOAD/DOWNLOAD ENDPOINTS
# ============================================================================

@app.post("/api/v1/files/upload", response_model=FileUploadResponse, tags=["data"])
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload file for processing"""
    try:
        # Validate file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 10MB)"
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Save file (implement your file storage logic)
        upload_path = f"uploads/{unique_filename}"

        # For now, just return upload info
        # In production, you'd save to S3, Google Cloud Storage, etc.

        return FileUploadResponse(
            success=True,
            message="File uploaded successfully",
            filename=unique_filename,
            file_size=file_size,
            upload_url=f"/api/v1/files/download/{unique_filename}",
            processing_status="uploaded"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

# ============================================================================
# MONITORING AND HEALTH ENDPOINTS
# ============================================================================

@app.get("/api/v1/health", tags=["monitoring"])
@limiter.limit("100/minute")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        try:
            db_health = app.state.supabase_client.table("submissions").select("id").limit(1).execute()
            db_status = "healthy" if db_health.data is not None else "unhealthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check Redis connection
        try:
            await app.state.redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"

        # Check active WebSocket connections
        active_connections = len(app.state.active_websockets)

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "services": {
                "database": db_status,
                "redis": redis_status,
                "websockets": {
                    "active_connections": active_connections,
                    "status": "healthy" if active_connections >= 0 else "unhealthy"
                }
            }
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/api/v1/metrics", tags=["monitoring"])
@limiter.limit("30/minute")
async def get_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get application metrics"""
    try:
        # Get basic counts from database
        metrics = {}

        # Submissions count
        submissions_count = app.state.supabase_client.table("submissions").select("id", count="exact").execute()
        metrics["total_submissions"] = submissions_count.count or 0

        # Opportunities count
        opportunities_count = app.state.supabase_client.table("opportunities_unified").select("id", count="exact").execute()
        metrics["total_opportunities"] = opportunities_count.count or 0

        # Business concepts count
        concepts_count = app.state.supabase_client.table("business_concepts").select("id", count="exact").execute()
        metrics["total_concepts"] = concepts_count.count or 0

        # Redis info
        redis_info = await app.state.redis_client.info()
        metrics["redis"] = {
            "connected_clients": redis_info.get("connected_clients", 0),
            "used_memory": redis_info.get("used_memory_human", "unknown"),
            "total_commands_processed": redis_info.get("total_commands_processed", 0)
        }

        # Active pipelines
        pipeline_keys = await app.state.redis_client.keys("pipeline:*")
        metrics["active_pipelines"] = len(pipeline_keys)

        return {
            "success": True,
            "message": "Metrics retrieved successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return create_error_response(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"exception": str(exc)},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# ============================================================================
# CUSTOM OPENAPI SCHEMA
# ============================================================================

def custom_openapi():
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="RedditHarbor API",
        version="2.0.0",
        description="Unified Opportunity Discovery Pipeline API",
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # Add security requirement to all endpoints except auth
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method not in ["get", "post", "put", "delete"]:
                continue
            if "/auth/" not in path and "/health" not in path:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )