# RedditHarbor Marimo Integration

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">Interactive Research Dashboards</h1>
  <p style="color: #004E89; font-size: 1.2em;">Reactive notebooks for Reddit data analysis and visualization</p>
</div>

## Overview

This directory contains Marimo reactive notebooks that provide interactive interfaces for RedditHarbor research workflows. These notebooks enable real-time data exploration, sentiment analysis, and privacy controls without writing code.

## Installation

```bash
# Install Marimo with recommended dependencies
pip install "marimo[recommended]"

# Install additional dependencies for sentiment analysis
pip install textblob

# Install dependencies for database connectivity
pip install pandas sqlalchemy psycopg2-binary
```

## Available Notebooks

### 📊 Opportunity Dashboard (`opportunity_dashboard_reactive.py`)
**Purpose**: Interactive dashboard for Reddit opportunity analysis
**Features**:
- Real-time filtering and sorting
- Opportunity scoring visualization
- Interactive charts and data exploration
- Subreddit analysis tools

**Launch**: `marimo run marimo_notebooks/opportunity_dashboard_reactive.py`

### 🏆 Top Contenders Dashboard (`top_contenders_dashboard.py`)
**Purpose**: Display top opportunities with AI-powered insights
**Features**:
- Top 5 opportunity cards
- AI insights (app concept, core functions, growth justification)
- Sector and score filters
- CSV export functionality

**Launch**: `marimo run marimo_notebooks/top_contenders_dashboard.py --port 8895`

### 🔍 Opportunity Analysis (`opportunity_analysis_dashboard.py`)
**Purpose**: Detailed analysis dashboard for opportunity research
**Features**:
- Comprehensive opportunity metrics
- Market validation data
- Competitive analysis tools
- Technical feasibility assessment

**Launch**: `marimo run marimo_notebooks/opportunity_analysis_dashboard.py`

### 💡 Opportunity Insights (`opportunity_insights_dashboard.py`)
**Purpose**: AI-powered insights and recommendations
**Features**:
- Z.AI GLM-4.6 integration for insights
- Growth justification analysis
- Monetization recommendations
- Technical implementation suggestions

**Launch**: `marimo run marimo_notebooks/opportunity_insights_dashboard.py`

### ⚡ Simple Dashboard (`simple_opportunity_dashboard.py`)
**Purpose**: Lightweight dashboard for quick exploration
**Features**:
- Basic filtering and visualization
- Quick data overview
- Minimal setup required

**Launch**: `marimo run marimo_notebooks/simple_opportunity_dashboard.py`

### 🎯 Database Dashboard (`db_dashboard.py`)
**Purpose**: Database management and query interface
**Features**:
- Direct database queries
- Table browsing
- Query execution
- Data export tools

**Launch**: `marimo run marimo_notebooks/db_dashboard.py`

### 📡 Live Dashboard (`live_dashboard.py`)
**Purpose**: Real-time data monitoring dashboard
**Features**:
- Real-time updates
- Live data collection monitoring
- Active research tracking

**Launch**: `marimo run marimo_notebooks/live_dashboard.py`

### 🎮 Reddit Demo (`redditharbor_demo.py`)
**Purpose**: Demo script showcasing RedditHarbor capabilities
**Features**:
- Basic data collection examples
- Simple Reddit API integration
- Quick start guide

**Launch**: `python marimo_notebooks/redditharbor_demo.py`

### 🚀 Marimo Dashboard (`redditharbor_marimo_dashboard.py`)
**Purpose**: Main dashboard combining multiple features
**Features**:
- Comprehensive data visualization
- Multiple analysis tools
- Interactive controls

**Launch**: `python marimo_notebooks/redditharbor_marimo_dashboard.py`

## Configuration

### Environment Variables
```bash
# Database configuration
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=your_supabase_key
DB_HOST=127.0.0.1
DB_PORT=54322
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
```

## Development

### Testing
```bash
# Run Marimo notebook tests
pytest tests/marimo/ -v

# Test individual notebook
pytest tests/marimo/test_marimo_config.py -v
```

## Integration with RedditHarbor

These notebooks integrate seamlessly with RedditHarbor's:
- **Database Schema**: Direct access to redditor, submission, comment tables
- **Privacy Features**: Built-in PII anonymization and privacy controls
- **Research Templates**: Specialized notebooks for different research types
- **Security**: Respect for RedditHarbor's security and privacy guidelines