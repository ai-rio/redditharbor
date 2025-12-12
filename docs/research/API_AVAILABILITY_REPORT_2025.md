# API Availability Report 2025

## Executive Summary

This report provides a comprehensive analysis of the availability, setup process, and access requirements for four critical APIs: Google Trends, GitHub, ProductHunt, and SimilarWeb. Each API has distinct characteristics regarding accessibility, cost, and implementation complexity.

## API Comparison Table

| API             | Priority  | Cost                     | Official Status    | Setup Time | Authentication       | Rate Limits                     |
|-----------------|-----------|--------------------------|--------------------|------------|---------------------|---------------------------------|
| Google Trends   | 🔴 HIGH   | FREE ( unofficial)       | Alpha Only         | 2 min      | None Required       | Self-imposed (60s intervals)    |
| GitHub API      | 🔴 HIGH   | FREE / Paid tiers        | Fully Available    | 5 min      | PAT / OAuth / Apps  | 5,000/hr (auth) / 60/hr (unauth) |
| ProductHunt API | 🟡 MEDIUM | FREE / Enterprise        | Fully Available    | 10 min     | OAuth 2.0           | 6,250 complexity points / 15min  |
| SimilarWeb API  | 🟡 MEDIUM | PAID / Free Trial        | Fully Available    | 10 min     | API Key             | 10 requests/second              |

## Detailed Analysis

### 1. Google Trends API

#### Status: LIMITED ACCESS (Alpha Program)
Google officially launched the **Google Trends API (Alpha)** in July 2025, but access is currently limited to approved alpha testers.

**Key Findings:**
- Official API exists but requires application for alpha access
- Unofficial alternatives like PyTrends are widely used but rate-limited
- Google Cloud billing required for official API access

#### Setup Options:

**Option A: Official API (If Accepted into Alpha)**
1. Apply at [developers.google.com/search/apis/trends](https://developers.google.com/search/apis/trends)
2. Set up Google Cloud project with billing
3. Enable Trends API and create credentials
4. Implement with official client libraries

**Option B: PyTrends (Immediate Access)**
```python
pip install pytrends
from pytrends.request import TrendReq
pytrends = TrendReq(hl='en-US', tz=360)
```

#### Limitations:
- Alpha access approval required (not guaranteed)
- PyTrends can be rate-limited by Google
- Commercial alternatives cost $200+/month

### 2. GitHub API

#### Status: FULLY AVAILABLE
GitHub offers robust, well-documented REST v3 and GraphQL v4 APIs with generous free tiers.

**Key Findings:**
- Multiple authentication methods available
- Generous rate limits for authenticated requests
- Comprehensive Python library support
- Suitable for both individual developers and enterprises

#### Setup Process:

**Personal Access Token (Most Common)**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create fine-grained token with required permissions
3. Set expiration (recommended: 30-90 days)
4. Store securely in environment variables

```python
from github import Github
g = Github("your_personal_access_token")
```

#### Advantages:
- 5,000 requests/hour for authenticated users
- Excellent documentation and community support
- Multiple mature Python libraries (PyGithub, github3.py)
- Backwards compatibility and regular updates

### 3. ProductHunt API

#### Status: FULLY AVAILABLE (GraphQL v2)
ProductHunt provides a modern GraphQL API with comprehensive data access to product launches, makers, and community engagement.

**Key Findings:**
- GraphQL-based API with REST-like functionality
- OAuth 2.0 authentication required
- Complexity-based rate limiting (6,250 points per 15 minutes)
- Rich dataset including posts, makers, comments, and user data

#### Setup Process:

1. Create ProductHunt account
2. Register application for API access
3. Obtain client credentials
4. Implement OAuth 2.0 flow

```python
import requests
import json

# OAuth client credentials
token_response = requests.post(
    "https://api.producthunt.com/v2/oauth/token",
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
)
access_token = token_response.json()['access_token']
```

#### Key Features:
- Access to real-time product launch data
- Maker and user information
- Engagement metrics (votes, comments)
- Category and collection data

### 4. SimilarWeb API

#### Status: PAID SERVICE WITH FREE TRIAL
SimilarWeb offers enterprise-grade web analytics data with strict rate limiting and custom pricing.

**Key Findings:**
- No substantial free tier for developers
- Pricing starts at $199/month (annual billing available)
- 7-day free trial available
- Rate limited to 10 requests per second

#### Setup Process:

1. Contact SimilarWeb sales for API access
2. Select appropriate pricing tier
3. Account admin generates API keys
4. Implement with custom Python library or direct REST calls

```python
# Using community library
pip install SimilarWeb-Python
from similarweb import SimilarWeb
```

#### Limitations:
- Requires sales contact for pricing
- Limited free access (7-day trial only)
- Strict rate limiting requires batch processing
- Enterprise focus rather than developer-friendly

## Recommendations

### For Quick Development (2-5 min setup):
1. **GitHub API** - Immediate access, generous limits, excellent documentation
2. **Google Trends (PyTrends)** - Quick setup but limited reliability

### For Production Applications:
1. **GitHub API** - Scalable, reliable, multiple authentication options
2. **ProductHunt API** - Rich data for competitive intelligence
3. **Google Trends** - Apply for official API or use commercial alternatives

### Budget Considerations:
- **Zero Cost**: GitHub API, Google Trends (PyTrends), ProductHunt API
- **Low Cost ($199+/month)**: SimilarWeb Starter
- **Enterprise**: SimilarWeb Professional/Enterprise, ProductHunt high-volume

## Implementation Priority

1. **Immediate (This Week)**:
   - GitHub API for tech maturity analysis
   - PyTrends for initial search trend data

2. **Short-term (Next 2 Weeks)**:
   - ProductHunt API for competitor intelligence
   - Apply for Google Trends official API access

3. **Long-term (Monthly)**:
   - Evaluate SimilarWeb API based on budget and data needs
   - Consider commercial Google Trends alternatives if needed

## Code Templates

### GitHub API Template
```python
from github import Github
import os

# Setup
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
g = Github(GITHUB_TOKEN)

# Example: Get repository information
repo = g.get_repo("owner/repository")
print(f"Stars: {repo.stargazers_count}")
print(f"Forks: {repo.forks_count}")
print(f"Language: {repo.language}")
```

### ProductHunt API Template
```python
import requests
import os

# Setup
CLIENT_ID = os.getenv('PRODUCTHUNT_CLIENT_ID')
CLIENT_SECRET = os.getenv('PRODUCTHUNT_CLIENT_SECRET')

# Get token
token_response = requests.post(
    "https://api.producthunt.com/v2/oauth/token",
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
)
token = token_response.json()['access_token']

# GraphQL query
query = """
query {
    posts(first: 10) {
        edges {
            node {
                name
                tagline
                url
                votesCount
                createdAt
            }
        }
    }
}
"""

response = requests.post(
    'https://api.producthunt.com/v2/api/graphql',
    json={'query': query},
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
)
data = response.json()
```

### Google Trends (PyTrends) Template
```python
from pytrends.request import TrendReq
import time
import pandas as pd

# Setup
pytrends = TrendReq(hl='en-US', tz=360)

# Keywords to analyze
keywords = ['python', 'javascript', 'rust']

# Build payload
pytrends.build_payload(
    kw_list=keywords,
    timeframe='today 12-m',
    geo='US',
    gprop='jobs'
)

# Get data
interest_over_time = pytrends.interest_over_time()
related_queries = pytrends.related_queries()

# Rate limiting
time.sleep(60)  # Wait between requests
```

## Conclusion

All four APIs are available with varying levels of accessibility. GitHub and ProductHunt offer immediate access with developer-friendly terms. Google Trends is accessible through unofficial methods but requires careful implementation. SimilarWeb provides valuable data but requires budget allocation.

For development priorities: start with GitHub API for tech analysis, implement PyTrends for search trend insights, and evaluate ProductHunt API for competitive intelligence. Consider SimilarWeb if budget allows for comprehensive market validation data.
