# DLT Collection Examples & Patterns

<div style="text-align: center; margin: 30px 0;">
  <h1 style="color: #FF6B35; font-size: 2.5em; margin-bottom: 10px;">Practical Collection Examples</h1>
  <p style="color: #004E89; font-size: 1.3em; font-weight: 300;">Real-world scenarios and copy-paste ready configurations</p>
  <div style="background: #F7B801; color: #1A1A1A; padding: 10px 20px; border-radius: 25px; display: inline-block; margin-top: 15px; font-weight: bold;">
    💡 15+ Production-Ready Examples
  </div>
</div>

---

## 📋 Table of Contents

- [🚀 Quick Start Examples](#-quick-start-examples)
- [🎯 Research Scenarios](#-research-scenarios)
- [📊 Business Intelligence](#-business-intelligence)
- [🔬 Academic Research](#-academic-research)
- [⚡ High-Performance Collection](#-high-performance-collection)
- [📈 Trend Analysis](#-trend-analysis)
- [🏢 Industry-Specific Examples](#-industry-specific-examples)
- [🔄 Scheduled Collections](#-scheduled-collections)
- [🛠️ Advanced Patterns](#️-advanced-patterns)
- [🚨 Troubleshooting Examples](#-troubleshooting-examples)

---

## 🚀 Quick Start Examples

### Example 1: Basic Test Collection

**Purpose:** First-time setup verification and basic functionality testing.

```bash
# Test with a single, highly active subreddit
python scripts/run_dlt_activity_collection.py \
  --subreddits "python" \
  --dry-run \
  --verbose
```

**Expected Output:**
```
🚀 Starting Enhanced DLT Activity Collection
🎯 Target subreddits: 1
⏰ Time filter: day
📊 Minimum activity score: 50.0
✅ Dry run completed successfully
📦 Source contains 3 resources
  • Resource 1: active_subreddits
  • Resource 2: validated_comments
  • Resource 3: activity_trends
```

### Example 2: Small Scale Production Collection

**Purpose:** Collect initial dataset for analysis and validation.

```bash
# Collect from 2-3 active subreddits with moderate filtering
python scripts/run_dlt_activity_collection.py \
  --subreddits "python,learnprogramming" \
  --time-filter "day" \
  --min-activity 50 \
  --pipeline "initial_collection"
```

**Expected Results:**
- 50-150 posts
- 500-2000 comments
- Activity scores: 50-85 range
- Collection time: 1-3 minutes

### Example 3: Quality-Focused Collection

**Purpose:** Collect only the highest quality content for premium analysis.

```bash
# High-threshold collection for maximum quality
python scripts/run_dlt_activity_collection.py \
  --subreddits "MachineLearning,datascience" \
  --time-filter "day" \
  --min-activity 80 \
  --pipeline "premium_content"
```

**Expected Results:**
- 10-30 posts (highest quality only)
- 100-500 high-engagement comments
- Activity scores: 80-95 range
- Collection time: 1-2 minutes

---

## 🎯 Research Scenarios

### Example 4: Programming Language Trend Analysis

**Purpose:** Track discussions and trends around programming languages.

```bash
# Collect from programming-focused subreddits
python scripts/run_dlt_activity_collection.py \
  --subreddits "python,javascript,java,golang,rust,typescript,cpp" \
  --time-filter "week" \
  --min-activity 60 \
  --pipeline "programming_trends_$(date +%Y%m%d)"
```

**Analysis Use Case:**
```python
# Post-collection analysis
import pandas as pd
from supabase import create_client

# Load data
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
response = supabase.table('submissions').select('*').gte('created_at', '2024-01-01').execute()
df = pd.DataFrame(response.data)

# Language mention analysis
languages = ['python', 'javascript', 'java', 'golang', 'rust', 'typescript', 'cpp']
for lang in languages:
    mentions = df['title'].str.contains(lang, case=False).sum()
    print(f"{lang}: {mentions} mentions")
```

### Example 5: Startup and SaaS Market Research

**Purpose:** Monitor startup discussions, funding news, and SaaS trends.

```bash
# Use predefined technology/SaaS segment
python scripts/run_dlt_activity_collection.py \
  --segment "technology_saas" \
  --time-filter "week" \
  --min-activity 65 \
  --pipeline "saas_market_research"
```

**Extended Analysis:**
```python
# Identify trending topics
from collections import Counter
import re

# Extract common startup-related keywords
startup_keywords = [
    'funding', 'investment', 'seed', 'series a', 'ipo', 'acquisition',
    'startup', 'saas', 'b2b', 'revenue', 'growth', 'metrics'
]

keyword_counts = Counter()
for text in df['title'].dropna():
    for keyword in startup_keywords:
        if keyword in text.lower():
            keyword_counts[keyword] += 1

print("Trending startup topics:")
for keyword, count in keyword_counts.most_common(10):
    print(f"  {keyword}: {count} mentions")
```

### Example 6: Academic Research Data Collection

**Purpose:** Gather comprehensive data for academic research papers.

```bash
# Broad collection with inclusive filtering
python scripts/run_dlt_activity_collection.py \
  --subreddits "science,AskScience,research,academia,politics" \
  --time-filter "month" \
  --min-activity 40 \
  --pipeline "academic_research_dataset"
```

**Research Analysis Template:**
```python
# Sentiment and topic analysis for academic research
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords

def analyze_reddit_discussions(df):
    """Analyze sentiment and key topics in Reddit discussions."""

    # Download required NLTK data
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

    results = {
        'total_posts': len(df),
        'avg_sentiment': 0,
        'top_keywords': [],
        'engagement_stats': {}
    }

    # Sentiment analysis
    sentiments = []
    all_words = []

    for text in df['title'].dropna():
        # Sentiment
        blob = TextBlob(text)
        sentiments.append(blob.sentiment.polarity)

        # Keywords
        words = [word.lower() for word in text.split()
                if word.isalpha() and word.lower() not in stop_words]
        all_words.extend(words)

    results['avg_sentiment'] = sum(sentiments) / len(sentiments)
    results['top_keywords'] = Counter(all_words).most_common(20)

    return results

# Usage
analysis_results = analyze_reddit_discussions(df)
print(f"Average sentiment: {analysis_results['avg_sentiment']:.2f}")
print("Top keywords:", analysis_results['top_keywords'][:10])
```

---

## 📊 Business Intelligence Examples

### Example 7: Competitor Monitoring

**Purpose:** Track discussions about competing products or companies.

```bash
# Monitor technology competitors
python scripts/run_dlt_activity_collection.py \
  --subreddits "technology,programming,software,gadgets" \
  --time-filter "day" \
  --min-activity 55 \
  --pipeline "competitor_intelligence"
```

**Competitor Analysis Script:**
```python
# Track competitor mentions and sentiment
def track_competitors(df, competitor_list):
    """Track mentions of specific competitors and analyze sentiment."""

    competitor_data = {}

    for competitor in competitor_list:
        # Find posts mentioning the competitor
        mentions = df[df['title'].str.contains(competitor, case=False, na=False)]

        if not mentions.empty:
            # Calculate sentiment for mentions
            sentiments = []
            for title in mentions['title']:
                blob = TextBlob(title)
                sentiments.append(blob.sentiment.polarity)

            competitor_data[competitor] = {
                'mentions': len(mentions),
                'avg_sentiment': sum(sentiments) / len(sentiments),
                'total_engagement': mentions['score'].sum(),
                'sample_titles': mentions['title'].head(3).tolist()
            }

    return competitor_data

# Example usage
competitors = ['openai', 'anthropic', 'google', 'microsoft', 'amazon']
competitor_analysis = track_competitors(df, competitors)

for comp, data in competitor_analysis.items():
    print(f"{comp.upper()}:")
    print(f"  Mentions: {data['mentions']}")
    print(f"  Sentiment: {data['avg_sentiment']:.2f}")
    print(f"  Engagement: {data['total_engagement']}")
    print()
```

### Example 8: Product Launch Monitoring

**Purpose:** Monitor community reaction to product launches or announcements.

```bash
# High-frequency collection during launch period
python scripts/run_dlt_activity_collection.py \
  --subreddits "technology,programming,gadgets,apple" \
  --time-filter "hour" \
  --min-activity 70 \
  --pipeline "product_launch_monitor"
```

**Launch Reaction Analysis:**
```python
# Analyze launch reactions over time
def analyze_launch_reaction(df, product_keywords):
    """Analyze community reaction to a product launch."""

    # Filter for posts about the product
    product_posts = df[df['title'].str.contains(
        '|'.join(product_keywords), case=False, na=False
    )]

    # Group by hour to track reaction timeline
    product_posts['hour'] = pd.to_datetime(product_posts['created_at']).dt.floor('H')
    hourly_stats = product_posts.groupby('hour').agg({
        'title': 'count',
        'score': 'sum',
        'comments_count': 'sum'
    }).rename(columns={
        'title': 'post_count',
        'score': 'total_score',
        'comments_count': 'total_comments'
    })

    return hourly_stats

# Example: Monitor iPhone launch
iphone_keywords = ['iphone', 'apple', 'ios 18', 'apple event']
launch_analysis = analyze_launch_reaction(df, iphone_keywords)

print("Hourly launch reaction:")
print(launch_analysis.head())
```

### Example 9: Customer Feedback Collection

**Purpose:** Gather customer feedback and pain points for product improvement.

```bash
# Collect from customer-focused communities
python scripts/run_dlt_activity_collection.py \
  --subreddits "productivity,freelance,smallbusiness,SideProject" \
  --time-filter "week" \
  --min-activity 45 \
  --pipeline "customer_feedback"
```

**Feedback Analysis:**
```python
# Extract customer pain points and feature requests
def analyze_customer_feedback(df):
    """Analyze customer feedback for pain points and feature requests."""

    pain_point_indicators = [
        'frustrated', 'annoying', 'difficult', 'confusing', 'broken',
        'wish', 'need', 'should', 'problem', 'issue', 'bug'
    ]

    feature_request_indicators = [
        'feature request', 'add', 'implement', 'support', 'integrate',
        'would love', 'please add', 'missing', 'lacking'
    ]

    feedback_data = {
        'pain_points': [],
        'feature_requests': [],
        'sentiment_distribution': {}
    }

    for _, post in df.iterrows():
        title = post['title'].lower()

        # Categorize feedback
        if any(indicator in title for indicator in pain_point_indicators):
            feedback_data['pain_points'].append({
                'title': post['title'],
                'score': post['score'],
                'comments': post['comments_count']
            })

        if any(indicator in title for indicator in feature_request_indicators):
            feedback_data['feature_requests'].append({
                'title': post['title'],
                'score': post['score'],
                'comments': post['comments_count']
            })

    return feedback_data

# Usage
feedback = analyze_customer_feedback(df)
print(f"Found {len(feedback['pain_points'])} pain points")
print(f"Found {len(feedback['feature_requests'])} feature requests")
```

---

## 🔬 Academic Research Examples

### Example 10: Community Behavior Study

**Purpose:** Study community dynamics and behavior patterns across different subreddits.

```bash
# Multi-community collection for comparative analysis
python scripts/run_dlt_activity_collection.py \
  --all \
  --time-filter "month" \
  --min-activity 30 \
  --pipeline "community_behavior_study"
```

**Community Analysis:**
```python
# Comprehensive community behavior analysis
def analyze_community_behavior(df):
    """Analyze behavior patterns across different communities."""

    community_stats = {}

    for subreddit in df['subreddit'].unique():
        community_data = df[df['subreddit'] == subreddit]

        # Calculate various metrics
        stats = {
            'post_count': len(community_data),
            'avg_score': community_data['score'].mean(),
            'avg_comments': community_data['comments_count'].mean(),
            'engagement_rate': (community_data['score'] + community_data['comments_count']).mean(),
            'activity_variance': community_data['score'].std(),
            'peak_hours': analyze_peak_hours(community_data)
        }

        community_stats[subreddit] = stats

    return community_stats

def analyze_peak_hours(community_data):
    """Analyze peak posting hours for a community."""
    community_data['hour'] = pd.to_datetime(community_data['created_at']).dt.hour
    hourly_counts = community_data.groupby('hour').size()
    peak_hour = hourly_counts.idxmax()
    return peak_hour

# Usage
behavior_analysis = analyze_community_behavior(df)

print("Community Behavior Analysis:")
for community, stats in behavior_analysis.items():
    print(f"\n{community}:")
    print(f"  Posts: {stats['post_count']}")
    print(f"  Avg Engagement: {stats['engagement_rate']:.1f}")
    print(f"  Peak Hour: {stats['peak_hours']}:00")
```

### Example 11: Content Virality Research

**Purpose:** Study factors that contribute to content going viral.

```bash
# High-activity collection to catch viral content early
python scripts/run_dlt_activity_collection.py \
  --subreddits "technology,news,worldnews,science" \
  --time-filter "hour" \
  --min-activity 85 \
  --pipeline "virality_research"
```

**Virality Analysis:**
```python
# Identify and analyze viral content patterns
def analyze_viral_content(df, viral_threshold=1000):
    """Analyze characteristics of viral content."""

    # Define viral content (high score or comments)
    viral_posts = df[
        (df['score'] > viral_threshold) |
        (df['comments_count'] > viral_threshold)
    ]

    viral_analysis = {
        'viral_count': len(viral_posts),
        'viral_rate': len(viral_posts) / len(df) * 100,
        'common_patterns': [],
        'timing_patterns': {},
        'subreddit_distribution': {}
    }

    # Analyze patterns in viral content
    for _, post in viral_posts.iterrows():
        title = post['title'].lower()

        # Common viral patterns
        if any(word in title for word in ['breaking', 'just announced', 'official', 'confirmed']):
            viral_analysis['common_patterns'].append('news_breaking')

        if any(word in title for word in ['study', 'research', 'scientists']):
            viral_analysis['common_patterns'].append('scientific_discovery')

        # Timing patterns
        hour = pd.to_datetime(post['created_at']).hour
        viral_analysis['timing_patterns'][hour] = viral_analysis['timing_patterns'].get(hour, 0) + 1

        # Subreddit distribution
        sub = post['subreddit']
        viral_analysis['subreddit_distribution'][sub] = viral_analysis['subreddit_distribution'].get(sub, 0) + 1

    return viral_analysis

# Usage
virality_data = analyze_viral_content(df)
print(f"Viral content rate: {virality_data['viral_rate']:.2f}%")
print("Common patterns:", Counter(virality_data['common_patterns']))
```

### Example 12: Longitudinal Study Setup

**Purpose:** Set up data collection for long-term trend analysis.

```bash
# Comprehensive baseline collection
python scripts/run_dlt_activity_collection.py \
  --segment "technology_saas" \
  --time-filter "month" \
  --min-activity 40 \
  --pipeline "longitudinal_baseline"

# Automated weekly follow-up collection
python scripts/run_dlt_activity_collection.py \
  --segment "technology_saas" \
  --time-filter "week" \
  --min-activity 45 \
  --pipeline "longitudinal_week_$(date +%Y_%U)"
```

**Longitudinal Analysis Framework:**
```python
# Framework for longitudinal data analysis
class LongitudinalAnalyzer:
    def __init__(self, supabase_client):
        self.client = supabase_client

    def load_time_series_data(self, subreddit, start_date, end_date):
        """Load data for specific time range."""
        response = self.client.table('submissions').select('*').eq('subreddit', subreddit)\
            .gte('created_at', start_date).lte('created_at', end_date).execute()
        return pd.DataFrame(response.data)

    def analyze_trends(self, df, time_window='week'):
        """Analyze trends over time."""
        df['date'] = pd.to_datetime(df['created_at']).dt.floor(time_window)

        trends = df.groupby('date').agg({
            'title': 'count',
            'score': ['mean', 'sum'],
            'comments_count': ['mean', 'sum']
        }).round(2)

        trends.columns = ['post_count', 'avg_score', 'total_score', 'avg_comments', 'total_comments']
        return trends

    def detect_anomalies(self, time_series_data, threshold=2):
        """Detect anomalous activity patterns."""
        from scipy import stats

        # Calculate z-scores for post counts
        post_counts = time_series_data['post_count']
        z_scores = stats.zscore(post_counts)

        anomalies = time_series_data[abs(z_scores) > threshold]
        return anomalies

# Usage
analyzer = LongitudinalAnalyzer(supabase)
time_series_data = analyzer.analyze_trends(df)
anomalies = analyzer.detect_anomalies(time_series_data)

print("Anomalous activity periods:")
print(anomalies)
```

---

## ⚡ High-Performance Collection Examples

### Example 13: Maximum Speed Collection

**Purpose:** Collect data as quickly as possible for time-sensitive analysis.

```bash
# Optimized for speed with minimal filtering
python scripts/run_dlt_activity_collection.py \
  --subreddits "python,technology,programming" \
  --time-filter "hour" \
  --min-activity 30 \
  --pipeline "speed_collection"
```

**Performance Optimization Script:**
```python
# Optimize collection parameters for maximum speed
def optimize_for_speed(target_subreddits, api_rate_limit=60):
    """Calculate optimal collection parameters for maximum speed."""

    optimization = {
        'min_activity_threshold': 30,  # Lower threshold for more data
        'time_filter': 'hour',          # Most recent data
        'batch_size': len(target_subreddits),  # Process all at once
        'api_calls_per_minute': api_rate_limit,
        'estimated_time': 0
    }

    # Estimate collection time
    # Assume 2 seconds per API call with rate limiting
    api_calls_needed = len(target_subreddits) * 10  # Estimate 10 calls per subreddit
    optimization['estimated_time'] = (api_calls_needed / api_rate_limit) * 60

    return optimization

# Usage
speed_config = optimize_for_speed(['python', 'technology', 'programming'])
print(f"Estimated collection time: {speed_config['estimated_time']:.1f} minutes")
```

### Example 14: Parallel Processing Collection

**Purpose:** Collect from multiple segments simultaneously.

```bash
# Collection script for parallel processing
#!/bin/bash

# Run multiple collections in parallel
python scripts/run_dlt_activity_collection.py \
  --segment "technology_saas" \
  --time-filter "day" \
  --min-activity 60 \
  --pipeline "tech_collection" &

python scripts/run_dlt_activity_collection.py \
  --segment "health_fitness" \
  --time-filter "day" \
  --min-activity 60 \
  --pipeline "health_collection" &

python scripts/run_dlt_activity_collection.py \
  --segment "finance_investing" \
  --time-filter "day" \
  --min-activity 60 \
  --pipeline "finance_collection" &

# Wait for all collections to complete
wait
echo "All parallel collections completed!"
```

### Example 15: Bulk Data Collection

**Purpose:** Collect large datasets for machine learning or comprehensive analysis.

```bash
# Large-scale collection with reasonable quality threshold
python scripts/run_dlt_activity_collection.py \
  --all \
  --time-filter "month" \
  --min-activity 40 \
  --pipeline "bulk_ml_dataset"
```

**Bulk Data Processing:**
```python
# Process large datasets efficiently
def process_bulk_data(df, batch_size=10000):
    """Process large datasets in batches to avoid memory issues."""

    total_rows = len(df)
    processed_batches = 0

    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        batch = df.iloc[start:end]

        # Process batch (example: feature extraction)
        batch_features = extract_features(batch)

        # Save batch results
        save_batch_results(batch_features, batch_id=processed_batches)

        processed_batches += 1
        print(f"Processed batch {processed_batches}/{(total_rows // batch_size) + 1}")

    print("Bulk data processing completed!")

def extract_features(batch_df):
    """Extract features from batch of Reddit data."""
    features = {}

    # Text features
    features['title_length'] = batch_df['title'].str.len()
    features['has_question'] = batch_df['title'].str.contains('?').astype(int)
    features['uppercase_ratio'] = batch_df['title'].str.count(r'[A-Z]') / batch_df['title'].str.len()

    # Engagement features
    features['engagement_score'] = batch_df['score'] + batch_df['comments_count']
    features['comment_to_score_ratio'] = batch_df['comments_count'] / (batch_df['score'] + 1)

    # Time features
    batch_df['hour'] = pd.to_datetime(batch_df['created_at']).dt.hour
    features['posting_hour'] = batch_df['hour']

    return pd.DataFrame(features)

# Usage
process_bulk_data(large_dataset)
```

---

## 📈 Trend Analysis Examples

### Example 16: Emerging Trend Detection

**Purpose:** Identify emerging trends before they become mainstream.

```bash
# High-sensitivity collection for trend detection
python scripts/run_dlt_activity_collection.py \
  --subreddits "technology,programming,MachineLearning,startups" \
  --time-filter "hour" \
  --min-activity 75 \
  --pipeline "emerging_trends"
```

**Trend Detection Algorithm:**
```python
# Detect emerging trends using activity velocity
def detect_emerging_trends(df, time_window_hours=6):
    """Detect topics showing rapid growth in activity."""

    # Convert timestamps and group by time windows
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['time_window'] = df['created_at'].dt.floor(f'{time_window_hours}H')

    # Extract keywords and count mentions over time
    keyword_trends = {}

    for _, post in df.iterrows():
        title_words = extract_keywords(post['title'])
        time_window = post['time_window']

        for word in title_words:
            if word not in keyword_trends:
                keyword_trends[word] = {}

            keyword_trends[word][time_window] = keyword_trends[word].get(time_window, 0) + 1

    # Calculate growth rates
    emerging_trends = []
    for keyword, timeline in keyword_trends.items():
        if len(timeline) >= 3:  # Need at least 3 time periods
            sorted_times = sorted(timeline.keys())
            recent_growth = calculate_growth_rate(timeline, sorted_times)

            if recent_growth > 2.0:  # 200%+ growth rate
                emerging_trends.append({
                    'keyword': keyword,
                    'growth_rate': recent_growth,
                    'recent_mentions': timeline[sorted_times[-1]],
                    'timeline': timeline
                })

    # Sort by growth rate
    emerging_trends.sort(key=lambda x: x['growth_rate'], reverse=True)
    return emerging_trends[:20]  # Top 20 emerging trends

def extract_keywords(title):
    """Extract relevant keywords from a title."""
    import re

    # Simple keyword extraction (can be enhanced with NLP)
    words = re.findall(r'\b\w+\b', title.lower())

    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}

    return [word for word in words if word not in stop_words and len(word) > 2]

def calculate_growth_rate(timeline, sorted_times):
    """Calculate growth rate between recent time periods."""
    if len(sorted_times) < 2:
        return 0

    # Compare most recent period to previous period
    recent_count = timeline[sorted_times[-1]]
    previous_count = timeline[sorted_times[-2]] if len(sorted_times) > 1 else 1

    if previous_count == 0:
        return float('inf') if recent_count > 0 else 0

    return (recent_count - previous_count) / previous_count

# Usage
trends = detect_emerging_trends(recent_data)
print("Top Emerging Trends:")
for i, trend in enumerate(trends[:10], 1):
    print(f"{i}. {trend['keyword']}: {trend['growth_rate']:.1f}% growth, {trend['recent_mentions']} recent mentions")
```

### Example 17: Seasonal Pattern Analysis

**Purpose:** Identify seasonal patterns in Reddit activity.

```bash
# Long-term collection for seasonal analysis
python scripts/run_dlt_activity_collection.py \
  --subreddits "travel,personalfinance,fitness,cooking" \
  --time-filter "month" \
  --min-activity 35 \
  --pipeline "seasonal_patterns"
```

**Seasonal Analysis:**
```python
# Analyze seasonal patterns in Reddit activity
def analyze_seasonal_patterns(df):
    """Analyze seasonal patterns in subreddit activity."""

    df['created_at'] = pd.to_datetime(df['created_at'])
    df['month'] = df['created_at'].dt.month
    df['season'] = df['month'].apply(get_season)

    seasonal_patterns = {}

    for subreddit in df['subreddit'].unique():
        subreddit_data = df[df['subreddit'] == subreddit]

        # Calculate metrics by season
        seasonal_stats = subreddit_data.groupby('season').agg({
            'title': 'count',
            'score': 'mean',
            'comments_count': 'mean'
        }).round(2)

        seasonal_patterns[subreddit] = {
            'stats': seasonal_stats.to_dict(),
            'peak_season': seasonal_stats['title'].idxmax(),
            'seasonality_index': calculate_seasonality_index(seasonal_stats['title'])
        }

    return seasonal_patterns

def get_season(month):
    """Convert month to season."""
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:
        return 'Fall'

def calculate_seasonality_index(season_counts):
    """Calculate how much activity varies by season."""
    if len(season_counts) < 2:
        return 0

    mean_activity = season_counts.mean()
    variance = ((season_counts - mean_activity) ** 2).mean()

    # Higher variance = stronger seasonality
    return variance / (mean_activity ** 2) if mean_activity > 0 else 0

# Usage
patterns = analyze_seasonal_patterns(seasonal_data)

for subreddit, pattern in patterns.items():
    print(f"\n{subreddit}:")
    print(f"  Peak season: {pattern['peak_season']}")
    print(f"  Seasonality index: {pattern['seasonality_index']:.3f}")
    print(f"  Season stats: {pattern['stats']['title']}")
```

---

## 🏢 Industry-Specific Examples

### Example 18: Healthcare Industry Monitoring

**Purpose:** Monitor healthcare discussions and medical trends.

```bash
# Healthcare-focused collection
python scripts/run_dlt_activity_collection.py \
  --subreddits "medicine,health,AskDocs,publichealth,mentalhealth" \
  --time-filter "day" \
  --min-activity 50 \
  --pipeline "healthcare_monitor"
```

### Example 19: Financial Services Analysis

**Purpose:** Track financial discussions and market sentiment.

```bash
# Financial sector collection
python scripts/run_dlt_activity_collection.py \
  --segment "finance_investing" \
  --time-filter "day" \
  --min-activity 60 \
  --pipeline "financial_analysis"
```

### Example 20: Education Technology Tracking

**Purpose:** Monitor EdTech trends and educational discussions.

```bash
# Education technology collection
python scripts/run_dlt_activity_collection.py \
  --subreddits "education,teachers,LearnProgramming,edtech" \
  --time-filter "week" \
  --min-activity 55 \
  --pipeline "edtech_trends"
```

---

## 🔄 Scheduled Collections

### Cron Job Examples

**Daily High-Quality Collection:**
```bash
# Edit crontab: crontab -e
0 8 * * * cd /path/to/redditharbor && python scripts/run_dlt_activity_collection.py --segment technology_saas --min-activity 70 --time-filter day --pipeline "daily_$(date +\%Y\%m\%d)"
```

**Weekly Comprehensive Analysis:**
```bash
# Every Sunday at 2 AM for weekly data
0 2 * * 0 cd /path/to/redditharbor && python scripts/run_dlt_activity_collection.py --all --min-activity 50 --time-filter week --pipeline "weekly_$(date +\%Y_\%U)"
```

**Monthly Trend Analysis:**
```bash
# First day of each month at 3 AM
0 3 1 * * cd /path/to/redditharbor && python scripts/run_dlt_activity_collection.py --segment technology_saas --min-activity 40 --time-filter month --pipeline "monthly_$(date +\%Y\%m)"
```

### Advanced Scheduling Script

```python
#!/usr/bin/env python3
"""
Advanced scheduling script for DLT collections with intelligent timing.
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
import subprocess

class DLTCollectionScheduler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def run_collection(self, **kwargs):
        """Execute DLT collection with specified parameters."""

        # Build command
        cmd = ['python', 'scripts/run_dlt_activity_collection.py']

        # Add parameters
        if kwargs.get('subreddits'):
            cmd.extend(['--subreddits', kwargs['subreddits']])
        elif kwargs.get('segment'):
            cmd.extend(['--segment', kwargs['segment']])
        elif kwargs.get('all'):
            cmd.append('--all')

        cmd.extend(['--time-filter', kwargs.get('time_filter', 'day')])
        cmd.extend(['--min-activity', str(kwargs.get('min_activity', 50))])
        cmd.extend(['--pipeline', kwargs.get('pipeline', f'scheduled_{datetime.now().strftime("%Y%m%d_%H%M")}')])

        if kwargs.get('dry_run'):
            cmd.append('--dry-run')

        # Execute command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Collection completed: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Collection failed: {e.stderr}")
            return False

    def schedule_collections(self):
        """Set up intelligent collection schedule."""

        # High-frequency trend monitoring (business hours)
        schedule.every().hour.at(":15").do(
            self.run_collection,
            segment="technology_saas",
            time_filter="hour",
            min_activity=80,
            pipeline="trend_monitor"
        )

        # Daily quality collection
        schedule.every().day.at("08:00").do(
            self.run_collection,
            segment="technology_saas",
            time_filter="day",
            min_activity=65,
            pipeline="daily_quality"
        )

        # Weekly comprehensive analysis
        schedule.every().sunday.at("02:00").do(
            self.run_collection,
            all=True,
            time_filter="week",
            min_activity=45,
            pipeline="weekly_comprehensive"
        )

        # Monthly deep analysis
        schedule.every().month.do(
            self.run_collection,
            segment="technology_saas",
            time_filter="month",
            min_activity=35,
            pipeline="monthly_deep_analysis"
        )

        # Intelligent off-peak collection (reduced API pressure)
        schedule.every().day.at("23:00").do(
            self.run_collection,
            subreddits="python,MachineLearning,datascience",
            time_filter="day",
            min_activity=40,
            pipeline="off_peak_collection"
        )

    def run_scheduler(self):
        """Run the scheduler continuously."""
        self.schedule_collections()

        self.logger.info("DLT Collection Scheduler started")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

# Usage
if __name__ == "__main__":
    scheduler = DLTCollectionScheduler()
    scheduler.run_scheduler()
```

---

## 🛠️ Advanced Patterns

### Example 21: Multi-Pipeline Orchestration

**Purpose:** Coordinate multiple collection pipelines for complex analysis.

```python
#!/usr/bin/env python3
"""
Multi-pipeline orchestration for complex Reddit data collection workflows.
"""

import asyncio
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

class DLTPipelineOrchestrator:
    def __init__(self):
        self.pipelines = {}

    def add_pipeline(self, name, config):
        """Add a pipeline configuration."""
        self.pipelines[name] = config

    async def run_parallel_pipelines(self, pipeline_names):
        """Run multiple pipelines in parallel."""

        async def run_single_pipeline(name):
            config = self.pipelines[name]

            # Build command
            cmd = self.build_command(config)

            # Execute pipeline
            try:
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()

                return {
                    'name': name,
                    'success': result.returncode == 0,
                    'stdout': stdout.decode(),
                    'stderr': stderr.decode(),
                    'duration': datetime.now()
                }

            except Exception as e:
                return {
                    'name': name,
                    'success': False,
                    'error': str(e),
                    'duration': datetime.now()
                }

        # Run all pipelines concurrently
        tasks = [run_single_pipeline(name) for name in pipeline_names]
        results = await asyncio.gather(*tasks)

        return results

    def build_command(self, config):
        """Build command from configuration."""
        cmd = ['python', 'scripts/run_dlt_activity_collection.py']

        if config.get('subreddits'):
            cmd.extend(['--subreddits', config['subreddits']])
        elif config.get('segment'):
            cmd.extend(['--segment', config['segment']])
        elif config.get('all'):
            cmd.append('--all')

        cmd.extend(['--time-filter', config.get('time_filter', 'day')])
        cmd.extend(['--min-activity', str(config.get('min_activity', 50))])
        cmd.extend(['--pipeline', config.get('pipeline', 'orchestrated_collection')])

        if config.get('dry_run'):
            cmd.append('--dry-run')

        return cmd

# Usage Example
async def main():
    orchestrator = DLTPipelineOrchestrator()

    # Define pipeline configurations
    orchestrator.add_pipeline('tech_trends', {
        'segment': 'technology_saas',
        'time_filter': 'day',
        'min_activity': 70,
        'pipeline': 'tech_trends_collection'
    })

    orchestrator.add_pipeline('health_monitoring', {
        'segment': 'health_fitness',
        'time_filter': 'day',
        'min_activity': 60,
        'pipeline': 'health_monitoring_collection'
    })

    orchestrator.add_pipeline('finance_analysis', {
        'segment': 'finance_investing',
        'time_filter': 'day',
        'min_activity': 65,
        'pipeline': 'finance_analysis_collection'
    })

    # Run pipelines in parallel
    results = await orchestrator.run_parallel_pipelines([
        'tech_trends', 'health_monitoring', 'finance_analysis'
    ])

    # Report results
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['name']}: Collection completed")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 22: Custom Quality Filters

**Purpose:** Implement custom quality filtering logic.

```python
# Custom quality filters for specific research needs
class CustomQualityFilters:
    def __init__(self):
        self.tech_keywords = [
            'api', 'algorithm', 'database', 'framework', 'library',
            'programming', 'software', 'development', 'coding'
        ]

        self.research_indicators = [
            'study', 'research', 'paper', 'analysis', 'findings',
            'experiment', 'survey', 'investigation', 'results'
        ]

    def technical_content_filter(self, post_data):
        """Filter for technical content quality."""
        title = post_data.get('title', '').lower()

        # Check for technical keywords
        tech_score = sum(1 for keyword in self.tech_keywords if keyword in title)

        # Check for question format (indicates discussion potential)
        has_question = '?' in title

        # Check length (longer titles often more detailed)
        length_score = min(len(title) / 100, 1.0)

        # Calculate combined score
        quality_score = (tech_score * 0.5) + (has_question * 0.3) + (length_score * 0.2)

        return quality_score > 0.3  # Threshold for technical content

    def research_content_filter(self, post_data):
        """Filter for research-oriented content."""
        title = post_data.get('title', '').lower()

        # Check for research indicators
        research_score = sum(1 for indicator in self.research_indicators if indicator in title)

        # Check for data/numbers (indicates empirical content)
        has_data = any(char.isdigit() for char in title)

        # Avoid overly sensational content
        sensational_words = ['breaking!', 'shocking!', 'unbelievable!', 'mind-blowing!']
        is_sensational = any(word in title for word in sensational_words)

        # Calculate quality score
        base_score = (research_score * 0.6) + (has_data * 0.4)
        final_score = base_score * (0.5 if is_sensational else 1.0)

        return final_score > 0.4  # Threshold for research content

    def engagement_prediction_filter(self, post_data):
        """Predict potential engagement based on title characteristics."""
        title = post_data.get('title', '')

        # Factors that correlate with higher engagement
        has_question = '?' in title
        has_numbers = any(char.isdigit() for char in title)
        is_listicle = title.lower().startswith(('top', 'best', 'worst', 'ultimate guide'))
        reasonable_length = 20 <= len(title) <= 200

        # Calculate engagement potential score
        engagement_score = (
            (has_question * 0.3) +
            (has_numbers * 0.2) +
            (is_listicle * 0.2) +
            (reasonable_length * 0.3)
        )

        return engagement_score > 0.5

# Integration with DLT pipeline
def apply_custom_filters(source_data, filter_class):
    """Apply custom quality filters to DLT source data."""

    filter_instance = filter_class()

    filtered_posts = []
    for post in source_data:
        # Apply multiple filters
        if (filter_instance.technical_content_filter(post) and
            filter_instance.engagement_prediction_filter(post)):

            # Add quality scores to post data
            post['tech_quality_score'] = filter_instance.technical_content_filter(post)
            post['engagement_prediction'] = filter_instance.engagement_prediction_filter(post)
            filtered_posts.append(post)

    return filtered_posts
```

---

## 🚨 Troubleshooting Examples

### Example 23: Diagnostic Collection

**Purpose:** Run diagnostic collection to identify issues.

```bash
# Diagnostic collection with maximum logging
python scripts/run_dlt_activity_collection.py \
  --subreddits "python" \
  --dry-run \
  --verbose \
  --min-activity 1 \
  --pipeline "diagnostic_test"
```

### Example 24: API Connection Testing

**Purpose:** Test Reddit API connection independently.

```python
#!/usr/bin/env python3
"""
Reddit API connection diagnostic tool.
"""

import praw
import sys
from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

def test_reddit_connection():
    """Test Reddit API connection with detailed diagnostics."""

    try:
        print("🔧 Initializing Reddit client...")
        reddit = praw.Reddit(
            client_id=REDDIT_PUBLIC,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            read_only=True
        )

        print("✅ Reddit client initialized successfully")

        # Test basic API calls
        print("\n🔍 Testing API functionality...")

        # Test subreddit access
        print("  • Testing subreddit access...")
        test_sub = reddit.subreddit('python')
        print(f"    r/python subscribers: {test_sub.subscribers:,}")
        print(f"    r/python active users: {getattr(test_sub, 'active_user_count', 'N/A')}")

        # Test post listing
        print("  • Testing post listing...")
        posts = list(test_sub.hot(limit=5))
        print(f"    Retrieved {len(posts)} posts from r/python")

        # Test comment access
        print("  • Testing comment access...")
        if posts:
            first_post = posts[0]
            print(f"    First post: {first_post.title[:50]}...")
            print(f"    Score: {first_post.score}, Comments: {first_post.num_comments}")

        print("\n✅ All Reddit API tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Reddit API test failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("  1. Verify API credentials in config/settings.py")
        print("  2. Check if API keys have read permissions")
        print("  3. Verify network connectivity")
        print("  4. Check Reddit API status at https://www.redditstatus.com/")
        return False

if __name__ == "__main__":
    success = test_reddit_connection()
    sys.exit(0 if success else 1)
```

### Example 25: Database Connectivity Test

**Purpose:** Test Supabase database connection independently.

```python
#!/usr/bin/env python3
"""
Supabase database connection diagnostic tool.
"""

import sys
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

def test_supabase_connection():
    """Test Supabase connection with detailed diagnostics."""

    try:
        print("🔧 Initializing Supabase client...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("✅ Supabase client initialized successfully")

        # Test basic database operations
        print("\n🔍 Testing database operations...")

        # Test table access (should fail gracefully if tables don't exist)
        print("  • Testing table access...")
        try:
            response = supabase.table('submissions').select('count').limit(1).execute()
            print(f"    submissions table accessible: {len(response.data) >= 0}")
        except Exception as e:
            print(f"    submissions table access failed: {e}")

        # Test API functionality
        print("  • Testing API functionality...")
        try:
            # This should work regardless of table existence
            response = supabase.auth.get_session()
            print(f"    API authentication: Working")
        except Exception as e:
            print(f"    API authentication issue: {e}")

        print("\n✅ Supabase connection tests completed!")
        return True

    except Exception as e:
        print(f"\n❌ Supabase connection test failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("  1. Verify Supabase URL in config/settings.py")
        print("  2. Check service role key permissions")
        print("  3. Ensure Supabase is running (supabase start)")
        print("  4. Test with Supabase Studio: http://127.0.0.1:54323")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
```

---

## 🎯 Collection Templates

### Quick Copy-Paste Templates

**Template 1: Basic Quality Collection**
```bash
python scripts/run_dlt_activity_collection.py \
  --subreddits "YOUR_SUBREDDITS_HERE" \
  --time-filter "day" \
  --min-activity 60
```

**Template 2: High-Speed Collection**
```bash
python scripts/run_dlt_activity_collection.py \
  --subreddits "YOUR_SUBREDDITS_HERE" \
  --time-filter "hour" \
  --min-activity 30
```

**Template 3: Premium Quality Collection**
```bash
python scripts/run_dlt_activity_collection.py \
  --subreddits "YOUR_SUBREDDITS_HERE" \
  --time-filter "week" \
  --min-activity 80
```

**Template 4: Comprehensive Research**
```bash
python scripts/run_dlt_activity_collection.py \
  --segment "YOUR_SEGMENT_HERE" \
  --time-filter "month" \
  --min-activity 40
```

**Template 5: Daily Monitoring**
```bash
python scripts/run_dlt_activity_collection.py \
  --all \
  --time-filter "day" \
  --min-activity 50 \
  --pipeline "daily_monitor_$(date +%Y%m%d)"
```

---

## 🎉 Conclusion

These examples provide a comprehensive toolkit for leveraging the DLT Activity Validation System across diverse use cases. From quick trend monitoring to academic research, the system's flexibility and intelligence make it suitable for virtually any Reddit data collection need.

### Key Takeaways

1. **Start Simple** - Begin with basic collections and gradually add complexity
2. **Use Dry Runs** - Always validate configuration before production runs
3. **Monitor Quality** - Adjust activity thresholds based on your specific needs
4. **Schedule Intelligently** - Use time-based collection for different research goals
5. **Leverage Segments** - Use predefined segments for organized, thematic collection

### Next Steps

1. **Choose your starting example** based on your research goals
2. **Customize parameters** to match your specific requirements
3. **Set up monitoring** to track collection performance
4. **Establish schedules** for regular data collection
5. **Build analysis pipelines** to process collected data

For more advanced configuration options, see the [DLT Activity Validation Guide](../guides/dlt-activity-validation.md).

---

<div style="text-align: center; margin-top: 50px; padding: 20px; background: linear-gradient(135deg, #FF6B35 0%, #004E89 100%); border-radius: 10px; color: white;">
  <h3 style="margin: 0 0 10px 0;">🚀 Start Your Collection Journey</h3>
  <p style="margin: 0; font-size: 1.1em;">Copy any example above and modify it for your specific research needs.</p>
</div>