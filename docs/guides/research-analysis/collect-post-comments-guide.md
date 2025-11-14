# Comment Collection Guide - DLT Extension 1.1

## Overview

The `collect_post_comments()` function collects all comments from Reddit submissions with threading metadata, enabling sophisticated discussion analysis and opportunity research.

**Extension Status:** Production Ready (v1.0)  
**API Stability:** Stable  
**Blocking:** Phase 1 scripts (collect_commercial_data.py, opportunity research)

---

## Quick Start

### Basic Usage

```python
from core.dlt_collection import collect_post_comments

# Collect comments from a single submission
comments = collect_post_comments('abc123')

# Collect from multiple submissions
comments = collect_post_comments([
    'abc123',
    'def456',
    'ghi789'
])

# Use existing Reddit client
import praw
reddit = praw.Reddit(...)
comments = collect_post_comments('abc123', reddit_client=reddit)
```

### Comment Data Structure

Each comment returned has this schema:

```python
{
    "comment_id": "xyz789",           # Reddit comment ID
    "submission_id": "abc123",        # Parent submission ID
    "author": "john_doe",              # Reddit username ('[deleted]' if removed)
    "body": "Great point!",            # Comment text content
    "score": 42,                       # Upvote score
    "created_utc": 1704067200,         # Unix timestamp
    "parent_id": "t1_parent_cmt",      # Parent comment ID (t1_*) or submission (t3_*)
    "depth": 1,                        # 0 = top-level, 1 = reply to top-level, etc.
}
```

---

## Detailed Function Reference

### Function Signature

```python
def collect_post_comments(
    submission_ids: List[str] | str,
    reddit_client: Optional[praw.Reddit] = None,
    merge_disposition: str = "merge",
    state_key: Optional[str] = None
) -> List[Dict[str, Any]] | bool:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `submission_ids` | `str` or `List[str]` | Required | Single ID (e.g., 'abc123') or list of IDs |
| `reddit_client` | `praw.Reddit` | None | Existing Reddit client; creates new if None |
| `merge_disposition` | `str` | "merge" | DLT write mode: 'merge', 'append', 'replace' |
| `state_key` | `str` | None | Future: incremental state tracking key |

### Return Values

**Success:** List of comment dictionaries

```python
[
    {"comment_id": "...", "submission_id": "...", ...},
    {"comment_id": "...", "submission_id": "...", ...},
    ...
]
```

**Empty Result:** Empty list `[]` if submission exists but has no comments

**Error Handling:** Returns empty list on errors (logged to `error_log/`)

---

## Usage Examples

### Example 1: Collect Comments from Single Submission

```python
from core.dlt_collection import collect_post_comments
import json

# Fetch comments from a specific Reddit post
comments = collect_post_comments('abc123')

print(f"Collected {len(comments)} comments")

# Save to JSON
with open('comments.json', 'w') as f:
    json.dump(comments, f, indent=2)

# Output:
# Collecting comments from 1 submission(s)...
# Processing submission: abc123
# ✓ Collected 142 comments from abc123 (3 deleted/removed)
# 
# ✓ Total comments collected: 142
#   - Merge disposition: merge
#   - Ready for DLT pipeline (use primary_key='comment_id')
```

### Example 2: Multi-Submission Collection with Stats

```python
from core.dlt_collection import collect_post_comments
from collections import defaultdict

# Collect from multiple posts
submission_ids = ['abc123', 'def456', 'ghi789']
all_comments = collect_post_comments(submission_ids)

# Analyze by submission
by_submission = defaultdict(list)
for comment in all_comments:
    by_submission[comment['submission_id']].append(comment)

# Print stats
for sub_id, comments in by_submission.items():
    avg_score = sum(c['score'] for c in comments) / len(comments)
    max_depth = max(c['depth'] for c in comments)
    print(f"r/{sub_id}: {len(comments)} comments, "
          f"avg score: {avg_score:.1f}, max depth: {max_depth}")

# Output:
# r/abc123: 142 comments, avg score: 12.3, max depth: 5
# r/def456: 87 comments, avg score: 8.7, max depth: 3
# r/ghi789: 156 comments, avg score: 15.2, max depth: 7
```

### Example 3: Filter Comments by Depth (Threading Analysis)

```python
from core.dlt_collection import collect_post_comments

comments = collect_post_comments('abc123')

# Get only top-level comments (direct replies to post)
top_level = [c for c in comments if c['depth'] == 0]

# Get only nested replies (depth > 1)
nested = [c for c in comments if c['depth'] > 1]

# Analyze discussion branches
for comment in top_level:
    # Find all replies to this comment
    child_comments = [
        c for c in comments
        if c['parent_id'] == f"t1_{comment['comment_id']}"
    ]
    if child_comments:
        avg_score = sum(c['score'] for c in child_comments) / len(child_comments)
        print(f"Top comment by {comment['author']}: "
              f"{len(child_comments)} replies, avg score: {avg_score:.1f}")
```

### Example 4: DLT Pipeline Integration

```python
from core.dlt_collection import collect_post_comments, create_dlt_pipeline
import dlt

# Collect comments
comments = collect_post_comments(['abc123', 'def456'])

# Load directly to Supabase using DLT
pipeline = create_dlt_pipeline()
load_info = pipeline.run(
    comments,
    table_name="comments",
    write_disposition="merge",
    primary_key="comment_id"
)

print(f"Loaded {len(comments)} comments to Supabase")
print(f"Merge disposition prevents duplicates on re-runs")
```

### Example 5: Error Handling and Logging

```python
from core.dlt_collection import collect_post_comments
from pathlib import Path

# Try to collect from invalid submission
comments = collect_post_comments('invalid_id_xyz')

# Returns empty list, errors logged to error_log/
print(f"Collected {len(comments)} comments")

# Check error logs
error_logs = list(Path('error_log').glob('collect_comments_*.log'))
if error_logs:
    with open(error_logs[-1]) as f:
        print(f.read())

# Output:
# Collected 0 comments
# 2025-11-07 14:30:00,123 - ERROR - Invalid submission ID: invalid_id_xyz
```

### Example 6: Reuse Reddit Client (Efficient)

```python
from core.dlt_collection import collect_post_comments, get_reddit_client

# Initialize client once
reddit = get_reddit_client()

# Reuse for multiple collections
submission_ids = ['abc123', 'def456', 'ghi789']

all_comments = []
for sub_id in submission_ids:
    comments = collect_post_comments(sub_id, reddit_client=reddit)
    all_comments.extend(comments)

print(f"Total: {len(all_comments)} comments from {len(submission_ids)} submissions")
# More efficient: 1 client initialization instead of 3
```

---

## Advanced Usage

### Threading Analysis

```python
from core.dlt_collection import collect_post_comments

def analyze_discussion_tree(submission_id):
    """Analyze the threaded structure of a discussion"""
    comments = collect_post_comments(submission_id)
    
    # Build parent-child map
    thread_structure = {}
    for comment in comments:
        parent_id = comment['parent_id']
        if parent_id not in thread_structure:
            thread_structure[parent_id] = []
        thread_structure[parent_id].append(comment)
    
    # Find longest discussion branch
    def get_branch_depth(comment_id, depth=0):
        if comment_id not in thread_structure:
            return depth
        children = thread_structure.get(f"t1_{comment_id}", [])
        if not children:
            return depth
        return max(get_branch_depth(c['comment_id']) for c in children) + 1
    
    max_depth = max(
        get_branch_depth(c['comment_id'])
        for c in thread_structure.get(f"t3_{submission_id}", [])
    )
    
    return {
        'total_comments': len(comments),
        'top_level': len(thread_structure.get(f"t3_{submission_id}", [])),
        'max_branch_depth': max_depth,
        'structure': thread_structure
    }

# Usage
analysis = analyze_discussion_tree('abc123')
print(f"Discussion has {analysis['total_comments']} comments")
print(f"Top level comments: {analysis['top_level']}")
print(f"Maximum nesting depth: {analysis['max_branch_depth']}")
```

### Sentiment Analysis on Comments

```python
from core.dlt_collection import collect_post_comments
from textblob import TextBlob  # Install: pip install textblob

comments = collect_post_comments('abc123')

# Score sentiment
for comment in comments:
    blob = TextBlob(comment['body'])
    polarity = blob.sentiment.polarity  # -1 to 1
    
    # Categorize
    if polarity > 0.5:
        sentiment = "positive"
    elif polarity < -0.5:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    comment['sentiment'] = sentiment
    comment['polarity'] = polarity

# Analyze results
positive = sum(1 for c in comments if c['sentiment'] == 'positive')
negative = sum(1 for c in comments if c['sentiment'] == 'negative')
neutral = sum(1 for c in comments if c['sentiment'] == 'neutral')

print(f"Sentiment distribution:")
print(f"  Positive: {positive} ({positive/len(comments)*100:.1f}%)")
print(f"  Negative: {negative} ({negative/len(comments)*100:.1f}%)")
print(f"  Neutral: {neutral} ({neutral/len(comments)*100:.1f}%)")
```

---

## Integration with Phase 1 Scripts

### collect_commercial_data.py Integration

```python
# In scripts/collect_commercial_data.py

from core.dlt_collection import collect_post_comments, collect_problem_posts

# Step 1: Collect problem posts
problem_posts = collect_problem_posts(
    subreddits=['SaaS', 'startups', 'productivity'],
    limit=100
)

# Step 2: Extract submission IDs
submission_ids = [post['id'] for post in problem_posts]

# Step 3: Collect comments from those posts
comments = collect_post_comments(submission_ids)

# Step 4: Filter for monetization signals
monetization_comments = []
keywords = ['price', 'cost', 'subscription', 'willing to pay', 'would pay']

for comment in comments:
    body_lower = comment['body'].lower()
    if any(kw in body_lower for kw in keywords):
        monetization_comments.append(comment)

print(f"Found {len(monetization_comments)} comments with monetization signals")

# Step 5: Load to Supabase for analysis
from core.dlt_collection import create_dlt_pipeline
pipeline = create_dlt_pipeline()
pipeline.run(
    monetization_comments,
    table_name="commercial_opportunities",
    write_disposition="merge"
)
```

---

## Error Handling

### Common Error Scenarios

**Scenario 1: Invalid Submission ID**
```python
comments = collect_post_comments('invalid_xyz')
# Returns: []
# Logged: error_log/collect_comments_*.log
```

**Scenario 2: API Rate Limit**
```python
# PRAW handles automatically with exponential backoff
comments = collect_post_comments(['sub1', 'sub2', 'sub3'])
# If rate limited, waits and retries automatically
```

**Scenario 3: Deleted/Removed Comments**
```python
comments = collect_post_comments('abc123')
# Deleted comments automatically filtered:
# ✓ Collected 150 comments from abc123 (5 deleted/removed)
```

**Scenario 4: Submission with No Comments**
```python
comments = collect_post_comments('empty_submission')
# Returns: []
# No error - empty submissions are valid
```

---

## Performance Characteristics

### Speed Metrics

- **Small submissions (10-50 comments):** ~1-2 seconds
- **Medium submissions (100-500 comments):** ~5-10 seconds
- **Large submissions (500+ comments):** ~15-30 seconds (depends on nesting)

### Rate Limiting

- Respects Reddit API rate limits (60 requests/minute for authenticated users)
- PRAW handles backoff automatically
- No manual rate limiting needed

### Memory Usage

- Comments stored in-memory (list of dicts)
- ~1KB per comment average
- 1000 comments ≈ 1MB memory

---

## Troubleshooting

### Issue: Returns empty list for valid submission
**Possible causes:**
- Submission deleted or removed
- Comment content not loading (rare API issue)
- Invalid submission ID format

**Solution:**
```python
# Check error log
from pathlib import Path
error_logs = list(Path('error_log').glob('collect_comments_*.log'))
if error_logs:
    print(open(error_logs[-1]).read())

# Verify submission exists
import praw
reddit = praw.Reddit(...)
sub = reddit.submission(id='your_id')
print(sub.title)  # Will raise exception if invalid
```

### Issue: Comments missing authors
**Cause:** Deleted/removed comments are filtered

**Expected behavior:** Deleted comments excluded (author = None → skipped)

### Issue: Slow collection for large threads
**Cause:** Deep nesting requires more API calls

**Solution:** Increase `replace_more(limit=0)` to control memory

---

## Migration from Legacy Collection

### From Manual Collection

**Old Way:**
```python
# Manual collection with manual error handling
for submission in subreddit.new(limit=100):
    for comment in submission.comments.list():
        # Manual filtering
        # Manual error handling
        # Manual storage
```

**New Way:**
```python
# Automatic collection with DLT
submission_ids = [s.id for s in subreddit.new(limit=100)]
comments = collect_post_comments(submission_ids)
```

---

## API Reference

### Function Signature
```python
def collect_post_comments(
    submission_ids: List[str] | str,
    reddit_client: Optional[praw.Reddit] = None,
    merge_disposition: str = "merge",
    state_key: Optional[str] = None
) -> List[Dict[str, Any]] | bool:
```

### Return Type Detail

**Success:**
```python
List[Dict] with keys:
  - comment_id: str
  - submission_id: str
  - author: str
  - body: str
  - score: int
  - created_utc: int (Unix timestamp)
  - parent_id: str (format: t3_* for submission, t1_* for comment)
  - depth: int (0 = top-level)
```

**Error:** Empty list `[]`

---

## Testing

Run tests:
```bash
pytest tests/test_dlt_collection_comments.py -v
```

Coverage:
- Single submission collection
- Multiple submissions
- Invalid ID handling
- Deleted comment filtering
- Data structure validation
- Error logging

---

## Related Functions

- `collect_problem_posts()` - Collect submissions with problem keywords
- `create_dlt_pipeline()` - Initialize DLT pipeline for Supabase
- `load_to_supabase()` - Load data using DLT

---

## FAQ

**Q: Can I collect from archived submissions?**
A: No, Reddit API restricts access to archived content (>6 months old)

**Q: How deep are comment threads?**
A: Typically 5-15 levels, max ~30 in extreme cases

**Q: What happens to deleted comments?**
A: Automatically filtered (author is None in API response)

**Q: Can I update existing comments?**
A: Yes, use `merge_disposition='merge'` with `primary_key='comment_id'` in DLT

**Q: Is PII filtering applied?**
A: No, comment body text is collected as-is. Apply PII anonymization in preprocessing.

---

## References

- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit API Limits](https://github.com/reddit-archive/reddit/wiki/API)
- [DLT Documentation](https://dlthub.com/docs)

---

*Last Updated: 2025-11-07*  
*Extension Version: 1.1*  
*Status: Production Ready*
