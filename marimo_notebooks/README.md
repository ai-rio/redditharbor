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

### 📊 Research Dashboard (`research_dashboard.py`)
**Purpose**: Main interactive dashboard for Reddit data exploration
**Features**:
- Subreddit selection and filtering
- Data type selection (submissions, comments, both)
- Real-time data visualization
- Interactive charts and tables

**Launch**: `python scripts/launch_marimo_notebook.py research_dashboard`

### 🧠 Sentiment Analysis (`sentiment_analysis.py`)
**Purpose**: Sentiment analysis of Reddit content with interactive controls
**Features**:
- Sentiment score calculation and visualization
- Adjustable sentiment thresholds
- Subreddit-specific analysis
- Sentiment distribution charts

**Launch**: `python scripts/launch_marimo_notebook.py sentiment_analysis`

### 🔒 Privacy Explorer (`privacy_explorer.py`)
**Purpose**: Privacy control and PII anonymization interface
**Features**:
- Three privacy levels (strict, moderate, permissive)
- Real-time PII anonymization preview
- Safe data exploration
- Original vs. anonymized comparison

**Launch**: `python scripts/launch_marimo_notebook.py privacy_explorer`

### 🔍 SQL Query Builder (`sql_query_builder.py`)
**Purpose**: Interactive SQL query interface for RedditHarbor database
**Features**:
- Pre-built query templates
- Custom SQL query editor
- Real-time query execution
- Results visualization

**Launch**: `python scripts/launch_marimo_notebook.py sql_query_builder`

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