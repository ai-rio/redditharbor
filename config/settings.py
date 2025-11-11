# RedditHarbor Configuration
# Load environment variables
import os

from dotenv import load_dotenv

# Load from .env if it exists
load_dotenv('.env')

# Reddit API Configuration
# Get from environment or use placeholders
REDDIT_PUBLIC = os.getenv("REDDIT_PUBLIC", "your_reddit_public_key_here")
REDDIT_SECRET = os.getenv("REDDIT_SECRET", "your_reddit_secret_key_here")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "project:RedditHarbor (by /u/your_username)")

# Supabase Configuration
# Get from environment or use defaults
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your_supabase_service_role_key_here")

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
DLT_MIN_ACTIVITY_SCORE = float(os.getenv("DLT_MIN_ACTIVITY_SCORE", "50.0"))  # Minimum subreddit activity score (0-100)
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
