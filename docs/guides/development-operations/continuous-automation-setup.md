# RedditHarbor Continuous Automation Setup Guide

## Overview

This guide covers the complete continuous automation system for RedditHarbor, including:

1. **Continuous Collection System**: Automated daily Reddit harvesting
2. **60+ Score Hunter**: Specialized ultra-rare opportunity detection
3. **Automated Harvester**: Complete automation with scheduling
4. **Ultra-Rare Dashboard**: Real-time monitoring and alerts

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                Automated RedditHarvester                      │
├─────────────────────────────────────────────────────────────┤
│  Morning Collection (9:00 AM)                                │
│  ├─ Ultra-premium subreddit targeting                       │
│  ├─ Adaptive subreddit rotation                             │
│  └─ Performance-based allocation                            │
├─────────────────────────────────────────────────────────────┤
│  Afternoon Score Hunt (2:00 PM)                             │
│  ├─ Ultra-rare opportunity detection                        │
│  ├─ Enhanced scoring algorithms                            │
│  └─ 60+ threshold specialized analysis                      │
├─────────────────────────────────────────────────────────────┤
│  Evening Analysis (7:00 PM)                                 │
│  ├─ Performance metrics                                     │
│  ├─ Strategy optimization                                   │
│  └─ Weekly trend analysis                                  │
└─────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### 1. Install Required Dependencies

```bash
# Install schedule for automation
pip install schedule

# Verify existing dependencies
pip install -r requirements.txt
```

### 2. Database Tables Setup

The system requires additional database tables. Run these in Supabase SQL:

```sql
-- Continuous collection metrics
CREATE TABLE IF NOT EXISTS continuous_collection_metrics (
    id SERIAL PRIMARY KEY,
    collection_date DATE,
    status TEXT,
    total_target INTEGER,
    total_collected INTEGER,
    overall_success_rate DECIMAL,
    subreddit_stats JSONB,
    subreddit_count INTEGER,
    avg_posts_per_subreddit DECIMAL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ultra-rare opportunities tracking
CREATE TABLE IF NOT EXISTS ultra_rare_opportunities (
    id SERIAL PRIMARY KEY,
    opportunity_id TEXT UNIQUE,
    score DECIMAL,
    confidence_level TEXT,
    rarity_tier TEXT,
    discovery_method TEXT,
    validation_status TEXT,
    market_size_estimate TEXT,
    competitive_advantage TEXT,
    discovery_timestamp TIMESTAMP,
    hunter_version TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ultra-rare alerts
CREATE TABLE IF NOT EXISTS ultra_rare_alerts (
    id SERIAL PRIMARY KEY,
    opportunity_id TEXT,
    score DECIMAL,
    rarity_tier TEXT,
    confidence_level TEXT,
    market_size_estimate TEXT,
    alert_timestamp TIMESTAMP,
    alert_type TEXT,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Daily performance metrics
CREATE TABLE IF NOT EXISTS daily_performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE,
    collections_completed INTEGER,
    total_posts_collected INTEGER,
    opportunities_found INTEGER,
    ultra_rare_discoveries INTEGER,
    hit_rate TEXT,
    ultra_rare_rate TEXT,
    estimated_value INTEGER,
    performance_grade TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Automation system metrics
CREATE TABLE IF NOT EXISTS automation_system_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    automation_stats JSONB,
    hunter_report JSONB,
    system_health TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. Environment Configuration

Ensure your `.env.local` has the required settings:

```env
# Supabase Configuration
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=your_supabase_key

# Reddit API Configuration
REDDIT_PUBLIC=your_reddit_client_id
REDDIT_SECRET=your_reddit_client_secret

# OpenRouter for AI Profiling
OPENROUTER_API_KEY=your_openrouter_key
```

## Usage

### 1. Test Individual Components

```bash
# Test continuous collection system
python scripts/continuous_collection_system.py --test

# Test 60+ score hunter
python scripts/score_hunter_60_plus.py

# Test complete automation (single run)
python scripts/automated_reddit_harvester.py --test
```

### 2. Start Full Automation

```bash
# Start complete automation system
python scripts/automated_reddit_harvester.py
```

The system will:
- Run collection at 9:00 AM daily
- Hunt for ultra-rare opportunities at 2:00 PM daily
- Perform evening analysis at 7:00 PM daily
- Conduct weekly deep analysis on Sundays at 3:00 PM

### 3. Monitor Progress

```bash
# Launch ultra-rare dashboard
marimo run marimo_notebooks/ultra_rare_dashboard.py --host 0.0.0.0 --port 8081
```

Access at: http://localhost:8081

## Automation Schedule

### Daily Routine

| Time | Activity | Focus |
|------|----------|-------|
| 9:00 AM | Morning Collection | Ultra-premium subreddits |
| 2:00 PM | Afternoon Hunt | 60+ score detection |
| 7:00 PM | Evening Analysis | Performance review |

### Weekly Routine

| Day | Time | Activity |
|-----|------|----------|
| Sunday | 3:00 PM | Weekly deep analysis |

## Expected Performance

### Based on Current Data (1,912 submissions analyzed)

- **Hit Rate (40+ scores)**: 5.7% (109 opportunities)
- **Highest Score**: 51.9
- **Ultra-Rare (60+ scores)**: 0 found yet (expected <0.1%)
- **Legendary (70+ scores)**: Expected ~0.01% (1 in 10,000)

### Rarity Classification

- **Legendary (70+)**: Unicorn-level - transformational potential
- **Epic (60-69)**: Exceptional - rare high-impact potential
- **Rare (50-59)**: High-value - uncommon market potential
- **Common (40-49)**: Solid - standard methodology-compliant

## Monitoring & Alerts

### Ultra-Rare Discovery Alerts

When a 60+ opportunity is found, the system:
1. Logs detailed discovery information
2. Stores alert record in database
3. Updates dashboard in real-time
4. Provides market size and competitive advantage analysis

### Performance Metrics

The system tracks:
- Daily collection success rates
- Opportunity discovery rates
- Subreddit performance rankings
- Hit rate improvements over time
- Estimated value of discoveries

## Advanced Features

### Adaptive Subreddit Selection

The system uses performance-based subreddit rotation:
- **High Performers (40%)**: Subreddits with historical 45+ scores
- **Rotation Tiers (60%)**: Daily rotation through premium categories
- **Dynamic Allocation**: More posts for better-performing subreddits

### Ultra-Rare Scoring Algorithm

Specialized detection for 60+ opportunities:
- **Market Explosiveness (30%)**: Explosive growth, massive pain, enterprise need
- **Pain Intensity (40%)**: Extreme frustration, business-critical issues
- **Monetization Potential (25%)**: High willingness to pay, recurring revenue
- **Simplicity Bonus (5%)**: 1-3 function constraint compliance

### Quality Control

- Pre-filtering for high-potential content
- Deduplication across collection runs
- Constraint validation (1-3 function rule)
- Performance-based strategy optimization

## Troubleshooting

### Common Issues

1. **Reddit API Rate Limits**
   - System includes exponential backoff
   - Respects rate limits automatically
   - Logs rate limit events

2. **No Ultra-Rare Discoveries**
   - Expected behavior - 60+ scores are extremely rare
   - Check hit rate for 40+ opportunities (should be 3-8%)
   - Review subreddit targeting strategy

3. **Collection Failures**
   - Check Reddit API credentials
   - Verify network connectivity
   - Review error logs in `error_log/`

### Log Locations

- Continuous collection: `error_log/continuous_collection.log`
- Score hunter: `error_log/score_hunter_60_plus.log`
- Automation system: `error_log/automated_harvester.log`

## Scaling Strategy

### Phase 1: Current Setup
- 50 posts daily from premium subreddits
- Focus on ultra-premium domains
- Baseline performance metrics

### Phase 2: Expansion
- Increase to 100+ posts daily
- Add emerging subreddit categories
- Enhanced scoring algorithms

### Phase 3: Full Scale
- 500+ posts daily across all tiers
- Machine learning optimization
- Real-time opportunity validation

## Cost Analysis

### Current Costs
- **LLM Profiling**: ~$0.001 per submission
- **Daily Collection**: ~$0.05 for 50 posts
- **Monthly Estimate**: ~$1.50 for profiling

### Ultra-Rare Discovery Value
- **Regular Opportunity (40+)**: ~$1,000 estimated value
- **Rare Opportunity (50+)**: ~$10,000 estimated value
- **Ultra-Rare (60+)**: ~$50,000+ estimated value
- **Legendary (70+)**: ~$500,000+ estimated value

### ROI Calculation
With current 5.7% hit rate:
- 50 posts/day × 30 days = 1,500 posts
- 1,500 × 5.7% = 86 opportunities/month
- 86 × $1,000 = $86,000 potential monthly value
- Cost: $1.50/month → 57,000x ROI potential

## Next Steps

1. **Start Automation**: Begin with daily collection routine
2. **Monitor Performance**: Use dashboard to track metrics
3. **Optimize Strategy**: Adjust subreddit selection based on performance
4. **Scale Gradually**: Increase collection volume as system proves reliable

The system is designed for "set it and forget it" operation while continuously hunting for ultra-rare, high-value app opportunities.