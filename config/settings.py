# RedditHarbor Configuration
# Replace with your actual Reddit API credentials

# Reddit API Configuration
REDDIT_PUBLIC = "jEAmLlbzr0TvxbR1W0ziBQ"
REDDIT_SECRET = "g2r7vhtAB_kEmCeGcXXEM_KIzDh8iQ"
REDDIT_USER_AGENT = "project:Guz-Harbor (u/carlos-dev)"

# Local Supabase Configuration (for multi-project setup)
SUPABASE_URL = "http://127.0.0.1:54321"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

# Remote Supabase (if needed for production/deployment)
# SUPABASE_URL = "https://<your-supabase-project>.supabase.co"
# SUPABASE_KEY = "<your-supabase-service-role-key>"

# RedditHarbor Database Configuration (using our dedicated schema)
DB_CONFIG = {"user": "redditor", "submission": "submission", "comment": "comment"}

# Collection Configuration
DEFAULT_SUBREDDITS = ["python", "MachineLearning", "datascience", "learnprogramming"]
DEFAULT_SORT_TYPES = ["hot", "top", "new"]
DEFAULT_LIMIT = 100

# Privacy Settings
ENABLE_PII_ANONYMIZATION = False  # Temporarily disabled for testing research framework
