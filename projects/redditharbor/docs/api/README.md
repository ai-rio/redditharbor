# RedditHarbor API Reference

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">Complete API Documentation</h2>
  <p style="color: #004E89;">Functions, classes, and methods reference</p>
</div>

## Table of Contents

- [Core Classes](#core-classes)
- [Data Collection Methods](#data-collection-methods)
- [Database Operations](#database-operations)
- [Utility Functions](#utility-functions)
- [Error Handling](#error-handling)

---

## Core Classes

### RedditCollector

The main class for collecting Reddit data.

```python
class RedditCollector:
    def __init__(self, client_id: str, client_secret: str,
                 user_agent: str = "RedditHarbor/1.0"):
        """Initialize the Reddit collector with credentials."""
```

**Parameters:**
- `client_id` (str): Reddit API client ID
- `client_secret` (str): Reddit API client secret
- `user_agent` (str): User agent string (default: "RedditHarbor/1.0")

**Example:**
```python
collector = RedditCollector(
    client_id="your_client_id",
    client_secret="your_client_secret",
    user_agent="ResearchProject/1.0 by u/your_username"
)
```

---

## Data Collection Methods

### collect_subreddit_posts()

Collect posts from a specific subreddit.

```python
def collect_subreddit_posts(self, subreddit: str, limit: int = 100,
                          sort: str = "hot", time_filter: str = "all") -> List[Dict]:
```

**Parameters:**
- `subreddit` (str): Subreddit name (without r/)
- `limit` (int): Maximum number of posts to collect
- `sort` (str): Sort method ("hot", "new", "top", "rising")
- `time_filter` (str): Time filter for "top" sort ("hour", "day", "week", "month", "year", "all")

**Returns:**
- `List[Dict]`: List of post data dictionaries

**Example:**
```python
# Collect 100 hot posts from r/python
posts = collector.collect_subreddit_posts("python", limit=100, sort="hot")

# Collect top posts from the last month
top_posts = collector.collect_subreddit_posts(
    "datascience",
    limit=50,
    sort="top",
    time_filter="month"
)
```

### collect_post_comments()

Collect comments for a specific post.

```python
def collect_post_comments(self, post_id: str, limit: int = 100) -> List[Dict]:
```

**Parameters:**
- `post_id` (str): Reddit post ID (t3_ prefix optional)
- `limit` (int): Maximum number of comments to collect

**Returns:**
- `List[Dict]`: List of comment data dictionaries

### collect_user_data()

Collect user profile and activity data.

```python
def collect_user_data(self, username: str, include_posts: bool = True,
                     include_comments: bool = True) -> Dict:
```

**Parameters:**
- `username` (str): Reddit username (without u/)
- `include_posts` (bool): Include user's posts
- `include_comments` (bool): Include user's comments

**Returns:**
- `Dict`: User profile and activity data

---

## Database Operations

### store_to_database()

Store collected data to a database.

```python
def store_to_database(self, data: List[Dict], database_url: str,
                     table_name: str = None) -> bool:
```

**Parameters:**
- `data` (List[Dict]): Data to store
- `database_url` (str): Database connection URL
- `table_name` (str): Custom table name (optional)

**Returns:**
- `bool`: Success status

**Supported Databases:**
- PostgreSQL: `postgresql://user:password@host:port/database`
- SQLite: `sqlite:///path/to/database.db`

### create_database_schema()

Create the necessary database tables.

```python
def create_database_schema(self, database_url: str) -> bool:
```

**Parameters:**
- `database_url` (str): Database connection URL

**Returns:**
- `bool`: Success status

---

## Utility Functions

### validate_credentials()

Validate Reddit API credentials.

```python
def validate_credentials(self) -> bool:
```

**Returns:**
- `bool`: Credentials validity status

### get_rate_limit_info()

Get current API rate limit information.

```python
def get_rate_limit_info(self) -> Dict:
```

**Returns:**
- `Dict`: Rate limit information

### export_data()

Export collected data to various formats.

```python
def export_data(self, data: List[Dict], format: str,
               filename: str) -> bool:
```

**Parameters:**
- `data` (List[Dict]): Data to export
- `format` (str): Export format ("json", "csv", "xlsx")
- `filename` (str): Output filename

**Returns:**
- `bool`: Success status

---

## Error Handling

RedditHarbor uses custom exceptions for better error handling:

### RedditHarborError

Base exception class for all RedditHarbor errors.

```python
class RedditHarborError(Exception):
    """Base exception for RedditHarbor errors."""
    pass
```

### APIError

Raised for Reddit API-related errors.

```python
class APIError(RedditHarborError):
    """Raised when Reddit API returns an error."""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)
```

### DatabaseError

Raised for database-related errors.

```python
class DatabaseError(RedditHarborError):
    """Raised when database operations fail."""
    pass
```

### RateLimitError

Raised when API rate limits are exceeded.

```python
class RateLimitError(RedditHarborError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, reset_time: int = None):
        self.reset_time = reset_time
        super().__init__(f"Rate limit exceeded. Reset at {reset_time}")
```

---

## Example Usage

<div style="background: #F5F5F5; padding: 15px; border-radius: 8px; border-left: 4px solid #F7B801; margin: 20px 0;">
  <h4 style="color: #1A1A1A; margin-top: 0;">Complete Workflow Example</h4>
  <pre style="background: #1A1A1A; color: #FFF; padding: 10px; border-radius: 4px; overflow-x: auto;"><code>from redditharbor import RedditCollector
from redditharbor.exceptions import APIError, DatabaseError

try:
    # Initialize collector
    collector = RedditCollector(
        client_id="your_client_id",
        client_secret="your_client_secret"
    )

    # Validate credentials
    if collector.validate_credentials():
        print("Credentials valid!")

        # Collect data
        posts = collector.collect_subreddit_posts("python", limit=50)
        print(f"Collected {len(posts)} posts")

        # Store to database
        success = collector.store_to_database(
            posts,
            "postgresql://user:pass@localhost/redditharbor"
        )

        if success:
            print("Data stored successfully!")

except APIError as e:
    print(f"API Error: {e}")
except DatabaseError as e:
    print(f"Database Error: {e}")
except RedditHarborError as e:
    print(f"RedditHarbor Error: {e}")</code></pre>
</div>

---

## Type Definitions

```python
from typing import Dict, List, Optional, Union

# Post data structure
PostData = Dict[str, Union[str, int, float, bool]]

# Comment data structure
CommentData = Dict[str, Union[str, int, float, bool, List]]

# User data structure
UserData = Dict[str, Union[str, int, float, bool, Dict]]
```

---

## Configuration Options

RedditHarbor supports various configuration options:

```python
# Set custom rate limits
collector.set_rate_limits(requests_per_minute=60, requests_per_second=1)

# Enable privacy mode
collector.enable_privacy_mode(redact_usernames=True, redact_emails=True)

# Set retry configuration
collector.set_retry_config(max_retries=3, backoff_factor=2)
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Need more help? Check our <a href="../guides/troubleshooting.md" style="color: #004E89;">Troubleshooting Guide</a>
  </p>
</div>