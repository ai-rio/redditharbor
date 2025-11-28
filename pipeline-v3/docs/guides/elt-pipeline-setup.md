# Pipeline v3 ELT Setup Guide

<div align="center">

**Complete Setup for Clean Reddit Data Processing**

*From zero to working ELT pipeline in 15 minutes*

</div>

## 📋 Table of Contents

- [🚀 Prerequisites](#-prerequisites)
- [⚙️ Environment Setup](#️-environment-setup)
- [🔧 Configuration](#-configuration)
- [🏃 Quick Start](#-quick-start)
- [🧪 Testing Your Setup](#-testing-your-setup)
- [🔍 Troubleshooting](#-troubleshooting)

---

## 🚀 Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, or Windows (WSL2)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB free space for database and logs

### Required Services

- **Supabase**: Local instance or cloud account
- **Reddit API**: Script application with credentials
- **OpenRouter API**: Account with API key (optional, can use mock initially)

### Development Tools

- **UV**: Python package manager (`pip install uv`)
- **Git**: Version control
- **Code Editor**: VS Code or similar with Python extensions

---

## ⚙️ Environment Setup

### 1. Clone and Navigate

```bash
# Clone the repository
git clone <repository-url>
cd redditharbor-core-functions-fix

# Navigate to Pipeline v3
cd pipeline-v3
```

### 2. Install Dependencies

```bash
# Install dependencies with UV (recommended)
uv sync

# Or with pip (fallback)
pip install -r requirements.txt
```

### 3. Start Supabase

```bash
# Start Supabase locally (if not already running)
supabase start

# Verify services are running
supabase status
```

**Expected Output:**
```
API URL: http://127.0.0.1:54321
DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
Studio URL: http://127.0.0.1:54323
```

---

## 🔧 Configuration

### 1. Environment Variables

Create a `.env` file in the `pipeline-v3` root:

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env
```

**Required `.env` configuration:**

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=your_supabase_anon_key

# Reddit API Configuration
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=RedditHarbor/1.0

# OpenRouter API (Optional - will use mock if not provided)
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Pipeline Configuration
LOG_LEVEL=INFO
BATCH_SIZE=100
MAX_RETRIES=3
```

### 2. Reddit API Setup

1. **Create Reddit App**:
   - Visit https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Select "script" as app type
   - Set name: "RedditHarbor Pipeline v3"
   - Add redirect URI: `http://localhost:8080`

2. **Get Credentials**:
   - Note the `client_id` (the string under the app name)
   - Generate and note the `client_secret`

3. **Update `.env`**:
   ```env
   REDDIT_CLIENT_ID=your_actual_client_id
   REDDIT_CLIENT_SECRET=your_actual_client_secret
   ```

### 3. OpenRouter API Setup (Optional)

1. **Create Account**:
   - Visit https://openrouter.ai
   - Sign up and add payment method

2. **Get API Key**:
   - Go to API Keys section
   - Create new API key

3. **Update `.env`**:
   ```env
   OPENROUTER_API_KEY=your_actual_api_key
   ```

---

## 🏃 Quick Start

### 1. Initialize Database

```bash
# Run database migrations
python -m pipeline_v3.scripts.init_database

# Verify tables created
python -m pipeline_v3.scripts.check_schema
```

### 2. Test Extraction Layer

```bash
# Test Reddit API connection
python -m pipeline_v3.extract.test_reddit_connection

# Test basic data extraction
python -m pipeline_v3.extract.test_extraction --subreddit productivity --limit 5
```

### 3. Run Full Pipeline

```bash
# Run complete ELT pipeline with sample data
python -m pipeline_v3.main \
  --subreddit productivity \
  --limit 10 \
  --dry-run

# Run with real data processing
python -m pipeline_v3.main \
  --subreddit productivity \
  --limit 25 \
  --enable-llm-analysis
```

### 4. Monitor Results

```bash
# Check processed data
python -m pipeline_v3.scripts.view_opportunities --limit 5

# Check pipeline statistics
python -m pipeline_v3.scripts.pipeline_stats
```

---

## 🧪 Testing Your Setup

### 1. Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test suites
pytest tests/test_extract/
pytest tests/test_transform/
pytest tests/test_load/

# Run with coverage
pytest --cov=pipeline_v3 tests/
```

### 2. Integration Tests

```bash
# Test full pipeline integration
pytest tests/integration/test_full_pipeline.py

# Test API integrations
pytest tests/integration/test_api_integration.py
```

### 3. Performance Tests

```bash
# Test batch processing performance
python -m pipeline_v3.scripts.performance_test --batch-sizes 10,50,100

# Test database performance
python -m pipeline_v3.scripts.database_performance_test
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Reddit API Connection Issues

**Problem**: `401 Unauthorized` or `Forbidden` errors

**Solution**:
```bash
# Verify credentials
python -c "
import praw
reddit = praw.Reddit(
    client_id='your_id',
    client_secret='your_secret',
    user_agent='RedditHarbor/1.0'
)
print(reddit.user.me())
"
```

#### 2. Database Connection Issues

**Problem**: `connection refused` or `authentication failed`

**Solution**:
```bash
# Check Supabase status
supabase status

# Test database connection
python -c "
import sqlalchemy
engine = sqlalchemy.create_engine('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
with engine.connect() as conn:
    print('Database connection successful')
"
```

#### 3. Missing Dependencies

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
# Reinstall dependencies
uv sync --reinstall

# Verify installation
python -c "import pipeline_v3; print('Import successful')"
```

#### 4. Pydantic Validation Errors

**Problem**: Data validation failures

**Solution**:
```bash
# Check validation logs
tail -f logs/validation.log

# Run with debug mode
python -m pipeline_v3.main --debug --limit 1
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Run with debug logging
python -m pipeline_v3.main \
  --debug \
  --log-level DEBUG \
  --subreddit productivity \
  --limit 1
```

### Log Locations

- **Application Logs**: `logs/pipeline_v3.log`
- **Validation Logs**: `logs/validation.log`
- **Error Logs**: `logs/error.log`
- **Performance Logs**: `logs/performance.log`

---

## 🔗 Next Steps

### After Successful Setup

1. **[Configuration Guide](./configuration-guide.md)** - Advanced configuration options
2. **[Performance Optimization](./performance-optimization.md)** - Speed up your pipeline
3. **[Production Deployment](./production-deployment.md)** - Deploy to production
4. **[Monitoring & Maintenance](./monitoring-guide.md)** - Keep your pipeline healthy

### Integration with Existing Systems

- **[RedditHarbor Live Testing](../../docs/live-test/)** - Real data validation
- **[Business Opportunity Scoring](../components/opportunity-scoring.md)** - Business logic integration
- **[API Documentation](../api/)** - External API usage

---

## 🆘 Get Help

If you encounter issues during setup:

1. **Check Logs**: Review log files for detailed error messages
2. **Run Diagnostics**: `python -m pipeline_v3.scripts.diagnostics`
3. **Check Troubleshooting**: Review common issues above
4. **Create Issue**: Report bugs with full error logs and system info

### Useful Diagnostic Commands

```bash
# Full system diagnostics
python -m pipeline_v3.scripts.diagnostics

# Check all service connections
python -m pipeline_v3.scripts.check_connections

# Validate configuration
python -m pipeline_v3.scripts.validate_config
```

---

<div align="center">

**🎉 Your Pipeline v3 ELT setup is complete!**

**Next: Run your first real data processing:**
```bash
python -m pipeline_v3.main --subreddit productivity --limit 25
```

</div>