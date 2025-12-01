# Type Safety Development Guide

<div align="center">

**Building Robust Type-Safe Code with Pydantic**

*Advanced patterns for type annotations, validation, and error handling in Pipeline v3*

</div>

## 📋 Table of Contents

- [🔒 Type Safety Overview](#-type-safety-overview)
- [🏗️ Pydantic Model Development](#️-pydantic-model-development)
- [📝 Type Annotation Best Practices](#-type-annotation-best-practices)
- [✅ Validation Pattern Implementation](#-validation-pattern-implementation)
- [⚠️ Error Handling with Type Safety](#️-error-handling-with-type-safety)
- [🧪 Testing Type-Safe Code](#-testing-type-safe-code)
- [🔧 Advanced Type Patterns](#-advanced-type-patterns)
- [📊 Type Safety Metrics and Quality](#-type-safety-metrics-and-quality)

---

## 🔒 Type Safety Overview

### Why Type Safety Matters

Type safety provides multiple benefits in Pipeline v3:

1. **Runtime Validation**: Catch data errors before they propagate
2. **IDE Support**: Better autocomplete and error detection
3. **Documentation**: Self-documenting code with clear contracts
4. **Refactoring Safety**: Confident code changes with type checking
5. **API Contracts**: Clear interfaces between components

### Type Safety Architecture

```mermaid
graph TB
    subgraph "Type Safety Layers"
        A[Static Type Checking]
        B[Runtime Validation]
        C[Serialization/Deserialization]
        D[Database ORM Mapping]
    end

    subgraph "Tools"
        E[Mypy]
        F[Pydantic]
        G[SQLAlchemy]
        H[Pydantic-SQLAlchemy]
    end

    subgraph "Benefits"
        I[Early Error Detection]
        J[IDE Support]
        K[Self-Documentation]
        L[Runtime Guarantees]
    end

    A --> E
    B --> F
    C --> F
    D --> G
    D --> H

    E --> I
    F --> J
    G --> K
    H --> L

    style A fill:#E3F2FD,stroke:#1976D2,stroke-width:2px
    style B fill:#E8F5E8,stroke:#388E3C,stroke-width:2px
    style C fill:#FFF3E0,stroke:#F57C00,stroke-width:2px
    style D fill:#FCE4EC,stroke:#C2185B,stroke-width:2px
```

---

## 🏗️ Pydantic Model Development

### 1. Core Model Architecture

**Base Model Patterns**
```python
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from datetime import datetime, timezone
from uuid import UUID
from enum import Enum
from pydantic import (
    BaseModel, Field, validator, field_validator,
    model_validator, ConfigDict, RootModel, constr
)
from pydantic.generics import GenericModel
import re
import math

# Generic type for model identification
ModelType = TypeVar('ModelType')

class BasePipelineModel(BaseModel):
    """Base model for all Pipeline v3 data models"""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',  # Prevent unexpected fields
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=False
    )

    @classmethod
    def get_model_name(cls) -> str:
        """Get the model class name for logging and debugging"""
        return cls.__name__

    def model_dump_safe(self, exclude_none: bool = True, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """Safe model dumping with sensitive data exclusion"""

        sensitive_fields = getattr(self, '_sensitive_fields', [])

        exclude = {}
        if exclude_none:
            exclude['none'] = True
        if exclude_sensitive:
            exclude['sensitive'] = sensitive_fields

        return self.model_dump(exclude=exclude)

class TimestampedModel(BasePipelineModel):
    """Base model with timestamp support"""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the model was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the model was last updated"
    )

    @model_validator(mode='after')
    def set_updated_at(self) -> 'TimestampedModel':
        """Automatically set updated_at on model updates"""
        if self.updated_at is None:
            self.updated_at = self.created_at
        return self

class AuditableModel(TimestampedModel):
    """Base model with audit trail support"""

    created_by: Optional[str] = Field(
        None,
        description="User or system that created the model"
    )
    updated_by: Optional[str] = Field(
        None,
        description="User or system that last updated the model"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Model version for optimistic locking"
    )

    @model_validator(mode='after')
    def increment_version_on_update(self) -> 'AuditableModel':
        """Increment version on model updates"""
        if self.updated_at and self.updated_at != self.created_at:
            self.version += 1
        return self
```

### 2. Advanced Validation Patterns

**Custom Validators and Constraints**
```python
class BusinessRuleValidator:
    """Reusable business rule validation patterns"""

    @staticmethod
    def validate_business_email(email: str) -> str:
        """Validate business email format"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")

        # Business email specific validation
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email.split('@')[1].lower()

        if domain in personal_domains:
            raise ValueError("Business email required (no personal email domains)")

        return email.lower()

    @staticmethod
    def validate_url(url: str, schemes: List[str] = None) -> str:
        """Validate URL with allowed schemes"""
        if schemes is None:
            schemes = ['http', 'https']

        url_pattern = re.compile(
            r'^(?:' + '|'.join(schemes) + r')://'
            r'(?:\S+(?::\S*)?@)?'
            r'(?:[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )

        if not url_pattern.match(url):
            raise ValueError(f"Invalid URL. Allowed schemes: {', '.join(schemes)}")

        return url

    @staticmethod
    def validate_score_range(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Validate score is within acceptable range"""
        if not isinstance(score, (int, float)):
            raise ValueError("Score must be a number")

        if not (min_val <= score <= max_val):
            raise ValueError(f"Score must be between {min_val} and {max_val}")

        # Round to 2 decimal places
        return round(float(score), 2)

    @staticmethod
    def validate_text_length(
        text: str,
        min_length: int = 1,
        max_length: int = 1000,
        field_name: str = "text"
    ) -> str:
        """Validate text length with meaningful error messages"""
        text = text.strip()

        if len(text) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters long")

        if len(text) > max_length:
            raise ValueError(f"{field_name} cannot exceed {max_length} characters")

        return text

class MarketMetricsModel(BasePipelineModel):
    """Enhanced market metrics with comprehensive validation"""

    market_demand: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Market demand score (0-100)"
    )
    pain_intensity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Pain point intensity (0-100)"
    )
    monetization_potential: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Monetization potential (0-100)"
    )
    competition_level: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Competition level (0-100, higher = less competition)"
    )
    technical_feasibility: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Technical feasibility (0-100)"
    )

    # Optional advanced metrics
    market_size: Optional[str] = Field(
        None,
        description="Market size category (small, medium, large, enterprise)"
    )
    regulatory_complexity: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Regulatory complexity (1=low, 5=high)"
    )
    time_to_market: Optional[int] = Field(
        None,
        ge=1,
        le=24,
        description="Time to market in months"
    )

    @field_validator('market_demand', 'pain_intensity', 'monetization_potential', 'competition_level', 'technical_feasibility')
    @classmethod
    def validate_metric_precision(cls, v: float) -> float:
        """Validate metric precision (max 2 decimal places)"""
        return BusinessRuleValidator.validate_score_range(v)

    @field_validator('market_size')
    @classmethod
    def validate_market_size(cls, v: Optional[str]) -> Optional[str]:
        """Validate market size category"""
        if v is None:
            return v

        allowed_sizes = ['small', 'medium', 'large', 'enterprise', 'niche']
        if v.lower() not in allowed_sizes:
            raise ValueError(f"Market size must be one of: {', '.join(allowed_sizes)}")

        return v.lower()

    @model_validator(mode='after')
    def validate_business_logic_consistency(cls, model) -> 'MarketMetricsModel':
        """Cross-field business logic validation"""

        # High pain should correlate with market demand
        if model.pain_intensity > 80 and model.market_demand < 30:
            raise ValueError(
                "Business logic error: High pain intensity (>80) should correlate with "
                "market demand (>30). Current: pain={model.pain_intensity}, demand={model.market_demand}"
            )

        # High technical feasibility should enable monetization
        if model.technical_feasibility < 20 and model.monetization_potential > 80:
            raise ValueError(
                "Business logic error: Low technical feasibility (<20) should limit "
                "monetization potential (<80). Current: feasibility={model.technical_feasibility}, "
                "monetization={model.monetization_potential}"
            )

        # Competition and market opportunity relationship
        if model.competition_level < 20 and model.market_demand < 40:
            raise ValueError(
                "Business logic error: Low competition (<20) should enable higher "
                "market opportunity (>40). Current: competition={model.competition_level}, "
                "demand={model.market_demand}"
            )

        # Validate realistic combination patterns
        extreme_count = sum([
            model.market_demand > 90,
            model.pain_intensity > 90,
            model.monetization_potential > 90,
            model.competition_level < 10,  # Remember: higher = less competition
            model.technical_feasibility > 90
        ])

        if extreme_count >= 4:
            raise ValueError(
                "Business logic error: Too many extreme metrics (>4) indicate unrealistic combination"
            )

        # Validate advanced metrics consistency
        if model.regulatory_complexity and model.time_to_market:
            if model.regulatory_complexity >= 4 and model.time_to_market < 6:
                raise ValueError(
                    "Business logic error: High regulatory complexity (>=4) should require "
                    "longer time to market (>=6 months)"
                )

        return model
```

### 3. Generic Models and Reusable Patterns

**Type-Safe Generic Patterns**
```python
from typing import TypeVar, Generic, List, Optional, Dict, Any
from abc import ABC, abstractmethod

T = TypeVar('T')

class PaginationParams(BasePipelineModel):
    """Type-safe pagination parameters"""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries"""
        return self.page_size

class PaginatedResponse(Generic[T], BasePipelineModel):
    """Generic paginated response model"""

    items: List[T] = Field(description="List of items in current page")
    total_count: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Items per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total_count: int,
        pagination: PaginationParams
    ) -> 'PaginatedResponse[T]':
        """Create paginated response from items and pagination params"""
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size

        return cls(
            items=items,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1
        )

class ApiResponse(Generic[T], BasePipelineModel):
    """Generic API response wrapper"""

    success: bool = Field(description="Whether the operation was successful")
    data: Optional[T] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Optional message")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    @classmethod
    def success_response(cls, data: T, message: str = None) -> 'ApiResponse[T]':
        """Create successful response"""
        return cls(
            success=True,
            data=data,
            message=message
        )

    @classmethod
    def error_response(cls, message: str, errors: List[str] = None) -> 'ApiResponse[None]':
        """Create error response"""
        return cls(
            success=False,
            message=message,
            errors=errors
        )

class SearchFilter(BasePipelineModel):
    """Generic search filter model"""

    field: str = Field(description="Field to filter on")
    operator: str = Field(
        regex="^(eq|ne|gt|gte|lt|lte|in|nin|contains|startswith|endswith)$",
        description="Filter operator"
    )
    value: Any = Field(description="Filter value")

class SearchParams(BasePipelineModel):
    """Generic search parameters"""

    filters: Optional[List[SearchFilter]] = Field(None, description="Search filters")
    query: Optional[str] = Field(None, description="Free-text search query")
    pagination: PaginationParams = Field(default_factory=PaginationParams, description="Pagination settings")
```

### 4. Enum Types and Constants

**Type-Safe Enums for Pipeline Configuration**
```python
from enum import Enum, IntEnum
from typing import Dict, Any

class TrustLevel(str, Enum):
    """Trust level enumeration with string values"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @classmethod
    def get_weight(cls, level: str) -> float:
        """Get numeric weight for trust level"""
        weights = {
            cls.LOW: 1.0,
            cls.MEDIUM: 2.0,
            cls.HIGH: 3.0
        }
        return weights.get(level, 1.0)

class ProcessingStatus(str, Enum):
    """Processing status enumeration"""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status is terminal (no further processing)"""
        return status in [cls.COMPLETED, cls.FAILED]

class LogLevel(str, Enum):
    """Log level enumeration"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def get_numeric_value(self) -> int:
        """Get numeric value for log level comparison"""
        return {
            self.DEBUG: 10,
            self.INFO: 20,
            self.WARNING: 30,
            self.ERROR: 40,
            self.CRITICAL: 50
        }[self]

class ModelSource(str, Enum):
    """Source of analysis model"""

    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    LLAMA_31_8B = "llama-3.1-8b"

    @classmethod
    def get_cost_per_1k_tokens(cls, model: str) -> float:
        """Get cost per 1K tokens for model"""
        costs = {
            cls.GPT_4O: 0.015,
            cls.GPT_4O_MINI: 0.00015,
            cls.CLAUDE_35_SONNET: 0.003,
            cls.CLAUDE_3_HAIKU: 0.00025,
            cls.LLAMA_31_8B: 0.0002
        }
        return costs.get(model, 0.001)

    @classmethod
    def get_quality_score(cls, model: str) -> float:
        """Get quality score for model"""
        scores = {
            cls.GPT_4O: 0.95,
            cls.GPT_4O_MINI: 0.85,
            cls.CLAUDE_35_SONNET: 0.92,
            cls.CLAUDE_3_HAIKU: 0.80,
            cls.LLAMA_31_8B: 0.75
        }
        return scores.get(model, 0.75)

class ProcessingPriority(IntEnum):
    """Processing priority enumeration"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

    def get_weight(self) -> float:
        """Get processing weight for queue priority"""
        return float(self.value)

# Type aliases for better readability
SubmissionId = str
AnalysisId = UUID
UserId = str
ConfidenceScore = float  # 0.0 to 1.0
OpportunityScore = float  # 0.0 to 100.0

# Complex type annotations
MarketAnalysis = Dict[str, Union[float, str, List[str]]]
ValidationErrorDict = Dict[str, List[str]]
ProcessingResult = Dict[str, Any]
```

---

## 📝 Type Annotation Best Practices

### 1. Function Type Annotations

**Comprehensive Function Typing**
```python
from typing import (
    Callable, Awaitable, List, Dict, Optional, Union,
    TypeVar, Generic, Protocol, runtime_checkable,
    Iterable, AsyncIterable, AsyncIterator, Iterator
)
from functools import wraps

# Generic type variables for function signatures
T = TypeVar('T')
U = TypeVar('U')
R = TypeVar('R')

def typed_async_function(
    func: Callable[..., Awaitable[R]]
) -> Callable[..., Awaitable[R]]:
    """Decorator for preserving async function type annotations"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> R:
        return await func(*args, **kwargs)
    return wrapper

class DataProcessor(Protocol[T, R]):
    """Protocol for data processing functions"""

    def __call__(self, data: T) -> R:
        ...

class AsyncDataProcessor(Protocol[T, R]):
    """Protocol for async data processing functions"""

    async def __call__(self, data: T) -> R:
        ...

# Type-safe repository pattern
class Repository(Generic[T]):
    """Generic repository interface with type safety"""

    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    async def create(self, data: Dict[str, Any]) -> T:
        """Create new model instance"""
        raise NotImplementedError

    async def get_by_id(self, id: Union[str, int, UUID]) -> Optional[T]:
        """Get model by ID"""
        raise NotImplementedError

    async def update(self, id: Union[str, int, UUID], data: Dict[str, Any]) -> Optional[T]:
        """Update model instance"""
        raise NotImplementedError

    async def delete(self, id: Union[str, int, UUID]) -> bool:
        """Delete model instance"""
        raise NotImplementedError

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PaginatedResponse[T]:
        """List model instances with optional filters and pagination"""
        raise NotImplementedError

# Usage example with typed functions
@typed_async_function
async def process_reddit_submission(
    submission: RedditSubmission,
    llm_processor: AsyncDataProcessor[RedditSubmission, AnalysisResult],
    validator: Callable[[AnalysisResult], bool],
    error_handler: Callable[[Exception, RedditSubmission], None]
) -> Optional[AnalysisResult]:
    """Process Reddit submission with comprehensive type annotations"""

    try:
        # Process submission through LLM
        analysis_result = await llm_processor(submission)

        # Validate result
        if not validator(analysis_result):
            raise ValueError("Analysis result validation failed")

        return analysis_result

    except Exception as e:
        # Handle errors with typed callback
        error_handler(e, submission)
        return None

def batch_processor(
    batch_size: int = 10,
    max_concurrent: int = 5
) -> Callable[[AsyncDataProcessor[T, R]], AsyncDataProcessor[List[T], List[R]]]:
    """Decorator for creating batch processors from single-item processors"""

    def decorator(processor: AsyncDataProcessor[T, R]) -> AsyncDataProcessor[List[T], List[R]]:
        @wraps(processor)
        async def batch_process(items: List[T]) -> List[R]:
            results = []

            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_single(item: T) -> R:
                async with semaphore:
                    return await processor(item)

            # Process in batches
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[process_single(item) for item in batch],
                    return_exceptions=True
                )

                # Filter successful results
                for result in batch_results:
                    if not isinstance(result, Exception):
                        results.append(result)

            return results

        return batch_process

    return decorator
```

### 2. Type-Safe Configuration

**Configuration with Type Validation**
```python
from typing import Literal, Union, Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class DatabaseConfig(BasePipelineModel):
    """Database configuration with type safety"""

    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=30, ge=0, le=100, description="Max overflow connections")
    pool_timeout: int = Field(default=30, ge=5, le=300, description="Pool timeout (seconds)")
    pool_recycle: int = Field(default=3600, ge=300, description="Connection recycle time (seconds)")
    echo: bool = Field(default=False, description="Enable SQL logging")

class RedisConfig(BasePipelineModel):
    """Redis configuration with type safety"""

    url: str = Field(..., description="Redis connection URL")
    max_connections: int = Field(default=100, ge=1, le=1000, description="Max connections")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    socket_timeout: int = Field(default=5, ge=1, le=60, description="Socket timeout (seconds)")

class LLMConfig(BasePipelineModel):
    """LLM configuration with comprehensive type safety"""

    api_key: str = Field(..., description="API key")
    base_url: Optional[str] = Field(None, description="Custom base URL")
    model: str = Field(..., description="Model name")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Temperature for creativity")
    max_tokens: int = Field(default=1000, ge=1, le=8000, description="Maximum tokens")
    timeout: int = Field(default=30, ge=5, le=300, description="Request timeout (seconds)")

    # Cost optimization
    enable_cost_optimization: bool = Field(default=True, description="Enable cost optimization")
    max_cost_per_request: Optional[float] = Field(None, ge=0.0, description="Max cost per request")

    # Rate limiting
    requests_per_minute: int = Field(default=120, ge=1, le=1000, description="Rate limit (requests/minute)")

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate base URL format"""
        if v is None:
            return v

        return BusinessRuleValidator.validate_url(v)

class RedditConfig(BasePipelineModel):
    """Reddit API configuration with type safety"""

    client_id: str = Field(..., description="Reddit client ID")
    client_secret: str = Field(..., description="Reddit client secret")
    user_agent: str = Field(..., description="User agent string")

    # Rate limiting
    requests_per_minute: int = Field(default=60, ge=1, le=100, description="Rate limit (requests/minute)")
    burst_allowance: int = Field(default=5, ge=1, le=20, description="Burst allowance")

    # Extraction settings
    default_limit: int = Field(default=100, ge=1, le=1000, description="Default extraction limit")
    min_score: int = Field(default=10, ge=0, description="Minimum score threshold")

    # Retry settings
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_backoff: float = Field(default=1.0, ge=0.1, le=60.0, description="Retry backoff multiplier")

class LoggingConfig(BasePipelineModel):
    """Logging configuration with type safety"""

    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: Optional[str] = Field(None, description="Log file path")
    max_file_size: int = Field(default=10485760, ge=1024, description="Max file size (bytes)")
    backup_count: int = Field(default=5, ge=1, le=50, description="Number of backup files")

    # Structured logging
    enable_json: bool = Field(default=False, description="Enable JSON logging")
    enable_structured: bool = Field(default=True, description="Enable structured logging")

class PipelineSettings(BaseSettings):
    """Main pipeline settings with comprehensive type safety"""

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Service configurations
    database: DatabaseConfig = Field(..., description="Database configuration")
    redis: Optional[RedisConfig] = Field(None, description="Redis configuration")
    llm: LLMConfig = Field(..., description="LLM configuration")
    reddit: RedditConfig = Field(..., description="Reddit configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")

    # Pipeline settings
    batch_size: int = Field(default=10, ge=1, le=100, description="Processing batch size")
    max_workers: int = Field(default=4, ge=1, le=16, description="Maximum worker threads")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Environment-specific validation"""
        if v == "production" and cls.debug:
            raise ValueError("Debug mode should not be enabled in production")
        return v

    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"
        case_sensitive = False

# Usage with type inference
def create_pipeline_settings() -> PipelineSettings:
    """Create pipeline settings with type safety"""
    return PipelineSettings(
        database=DatabaseConfig(
            url="postgresql://user:pass@localhost/db",
            pool_size=20
        ),
        llm=LLMConfig(
            api_key="your-key",
            model="gpt-4o-mini"
        ),
        reddit=RedditConfig(
            client_id="your-client-id",
            client_secret="your-secret",
            user_agent="RedditHarbor Pipeline v3/1.0"
        )
    )
```

---

## ✅ Validation Pattern Implementation

### 1. Custom Validation Rules

**Business Logic Validation Framework**
```python
from typing import Any, Callable, List, Dict, Optional, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class ValidationSeverity(Enum):
    """Validation error severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationError:
    """Structured validation error"""

    field: str
    message: str
    severity: ValidationSeverity
    code: Optional[str] = None
    value: Optional[Any] = None

class ValidationResult:
    """Validation result with errors and warnings"""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(
        self,
        field: str,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        code: Optional[str] = None,
        value: Optional[Any] = None
    ):
        """Add validation error"""
        error = ValidationError(
            field=field,
            message=message,
            severity=severity,
            code=code,
            value=value
        )

        if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.errors.append(error)
        else:
            self.warnings.append(error)

    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0

    def has_warnings(self) -> bool:
        """Check if there are warnings"""
        return len(self.warnings) > 0

    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        return {
            "is_valid": self.is_valid(),
            "has_warnings": self.has_warnings(),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "severity": e.severity.value,
                    "code": e.code,
                    "value": e.value
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "field": w.field,
                    "message": w.message,
                    "severity": w.severity.value,
                    "code": w.code,
                    "value": w.value
                }
                for w in self.warnings
            ]
        }

class ValidationRule(ABC):
    """Abstract base class for validation rules"""

    def __init__(self, field: str, code: Optional[str] = None):
        self.field = field
        self.code = code

    @abstractmethod
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate the value"""
        pass

class BusinessRuleValidator(ValidationRule):
    """Custom business rule validator"""

    def __init__(
        self,
        field: str,
        rule_func: Callable[[Any, Optional[Dict[str, Any]]], ValidationResult],
        code: Optional[str] = None
    ):
        super().__init__(field, code)
        self.rule_func = rule_func

    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate using the provided rule function"""
        return self.rule_func(value, context)

class CrossFieldValidator(ValidationRule):
    """Validator that checks multiple fields together"""

    def __init__(
        self,
        fields: List[str],
        rule_func: Callable[[Dict[str, Any]], ValidationResult],
        code: Optional[str] = None
    ):
        super().__init__(fields[0], code)  # Use first field as primary
        self.fields = fields
        self.rule_func = rule_func

    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate using all fields in context"""
        if context is None:
            raise ValueError("Cross-field validators require context")

        field_values = {field: context.get(field) for field in self.fields}
        return self.rule_func(field_values)

# Predefined validation rules
class CommonValidationRules:
    """Commonly used validation rules"""

    @staticmethod
    def non_empty_string(field: str, min_length: int = 1, max_length: int = None) -> ValidationRule:
        """Non-empty string validation"""

        def rule(value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
            result = ValidationResult()

            if value is None:
                result.add_error(field, f"{field} is required")
                return result

            if not isinstance(value, str):
                result.add_error(field, f"{field} must be a string")
                return result

            value = value.strip()

            if len(value) < min_length:
                result.add_error(
                    field,
                    f"{field} must be at least {min_length} characters long",
                    value=value
                )

            if max_length and len(value) > max_length:
                result.add_error(
                    field,
                    f"{field} cannot exceed {max_length} characters",
                    value=value
                )

            return result

        return BusinessRuleValidator(field, rule, "NON_EMPTY_STRING")

    @staticmethod
    def email_format(field: str) -> ValidationRule:
        """Email format validation"""

        def rule(value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
            result = ValidationResult()

            if value is None:
                return result

            if not isinstance(value, str):
                result.add_error(field, f"{field} must be a string")
                return result

            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

            if not re.match(email_pattern, value):
                result.add_error(
                    field,
                    f"{field} must be a valid email address",
                    value=value
                )

            return result

        return BusinessRuleValidator(field, rule, "EMAIL_FORMAT")

    @staticmethod
    def score_range(
        field: str,
        min_value: float = 0.0,
        max_value: float = 100.0
    ) -> ValidationRule:
        """Score range validation"""

        def rule(value: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
            result = ValidationResult()

            if value is None:
                result.add_error(field, f"{field} is required")
                return result

            if not isinstance(value, (int, float)):
                result.add_error(field, f"{field} must be a number")
                return result

            if not (min_value <= value <= max_value):
                result.add_error(
                    field,
                    f"{field} must be between {min_value} and {max_value}",
                    value=value
                )

            return result

        return BusinessRuleValidator(field, rule, "SCORE_RANGE")

    @staticmethod
    def mutually_exclusive(fields: List[str]) -> CrossFieldValidator:
        """Mutually exclusive fields validation"""

        def rule(field_values: Dict[str, Any]) -> ValidationResult:
            result = ValidationResult()

            provided_fields = [field for field, value in field_values.items() if value is not None]

            if len(provided_fields) > 1:
                result.add_error(
                    fields[0],
                    f"Only one of {', '.join(fields)} can be provided",
                    value=provided_fields
                )

            return result

        return CrossFieldValidator(fields, rule, "MUTUALLY_EXCLUSIVE")

    @staticmethod
    def conditional_required(
        condition_field: str,
        condition_value: Any,
        required_field: str
    ) -> CrossFieldValidator:
        """Conditional required field validation"""

        def rule(field_values: Dict[str, Any]) -> ValidationResult:
            result = ValidationResult()

            condition_met = field_values.get(condition_field) == condition_value

            if condition_met and field_values.get(required_field) is None:
                result.add_error(
                    required_field,
                    f"{required_field} is required when {condition_field} is {condition_value}"
                )

            return result

        return CrossFieldValidator([condition_field, required_field], rule, "CONDITIONAL_REQUIRED")

# Enhanced model with custom validation
class EnhancedAppIdea(AppIdea):
    """Enhanced AppIdea with comprehensive validation rules"""

    # Custom validation rules
    validation_rules: List[ValidationRule] = []

    def __init__(self, **data):
        super().__init__(**data)
        self._setup_validation_rules()

    def _setup_validation_rules(self):
        """Setup validation rules for this model"""

        self.validation_rules = [
            # Title validation
            CommonValidationRules.non_empty_string(
                "title",
                min_length=5,
                max_length=100
            ),

            # Concept validation
            CommonValidationRules.non_empty_string(
                "app_concept",
                min_length=10,
                max_length=500
            ),

            # Problem validation
            CommonValidationRules.non_empty_string(
                "problem_statement",
                min_length=10,
                max_length=1000
            ),

            # Target audience validation
            CommonValidationRules.non_empty_string(
                "target_audience",
                min_length=10,
                max_length=500
            ),

            # Cross-field validation
            CrossFieldValidator(
                ["app_concept", "problem_statement"],
                self._validate_concept_problem_alignment,
                "CONCEPT_PROBLEM_ALIGNMENT"
            )
        ]

    def _validate_concept_problem_alignment(self, field_values: Dict[str, Any]) -> ValidationResult:
        """Validate that concept addresses the problem"""

        result = ValidationResult()
        concept = field_values.get("app_concept", "").lower()
        problem = field_values.get("problem_statement", "").lower()

        # Simple keyword matching for demonstration
        problem_keywords = ["time", "money", "difficult", "complex", "manual"]
        concept_keywords = ["automate", "save", "simplify", "efficient", "easy"]

        has_problem_keyword = any(keyword in problem for keyword in problem_keywords)
        has_solution_keyword = any(keyword in concept for keyword in concept_keywords)

        if has_problem_keyword and not has_solution_keyword:
            result.add_error(
                "app_concept",
                "App concept should explicitly address the stated problem",
                severity=ValidationSeverity.WARNING,
                code="SOLUTION_NOT_CLEAR"
            )

        return result

    def validate_with_rules(self) -> ValidationResult:
        """Validate model using configured rules"""

        overall_result = ValidationResult()

        # Run individual field validations
        for rule in self.validation_rules:
            if isinstance(rule, BusinessRuleValidator):
                field_value = getattr(self, rule.field, None)
                result = rule.validate(field_value)

                # Merge results
                overall_result.errors.extend(result.errors)
                overall_result.warnings.extend(result.warnings)

            elif isinstance(rule, CrossFieldValidator):
                context = self.model_dump()
                result = rule.validate(None, context)

                # Merge results
                overall_result.errors.extend(result.errors)
                overall_result.warnings.extend(result.warnings)

        return overall_result

    def model_post_init(self, __context):
        """Post-initialization hook for custom validation"""
        super().model_post_init(__context)

        # Run custom validation rules
        validation_result = self.validate_with_rules()

        if not validation_result.is_valid():
            # Convert to Pydantic validation error
            error_messages = [f"{error.field}: {error.message}" for error in validation_result.errors]
            raise ValueError(f"Validation failed: {'; '.join(error_messages)}")
```

### 2. Type-Safe Error Handling

**Structured Error Management**
```python
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum
import traceback
import uuid

class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""

    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class PipelineError:
    """Structured error information"""

    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    exception: Optional[Exception] = None
    traceback: Optional[str] = None
    timestamp: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

        if self.error_id is None:
            self.error_id = str(uuid.uuid4())

        if self.exception and self.traceback is None:
            self.traceback = traceback.format_exc()

class TypeSafeErrorHandler:
    """Type-safe error handling with classification and recovery"""

    def __init__(self):
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.error_history: List[PipelineError] = []
        self.max_history = 1000

    def register_handler(
        self,
        category: ErrorCategory,
        handler: Callable[[PipelineError], Optional[Any]]
    ):
        """Register error handler for specific category"""
        if category not in self.error_handlers:
            self.error_handlers[category] = []

        self.error_handlers[category].append(handler)

    def handle_error(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> PipelineError:
        """Handle and classify error"""

        # Create structured error
        error = PipelineError(
            error_id=str(uuid.uuid4()),
            category=category,
            severity=severity,
            message=message or str(exception),
            exception=exception,
            context=context or {}
        )

        # Add to history
        self.error_history.append(error)

        # Trim history if needed
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

        # Try to handle error with registered handlers
        handlers = self.error_handlers.get(category, [])

        for handler in handlers:
            try:
                result = handler(error)
                if result is not None:
                    return result
            except Exception as handler_error:
                # Log handler error but don't let it crash
                print(f"Error in error handler: {handler_error}")

        return error

    def classify_error(self, exception: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify exception type and severity"""

        exception_type = type(exception).__name__
        exception_message = str(exception).lower()

        # Classification logic
        if "ValidationError" in exception_type or "validation" in exception_message:
            return ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM

        elif "TimeoutError" in exception_type or "timeout" in exception_message:
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH

        elif "ConnectionError" in exception_type or "connection" in exception_message:
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH

        elif "DatabaseError" in exception_type or "database" in exception_message:
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH

        elif "APIError" in exception_type or "rate limit" in exception_message:
            return ErrorCategory.EXTERNAL_API, ErrorSeverity.MEDIUM

        elif "BusinessLogicError" in exception_type:
            return ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM

        elif "PermissionError" in exception_type or "forbidden" in exception_message:
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH

        else:
            return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    def get_error_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error summary for monitoring"""

        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_errors = [
            error for error in self.error_history
            if error.timestamp and error.timestamp > cutoff_time
        ]

        # Count by category and severity
        category_counts = {}
        severity_counts = {}

        for error in recent_errors:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1

        return {
            "time_window_hours": time_window_hours,
            "total_errors": len(recent_errors),
            "errors_by_category": category_counts,
            "errors_by_severity": severity_counts,
            "recent_errors": [
                {
                    "error_id": error.error_id,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "message": error.message,
                    "timestamp": error.timestamp.isoformat() if error.timestamp else None
                }
                for error in recent_errors[-10:]  # Last 10 errors
            ]
        }

# Decorator for type-safe error handling
def handle_errors(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    retries: int = 0,
    retry_delay: float = 1.0
):
    """Decorator for automatic error handling with type safety"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = TypeSafeErrorHandler()
            last_error = None

            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Classify error
                    error_category, error_severity = error_handler.classify_error(e)

                    # Use specified category/severity if provided
                    error_category = category if category != ErrorCategory.UNKNOWN else error_category
                    error_severity = severity if severity != ErrorSeverity.MEDIUM else error_severity

                    # Handle error
                    handled_error = error_handler.handle_error(
                        e,
                        category=error_category,
                        severity=error_severity,
                        context={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "args": str(args)[:100],  # Truncate for logging
                            "kwargs": str(kwargs)[:100]
                        }
                    )

                    # Retry if we have attempts left and error is retryable
                    if attempt < retries and error_category in [
                        ErrorCategory.NETWORK,
                        ErrorCategory.EXTERNAL_API,
                        ErrorCategory.DATABASE
                    ]:
                        await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue

                    # Re-raise if we can't retry or shouldn't retry
                    raise handled_error.exception or e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = TypeSafeErrorHandler()
            last_error = None

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_error = e

                    # Classify error
                    error_category, error_severity = error_handler.classify_error(e)

                    # Use specified category/severity if provided
                    error_category = category if category != ErrorCategory.UNKNOWN else error_category
                    error_severity = severity if severity != ErrorSeverity.MEDIUM else error_severity

                    # Handle error
                    handled_error = error_handler.handle_error(
                        e,
                        category=error_category,
                        severity=error_severity,
                        context={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "args": str(args)[:100],
                            "kwargs": str(kwargs)[:100]
                        }
                    )

                    # Retry if we have attempts left and error is retryable
                    if attempt < retries and error_category in [
                        ErrorCategory.NETWORK,
                        ErrorCategory.EXTERNAL_API,
                        ErrorCategory.DATABASE
                    ]:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue

                    # Re-raise if we can't retry or shouldn't retry
                    raise handled_error.exception or e

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Usage examples
@handle_errors(category=ErrorCategory.EXTERNAL_API, retries=3, retry_delay=2.0)
async def call_external_api(data: Dict[str, Any]) -> Dict[str, Any]:
    """Type-safe API call with automatic retry and error handling"""

    # This function will automatically handle errors with 3 retries
    # and 2-second exponential backoff
    pass
```

---

## 🧪 Testing Type-Safe Code

### 1. Pydantic Model Testing

**Comprehensive Model Testing Strategies**
```python
import pytest
from typing import Any, Dict, List
from pydantic import ValidationError
from unittest.mock import Mock, patch

class TestPydanticModels:
    """Comprehensive test suite for Pydantic models"""

    def test_app_idea_validation_success(self):
        """Test successful AppIdea validation"""

        data = {
            "title": "Productivity Tracker",
            "app_concept": "A simple app to track daily tasks and productivity metrics",
            "problem_statement": "People struggle to track their daily productivity and goals",
            "target_audience": "Professionals and students who want to improve productivity",
            "core_functions": ["Task management", "Progress tracking", "Daily reports"]
        }

        # This should pass validation
        app_idea = AppIdea(**data)

        assert app_idea.title == "Productivity Tracker"
        assert len(app_idea.core_functions) == 3
        assert all(len(func.strip()) >= 3 for func in app_idea.core_functions)

    def test_app_idea_validation_errors(self):
        """Test AppIdea validation failures"""

        # Test title too short
        with pytest.raises(ValidationError) as exc_info:
            AppIdea(
                title="App",  # Too short
                app_concept="A valid concept description",
                problem_statement="A valid problem statement",
                target_audience="A valid audience",
                core_functions=["Function 1"]
            )

        assert "title" in str(exc_info.value)

        # Test too many core functions
        with pytest.raises(ValidationError) as exc_info:
            AppIdea(
                title="Valid Title",
                app_concept="A valid concept description",
                problem_statement="A valid problem statement",
                target_audience="A valid audience",
                core_functions=["Function 1", "Function 2", "Function 3", "Function 4"]  # Too many
            )

        assert "core_functions" in str(exc_info.value)

    def test_market_metrics_validation(self):
        """Test MarketMetrics validation"""

        # Valid metrics
        metrics = MarketMetrics(
            market_demand=75.5,
            pain_intensity=80.2,
            monetization_potential=65.8,
            competition_level=40.3,
            technical_feasibility=85.7
        )

        assert metrics.market_demand == 75.5
        assert 0.0 <= metrics.market_demand <= 100.0

        # Test out of range values
        with pytest.raises(ValidationError):
            MarketMetrics(
                market_demand=150.0,  # Too high
                pain_intensity=80.0,
                monetization_potential=60.0,
                competition_level=40.0,
                technical_feasibility=85.0
            )

    def test_business_logic_validation(self):
        """Test cross-field business logic validation"""

        # Test inconsistent metrics
        with pytest.raises(ValidationError) as exc_info:
            MarketMetrics(
                market_demand=20.0,  # Low demand
                pain_intensity=95.0,  # High pain
                monetization_potential=60.0,
                competition_level=40.0,
                technical_feasibility=85.0
            )

        assert "business logic error" in str(exc_info.value).lower()
        assert "pain intensity" in str(exc_info.value).lower()

    def test_model_serialization(self):
        """Test model serialization and deserialization"""

        # Create model
        app_idea = AppIdea(
            title="Test App",
            app_concept="Test concept",
            problem_statement="Test problem",
            target_audience="Test audience",
            core_functions=["Function 1", "Function 2"]
        )

        # Serialize
        data = app_idea.model_dump()

        # Verify serialization
        assert isinstance(data, dict)
        assert data["title"] == "Test App"
        assert isinstance(data["core_functions"], list)

        # Deserialize
        restored_app_idea = AppIdea(**data)

        # Verify restoration
        assert restored_app_idea.title == app_idea.title
        assert restored_app_idea.core_functions == app_idea.core_functions

    def test_model_json_serialization(self):
        """Test JSON serialization"""

        app_idea = AppIdea(
            title="Test App",
            app_concept="Test concept",
            problem_statement="Test problem",
            target_audience="Test audience",
            core_functions=["Function 1"]
        )

        # Test JSON serialization
        json_str = app_idea.model_dump_json()

        assert isinstance(json_str, str)

        # Test JSON deserialization
        restored_app_idea = AppIdea.model_validate_json(json_str)

        assert restored_app_idea.title == app_idea.title

class TestModelValidation:
    """Test custom validation patterns"""

    def test_enhanced_validation_rules(self):
        """Test enhanced validation rules"""

        # Create enhanced app idea
        app_idea = EnhancedAppIdea(
            title="Time Saver App",
            app_concept="Automate repetitive tasks to save time",
            problem_statement="Users waste time on manual repetitive tasks",
            target_audience="Busy professionals",
            core_functions=["Task automation", "Time tracking"]
        )

        # Test custom validation
        validation_result = app_idea.validate_with_rules()

        assert validation_result.is_valid()
        assert len(validation_result.errors) == 0

    def test_validation_error_accumulation(self):
        """Test that multiple validation errors are accumulated"""

        # Create app idea with multiple issues
        try:
            EnhancedAppIdea(
                title="Bad",  # Too short
                app_concept="A",  # Too short
                problem_statement="B",  # Too short
                target_audience="C",  # Too short
                core_functions=["D"]  # Valid length but should be meaningful
            )
            assert False, "Should have raised ValidationError"

        except ValueError as e:
            # Should include multiple validation errors
            error_str = str(e)
            assert "title" in error_str
            assert "app_concept" in error_str
            assert "problem_statement" in error_str
            assert "target_audience" in error_str

class TestTypeSafeRepositories:
    """Test type-safe repository patterns"""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository for testing"""

        class MockRepository(Repository[AppIdea]):
            def __init__(self):
                super().__init__(AppIdea)
                self.items = {}

            async def create(self, data: Dict[str, Any]) -> AppIdea:
                app_idea = AppIdea(**data)
                self.items[app_idea.title] = app_idea
                return app_idea

            async def get_by_id(self, id: str) -> Optional[AppIdea]:
                for item in self.items.values():
                    if item.title == id:  # Simplified ID matching
                        return item
                return None

            async def update(self, id: str, data: Dict[str, Any]) -> Optional[AppIdea]:
                item = await self.get_by_id(id)
                if item:
                    for key, value in data.items():
                        setattr(item, key, value)
                return item

            async def delete(self, id: str) -> bool:
                item = await self.get_by_id(id)
                if item:
                    del self.items[item.title]
                    return True
                return False

            async def list(
                self,
                filters: Optional[Dict[str, Any]] = None,
                pagination: Optional[PaginationParams] = None
            ) -> PaginatedResponse[AppIdea]:
                items = list(self.items.values())

                if pagination:
                    start = pagination.offset
                    end = start + pagination.limit
                    paginated_items = items[start:end]

                    return PaginatedResponse.create(
                        items=paginated_items,
                        total_count=len(items),
                        pagination=pagination
                    )

                return PaginatedResponse.create(
                    items=items,
                    total_count=len(items),
                    pagination=PaginationParams(page=1, page_size=len(items))
                )

        return MockRepository()

    @pytest.mark.asyncio
    async def test_repository_crud_operations(self, mock_repo):
        """Test CRUD operations with type safety"""

        # Create
        app_data = {
            "title": "Test App",
            "app_concept": "Test concept",
            "problem_statement": "Test problem",
            "target_audience": "Test audience",
            "core_functions": ["Function 1"]
        }

        created_app = await mock_repo.create(app_data)
        assert isinstance(created_app, AppIdea)
        assert created_app.title == "Test App"

        # Read
        retrieved_app = await mock_repo.get_by_id("Test App")
        assert retrieved_app is not None
        assert retrieved_app.title == "Test App"

        # Update
        updated_app = await mock_repo.update("Test App", {"title": "Updated App"})
        assert updated_app is not None
        assert updated_app.title == "Updated App"

        # Delete
        deleted = await mock_repo.delete("Updated App")
        assert deleted is True

        # Verify deletion
        deleted_app = await mock_repo.get_by_id("Updated App")
        assert deleted_app is None

    @pytest.mark.asyncio
    async def test_repository_pagination(self, mock_repo):
        """Test repository pagination"""

        # Create multiple items
        for i in range(25):
            await mock_repo.create({
                "title": f"App {i}",
                "app_concept": f"Concept {i}",
                "problem_statement": f"Problem {i}",
                "target_audience": f"Audience {i}",
                "core_functions": [f"Function {i}"]
            })

        # Test pagination
        pagination = PaginationParams(page=1, page_size=10)
        result = await mock_repo.list(pagination=pagination)

        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.total_pages == 3
        assert result.has_next is True
        assert result.has_previous is False

class TestTypeSafetyIntegration:
    """Integration tests for type safety"""

    @pytest.mark.asyncio
    async def test_end_to_end_type_safety(self):
        """Test end-to-end type safety in pipeline operations"""

        # Test data
        submission_data = {
            "id": "test123",
            "title": "Need a better way to track my daily habits",
            "text": "I've been trying to build good habits but struggle to track them consistently. Manual tracking is tedious and I often forget.",
            "author": "user123",
            "upvotes": 45,
            "score": 45,
            "comments_count": 23,
            "subreddit": "productivity",
            "created_utc": 1640995200.0,
            "permalink": "/r/productivity/comments/test123",
            "url": "https://reddit.com/r/productivity/comments/test123"
        }

        # Create typed submission
        submission = RedditSubmission(**submission_data)
        assert isinstance(submission, RedditSubmission)

        # Mock LLM processor that returns typed result
        async def mock_llm_processor(sub: RedditSubmission) -> AnalysisResult:
            return AnalysisResult(
                submission_id=sub.id,
                app_idea=AppIdea(
                    title="Habit Tracker Pro",
                    app_concept="An automated habit tracking app with reminders and insights",
                    problem_statement="People struggle to consistently track and build good habits",
                    target_audience="Individuals looking to improve daily habits",
                    core_functions=["Automated tracking", "Smart reminders", "Progress insights"]
                ),
                market_metrics=MarketMetrics(
                    market_demand=75.0,
                    pain_intensity=80.0,
                    monetization_potential=65.0,
                    competition_level=45.0,
                    technical_feasibility=85.0
                ),
                final_score=75.5,
                confidence_score=85.2,
                trust_level="HIGH"
            )

        # Process with type safety
        result = await mock_llm_processor(submission)

        # Verify type safety throughout
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.app_idea, AppIdea)
        assert isinstance(result.market_metrics, MarketMetrics)
        assert result.final_score >= 0.0 and result.final_score <= 100.0
        assert result.trust_level in ["LOW", "MEDIUM", "HIGH"]
```

### 2. Static Type Checking

**Mypy Configuration and Usage**
```python
# mypy.ini configuration for Pipeline v3
"""
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

# Start off with these
warn_unreachable = True
warn_no_return = True
ignore_missing_imports = True

# Migration: set to True after all imports are fixed
disallow_any_generics = True

[mypy-pydantic.*]
ignore_missing_imports = True

[mypy-pyaw.*]
ignore_missing_imports = True

[mypy-supabase.*]
ignore_missing_imports = True

[mypy-tests.*]
disallow_untyped_defs = False
"""

# Type-safe service interface
class TypeSafePipelineService(Protocol):
    """Protocol defining type-safe pipeline service interface"""

    async def process_submission(self, submission: RedditSubmission) -> Optional[AnalysisResult]:
        """Process a single Reddit submission"""
        ...

    async def process_batch(
        self,
        submissions: List[RedditSubmission],
        batch_size: int = 10
    ) -> List[AnalysisResult]:
        """Process multiple submissions in batch"""
        ...

    async def get_analysis_result(self, submission_id: str) -> Optional[AnalysisResult]:
        """Get analysis result by submission ID"""
        ...

# Implementation with type safety
class ConcretePipelineService:
    """Concrete implementation of type-safe pipeline service"""

    def __init__(
        self,
        llm_processor: AsyncDataProcessor[RedditSubmission, AnalysisResult],
        repository: Repository[AnalysisResult],
        validator: Callable[[AnalysisResult], bool]
    ):
        self.llm_processor = llm_processor
        self.repository = repository
        self.validator = validator

    async def process_submission(self, submission: RedditSubmission) -> Optional[AnalysisResult]:
        """Process submission with comprehensive type safety"""

        try:
            # Process through LLM (type-safe)
            result = await self.llm_processor(submission)

            # Validate result (type-safe)
            if not self.validator(result):
                raise ValueError("Analysis result failed validation")

            # Store result (type-safe)
            await self.repository.create(result.model_dump())

            return result

        except Exception as e:
            # Type-safe error handling
            print(f"Error processing submission {submission.id}: {e}")
            return None

    async def process_batch(
        self,
        submissions: List[RedditSubmission],
        batch_size: int = 10
    ) -> List[AnalysisResult]:
        """Process batch with type safety"""

        results = []

        # Process in batches
        for i in range(0, len(submissions), batch_size):
            batch = submissions[i:i + batch_size]

            # Process batch concurrently
            tasks = [self.process_submission(sub) for sub in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter successful results
            for result in batch_results:
                if isinstance(result, AnalysisResult):
                    results.append(result)
                elif isinstance(result, Exception):
                    print(f"Batch processing error: {result}")

        return results

    async def get_analysis_result(self, submission_id: str) -> Optional[AnalysisResult]:
        """Get analysis result with type safety"""

        try:
            # Get from repository (type-safe)
            result = await self.repository.get_by_id(submission_id)

            # Convert to Pydantic model if needed
            if isinstance(result, dict):
                return AnalysisResult(**result)

            return result

        except Exception as e:
            print(f"Error retrieving analysis result {submission_id}: {e}")
            return None

# Type-safe dependency injection
class ServiceContainer:
    """Type-safe dependency injection container"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}

    def register(self, service_type: Type[T], implementation: T):
        """Register service implementation"""
        self._services[service_type] = implementation

    def get(self, service_type: Type[T]) -> T:
        """Get service implementation with type safety"""
        implementation = self._services.get(service_type)

        if implementation is None:
            raise ValueError(f"Service {service_type} not registered")

        if not isinstance(implementation, service_type):
            raise TypeError(f"Implementation {type(implementation)} is not of type {service_type}")

        return implementation

# Usage example
async def setup_type_safe_pipeline() -> TypeSafePipelineService:
    """Setup type-safe pipeline with all dependencies"""

    container = ServiceContainer()

    # Register LLM processor
    llm_processor = OpenRouterLLMProcessor(settings)
    container.register(AsyncDataProcessor, llm_processor)

    # Register repository
    repository = AnalysisResultRepository(database)
    container.register(Repository, repository)

    # Register validator
    validator = AnalysisResultValidator()
    container.register(Callable, validator.validate)

    # Create service
    service = ConcretePipelineService(
        llm_processor=container.get(AsyncDataProcessor),
        repository=container.get(Repository),
        validator=container.get(Callable)
    )

    return service
```

---

## 🔧 Advanced Type Patterns

### 1. Union Types and Discriminated Unions

**Advanced Union Type Patterns**
```python
from typing import Union, Literal, Dict, Any, Optional
from pydantic import Field, Discriminator
from enum import Enum

# Discriminated union for different analysis types
class AnalysisType(str, Enum):
    """Analysis type enumeration"""

    APP_IDEA = "app_idea"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"

class BaseAnalysis(BasePipelineModel):
    """Base analysis model with discriminator"""

    analysis_type: AnalysisType = Field(..., discriminator="analysis_type")
    submission_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AppIdeaAnalysis(BaseAnalysis):
    """App idea analysis model"""

    analysis_type: Literal[AnalysisType.APP_IDEA] = AnalysisType.APP_IDEA
    app_idea: AppIdea
    market_metrics: MarketMetrics

class MarketResearchAnalysis(BaseAnalysis):
    """Market research analysis model"""

    analysis_type: Literal[AnalysisType.MARKET_RESEARCH] = AnalysisType.MARKET_RESEARCH
    market_size: str
    target_demographics: List[str]
    market_trends: List[str]
    competitive_landscape: str

class CompetitiveAnalysis(BaseAnalysis):
    """Competitive analysis model"""

    analysis_type: Literal[AnalysisType.COMPETITIVE_ANALYSIS] = AnalysisType.COMPETITIVE_ANALYSIS
    competitors: List[Dict[str, Any]]
    competitive_advantages: List[str]
    market_positioning: str
    differentiation_factors: List[str]

# Union type for any analysis
AnyAnalysis = Union[
    AppIdeaAnalysis,
    MarketResearchAnalysis,
    CompetitiveAnalysisAnalysis
]

# Function working with discriminated unions
def process_analysis(analysis: AnyAnalysis) -> Dict[str, Any]:
    """Process analysis based on its type"""

    if isinstance(analysis, AppIdeaAnalysis):
        return {
            "type": "app_idea",
            "title": analysis.app_idea.title,
            "score": analysis.market_metrics.final_score,
            "functions": analysis.app_idea.core_functions
        }

    elif isinstance(analysis, MarketResearchAnalysis):
        return {
            "type": "market_research",
            "market_size": analysis.market_size,
            "demographics": analysis.target_demographics,
            "trends": analysis.market_trends
        }

    elif isinstance(analysis, CompetitiveAnalysis):
        return {
            "type": "competitive_analysis",
            "competitors": len(analysis.competitors),
            "advantages": analysis.competitive_advantages,
            "positioning": analysis.market_positioning
        }

    else:
        raise ValueError(f"Unknown analysis type: {type(analysis)}")
```

### 2. Generic Pipeline Components

**Type-Safe Generic Pipeline Components**
```python
from typing import Generic, TypeVar, List, Optional, Callable, Awaitable
from abc import ABC, abstractmethod

# Type variables for pipeline stages
InputType = TypeVar('InputType')
IntermediateType = TypeVar('IntermediateType')
OutputType = TypeVar('OutputType')

class PipelineStage(ABC, Generic[InputType, OutputType]):
    """Abstract base class for pipeline stages"""

    @abstractmethod
    async def process(self, input_data: InputType) -> OutputType:
        """Process input data and return output data"""
        pass

class ExtractStage(PipelineStage[RedditSubmission, IntermediateType]):
    """Extraction stage with type safety"""

    def __init__(self, extractor: Callable[[str], Awaitable[List[RedditSubmission]]]):
        self.extractor = extractor

    async def process(self, subreddit: str) -> List[IntermediateType]:
        """Extract Reddit submissions"""

        submissions = await self.extractor(subreddit)

        # Convert to intermediate type if needed
        return [
            {
                "submission": sub,
                "extracted_at": datetime.utcnow()
            }
            for sub in submissions
        ]

class TransformStage(PipelineStage[IntermediateType, AnalysisResult]):
    """Transformation stage with type safety"""

    def __init__(self, processor: AsyncDataProcessor[RedditSubmission, AnalysisResult]):
        self.processor = processor

    async def process(self, intermediate_data: IntermediateType) -> AnalysisResult:
        """Transform submission to analysis result"""

        submission = intermediate_data["submission"]
        return await self.processor(submission)

class LoadStage(PipelineStage[AnalysisResult, bool]):
    """Load stage with type safety"""

    def __init__(self, repository: Repository[AnalysisResult]):
        self.repository = repository

    async def process(self, analysis_result: AnalysisResult) -> bool:
        """Load analysis result to database"""

        try:
            await self.repository.create(analysis_result.model_dump())
            return True
        except Exception:
            return False

class TypeSafePipeline(Generic[InputType, OutputType]):
    """Type-safe pipeline composition"""

    def __init__(self):
        self.stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> 'TypeSafePipeline':
        """Add stage to pipeline"""
        self.stages.append(stage)
        return self

    async def execute(self, input_data: InputType) -> OutputType:
        """Execute pipeline with type safety"""

        current_data = input_data

        for stage in self.stages:
            current_data = await stage.process(current_data)

        return current_data

# Usage example
async def create_type_safe_pipeline(
    extractor: Callable[[str], Awaitable[List[RedditSubmission]]],
    processor: AsyncDataProcessor[RedditSubmission, AnalysisResult],
    repository: Repository[AnalysisResult]
) -> TypeSafePipeline[str, bool]:
    """Create type-safe pipeline"""

    pipeline = TypeSafePipeline[str, bool]()

    pipeline.add_stage(ExtractStage(extractor))
    pipeline.add_stage(TransformStage(processor))
    pipeline.add_stage(LoadStage(repository))

    return pipeline
```

---

## 📊 Type Safety Metrics and Quality

### 1. Type Coverage Analysis

**Measuring Type Safety Quality**
```python
import ast
import inspect
from typing import Dict, List, Set, Tuple
from pathlib import Path

class TypeCoverageAnalyzer:
    """Analyze type coverage in codebase"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.files_analyzed = 0
        self.functions_analyzed = 0
        self.fully_typed_functions = 0
        self.partially_typed_functions = 0
        self.untyped_functions = 0

    def analyze_directory(self, directory: str) -> Dict[str, Any]:
        """Analyze type coverage in directory"""

        results = {
            "total_files": 0,
            "files_with_types": 0,
            "total_functions": 0,
            "fully_typed_functions": 0,
            "partially_typed_functions": 0,
            "untyped_functions": 0,
            "coverage_percentage": 0.0,
            "detailed_results": []
        }

        dir_path = self.project_root / directory

        for py_file in dir_path.glob("**/*.py"):
            if py_file.name.startswith("__"):
                continue

            file_result = self.analyze_file(py_file)
            results["detailed_results"].append(file_result)

            results["total_files"] += 1
            if file_result["has_type_annotations"]:
                results["files_with_types"] += 1

            results["total_functions"] += file_result["total_functions"]
            results["fully_typed_functions"] += file_result["fully_typed_functions"]
            results["partially_typed_functions"] += file_result["partially_typed_functions"]
            results["untyped_functions"] += file_result["untyped_functions"]

        # Calculate coverage
        if results["total_functions"] > 0:
            typed_functions = results["fully_typed_functions"] + results["partially_typed_functions"]
            results["coverage_percentage"] = (typed_functions / results["total_functions"]) * 100

        return results

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze type coverage in a single file"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            result = {
                "file_path": str(file_path.relative_to(self.project_root)),
                "has_type_annotations": False,
                "total_functions": 0,
                "fully_typed_functions": 0,
                "partially_typed_functions": 0,
                "untyped_functions": 0,
                "functions": []
            }

            # Check for imports
            has_typing_import = any(
                isinstance(node, ast.ImportFrom) and node.module == "typing"
                for node in ast.walk(tree)
            )

            result["has_type_annotations"] = has_typing_import

            # Analyze functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_analysis = self.analyze_function(node)
                    result["functions"].append(function_analysis)
                    result["total_functions"] += 1

                    if function_analysis["fully_typed"]:
                        result["fully_typed_functions"] += 1
                    elif function_analysis["has_types"]:
                        result["partially_typed_functions"] += 1
                    else:
                        result["untyped_functions"] += 1

            return result

        except Exception as e:
            return {
                "file_path": str(file_path.relative_to(self.project_root)),
                "error": str(e),
                "has_type_annotations": False,
                "total_functions": 0,
                "fully_typed_functions": 0,
                "partially_typed_functions": 0,
                "untyped_functions": 0,
                "functions": []
            }

    def analyze_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Dict[str, Any]:
        """Analyze type annotations in a function"""

        analysis = {
            "name": node.name,
            "line": node.lineno,
            "fully_typed": False,
            "has_types": False,
            "parameter_types": {},
            "return_type": None
        }

        # Check parameter annotations
        has_param_types = True
        all_params_typed = True

        for arg in node.args.args:
            if arg.annotation:
                analysis["parameter_types"][arg.arg] = ast.unparse(arg.annotation)
            else:
                has_param_types = True  # Some params might be typed
                all_params_typed = False

        # Check return annotation
        if node.returns:
            analysis["return_type"] = ast.unparse(node.returns)

        # Determine overall typing status
        analysis["has_types"] = bool(analysis["parameter_types"]) or analysis["return_type"] is not None
        analysis["fully_typed"] = all_params_typed and analysis["return_type"] is not None

        return analysis

# Usage example
def generate_type_safety_report(project_root: Path) -> Dict[str, Any]:
    """Generate comprehensive type safety report"""

    analyzer = TypeCoverageAnalyzer(project_root)

    # Analyze main source directories
    directories_to_analyze = ["models", "extract", "transform", "load"]

    report = {
        "project_root": str(project_root),
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "overall_coverage": 0.0,
        "directory_analysis": {},
        "summary": {
            "total_files": 0,
            "total_functions": 0,
            "fully_typed_functions": 0,
            "coverage_percentage": 0.0
        }
    }

    total_functions = 0
    fully_typed_functions = 0

    for directory in directories_to_analyze:
        dir_result = analyzer.analyze_directory(directory)
        report["directory_analysis"][directory] = dir_result

        total_functions += dir_result["total_functions"]
        fully_typed_functions += dir_result["fully_typed_functions"]

    # Calculate overall coverage
    report["summary"]["total_functions"] = total_functions
    report["summary"]["fully_typed_functions"] = fully_typed_functions

    if total_functions > 0:
        report["overall_coverage"] = (fully_typed_functions / total_functions) * 100
        report["summary"]["coverage_percentage"] = report["overall_coverage"]

    return report
```

---

<div align="center">

**🔒 Type Safety is Your Foundation for Reliable Code**

*Implement these patterns to build robust, maintainable, and error-free Pipeline v3 applications*

</div>