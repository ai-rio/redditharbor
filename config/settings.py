# RedditHarbor Configuration
# Load environment variables with proper priority
import os
from pathlib import Path

from dotenv import load_dotenv

# =============================================================================
# ENVIRONMENT LOADING STRATEGY
# =============================================================================
# Priority order (first found wins):
# 1. .env.local (local development, gitignored, contains secrets)
# 2. .env (template/defaults, committed to repo, NO secrets)
# 3. Defaults in this file (fallback)
#
# This allows:
# - Developers to use .env.local for local secrets (never committed)
# - Production to use environment variables directly
# - .env to serve as documentation template
# =============================================================================

project_root = Path(__file__).parent.parent

# Load .env.local first (if exists), then .env (if exists)
load_dotenv(project_root / '.env.local', override=True)
load_dotenv(project_root / '.env', override=False)  # Don't override .env.local

# Reddit API Configuration
REDDIT_PUBLIC = os.getenv("REDDIT_PUBLIC", "your_reddit_public_key_here")
REDDIT_SECRET = os.getenv("REDDIT_SECRET", "your_reddit_secret_key_here")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "project:RedditHarbor (by /u/your_username)")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your_supabase_service_role_key_here")

# Error Log Configuration
ERROR_LOG_DIR = "error_log"

# Remote Supabase (if needed for production/deployment)
# SUPABASE_URL = "https://<your-supabase-project>.supabase.co"
# SUPABASE_KEY = "<your-supabase-service-role-key>"

# RedditHarbor Database Configuration (using our dedicated schema)
DB_CONFIG = {"user": "redditors", "submission": "submissions", "comment": "comments"}

# Collection Configuration - Target Finance & Health Subreddits for Opportunity Analysis
DEFAULT_SUBREDDITS = [
    # Finance & Investing Subreddits
    "personalfinance", "investing", "stocks", "Bogleheads", "financialindependence",
    "CryptoCurrency", "tax", "Accounting", "RealEstateInvesting", "FinancialCareers",

    # Health & Fitness Subreddits
    "fitness", "loseit", "bodyweightfitness", "nutrition", "keto", "running",
    "cycling", "yoga", "meditation", "mentalhealth", "fitness30plus", "homegym"
]
DEFAULT_SORT_TYPES = ["hot", "top", "new", "rising"]
DEFAULT_LIMIT = 500  # Increased limit for better opportunity analysis

# Privacy Settings
ENABLE_PII_ANONYMIZATION = False  # Temporarily disabled for testing research framework

# DLT Configuration Settings
# DLT pipeline configuration for enhanced Reddit data collection
DLT_MIN_ACTIVITY_SCORE = float(os.getenv("DLT_MIN_ACTIVITY_SCORE", "25.0"))  # Minimum subreddit activity score (0-100) - optimized for balance
DLT_TIME_FILTER = os.getenv("DLT_TIME_FILTER", "day")  # Time period for activity analysis
DLT_PIPELINE_NAME = os.getenv("DLT_PIPELINE_NAME", "reddit_harbor_activity_collection")  # DLT pipeline identifier
DLT_DATASET_NAME = os.getenv("DLT_DATASET_NAME", "reddit_activity_data")  # DLT dataset for data organization

# DLT Quality Filter Settings
DLT_QUALITY_MIN_COMMENT_LENGTH = int(os.getenv("DLT_QUALITY_MIN_COMMENT_LENGTH", "10"))  # Minimum comment character length
DLT_QUALITY_MIN_SCORE = int(os.getenv("DLT_QUALITY_MIN_SCORE", "1"))  # Minimum comment score
DLT_QUALITY_COMMENTS_PER_POST = int(os.getenv("DLT_QUALITY_COMMENTS_PER_POST", "10"))  # Max comments per post

# DLT Collection Settings
DLT_ENABLED = os.getenv("DLT_ENABLED", "false").lower() == "true"  # Enable/disable DLT collection
DLT_USE_ACTIVITY_VALIDATION = os.getenv("DLT_USE_ACTIVITY_VALIDATION", "true").lower() == "true"  # Enable activity-aware validation
DLT_MAX_SUBREDDITS_PER_RUN = int(os.getenv("DLT_MAX_SUBREDDITS_PER_RUN", "50"))  # Maximum subreddits to process per run

# =============================================================================
# LLM CONFIGURATION (OpenRouter for unified model access)
# =============================================================================
# RedditHarbor uses OpenRouter as the unified LLM gateway, which provides:
# - Access to multiple model providers (Anthropic, OpenAI, Google, etc.)
# - Unified API for cost tracking and model management
# - Pay-as-you-go pricing without multiple subscriptions
# - Automatic failover and load balancing
#
# Configuration Priority:
# 1. Component-specific model (e.g., MONETIZATION_LLM_MODEL)
# 2. Global model (OPENROUTER_MODEL)
# 3. Default (anthropic/claude-haiku-4.5 for cost efficiency)
# =============================================================================

# OpenRouter API Key (Required)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Primary LLM Model (used by EnhancedLLMProfiler and as fallback)
# Available models via OpenRouter:
# - anthropic/claude-haiku-4.5 (fast, cheap: $1/$5 per 1M tokens)
# - anthropic/claude-3.5-sonnet (balanced: $3/$15 per 1M tokens)
# - openai/gpt-4o-mini (very cheap: $0.15/$0.60 per 1M tokens)
# - openai/gpt-4o (powerful: $2.50/$10 per 1M tokens)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")

# =============================================================================
# HYBRID STRATEGY CONFIGURATION
# =============================================================================

# Option A: LLM-Enhanced Monetization Analysis
# Uses DSPy with 4 analyzers for sophisticated monetization scoring
MONETIZATION_LLM_ENABLED = os.getenv("MONETIZATION_LLM_ENABLED", "true").lower() == "true"
MONETIZATION_LLM_THRESHOLD = float(os.getenv("MONETIZATION_LLM_THRESHOLD", "60.0"))

# Monetization analyzer can use different model for cost optimization
# If not set, inherits from OPENROUTER_MODEL
# Set to gpt-4o-mini if you want cheaper monetization analysis
MONETIZATION_LLM_MODEL = os.getenv("MONETIZATION_LLM_MODEL", OPENROUTER_MODEL)

# Option B: Customer Lead Extraction
# Regex-based extraction (zero LLM cost)
LEAD_EXTRACTION_ENABLED = os.getenv("LEAD_EXTRACTION_ENABLED", "true").lower() == "true"
LEAD_EXTRACTION_THRESHOLD = float(os.getenv("LEAD_EXTRACTION_THRESHOLD", "60.0"))

# Optional: Slack webhook for hot lead notifications
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# =============================================================================
# AGNO AND AGENTOPS CONFIGURATION
# =============================================================================
# Cost tracking and multi-agent architecture configuration

# AgentOps API Key for comprehensive cost tracking
# Optional: If not provided, cost tracking will be disabled
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")

# Monetization analyzer framework selection
# "dspy" for original DSPy implementation
# "agno" for new multi-agent architecture with cost tracking
MONETIZATION_FRAMEWORK = os.getenv("MONETIZATION_FRAMEWORK", "agno")

# Agno-specific settings
AGNO_TIMEOUT = int(os.getenv("AGNO_TIMEOUT", "30"))  # Timeout in seconds
AGNO_MAX_RETRIES = int(os.getenv("AGNO_MAX_RETRIES", "3"))  # Max retry attempts

# =============================================================================
# HTTP CLIENT CONFIGURATION (Connection Pool Management)
# =============================================================================
# Configure connection pooling to prevent exhaustion with multiple LLM clients
# - max_connections: Total connections across all hosts
# - max_keepalive_connections: Reusable connections (improves performance)
# - Timeout: Prevent hanging requests
# =============================================================================

HTTP_MAX_CONNECTIONS = int(os.getenv("HTTP_MAX_CONNECTIONS", "100"))
HTTP_MAX_KEEPALIVE = int(os.getenv("HTTP_MAX_KEEPALIVE", "20"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

# =============================================================================
# JINA READER API CONFIGURATION (Data-Driven Market Validation)
# =============================================================================
# Jina AI Reader API for fetching and extracting web content
# - r.jina.ai: Reads and extracts content from URLs (500 RPM free tier)
# - s.jina.ai: Web search with LLM-optimized results (100 RPM free tier)
# Used for data-driven monetization validation with real market evidence
# =============================================================================

JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_READER_BASE_URL = "https://r.jina.ai/"
JINA_SEARCH_BASE_URL = "https://s.jina.ai/"
JINA_READ_RPM_LIMIT = int(os.getenv("JINA_READ_RPM_LIMIT", "500"))
JINA_SEARCH_RPM_LIMIT = int(os.getenv("JINA_SEARCH_RPM_LIMIT", "100"))
JINA_REQUEST_TIMEOUT = int(os.getenv("JINA_REQUEST_TIMEOUT", "30"))

# Market validation settings
MARKET_VALIDATION_ENABLED = os.getenv("MARKET_VALIDATION_ENABLED", "true").lower() == "true"
MARKET_VALIDATION_CACHE_TTL = int(os.getenv("MARKET_VALIDATION_CACHE_TTL", "86400"))  # 24 hours default
MARKET_VALIDATION_MIN_COMPETITORS = int(os.getenv("MARKET_VALIDATION_MIN_COMPETITORS", "3"))
MARKET_VALIDATION_MAX_SEARCHES = int(os.getenv("MARKET_VALIDATION_MAX_SEARCHES", "10"))

# =============================================================================
# HYBRID WEB CRAWLER CONFIGURATION (Crawl4AI + Jina AI)
# =============================================================================
# Smart crawler that combines Crawl4AI (primary) with Jina AI (fallback)
# - Crawl4AI: No token limits, full browser control, better for complex sites
# - Jina AI: Simple API integration, good for basic content extraction
# - Automatic switching based on performance and success rates
# =============================================================================

# Enable/disable hybrid crawler functionality
HYBRID_CRAWLER_ENABLED = os.getenv("HYBRID_CRAWLER_ENABLED", "true").lower() == "true"

# Crawler preferences
HYBRID_CRAWLER_ENABLE_CRAWL4AI = os.getenv("HYBRID_CRAWLER_ENABLE_CRAWL4AI", "true").lower() == "true"
HYBRID_CRAWLER_ENABLE_JINA_FALLBACK = os.getenv("HYBRID_CRAWLER_ENABLE_JINA_FALLBACK", "true").lower() == "true"

# Performance thresholds
HYBRID_CRAWLER_PERFORMANCE_THRESHOLD = float(os.getenv("HYBRID_CRAWLER_PERFORMANCE_THRESHOLD", "80.0"))  # Switch if success rate below this
HYBRID_CRAWLER_ENABLE_QUALITY_COMPARISON = os.getenv("HYBRID_CRAWLER_ENABLE_QUALITY_COMPARISON", "false").lower() == "true"

# Crawl4AI specific settings
HYBRID_CRAWLER_CRAWL4AI_TIMEOUT = int(os.getenv("HYBRID_CRAWLER_CRAWL4AI_TIMEOUT", "30"))  # seconds
HYBRID_CRAWLER_CRAWL4AI_HEADLESS = os.getenv("HYBRID_CRAWLER_CRAWL4AI_HEADLESS", "true").lower() == "true"
HYBRID_CRAWLER_CRAWL4AI_VIEWPORT_WIDTH = int(os.getenv("HYBRID_CRAWLER_CRAWL4AI_VIEWPORT_WIDTH", "1920"))
HYBRID_CRAWLER_CRAWL4AI_VIEWPORT_HEIGHT = int(os.getenv("HYBRID_CRAWLER_CRAWL4AI_VIEWPORT_HEIGHT", "1080"))

# Fallback behavior
HYBRID_CRAWLER_USE_FALLBACK = os.getenv("HYBRID_CRAWLER_USE_FALLBACK", "true").lower() == "true"
HYBRID_CRAWLER_FALLBACK_TIMEOUT = int(os.getenv("HYBRID_CRAWLER_FALLBACK_TIMEOUT", "30"))  # seconds

# Token usage monitoring for Jina AI
HYBRID_CRAWLER_JINA_TOKEN_THRESHOLD = int(os.getenv("HYBRID_CRAWLER_JINA_TOKEN_THRESHOLD", "1000000"))  # Switch to Crawl4AI near token limits
HYBRID_CRAWLER_MONITOR_TOKEN_USAGE = os.getenv("HYBRID_CRAWLER_MONITOR_TOKEN_USAGE", "true").lower() == "true"

# =============================================================================
# DATABASE CONFIGURATION FUNCTION
# =============================================================================

def get_database_config():
    """
    Get database configuration for PostgreSQL connection.

    Returns:
        dict: Database connection parameters for asyncpg
    """
    # Parse Supabase URL to extract connection details
    supabase_url = SUPABASE_URL
    if supabase_url.endswith('/'):
        supabase_url = supabase_url[:-1]

    # Extract host and port from Supabase URL
    if 'localhost' in supabase_url or '127.0.0.1' in supabase_url:
        # Local development setup
        host = '127.0.0.1'
        port = 54322  # Default Supabase local port
    else:
        # Production setup - parse from URL
        # Expected format: https://<project>.supabase.co
        host = supabase_url.replace('https://', '').replace('http://', '')
        port = 5432  # Default PostgreSQL port

    return {
        'host': host,
        'port': port,
        'user': 'postgres',
        'password': 'postgres',
        'database': 'postgres',
        'min_size': 2,
        'max_size': 10
    }


def get_redis_config():
    """
    Get Redis configuration for caching.

    Returns:
        dict: Redis connection parameters
    """
    # Redis configuration with local development defaults
    host = os.getenv('REDIS_HOST', 'localhost')
    port = int(os.getenv('REDIS_PORT', 6379))
    db = int(os.getenv('REDIS_DB', 0))
    password = os.getenv('REDIS_PASSWORD', None)

    return {
        'host': host,
        'port': port,
        'db': db,
        'password': password,
        'url': f"redis://{host}:{port}/{db}"
    }
