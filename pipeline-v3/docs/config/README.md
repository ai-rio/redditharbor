# Pipeline v3 Configuration Guide

<div align="center">

**Environment Setup and Configuration Management**

*Complete guide to configuring RedditHarbor Pipeline v3*

</div>

## 📋 Table of Contents

- [⚙️ Environment Variables](#️-environment-variables)
- [🔧 Configuration Files](#-configuration-files)
- [🗄️ Database Configuration](#️-database-configuration)
- [🔑 API Configuration](#-api-configuration)
- [🚀 Production Configuration](#-production-configuration)

---

## ⚙️ Environment Variables

### Required `.env` File
Create a `.env` file in the pipeline-v3 root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Reddit API Configuration
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditHarbor/1.0

# OpenRouter API Configuration (Optional)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Pipeline Configuration
LOG_LEVEL=INFO
BATCH_SIZE=100
MAX_RETRIES=3
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Quality Thresholds
MIN_QUALITY_SCORE=0.7
MIN_TRUST_SCORE=0.6
MIN_OPPORTUNITY_SCORE=70.0
```

### Environment Setup Steps

#### 1. Copy Template
```bash
# Copy the example configuration
cp .env.example .env

# Edit with your values
nano .env
```

#### 2. Database Configuration
```bash
# For local Supabase development
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=your_local_anon_key
```

#### 3. Reddit API Setup
1. Visit https://www.reddit.com/prefs/apps
2. Create a "script" type app
3. Get client_id and client_secret
4. Add to `.env` file

#### 4. OpenRouter API (Optional)
1. Visit https://openrouter.ai
2. Create account and get API key
3. Add to `.env` file (or leave empty to use mock LLM)

---

## 🔧 Configuration Files

### Configuration Loading
Configuration is loaded through the `pipeline_v3.config` module:

```python
from pipeline_v3.config import get_config

config = get_config()
print(f"Database URL: {config.database_url}")
print(f"Batch size: {config.batch_size}")
```

### Default Configuration
```python
# pipeline_v3/config/settings.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # Reddit API
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "RedditHarbor/1.0"

    # OpenRouter API
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "anthropic/claude-3.5-sonnet"

    # Pipeline Settings
    log_level: str = "INFO"
    batch_size: int = 100
    max_retries: int = 3
    rate_limit_requests_per_minute: int = 60

    # Quality Thresholds
    min_quality_score: float = 0.7
    min_trust_score: float = 0.6
    min_opportunity_score: float = 70.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### Configuration Validation
```python
def validate_config(config: Settings) -> bool:
    """Validate required configuration settings."""

    required_vars = [
        "database_url",
        "reddit_client_id",
        "reddit_client_secret"
    ]

    for var in required_vars:
        if not getattr(config, var, None):
            raise ValueError(f"Missing required configuration: {var}")

    return True
```

---

## 🗄️ Database Configuration

### Local Development
```bash
# Start Supabase locally
supabase start

# Check status
supabase status

# Run migrations
supabase db push
```

### Database URL Formats
```bash
# Local Supabase
postgresql://postgres:postgres@127.0.0.1:54322/postgres

# Production Supabase
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Amazon RDS
postgresql://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
```

### Connection Pooling
```python
# Database connection configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

### Database Initialization
```bash
# Initialize database schema
python -m pipeline_v3.scripts.init_database

# Check schema
python -m pipeline_v3.scripts.check_schema

# Seed test data (optional)
python -m pipeline_v3.scripts.seed_test_data
```

---

## 🔑 API Configuration

### Reddit API Configuration

#### Required Settings
```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=RedditHarbor/1.0
```

#### Rate Limiting Configuration
```python
REDDIT_RATE_LIMIT = {
    "requests_per_minute": 60,
    "burst_requests": 300,
    "burst_window_seconds": 600,
    "backoff_factor": 2,
    "max_retries": 3
}
```

#### Reddit App Setup
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" as app type
4. Set name: "RedditHarbor Pipeline v3"
5. Set about url: your repository URL
6. Set redirect uri: `http://localhost:8080`

### OpenRouter API Configuration

#### Required Settings
```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

#### Supported Models
```python
SUPPORTED_MODELS = [
    "anthropic/claude-3.5-sonnet",     # Default
    "openai/gpt-4o",                   # Alternative
    "google/gemini-pro",               # Alternative
    "meta-llama/llama-3.1-405b-instruct"  # Alternative
]
```

#### LLM Rate Limiting
```python
LLM_RATE_LIMIT = {
    "requests_per_minute": 100,
    "tokens_per_minute": 150000,
    "backoff_factor": 1.5,
    "max_retries": 3
}
```

---

## 🚀 Production Configuration

### Production Environment Variables
```env
# Production Database
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/redditharbor
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_prod_anon_key
SUPABASE_SERVICE_KEY=your_prod_service_key

# Production Reddit API
REDDIT_CLIENT_ID=prod_client_id
REDDIT_CLIENT_SECRET=prod_client_secret
REDDIT_USER_AGENT=RedditHarbor-Prod/1.0

# Production LLM API
OPENROUTER_API_KEY=prod_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Production Pipeline Settings
LOG_LEVEL=WARNING
BATCH_SIZE=500
MAX_RETRIES=5
RATE_LIMIT_REQUESTS_PER_MINUTE=120

# Production Quality Thresholds
MIN_QUALITY_SCORE=0.8
MIN_TRUST_SCORE=0.7
MIN_OPPORTUNITY_SCORE=80.0
```

### Security Configuration
```python
# Security settings
SECURITY_CONFIG = {
    "enable_ssl_verification": True,
    "api_key_rotation_days": 90,
    "max_request_size_mb": 10,
    "enable_request_logging": True,
    "sensitive_data_masking": True
}
```

### Logging Configuration
```python
# Production logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler"
        },
        "file": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "/var/log/pipeline_v3.log",
            "mode": "a"
        }
    },
    "loggers": {
        "pipeline_v3": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}
```

### Monitoring Configuration
```python
# Production monitoring
MONITORING_CONFIG = {
    "enable_metrics": True,
    "metrics_port": 9090,
    "health_check_endpoint": "/health",
    "prometheus_enabled": True,
    "alert_webhook_url": "https://hooks.slack.com/your-webhook"
}
```

---

## 🔍 Configuration Validation

### Validation Script
```bash
# Validate configuration
python -m pipeline_v3.scripts.validate_config

# Expected output:
# ✓ Database configuration valid
# ✓ Reddit API credentials valid
# ✓ OpenRouter API accessible
# ✓ Quality thresholds valid
# ✓ Configuration complete
```

### Test Configuration
```bash
# Test all API connections
python -m pipeline_v3.scripts.check_connections

# Test specific connections
python -m pipeline_v3.scripts.check_reddit_connection
python -m pipeline_v3.scripts.check_database_connection
python -m pipeline_v3.scripts.check_llm_connection
```

### Configuration Diagnostics
```bash
# Full diagnostics
python -m pipeline_v3.scripts.diagnostics

# Output includes:
# - Environment variables status
# - API connectivity tests
# - Database schema validation
# - Configuration completeness check
```

---

## 📝 Configuration Best Practices

### 1. Environment Management
```bash
# Use different .env files for different environments
cp .env.example .env.development
cp .env.example .env.staging
cp .env.example .env.production

# Load specific environment
export ENVIRONMENT=development
# Pipeline will automatically load .env.${ENVIRONMENT}
```

### 2. Secret Management
```bash
# Use environment-specific secret files
.env.local           # Local development secrets
.env.development     # Development environment
.env.staging        # Staging environment
.env.production     # Production secrets

# Add all .env* files to .gitignore
echo ".env*" >> .gitignore
```

### 3. Configuration Testing
```bash
# Always validate configuration in CI/CD
name: Validate Configuration
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Validate Config
        run: |
          python -m pipeline_v3.scripts.validate_config
          python -m pipeline_v3.scripts.check_connections
```

---

## 🆘 Troubleshooting

### Common Configuration Issues

#### 1. Database Connection Failed
```bash
# Check database status
supabase status

# Test connection manually
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

# Common solutions:
# - Start Supabase: supabase start
# - Check DATABASE_URL format
# - Verify database is running
```

#### 2. Reddit API Authentication
```bash
# Test Reddit API
python -c "
import praw
reddit = praw.Reddit(
    client_id='YOUR_ID',
    client_secret='YOUR_SECRET',
    user_agent='RedditHarbor/1.0'
)
print(reddit.user.me())
"
```

#### 3. Missing Environment Variables
```bash
# Check for missing variables
python -m pipeline_v3.scripts.validate_config

# List all environment variables
env | grep -E "(REDDIT|OPENROUTER|DATABASE|SUPABASE)"
```

---

<div align="center">

**⚙️ Configuration Complete!**

**Your Pipeline v3 is now properly configured and ready to run.**

</div>