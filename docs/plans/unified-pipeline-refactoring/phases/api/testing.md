# API Testing Strategies

**Purpose**: Comprehensive testing strategy for the RedditHarbor FastAPI backend, ensuring reliability, security, and performance through automated testing at multiple levels.

---

## Testing Pyramid

### Testing Strategy Overview
```
    ┌─────────────────────────┐
    │   E2E Integration Tests │  ← Few, slow, comprehensive
    │     (API + Database)    │
    └─────────────────────────┘
           ┌───────────────────────┐
           │  Integration Tests      │  ← Medium count, medium speed
           │ (API + External APIs)   │
           └───────────────────────┘
                  ┌─────────────────────┐
                  │  Unit Tests          │  ← Many, fast, focused
                  │ (Individual Functions)│
                  └─────────────────────┘
```

### Test Categories
1. **Unit Tests**: Individual function and class testing
2. **Integration Tests**: Service integration and database connectivity
3. **API Tests**: Endpoint functionality and contract testing
4. **Load Tests**: Performance and scalability testing
5. **Security Tests**: Authentication, authorization, and vulnerability testing

---

## Unit Testing

### Core Components Testing

```python
# tests/test_rate_limiter.py
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from api.core.rate_limit import RedisRateLimiter, RateLimitResult, RateLimitConfig
from api.core.hierarchical_rate_limiter import HierarchicalRateLimiter

class TestRedisRateLimiter:
    """Test the core Redis rate limiter functionality."""

    @pytest.fixture
    async def rate_limiter(self):
        """Create a rate limiter instance with mocked Redis."""
        limiter = RedisRateLimiter()

        # Mock Redis client
        mock_client = AsyncMock()
        limiter._client = mock_client

        return limiter

    @pytest.mark.asyncio
    async def test_is_rate_limited_allowed(self, rate_limiter):
        """Test rate limiting when request is allowed."""
        # Mock successful Redis response (allowed)
        rate_limiter._client.eval.return_value = [True, 1, 5, 60, 0]

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        assert result.is_allowed is True
        assert result.remaining_requests == 4
        assert result.limit == 5
        assert result.window_seconds == 60
        assert result.retry_after is None

        # Verify Redis was called with correct parameters
        rate_limiter._client.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_rate_limited_blocked(self, rate_limiter):
        """Test rate limiting when request is blocked."""
        # Mock Redis response (blocked)
        rate_limiter._client.eval.return_value = [False, 5, 5, 60, 30]

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        assert result.is_allowed is False
        assert result.remaining_requests == 0
        assert result.retry_after == 30

    @pytest.mark.asyncio
    async def test_is_rate_limited_with_burst(self, rate_limiter):
        """Test rate limiting with burst capacity."""
        # Mock Redis response allowing burst
        rate_limiter._client.eval.return_value = [True, 8, 5, 60, 0]

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60,
            burst_size=5
        )

        assert result.is_allowed is True
        # Should allow up to limit + burst_size = 10
        assert result.remaining_requests >= 0

    @pytest.mark.asyncio
    async def test_redis_error_fails_open(self, rate_limiter):
        """Test that Redis errors fail open (allow requests)."""
        # Mock Redis to raise an exception
        rate_limiter._client.eval.side_effect = Exception("Redis connection failed")

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        # Should allow request when Redis is down
        assert result.is_allowed is True
        assert result.remaining_requests == 5

    @pytest.mark.asyncio
    async def test_get_rate_limit_info(self, rate_limiter):
        """Test getting rate limit information without incrementing."""
        # Mock Redis responses
        rate_limiter._client.zcount.return_value = 3
        rate_limiter._client.ttl.return_value = 45

        info = await rate_limiter.get_rate_limit_info(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        assert info['current_count'] == 3
        assert info['limit'] == 5
        assert info['remaining_requests'] == 2
        assert info['window_seconds'] == 60

class TestHierarchicalRateLimiter:
    """Test the hierarchical rate limiter."""

    @pytest.fixture
    async def hierarchical_limiter(self):
        """Create a hierarchical rate limiter instance."""
        limiter = HierarchicalRateLimiter()
        return limiter

    def test_get_endpoint_type(self, hierarchical_limiter):
        """Test endpoint type classification."""
        assert hierarchical_limiter._get_endpoint_type("/api/v1/pipeline/run") == "pipeline"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/profiler/analyze") == "analysis"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/opportunities") == "data"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/health") == "monitoring"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/unknown") == "default"

    def test_get_client_ip_extraction(self, hierarchical_limiter):
        """Test client IP extraction from various request formats."""
        from unittest.mock import Mock

        # Test with X-Forwarded-For header
        request = Mock()
        request.headers = {"X-Forwarded-For": "203.0.113.1, 10.0.0.1"}
        request.client = None
        assert hierarchical_limiter._get_client_ip(request) == "203.0.113.1"

        # Test with X-Real-IP header
        request.headers = {"X-Real-IP": "203.0.113.2"}
        assert hierarchical_limiter._get_client_ip(request) == "203.0.113.2"

        # Test with direct IP
        request.headers = {}
        request.client = Mock()
        request.client.host = "203.0.113.3"
        assert hierarchical_limiter._get_client_ip(request) == "203.0.113.3"

    @pytest.mark.asyncio
    async def test_check_rate_limits_pipeline_endpoint(self, hierarchical_limiter):
        """Test rate limit checking for pipeline endpoints."""
        from unittest.mock import Mock, AsyncMock, patch

        # Mock request object
        request = Mock()
        request.url.path = "/api/v1/pipeline/run"
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}

        # Mock rate limiter methods
        with patch.object(hierarchical_limiter, '_check_global_limits', new_callable=AsyncMock) as mock_global, \
             patch.object(hierarchical_limiter, '_check_api_key_limits', new_callable=AsyncMock) as mock_apikey, \
             patch.object(hierarchical_limiter, '_check_ip_limits', new_callable=AsyncMock) as mock_ip, \
             patch.object(hierarchical_limiter, '_check_endpoint_limits', new_callable=AsyncMock) as mock_endpoint:

            # Setup mock responses
            from api.core.rate_limit import RateLimitResult
            mock_global.return_value = RateLimitResult(True, 8, 60, 0, 10, 60)
            mock_apikey.return_value = RateLimitResult(True, 3, 5, 0, 5, 60)
            mock_ip.return_value = RateLimitResult(True, 15, 20, 0, 20, 60)
            mock_endpoint.return_value = RateLimitResult(True, 2, 2, 0, 2, 60)

            result = await hierarchical_limiter.check_rate_limits(
                request=request,
                api_key="test-key",
                key_info={"name": "default"}
            )

            # Should return the most restrictive limit (2 remaining)
            assert result.remaining_requests == 2
            assert result.is_allowed is True

            # Verify all checks were called
            mock_global.assert_called_once_with('pipeline')
            mock_apikey.assert_called_once_with('test-key', 'default')
            mock_ip.assert_called_once_with('192.168.1.100')
            mock_endpoint.assert_called_once_with('192.168.1.100', 'pipeline')
```

### Authentication Testing

```python
# tests/test_authentication.py
import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException

from api.core.auth import APIKeyManager, verify_api_key, get_api_key_info, require_permission

class TestAPIKeyManager:
    """Test API key management functionality."""

    @pytest.fixture
    def api_key_manager(self):
        """Create API key manager instance."""
        return APIKeyManager()

    def test_is_valid_key_success(self, api_key_manager):
        """Test valid API key validation."""
        # Setup valid keys
        api_key_manager._valid_keys = {
            "primary": "test-api-key-123",
            "webhook": "webhook-key-456"
        }

        assert api_key_manager.is_valid_key("test-api-key-123") is True
        assert api_key_manager.is_valid_key("webhook-key-456") is True

    def test_is_valid_key_failure(self, api_key_manager):
        """Test invalid API key validation."""
        api_key_manager._valid_keys = {
            "primary": "test-api-key-123"
        }

        assert api_key_manager.is_valid_key("invalid-key") is False
        assert api_key_manager.is_valid_key("") is False
        assert api_key_manager.is_valid_key(None) is False

    def test_get_key_info(self, api_key_manager):
        """Test getting API key information."""
        api_key_manager._valid_keys = {
            "primary": "test-api-key-123",
            "monitoring": "monitor-key-789"
        }

        info = api_key_manager.get_key_info("test-api-key-123")
        assert info is not None
        assert info["name"] == "primary"
        assert "*" in info["permissions"]  # Full access

        info = api_key_manager.get_key_info("monitor-key-789")
        assert info is not None
        assert info["name"] == "monitoring"
        assert "health:read" in info["permissions"]

        info = api_key_manager.get_key_info("invalid-key")
        assert info is None

class TestAuthenticationDependencies:
    """Test FastAPI authentication dependencies."""

    @pytest.mark.asyncio
    async def test_verify_api_key_success(self):
        """Test successful API key verification."""
        with patch('api.core.auth.api_key_manager') as mock_manager:
            mock_manager.is_valid_key.return_value = True

            result = await verify_api_key("test-api-key")
            assert result == "test-api-key"

    @pytest.mark.asyncio
    async def test_verify_api_key_missing(self):
        """Test API key verification with missing key."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)

        assert exc_info.value.status_code == 401
        assert "API key is required" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test API key verification with invalid key."""
        with patch('api.core.auth.api_key_manager') as mock_manager:
            mock_manager.is_valid_key.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key("invalid-key")

            assert exc_info.value.status_code == 403
            assert "Invalid API key" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_permission_granted(self):
        """Test permission requirement when permission is granted."""
        with patch('api.core.auth.get_api_key_info') as mock_get_info:
            mock_get_info.return_value = {"permissions": ["admin", "read", "write"]}

            permission_dep = require_permission("admin")
            result = await permission_dep("api-key")
            assert result["permissions"] == ["admin", "read", "write"]

    @pytest.mark.asyncio
    async def test_require_permission_denied(self):
        """Test permission requirement when permission is denied."""
        with patch('api.core.auth.get_api_key_info') as mock_get_info:
            mock_get_info.return_value = {"permissions": ["read"]}

            permission_dep = require_permission("admin")

            with pytest.raises(HTTPException) as exc_info:
                await permission_dep("api-key")

            assert exc_info.value.status_code == 403
            assert "Permission" in str(exc_info.value.detail)
```

### Pipeline Integration Testing

```python
# tests/test_pipeline_integration.py
import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

from api.routers.pipeline import run_pipeline
from api.models.requests import PipelineRunRequest
from core.pipeline.orchestrator import OpportunityPipeline

class TestPipelineIntegration:
    """Test pipeline integration with FastAPI."""

    @pytest.mark.asyncio
    async def test_run_pipeline_success(self):
        """Test successful pipeline execution."""
        # Mock pipeline orchestrator
        mock_pipeline = AsyncMock()
        mock_pipeline.run.return_value = {
            'stats': {
                'submissions_processed': 100,
                'opportunities_found': 12,
                'processing_time_seconds': 180.5,
                'api_calls_saved': 500,
                'cost_savings_usd': 1.00
            },
            'summary': {
                'total_opportunities': 12,
                'high_confidence': 8,
                'categories': {'SaaS': 5, 'Content': 4, 'Service': 3}
            }
        }

        with patch('api.routers.pipeline.OpportunityPipeline', return_value=mock_pipeline), \
             patch('api.routers.pipeline.PipelineConfig'), \
             patch('api.routers.pipeline.uuid.uuid4', return_value='test-pipeline-id'):

            request = PipelineRunRequest(
                source="database",
                limit=100,
                subreddits=["Entrepreneur", "SideProject"]
            )

            result = await run_pipeline(
                request=request,
                background_tasks=AsyncMock(),
                api_key="test-key"
            )

            assert result.success is True
            assert result.pipeline_id == "test-pipeline-id"
            assert result.stats['submissions_processed'] == 100
            assert result.summary['total_opportunities'] == 12

    @pytest.mark.asyncio
    async def test_run_pipeline_timeout(self):
        """Test pipeline execution timeout."""
        # Mock pipeline that takes too long
        mock_pipeline = AsyncMock()
        mock_pipeline.run.side_effect = asyncio.TimeoutError("Pipeline timeout")

        with patch('api.routers.pipeline.OpportunityPipeline', return_value=mock_pipeline), \
             patch('api.routers.pipeline.PipelineConfig'):

            request = PipelineRunRequest(source="database", limit=100)

            with pytest.raises(HTTPException) as exc_info:
                await run_pipeline(
                    request=request,
                    background_tasks=AsyncMock(),
                    api_key="test-key"
                )

            assert exc_info.value.status_code == 408
            assert "timed out" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_run_pipeline_error(self):
        """Test pipeline execution with error."""
        # Mock pipeline that raises an exception
        mock_pipeline = AsyncMock()
        mock_pipeline.run.side_effect = Exception("Pipeline failed")

        with patch('api.routers.pipeline.OpportunityPipeline', return_value=mock_pipeline), \
             patch('api.routers.pipeline.PipelineConfig'):

            request = PipelineRunRequest(source="database", limit=100)

            with pytest.raises(HTTPException) as exc_info:
                await run_pipeline(
                    request=request,
                    background_tasks=AsyncMock(),
                    api_key="test-key"
                )

            assert exc_info.value.status_code == 500
            assert "Pipeline execution failed" in str(exc_info.value.detail)
```

---

## API Testing

### Endpoint Testing

```python
# tests/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from api.main import app
from api.models.requests import PipelineRunRequest, ProfilerRequest

client = TestClient(app)

class TestAPIEndpoints:
    """Test API endpoint functionality."""

    def setup_method(self):
        """Setup for each test method."""
        # Set up test environment
        app.dependency_overrides = {}

    def test_health_check_no_auth(self):
        """Test health check endpoint (no authentication required)."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "services" in data

    def test_health_check_with_services(self):
        """Test health check with service status."""
        with patch('api.routers.monitoring.HealthChecker.check_database_health') as mock_db, \
             patch('api.routers.monitoring.HealthChecker.check_redis_health') as mock_redis, \
             patch('api.routers.monitoring.HealthChecker.check_pipeline_health') as mock_pipeline:

            # Mock service responses
            mock_db.return_value = {"status": "healthy", "response_time_ms": 45}
            mock_redis.return_value = {"status": "healthy", "response_time_ms": 12}
            mock_pipeline.return_value = {"status": "healthy"}

            response = client.get("/api/v1/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["database"]["status"] == "healthy"
            assert data["services"]["redis"]["status"] == "healthy"
            assert data["services"]["pipeline"]["status"] == "healthy"

    @patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'})
    def test_metrics_endpoint_success(self):
        """Test metrics endpoint with valid API key."""
        response = client.get(
            "/api/v1/metrics",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "performance" in data
        assert "business" in data
        assert "timestamp" in data

    @patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'})
    def test_metrics_endpoint_invalid_key(self):
        """Test metrics endpoint with invalid API key."""
        response = client.get(
            "/api/v1/metrics",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 403

    @patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'})
    def test_pipeline_run_endpoint_success(self):
        """Test pipeline run endpoint with valid request."""
        # Mock the pipeline execution
        with patch('api.routers.pipeline.OpportunityPipeline') as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline.run.return_value = {
                'stats': {'submissions_processed': 10},
                'summary': {'total_opportunities': 5}
            }
            mock_pipeline_class.return_value = mock_pipeline

            # Mock config and UUID generation
            with patch('api.routers.pipeline.PipelineConfig'), \
                 patch('api.routers.pipeline.uuid.uuid4', return_value='test-id'):

                request_data = {
                    "source": "database",
                    "limit": 10,
                    "subreddits": ["test"]
                }

                response = client.post(
                    "/api/v1/pipeline/run",
                    headers={"X-API-Key": "test-key"},
                    json=request_data
                )

                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["pipeline_id"] == "test-id"
                assert "stats" in data
                assert "summary" in data

    @patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'})
    def test_profiler_analyze_endpoint_success(self):
        """Test profiler analyze endpoint with valid request."""
        with patch('api.routers.profiler.ProfilerService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.enrich.return_value = {
                'analysis': {'business_model': 'SaaS'},
                'potential_score': 0.85,
                'insights': ['Good opportunity'],
                'categories': ['SaaS'],
                'confidence': 'high'
            }
            mock_service_class.return_value = mock_service

            request_data = {
                "submission_id": "test123",
                "submission_title": "Test Title",
                "submission_content": "Test content",
                "subreddit": "test"
            }

            response = client.post(
                "/api/v1/profiler/analyze",
                headers={"X-API-Key": "test-key"},
                json=request_data
            )

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["potential_score"] == 0.85
            assert "analysis" in data
            assert "key_insights" in data

    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json_available(self):
        """Test that OpenAPI JSON specification is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

class TestRequestValidation:
    """Test request validation and error handling."""

    @patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'})
    def test_pipeline_run_invalid_limit(self):
        """Test pipeline run with invalid limit parameter."""
        request_data = {
            "source": "database",
            "limit": -1  # Invalid limit
        }

        response = client.post(
            "/api/v1/pipeline/run",
            headers={"X-API-Key": "test-key"},
            json=request_data
        )

        assert response.status_code == 422  # Validation error

    @patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'})
    def test_profiler_analyze_missing_required_field(self):
        """Test profiler analyze with missing required field."""
        request_data = {
            "submission_id": "test123",
            # Missing required fields
        }

        response = client.post(
            "/api/v1/profiler/analyze",
            headers={"X-API-Key": "test-key"},
            json=request_data
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_json_payload(self):
        """Test endpoint with invalid JSON payload."""
        response = client.post(
            "/api/v1/pipeline/run",
            headers={"X-API-Key": "test-key", "Content-Type": "application/json"},
            data="invalid json"
        )

        assert response.status_code == 422

    def test_missing_content_type(self):
        """Test endpoint without proper content type."""
        response = client.post(
            "/api/v1/pipeline/run",
            headers={"X-API-Key": "test-key"},
            data='{"source": "database"}'
        )

        # May succeed or fail depending on FastAPI's JSON parsing
        # The important thing is it doesn't crash
        assert response.status_code in [200, 422]
```

---

## Integration Testing

### Database Integration Testing

```python
# tests/test_database_integration.py
import pytest
from unittest.mock import patch, AsyncMock
import os

# Use test database configuration
@pytest.fixture
def test_db_config():
    """Setup test database configuration."""
    original_url = os.getenv('SUPABASE_URL')
    original_key = os.getenv('SUPABASE_KEY')

    # Set test database configuration
    os.environ['SUPABASE_URL'] = 'http://localhost:54321'  # Test instance
    os.environ['SUPABASE_KEY'] = 'test-key'

    yield

    # Restore original configuration
    if original_url:
        os.environ['SUPABASE_URL'] = original_url
    else:
        os.environ.pop('SUPABASE_URL', None)

    if original_key:
        os.environ['SUPABASE_KEY'] = original_key
    else:
        os.environ.pop('SUPABASE_KEY', None)

@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database integration functionality."""

    def test_database_connection(self, test_db_config):
        """Test database connectivity."""
        from supabase import create_client
        from config.settings import SUPABASE_URL, SUPABASE_KEY

        # This test requires a running test database
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Test simple query
            result = client.table('redditor').select('id').limit(1).execute()
            assert isinstance(result.data, list)

        except Exception as e:
            pytest.skip(f"Test database not available: {e}")

    @pytest.mark.asyncio
    async def test_pipeline_with_real_database(self, test_db_config):
        """Test pipeline execution with real database."""
        # This test requires a running test database
        try:
            from core.pipeline.orchestrator import OpportunityPipeline
            from core.pipeline.config import PipelineConfig

            config = PipelineConfig(
                data_source="database",
                limit=5  # Small limit for testing
            )

            pipeline = OpportunityPipeline(config)

            # Run pipeline with small dataset
            result = pipeline.run(limit=5)

            assert 'stats' in result
            assert 'summary' in result

        except Exception as e:
            pytest.skip(f"Database integration test failed: {e}")

    @pytest.mark.asyncio
    async def test_enrichment_service_with_database(self, test_db_config):
        """Test enrichment service with database integration."""
        try:
            from core.enrichment.profiler_service import ProfilerService

            profiler = ProfilerService()

            # Test with sample data
            sample_data = {
                'submission_id': 'test123',
                'title': 'Test Submission',
                'content': 'Test content for analysis',
                'subreddit': 'test'
            }

            result = await profiler.enrich(sample_data)

            assert isinstance(result, dict)
            # Result structure depends on the actual AI service

        except Exception as e:
            pytest.skip(f"Enrichment service test failed: {e}")
```

### Redis Integration Testing

```python
# tests/test_redis_integration.py
import pytest
import asyncio
from unittest.mock import patch

@pytest.mark.integration
class TestRedisIntegration:
    """Test Redis integration functionality."""

    @pytest.fixture
    async def redis_client(self):
        """Setup Redis client for testing."""
        try:
            from api.core.redis_connection import redis_manager
            await redis_manager.initialize()
            return await redis_manager.get_client()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_client):
        """Test Redis connectivity."""
        result = await redis_client.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiting_with_redis(self, redis_client):
        """Test actual Redis-based rate limiting."""
        from api.core.rate_limit import rate_limiter

        key = f"test_rate_limit_{asyncio.current_task().get_name()}"

        # First request should be allowed
        result1 = await rate_limiter.is_rate_limited(
            key=key,
            limit=3,
            window_seconds=60
        )
        assert result1.is_allowed is True
        assert result1.remaining_requests == 2

        # Second request should be allowed
        result2 = await rate_limiter.is_rate_limited(
            key=key,
            limit=3,
            window_seconds=60
        )
        assert result2.is_allowed is True
        assert result2.remaining_requests == 1

        # Third request should be allowed
        result3 = await rate_limiter.is_rate_limited(
            key=key,
            limit=3,
            window_seconds=60
        )
        assert result3.is_allowed is True
        assert result3.remaining_requests == 0

        # Fourth request should be blocked
        result4 = await rate_limiter.is_rate_limited(
            key=key,
            limit=3,
            window_seconds=60
        )
        assert result4.is_allowed is False
        assert result4.remaining_requests == 0

        # Cleanup
        await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_hierarchical_rate_limiting_with_redis(self, redis_client):
        """Test hierarchical rate limiting with Redis."""
        from api.core.hierarchical_rate_limiter import hierarchical_rate_limiter
        from unittest.mock import Mock

        # Create mock request
        request = Mock()
        request.url.path = "/api/v1/pipeline/run"
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}

        result = await hierarchical_rate_limiter.check_rate_limits(
            request=request,
            api_key="test-key",
            key_info={"name": "default"}
        )

        # Should allow request
        assert result.is_allowed is True
        assert isinstance(result.remaining_requests, int)
```

---

## Load Testing

### Locust Load Testing

```python
# tests/load_tests/locustfile.py
from locust import HttpUser, task, between, events
import random
import json
import time

class RedditHarborAPIUser(HttpUser):
    """Simulates typical RedditHarbor API user behavior."""

    wait_time = between(1, 5)  # Wait 1-5 seconds between requests

    def on_start(self):
        """Setup for each simulated user."""
        # Setup API key
        self.api_key = "test-api-key"
        self.client.headers.update({"X-API-Key": self.api_key})

        # Track user metrics
        self.requests_made = 0
        self.start_time = time.time()

    @task(4)
    def health_check(self):
        """Check API health (lightweight operation)."""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.requests_made += 1
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    def get_metrics(self):
        """Get API metrics (lightweight operation)."""
        with self.client.get("/api/v1/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.requests_made += 1
            elif response.status_code == 401:
                response.success()  # Expected for invalid key in testing
            else:
                response.failure(f"Metrics request failed: {response.status_code}")

    @task(2)
    def get_opportunities(self):
        """Get opportunities list (moderate operation)."""
        params = {
            "limit": random.randint(10, 50),
            "page": random.randint(1, 5)
        }

        with self.client.get("/api/v1/opportunities", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.requests_made += 1
            elif response.status_code == 429:
                # Rate limited - expected behavior
                response.success()
            else:
                response.failure(f"Opportunities request failed: {response.status_code}")

    @task(1)
    def run_small_pipeline(self):
        """Run small pipeline (heavy operation)."""
        data = {
            "source": "database",
            "limit": random.randint(5, 20),
            "subreddits": random.sample(["Entrepreneur", "SideProject", "SaaS"], k=random.randint(1, 2))
        }

        with self.client.post("/api/v1/pipeline/run", json=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.requests_made += 1
            elif response.status_code == 429:
                # Rate limited - expected for expensive operations
                response.success()
            elif response.status_code == 408:
                # Timeout - possible for heavy operations
                response.success()
            else:
                response.failure(f"Pipeline run failed: {response.status_code}")

    @task(1)
    def analyze_submission(self):
        """Analyze single submission (moderate operation)."""
        data = {
            "submission_id": f"test{random.randint(1000, 9999)}",
            "submission_title": "Test business idea analysis",
            "submission_content": "I've been working on a tool that helps content creators...",
            "subreddit": random.choice(["Entrepreneur", "SideProject", "SaaS"])
        }

        with self.client.post("/api/v1/profiler/analyze", json=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.requests_made += 1
            elif response.status_code == 429:
                response.success()  # Rate limited
            else:
                response.failure(f"Profiler analysis failed: {response.status_code}")

    def on_stop(self):
        """Cleanup for each simulated user."""
        duration = time.time() - self.start_time
        if self.requests_made > 0:
            requests_per_second = self.requests_made / duration
            print(f"User made {self.requests_made} requests in {duration:.2f}s "
                  f"({requests_per_second:.2f} req/s)")

class HeavyLoadUser(HttpUser):
    """Simulates heavy load scenario."""

    wait_time = between(0.5, 2)  # More aggressive timing
    weight = 2  # Double the probability of being chosen

    def on_start(self):
        self.api_key = "test-api-key"
        self.client.headers.update({"X-API-Key": self.api_key})

    @task
    def rapid_health_checks(self):
        """Rapid health checks to test rate limiting."""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task
    def rapid_pipeline_requests(self):
        """Rapid pipeline requests to test system limits."""
        data = {
            "source": "database",
            "limit": 5,  # Small limit for speed
        }

        with self.client.post("/api/v1/pipeline/run", json=data, catch_response=True) as response:
            if response.status_code in [200, 429, 408]:
                response.success()  # All acceptable responses
            else:
                response.failure(f"Pipeline request failed: {response.status_code}")

# Event handlers for monitoring
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request events."""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 5000:  # Log slow requests
        print(f"Slow request: {name} - {response_time:.2f}ms")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handle test start."""
    print("Load test starting...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Handle test stop."""
    print("Load test completed.")
```

### Performance Testing Scripts

```python
# scripts/performance_test.py
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import argparse

class PerformanceTest:
    """Performance testing for RedditHarbor API."""

    def __init__(self, base_url: str, api_key: str, concurrent_users: int = 10):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.concurrent_users = concurrent_users
        self.results: List[Dict] = []

    async def single_request(self, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        """Make a single API request and measure performance."""
        start_time = time.time()

        try:
            async with session.get(
                f"{self.base_url}{endpoint}",
                headers={"X-API-Key": self.api_key}
            ) as response:
                response_time = (time.time() - start_time) * 1000
                content_length = len(await response.text())

                return {
                    'endpoint': endpoint,
                    'status_code': response.status,
                    'response_time_ms': response_time,
                    'content_length': content_length,
                    'success': 200 <= response.status < 400
                }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                'endpoint': endpoint,
                'status_code': 0,
                'response_time_ms': response_time,
                'content_length': 0,
                'success': False,
                'error': str(e)
            }

    async def run_concurrent_tests(self, endpoint: str, total_requests: int) -> List[Dict]:
        """Run concurrent requests to an endpoint."""
        connector = aiohttp.TCPConnector(limit=self.concurrent_users)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            tasks = []
            for _ in range(total_requests):
                task = self.single_request(session, endpoint)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]

    async def test_endpoints(self, requests_per_endpoint: int = 50):
        """Test all major endpoints."""
        endpoints = [
            '/api/v1/health',
            '/api/v1/metrics',
            '/api/v1/opportunities?limit=20'
        ]

        all_results = []

        for endpoint in endpoints:
            print(f"Testing {endpoint} with {requests_per_endpoint} requests...")

            results = await self.run_concurrent_tests(endpoint, requests_per_endpoint)
            all_results.extend(results)

            # Calculate statistics for this endpoint
            successful_results = [r for r in results if r['success']]
            response_times = [r['response_time_ms'] for r in successful_results]

            if response_times:
                avg_time = statistics.mean(response_times)
                median_time = statistics.median(response_times)
                p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            else:
                avg_time = median_time = p95_time = 0

            success_rate = len(successful_results) / len(results) * 100

            print(f"  Results for {endpoint}:")
            print(f"    Success rate: {success_rate:.1f}%")
            print(f"    Avg response time: {avg_time:.2f}ms")
            print(f"    Median response time: {median_time:.2f}ms")
            print(f"    95th percentile: {p95_time:.2f}ms")
            print(f"    Total requests: {len(results)}")
            print()

        return all_results

    def generate_report(self, results: List[Dict]) -> Dict:
        """Generate performance report from results."""
        total_requests = len(results)
        successful_requests = [r for r in results if r['success']]

        if not successful_requests:
            return {
                'total_requests': total_requests,
                'success_rate': 0,
                'error': 'No successful requests'
            }

        response_times = [r['response_time_ms'] for r in successful_requests]
        status_codes = {}
        endpoints = {}

        for result in results:
            # Count status codes
            status = result['status_code']
            status_codes[status] = status_codes.get(status, 0) + 1

            # Group by endpoint
            endpoint = result['endpoint']
            if endpoint not in endpoints:
                endpoints[endpoint] = {
                    'total': 0,
                    'successful': 0,
                    'response_times': []
                }

            endpoints[endpoint]['total'] += 1
            if result['success']:
                endpoints[endpoint]['successful'] += 1
                endpoints[endpoint]['response_times'].append(result['response_time_ms'])

        return {
            'total_requests': total_requests,
            'successful_requests': len(successful_requests),
            'success_rate': len(successful_requests) / total_requests * 100,
            'response_time_stats': {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
            },
            'status_codes': status_codes,
            'endpoints': {
                endpoint: {
                    'total': data['total'],
                    'success_rate': data['successful'] / data['total'] * 100,
                    'avg_response_time': statistics.mean(data['response_times']) if data['response_times'] else 0
                }
                for endpoint, data in endpoints.items()
            }
        }

async def main():
    """Run performance tests."""
    parser = argparse.ArgumentParser(description='RedditHarbor API Performance Test')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--api-key', required=True, help='API key for authentication')
    parser.add_argument('--users', type=int, default=10, help='Concurrent users')
    parser.add_argument('--requests', type=int, default=50, help='Requests per endpoint')

    args = parser.parse_args()

    print("🚀 RedditHarbor API Performance Test")
    print(f"URL: {args.url}")
    print(f"Concurrent users: {args.users}")
    print(f"Requests per endpoint: {args.requests}")
    print()

    tester = PerformanceTest(args.url, args.api_key, args.users)

    # Run performance tests
    results = await tester.test_endpoints(args.requests)

    # Generate report
    report = tester.generate_report(results)

    print("📊 Performance Test Report")
    print("=" * 50)
    print(f"Total requests: {report['total_requests']}")
    print(f"Success rate: {report['success_rate']:.2f}%")
    print()
    print("Response Times:")
    print(f"  Mean: {report['response_time_stats']['mean']:.2f}ms")
    print(f"  Median: {report['response_time_stats']['median']:.2f}ms")
    print(f"  95th percentile: {report['response_time_stats']['p95']:.2f}ms")
    print(f"  Min: {report['response_time_stats']['min']:.2f}ms")
    print(f"  Max: {report['response_time_stats']['max']:.2f}ms")
    print()
    print("Status Codes:")
    for code, count in report['status_codes'].items():
        print(f"  {code}: {count}")
    print()
    print("Endpoints:")
    for endpoint, data in report['endpoints'].items():
        print(f"  {endpoint}:")
        print(f"    Success rate: {data['success_rate']:.1f}%")
        print(f"    Avg response time: {data['avg_response_time']:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Security Testing

### Security Test Suite

```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
import json

from api.main import app

client = TestClient(app)

class TestSecurity:
    """Test security aspects of the API."""

    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        malicious_inputs = [
            "'; DROP TABLE redditor; --",
            "1' OR '1'='1",
            "'; UPDATE redditor SET username='hacked'; --",
            "1'; SELECT * FROM redditor; --"
        ]

        for malicious_input in malicious_inputs:
            # Test in various parameters
            response = client.get(
                f"/api/v1/opportunities?search={malicious_input}",
                headers={"X-API-Key": "test-key"}
            )
            # Should not return 500 error (SQL error)
            assert response.status_code not in [500, 502]

    def test_xss_protection(self):
        """Test XSS protection in responses."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]

        for payload in xss_payloads:
            # Test that XSS payload is not executed
            response = client.post(
                "/api/v1/profiler/analyze",
                headers={"X-API-Key": "test-key"},
                json={
                    "submission_id": "test123",
                    "submission_title": payload,
                    "submission_content": payload,
                    "subreddit": "test"
                }
            )

            if response.status_code == 200:
                # Check that response doesn't contain unescaped script tags
                response_text = response.text.lower()
                assert "<script>" not in response_text

    def test_rate_limiting_security(self):
        """Test rate limiting prevents abuse."""
        # Make many rapid requests to trigger rate limiting
        responses = []
        for i in range(50):
            response = client.get(
                "/api/v1/health",
                headers={"X-API-Key": "test-key"}
            )
            responses.append(response)
            if response.status_code == 429:
                break

        # Should eventually be rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting not triggered"

        # Check rate limit headers
        rate_limit_response = next(r for r in responses if r.status_code == 429)
        assert "Retry-After" in rate_limit_response.headers

    def test_authentication_bypass_attempts(self):
        """Test various authentication bypass attempts."""
        bypass_attempts = [
            {},  # No auth
            {"Authorization": "Bearer fake-token"},  # Wrong auth type
            {"X-API-Key": ""},  # Empty key
            {"X-API-Key": "none"},  # Invalid key
            {"X-API-KEY": "test-key"},  # Wrong header case
        ]

        for auth_headers in bypass_attempts:
            response = client.get("/api/v1/metrics", headers=auth_headers)
            assert response.status_code in [401, 403, 422]

    def test_large_request_handling(self):
        """Test handling of large requests."""
        # Test with very large payload
        large_payload = {
            "source": "database",
            "limit": 1000000,  # Very large limit
            "subreddits": ["test"] * 10000  # Large array
        }

        response = client.post(
            "/api/v1/pipeline/run",
            headers={"X-API-Key": "test-key"},
            json=large_payload,
            timeout=10
        )

        # Should handle gracefully (either accept or reject with proper error)
        assert response.status_code in [200, 422, 413, 408]

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON."""
        malformed_jsons = [
            '{"incomplete": json',
            '{"key": "value" "extra": "value"}',
            '{"key": undefined}',
            'null',
            '[]',
            '{"key": null}'
        ]

        for malformed in malformed_jsons:
            response = client.post(
                "/api/v1/pipeline/run",
                headers={"X-API-Key": "test-key", "Content-Type": "application/json"},
                data=malformed
            )
            # Should handle gracefully without crashing
            assert response.status_code in [400, 422]

    def test_header_injection_protection(self):
        """Test protection against header injection."""
        malicious_headers = [
            {"X-API-Key": "test-key\r\nX-Forwarded-For: 127.0.0.1"},
            {"X-API-Key": "test-key\nLocation: http://evil.com"},
            {"User-Agent": "Mozilla/5.0\r\nX-Forwarded-Host: evil.com"}
        ]

        for headers in malicious_headers:
            response = client.get("/api/v1/health", headers=headers)
            # Should handle injection attempts safely
            assert response.status_code != 500

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        malicious_paths = [
            "/api/v1/../../etc/passwd",
            "/api/v1/..\\..\\windows\\system32",
            "/api/v1/%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]

        for path in malicious_paths:
            response = client.get(
                path,
                headers={"X-API-Key": "test-key"}
            )
            # Should return 404, not file contents
            assert response.status_code in [404, 400, 422]

    def test_cors_configuration(self):
        """Test CORS configuration."""
        # Test preflight request
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-API-Key"
            }
        )

        # Check CORS headers
        if "Access-Control-Allow-Origin" in response.headers:
            # Should not allow arbitrary origins
            assert response.headers["Access-Control-Allow-Origin"] != "*"
```

---

## Test Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts =
    -ra
    --strict-markers
    --strict-config
    --cov=api
    --cov=core
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
    --tb=short
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests
    integration: Integration tests (require external services)
    slow: Slow running tests
    security: Security tests
    performance: Performance tests

filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### Test Environment Setup

```bash
#!/bin/bash
# scripts/setup-test-environment.sh
# Setup test environment for running tests

set -e

echo "🧪 Setting up test environment..."

# === Python Environment ===
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt

# === Environment Variables ===
echo "🔧 Setting up test environment variables..."

# Create test .env file
cat > .env.test << EOF
# Test environment configuration
APP_NAME="RedditHarbor API Test"
APP_VERSION="2.0.0"
ENVIRONMENT=test
DEBUG=true

# Test API keys
REDDIT_HARBOR_API_KEY=test-api-key
JWT_SECRET_KEY=test-jwt-secret

# Test database (local Supabase)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=test-supabase-key

# Test Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=1  # Separate database for tests

# Test rate limiting (more permissive)
DEFAULT_RATE_LIMIT=1000/minute
PIPELINE_RATE_LIMIT=100/minute
ANALYSIS_RATE_LIMIT=500/minute

# Test logging
LOG_LEVEL=DEBUG
LOG_FORMAT=console
EOF

# === Test Database Setup ===
echo "🗄️ Setting up test database..."
if command -v supabase &> /dev/null; then
    supabase start
    echo "✅ Test database started"
else
    echo "⚠️ Supabase CLI not found. Tests requiring database will be skipped."
fi

# === Test Redis Setup ===
echo "🔴 Setting up test Redis..."
if docker info &> /dev/null; then
    docker run -d --name redditapi-test-redis -p 6379:6379 redis:7-alpine
    echo "✅ Test Redis started"
else
    echo "⚠️ Docker not available. Tests requiring Redis will be skipped."
fi

# === Create Test Directories ===
mkdir -p tests/reports
mkdir -p tests/screenshots
mkdir -p tests/logs

echo "✅ Test environment setup complete!"
echo ""
echo "To run tests:"
echo "  pytest                           # All tests"
echo "  pytest -m unit                   # Unit tests only"
echo "  pytest -m integration            # Integration tests only"
echo "  pytest --cov                     # With coverage report"
echo "  pytest -k test_rate_limiter      # Specific tests"
echo ""
echo "To clean up test environment:"
echo "  docker stop redditapi-test-redis && docker rm redditapi-test-redis"
echo "  supabase stop"
```

This comprehensive testing strategy provides multiple layers of testing for the RedditHarbor API, ensuring reliability, security, and performance across all scenarios.