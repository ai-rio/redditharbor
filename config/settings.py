# RedditHarbor Configuration
# Load environment variables
import os
from dotenv import load_dotenv

# Load from .env.local if it exists
load_dotenv('.env.local')

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
