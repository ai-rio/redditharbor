"""
Performance configuration and optimization settings
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os


@dataclass
class EmbeddingPerformanceConfig:
    """Configuration for embedding generation performance"""
    batch_size: int = 32
    max_concurrent_requests: int = 4
    request_timeout: float = 30.0
    retry_attempts: int = 3
    retry_backoff_factor: float = 2.0
    cache_embeddings: bool = True
    cache_ttl: int = 3600  # 1 hour


@dataclass
class DatabasePerformanceConfig:
    """Configuration for database performance"""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: float = 30.0
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    echo_sql: bool = False
    connection_timeout: float = 10.0


@dataclass
class LLMPerformanceConfig:
    """Configuration for LLM API performance"""
    batch_size: int = 5
    max_concurrent_requests: int = 2
    request_timeout: float = 60.0
    retry_attempts: int = 2
    retry_backoff_factor: float = 1.5
    rate_limit_per_minute: int = 60


@dataclass
class CachingConfig:
    """Configuration for caching strategies"""
    enable_redis: bool = False
    redis_url: Optional[str] = None
    redis_ttl: int = 3600
    enable_memory_cache: bool = True
    memory_cache_size: int = 1000
    cache_key_prefix: str = "pipeline_v3"


@dataclass
class PerformanceConfig:
    """Combined performance configuration"""
    embedding: EmbeddingPerformanceConfig
    database: DatabasePerformanceConfig
    llm: LLMPerformanceConfig
    caching: CachingConfig

    # Global settings
    enable_profiling: bool = False
    log_performance_metrics: bool = True
    metrics_sample_rate: float = 0.1  # 10% sampling


class PerformanceConfigManager:
    """Manages performance configuration with environment variable support"""

    def __init__(self):
        """Initialize configuration manager with default values"""
        self.config = PerformanceConfig(
            embedding=EmbeddingPerformanceConfig(),
            database=DatabasePerformanceConfig(),
            llm=LLMPerformanceConfig(),
            caching=CachingConfig()
        )
        self._load_from_environment()

    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Embedding settings
        if os.getenv('EMBEDDING_BATCH_SIZE'):
            self.config.embedding.batch_size = int(os.getenv('EMBEDDING_BATCH_SIZE'))

        if os.getenv('EMBEDDING_MAX_CONCURRENT'):
            self.config.embedding.max_concurrent_requests = int(os.getenv('EMBEDDING_MAX_CONCURRENT'))

        # Database settings
        if os.getenv('DB_POOL_SIZE'):
            self.config.database.pool_size = int(os.getenv('DB_POOL_SIZE'))

        if os.getenv('DB_MAX_OVERFLOW'):
            self.config.database.max_overflow = int(os.getenv('DB_MAX_OVERFLOW'))

        # LLM settings
        if os.getenv('LLM_BATCH_SIZE'):
            self.config.llm.batch_size = int(os.getenv('LLM_BATCH_SIZE'))

        if os.getenv('LLM_RATE_LIMIT'):
            self.config.llm.rate_limit_per_minute = int(os.getenv('LLM_RATE_LIMIT'))

        # Caching settings
        if os.getenv('REDIS_URL'):
            self.config.caching.enable_redis = True
            self.config.caching.redis_url = os.getenv('REDIS_URL')

        if os.getenv('ENABLE_CACHE'):
            self.config.caching.enable_memory_cache = os.getenv('ENABLE_CACHE').lower() == 'true'

        # Performance monitoring
        if os.getenv('ENABLE_PROFILING'):
            self.config.enable_profiling = os.getenv('ENABLE_PROFILING').lower() == 'true'

    def get_database_url_config(self, database_url: str) -> Dict[str, Any]:
        """Get database configuration for SQLAlchemy create_engine"""
        return {
            'url': database_url,
            'echo': self.config.database.echo_sql,
            'pool_size': self.config.database.pool_size,
            'max_overflow': self.config.database.max_overflow,
            'pool_timeout': self.config.database.pool_timeout,
            'pool_recycle': self.config.database.pool_recycle,
            'pool_pre_ping': self.config.database.pool_pre_ping,
            'connect_args': {
                'connect_timeout': self.config.database.connection_timeout
            }
        }

    def optimize_for_environment(self, environment: str = 'development'):
        """Optimize configuration for specific environment"""
        if environment == 'production':
            # Production optimizations
            self.config.embedding.batch_size = 64
            self.config.database.pool_size = 20
            self.config.database.max_overflow = 40
            self.config.llm.batch_size = 10
            self.config.caching.enable_memory_cache = True
            self.config.caching.enable_redis = True
            self.config.enable_profiling = False

        elif environment == 'testing':
            # Testing optimizations
            self.config.embedding.batch_size = 8
            self.config.database.pool_size = 2
            self.config.database.max_overflow = 4
            self.config.llm.batch_size = 2
            self.config.caching.enable_memory_cache = False
            self.config.caching.enable_redis = False
            self.config.enable_profiling = False

        elif environment == 'development':
            # Development optimizations
            self.config.embedding.batch_size = 16
            self.config.database.pool_size = 5
            self.config.database.max_overflow = 10
            self.config.llm.batch_size = 3
            self.config.caching.enable_memory_cache = True
            self.config.caching.enable_redis = False
            self.config.enable_profiling = True

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary for logging/debugging"""
        return {
            'embedding': {
                'batch_size': self.config.embedding.batch_size,
                'max_concurrent_requests': self.config.embedding.max_concurrent_requests,
                'cache_enabled': self.config.embedding.cache_embeddings
            },
            'database': {
                'pool_size': self.config.database.pool_size,
                'max_overflow': self.config.database.max_overflow,
                'pool_timeout': self.config.database.pool_timeout
            },
            'llm': {
                'batch_size': self.config.llm.batch_size,
                'max_concurrent_requests': self.config.llm.max_concurrent_requests,
                'rate_limit_per_minute': self.config.llm.rate_limit_per_minute
            },
            'caching': {
                'memory_cache_enabled': self.config.caching.enable_memory_cache,
                'redis_enabled': self.config.caching.enable_redis,
                'cache_size': self.config.caching.memory_cache_size
            },
            'monitoring': {
                'profiling_enabled': self.config.enable_profiling,
                'metrics_enabled': self.config.log_performance_metrics,
                'sample_rate': self.config.metrics_sample_rate
            }
        }


# Global configuration instance
_performance_config = None


def get_performance_config() -> PerformanceConfig:
    """Get global performance configuration"""
    global _performance_config
    if _performance_config is None:
        _performance_config = PerformanceConfigManager()
    return _performance_config.config