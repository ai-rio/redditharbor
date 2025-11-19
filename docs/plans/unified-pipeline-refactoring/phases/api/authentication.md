# API Authentication Patterns

**Purpose**: Implement production-ready authentication patterns for the RedditHarbor API, ensuring secure access while maintaining compatibility with existing systems.

---

## Authentication Strategy

### Primary Approach: API Key Authentication
- Simple, secure, and easy to integrate
- Compatible with existing RedditHarbor systems
- Low overhead for internal services
- Easy to rotate and manage

### Secondary Option: JWT Tokens
- For future web application integration
- Supports session management
- Allows for fine-grained permissions
- More complex but more flexible

---

## Configuration Management

### Pydantic Settings Pattern

Based on the extracted boilerplate, implement robust configuration management:

```python
# api/core/config.py
from enum import Enum
from pydantic import SecretStr, computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class AppSettings(BaseSettings):
    """Core application settings."""
    APP_NAME: str = "RedditHarbor API"
    APP_DESCRIPTION: str = "Unified opportunity discovery pipeline API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

class EnvironmentOption(str, Enum):
    """Environment options."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

class EnvironmentSettings(BaseSettings):
    """Environment-specific settings."""
    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL

    @computed_field
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == EnvironmentOption.PRODUCTION

    @computed_field
    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENVIRONMENT in [EnvironmentOption.LOCAL, EnvironmentOption.STAGING]

class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True

class RedisSettings(BaseSettings):
    """Redis connection settings."""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        auth_part = ""
        if self.REDIS_PASSWORD:
            auth_part = f":{self.REDIS_PASSWORD}@"
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

class AuthSettings(BaseSettings):
    """Authentication configuration."""
    # API Key Settings
    API_KEY_HEADER_NAME: str = "X-API-Key"
    API_KEY_ALGORITHM: str = "HS256"

    # JWT Settings (for future use)
    JWT_SECRET_KEY: SecretStr = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    DEFAULT_RATE_LIMIT: str = "60/minute"
    PIPELINE_RATE_LIMIT: str = "5/minute"
    ANALYSIS_RATE_LIMIT: str = "20/minute"

class Settings(
    AppSettings,
    CORSSettings,
    RedisSettings,
    EnvironmentSettings,
    AuthSettings
):
    """Unified application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

# Global settings instance
settings = Settings()
```

### Environment Configuration

**Development (.env)**:
```bash
# Application
APP_NAME="RedditHarbor API"
APP_VERSION="2.0.0"
ENVIRONMENT="local"
DEBUG=true

# API Keys
REDDIT_HARBOR_API_KEY="dev-api-key-change-in-production"
JWT_SECRET_KEY="dev-jwt-secret-change-in-production"

# CORS (allow all for development)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Redis
REDIS_HOST="localhost"
REDIS_PORT=6379

# Rate Limiting
DEFAULT_RATE_LIMIT="100/minute"
PIPELINE_RATE_LIMIT="10/minute"
```

**Production (.env.production)**:
```bash
# Application
APP_NAME="RedditHarbor API"
APP_VERSION="2.0.0"
ENVIRONMENT="production"
DEBUG=false

# API Keys (use secret management)
REDDIT_HARBOR_API_KEY="${REDDIT_HARBOR_API_KEY_FROM_VAULT}"
JWT_SECRET_KEY="${JWT_SECRET_KEY_FROM_VAULT}"

# CORS (restrict to specific domains)
CORS_ORIGINS=["https://app.redditharbor.com", "https://api.redditharbor.com"]

# Redis (production instance)
REDIS_HOST="${REDIS_HOST}"
REDIS_PORT=6379
REDIS_PASSWORD="${REDIS_PASSWORD}"

# Rate Limiting (stricter for production)
DEFAULT_RATE_LIMIT="60/minute"
PIPELINE_RATE_LIMIT="5/minute"
ANALYSIS_RATE_LIMIT="15/minute"
```

---

## API Key Authentication Implementation

### Simple API Key Validation

```python
# api/core/auth.py
import os
import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, Header, Depends, Request
from fastapi.security import APIKeyHeader
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)

# FastAPI security scheme
API_KEY_HEADER = APIKeyHeader(
    name=settings.API_KEY_HEADER_NAME,
    auto_error=False
)

class APIKeyManager:
    """Manage API key validation and storage."""

    def __init__(self):
        self._valid_keys = self._load_valid_keys()

    def _load_valid_keys(self) -> dict:
        """Load valid API keys from environment or secure storage."""
        keys = {}

        # Primary API key from environment
        primary_key = os.getenv("REDDIT_HARBOR_API_KEY")
        if primary_key:
            keys["primary"] = primary_key

        # Additional keys for different services
        webhook_key = os.getenv("WEBHOOK_API_KEY")
        if webhook_key:
            keys["webhook"] = webhook_key

        monitoring_key = os.getenv("MONITORING_API_KEY")
        if monitoring_key:
            keys["monitoring"] = monitoring_key

        return keys

    def is_valid_key(self, api_key: str) -> bool:
        """Validate an API key."""
        if not api_key:
            return False

        # Check against valid keys
        for key_name, key_value in self._valid_keys.items():
            if secrets.compare_digest(api_key, key_value):
                logger.info(f"Valid API key used: {key_name}")
                return True

        # Log invalid attempt
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        return False

    def get_key_info(self, api_key: str) -> Optional[dict]:
        """Get information about an API key."""
        for key_name, key_value in self._valid_keys.items():
            if secrets.compare_digest(api_key, key_value):
                return {
                    "name": key_name,
                    "type": "api_key",
                    "permissions": self._get_key_permissions(key_name)
                }
        return None

    def _get_key_permissions(self, key_name: str) -> List[str]:
        """Get permissions for a specific key."""
        permissions = {
            "primary": ["*"],  # Full access
            "webhook": ["pipeline:run", "opportunities:create"],
            "monitoring": ["health:read", "metrics:read"]
        }
        return permissions.get(key_name, [])

# Global API key manager instance
api_key_manager = APIKeyManager()

async def verify_api_key(
    api_key: str = Header(..., alias=settings.API_KEY_HEADER_NAME)
) -> str:
    """
    Verify API key from request header.

    This function is used as a FastAPI dependency to protect endpoints.
    It validates the API key and raises an HTTPException if invalid.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        str: The validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required",
            headers={"WWW-Authenticate": f'ApiKey realm="{settings.APP_NAME}"'}
        )

    if not api_key_manager.is_valid_key(api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
            headers={"WWW-Authenticate": f'ApiKey realm="{settings.APP_NAME}"'}
        )

    return api_key

async def get_api_key_info(
    api_key: str = Depends(verify_api_key)
) -> dict:
    """
    Get information about the current API key.

    This dependency provides additional context about the API key
    being used, such as permissions and key type.

    Args:
        api_key: Validated API key

    Returns:
        dict: API key information including permissions
    """
    info = api_key_manager.get_key_info(api_key)
    if not info:
        raise HTTPException(
            status_code=403,
            detail="API key information not found"
        )

    return info

def require_permission(permission: str):
    """
    Create a dependency that requires specific permission.

    Args:
        permission: Required permission string

    Returns:
        function: FastAPI dependency function
    """
    async def permission_checker(
        key_info: dict = Depends(get_api_key_info)
    ) -> dict:
        permissions = key_info.get("permissions", [])

        if "*" not in permissions and permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )

        return key_info

    return permission_checker
```

### Enhanced Security Features

```python
# api/core/security.py
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from api.core.auth import api_key_manager
import logging

logger = logging.getLogger(__name__)

class SecurityMetrics:
    """Track security-related metrics."""

    def __init__(self):
        self.failed_attempts: Dict[str, list] = {}
        self.successful_requests: Dict[str, int] = {}
        self.blocked_ips: Dict[str, datetime] = {}

    def record_failed_attempt(self, ip_address: str):
        """Record a failed authentication attempt."""
        now = time.time()

        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []

        # Clean old attempts (older than 1 hour)
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address]
            if now - attempt < 3600
        ]

        # Add new attempt
        self.failed_attempts[ip_address].append(now)

        # Check if IP should be blocked
        if len(self.failed_attempts[ip_address]) >= 10:
            self.blocked_ips[ip_address] = datetime.now()
            logger.warning(f"IP {ip_address} blocked due to too many failed attempts")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked."""
        if ip_address in self.blocked_ips:
            # Unblock after 24 hours
            if datetime.now() - self.blocked_ips[ip_address] > timedelta(hours=24):
                del self.blocked_ips[ip_address]
                return False
            return True
        return False

    def get_failed_attempts_count(self, ip_address: str) -> int:
        """Get number of failed attempts for an IP."""
        return len(self.failed_attempts.get(ip_address, []))

    def record_successful_request(self, api_key: str):
        """Record a successful API request."""
        self.successful_requests[api_key] = self.successful_requests.get(api_key, 0) + 1

# Global security metrics
security_metrics = SecurityMetrics()

async def security_middleware(request: Request, call_next):
    """
    Security middleware for request processing.

    This middleware adds security features:
    - IP blocking for repeated failures
    - Request logging
    - Security headers
    """
    client_ip = request.client.host

    # Check if IP is blocked
    if security_metrics.is_ip_blocked(client_ip):
        raise HTTPException(
            status_code=429,
            detail="IP address temporarily blocked due to suspicious activity"
        )

    # Add security headers
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response

def hash_api_key(api_key: str) -> str:
    """Hash an API key for logging (don't log the actual key)."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]
```

---

## JWT Authentication (Future Enhancement)

### JWT Token Implementation

```python
# api/core/jwt_auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.core.config import settings
import logging

logger = logging.getLogger(__name())

# JWT security scheme
jwt_scheme = HTTPBearer()

class JWTManager:
    """Manage JWT token creation and validation."""

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithm=settings.JWT_ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"JWT creation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Could not create access token"
            )

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"JWT processing error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Token processing error"
            )

# Global JWT manager
jwt_manager = JWTManager()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(jwt_scheme)
) -> Dict[str, Any]:
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = jwt_manager.verify_token(token)

    # Extract user information
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )

    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "permissions": payload.get("permissions", []),
        "token_exp": payload.get("exp")
    }

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user (can be extended with user status checks)."""
    return current_user
```

### JWT Token Endpoint

```python
# api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from api.core.jwt_auth import jwt_manager
from api.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    """Token data model."""
    access_token: str
    expires_in: int

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Get access token using OAuth2 password flow.

    This endpoint supports both API key and username/password authentication.
    For API keys, use the API key as username and any value as password.
    """
    # Check if this is an API key login
    if api_key_manager.is_valid_key(form_data.username):
        # Create JWT token for API key user
        key_info = api_key_manager.get_key_info(form_data.username)

        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = jwt_manager.create_access_token(
            data={
                "sub": key_info["name"],
                "type": "api_key",
                "permissions": key_info["permissions"]
            },
            expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60
        )

    # For future: Implement username/password authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/token/refresh")
async def refresh_access_token(
    current_user: dict = Depends(get_current_user)
):
    """Refresh an existing JWT token."""
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = jwt_manager.create_access_token(
        data={
            "sub": current_user["user_id"],
            "type": "jwt",
            "permissions": current_user["permissions"]
        },
        expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60
    )

@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user)
):
    """Get information about the current authenticated user."""
    return {
        "user_id": current_user["user_id"],
        "permissions": current_user["permissions"],
        "token_expires_at": datetime.fromtimestamp(current_user["token_exp"])
    }
```

---

## Integration Examples

### Python Client with API Key

```python
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedditHarborAPI:
    """Python client for RedditHarbor API with API key authentication."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'User-Agent': 'RedditHarbor-Python-Client/1.0'
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if e.response.status_code == 401:
                raise ValueError("Invalid API key")
            elif e.response.status_code == 403:
                raise ValueError("Access forbidden")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ValueError(f"API request failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._make_request('GET', '/api/v1/health')

    def run_pipeline(
        self,
        source: str = "database",
        limit: int = 100,
        subreddits: Optional[list] = None
    ) -> Dict[str, Any]:
        """Run the opportunity discovery pipeline."""
        data = {
            "source": source,
            "limit": limit
        }
        if subreddits:
            data["subreddits"] = subreddits

        return self._make_request('POST', '/api/v1/pipeline/run', json_data=data)

# Usage
api = RedditHarborAPI(
    base_url="http://localhost:8000",
    api_key="your-api-key-here"
)

try:
    health = api.health_check()
    print(f"API Status: {health['status']}")

    result = api.run_pipeline(
        source="database",
        limit=50,
        subreddits=["Entrepreneur"]
    )
    print(f"Pipeline completed: {result['success']}")

except ValueError as e:
    print(f"API Error: {e}")
```

### Python Client with JWT

```python
import requests
from datetime import datetime, timedelta

class RedditHarborJWTAPI:
    """Python client using JWT authentication."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.access_token = None
        self.token_expires = None
        self.session = requests.Session()

    def get_access_token(self) -> str:
        """Get or refresh JWT access token."""
        # Check if current token is still valid
        if (self.access_token and
            self.token_expires and
            datetime.now() < self.token_expires):
            return self.access_token

        # Get new token
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/token",
            data={
                "username": self.api_key,  # Use API key as username
                "password": "unused",      # Password not needed for API keys
                "grant_type": "password"
            }
        )

        response.raise_for_status()
        token_data = response.json()

        self.access_token = token_data["access_token"]
        self.token_expires = datetime.now() + timedelta(
            seconds=token_data["expires_in"]
        )

        # Update session headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        })

        return self.access_token

    def _make_authenticated_request(self, method: str, endpoint: str, **kwargs):
        """Make request with JWT authentication."""
        # Ensure we have a valid token
        self.get_access_token()

        url = f"{self.base_url}{endpoint}"

        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()

        return response.json()

    def get_user_info(self) -> dict:
        """Get current user information."""
        return self._make_authenticated_request('GET', '/api/v1/auth/me')
```

---

## Testing Authentication

### Unit Tests

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from api.main import app

client = TestClient(app)

def test_api_key_valid():
    """Test valid API key."""
    with patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'}):
        response = client.get(
            "/api/v1/health",
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200

def test_api_key_invalid():
    """Test invalid API key."""
    response = client.get(
        "/api/v1/health",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 403
    assert "Invalid API key" in response.json()["detail"]

def test_api_key_missing():
    """Test missing API key."""
    response = client.get("/api/v1/health")
    assert response.status_code == 401
    assert "API key is required" in response.json()["detail"]

def test_jwt_token_creation():
    """Test JWT token creation and validation."""
    from api.core.jwt_auth import jwt_manager

    # Create token
    token = jwt_manager.create_access_token(
        data={"sub": "test-user", "permissions": ["read"]}
    )

    # Verify token
    payload = jwt_manager.verify_token(token)
    assert payload["sub"] == "test-user"
    assert "permissions" in payload

def test_permission_checker():
    """Test permission-based access control."""
    from api.core.auth import require_permission

    # Mock key info with full permissions
    key_info = {"permissions": ["*"]}

    # Should not raise exception
    permission_dep = require_permission("admin:access")
    result = permission_dep(key_info)
    assert result == key_info

    # Test denied permission
    key_info = {"permissions": ["read"]}
    permission_dep = require_permission("admin:access")

    with pytest.raises(HTTPException) as exc_info:
        permission_dep(key_info)

    assert exc_info.value.status_code == 403
    assert "Permission" in str(exc_info.value.detail)
```

### Integration Tests

```python
# tests/test_auth_integration.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_full_authentication_flow():
    """Test complete authentication flow."""

    # 1. Get JWT token using API key
    with patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'}):
        token_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "test-key",
                "password": "unused",
                "grant_type": "password"
            }
        )
        assert token_response.status_code == 200

        token_data = token_response.json()
        access_token = token_data["access_token"]

        # 2. Use JWT token for authenticated requests
        protected_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert protected_response.status_code == 200

        user_data = protected_response.json()
        assert "user_id" in user_data
        assert "permissions" in user_data

        # 3. Test protected endpoint with JWT token
        pipeline_response = client.post(
            "/api/v1/pipeline/run",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"source": "database", "limit": 5}
        )
        assert pipeline_response.status_code == 200
```

---

## Security Best Practices

### API Key Management

1. **Storage**: Store API keys securely using environment variables or secret management
2. **Rotation**: Implement API key rotation policies
3. **Scope**: Use scoped API keys for different services
4. **Revocation**: Implement immediate API key revocation
5. **Auditing**: Log all API key usage for security monitoring

### JWT Token Security

1. **Expiration**: Use short-lived tokens (15-30 minutes)
2. **Refresh**: Implement token refresh mechanism
3. **Secure Storage**: Store JWT secrets securely
4. **Claims**: Include minimal necessary information in tokens
5. **Validation**: Validate all tokens on every request

### Rate Limiting Integration

```python
# api/core/auth_rate_limit.py
from api.core.rate_limit import rate_limiter
from fastapi import HTTPException

async def check_rate_limit_with_auth(
    api_key: str = Depends(verify_api_key),
    request: Request = None
):
    """Check rate limits based on API key permissions."""

    # Get key info to determine rate limits
    key_info = api_key_manager.get_key_info(api_key)

    # Different rate limits based on key type
    if key_info["name"] == "primary":
        limit = 100  # Higher limit for primary key
        period = 60
    else:
        limit = 20   # Lower limit for service keys
        period = 60

    # Check rate limit
    is_limited = await rate_limiter.is_rate_limited(
        api_key=api_key,
        path=request.url.path,
        limit=limit,
        period=period
    )

    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + period)
            }
        )

    return api_key
```

### Monitoring and Alerting

```python
# api/monitoring/security_monitor.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)

class SecurityMonitor:
    """Monitor security-related events and generate alerts."""

    def __init__(self):
        self.suspicious_activities: List[Dict] = []
        self.alert_thresholds = {
            "failed_attempts_per_hour": 50,
            "requests_per_minute": 1000,
            "concurrent_requests": 100
        }

    def record_failed_login(self, ip_address: str, api_key: str):
        """Record a failed login attempt."""
        self.suspicious_activities.append({
            "type": "failed_login",
            "ip_address": ip_address,
            "api_key_hash": hash_api_key(api_key),
            "timestamp": datetime.now()
        })

        # Check if we should alert
        self.check_failed_login_alerts()

    def check_failed_login_alerts(self):
        """Check if failed login attempts exceed thresholds."""
        one_hour_ago = datetime.now() - timedelta(hours=1)

        recent_failures = [
            activity for activity in self.suspicious_activities
            if (activity["type"] == "failed_login" and
                activity["timestamp"] > one_hour_ago)
        ]

        if len(recent_failures) > self.alert_thresholds["failed_attempts_per_hour"]:
            logger.error(
                f"SECURITY ALERT: {len(recent_failures)} failed login attempts "
                f"in the last hour. Possible brute force attack."
            )

            # In production, send alert to security team
            # self.send_security_alert("High failed login rate detected")

# Global security monitor
security_monitor = SecurityMonitor()
```

---

## Production Deployment Considerations

### Environment Variables

```bash
# Required for production
REDDIT_HARBOR_API_KEY=your-production-api-key
JWT_SECRET_KEY=your-jwt-secret-key

# Security settings
ENVIRONMENT=production
DEBUG=false

# CORS (restrict to your domains)
CORS_ORIGINS=["https://your-app.com", "https://api.your-app.com"]

# Redis (production instance)
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Rate limiting (stricter in production)
DEFAULT_RATE_LIMIT=60/minute
PIPELINE_RATE_LIMIT=5/minute
ANALYSIS_RATE_LIMIT=15/minute
```

### Docker Security Configuration

```dockerfile
# api/Dockerfile (security-focused)
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r redditapi && useradd -r -g redditapi redditapi

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=redditapi:redditapi ./api /app/api

# Switch to non-root user
USER redditapi

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx Security Headers

```nginx
# nginx.conf (security configuration)
server {
    listen 80;
    server_name api.redditharbor.com;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API proxy
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```