# Pipeline v3 - Clean Reddit Data Processing Pipeline

A minimal, type-safe Reddit data extraction and analysis pipeline following ELT pattern: **Extract → Transform → Load**.

## Features

- 🔍 **Reddit Data Extraction**: PRAW-based Reddit API client with robust error handling
- 🤖 **LLM Analysis**: OpenAI integration with Pydantic + Instructor for structured output validation
- 💾 **Unified Storage**: SQLAlchemy with pgvector embeddings in a single PostgreSQL database
- 🔒 **Type Safety**: Full Pydantic model validation throughout the pipeline
- ⚡ **Performance**: Batch processing and transaction safety
- 🧪 **Testing**: Comprehensive test coverage with pytest

## Architecture

```
pipeline-v3/
├── models/           # Pydantic data models
├── extract/          # Reddit data extraction (PRAW)
├── transform/        # LLM analysis (Instructor + Pydantic)
├── load/            # Database loading (SQLAlchemy + pgvector)
├── config/          # Pydantic settings management
└── tests/           # Test suite
```

## Quick Start

### 1. Install Dependencies

```bash
cd pipeline-v3
uv sync
```

### 2. Configure Environment

Create `.env.local` file:

```bash
# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Database (optional - defaults to local Supabase)
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

### 3. Run the Pipeline

```bash
# Basic usage
python -m pipeline_v3 --limit 10 --subreddits productivity

# Advanced usage
python -m pipeline_v3 \
  --limit 25 \
  --subreddits productivity tools freelance \
  --sort-by top \
  --time-filter month \
  --min-score 70.0 \
  --min-confidence 60.0 \
  --validate-quality

# Test mode (mock data)
python -m pipeline_v3 --test-mode --limit 5

# Dry run (process but don't store)
python -m pipeline_v3 --dry-run --limit 10
```

## Configuration

All configuration is managed through Pydantic settings with environment variable support:

```python
# config/settings.py
class Settings(BaseSettings):
    # Reddit API
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "RedditHarbor Pipeline v3/1.0"

    # Database
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    # LLM
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3

    # Pipeline
    default_subreddits: List[str] = ["productivity", "tools"]
    default_limit: int = 10
    batch_size: int = 5

    # pgvector
    embedding_dimension: int = 384
    similarity_threshold: float = 0.8
```

## Data Models

### Reddit Data
```python
class RedditSubmission(BaseModel):
    id: str
    title: str
    text: str
    author: str
    upvotes: int
    score: int
    comments_count: int
    subreddit: str
    created_utc: datetime
    permalink: str
```

### Analysis Results
```python
class AppIdea(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    app_concept: str
    problem_statement: str
    target_audience: str
    core_functions: List[str] = Field(..., min_items=1, max_items=3)  # MAX 3!
```

### Database Storage
```python
class Opportunity(Base):
    id: UUID
    app_title: str
    final_score: float
    trust_level: str
    embedding: Vector(384)  # pgvector in same table
    created_at: datetime
```

## Key Design Principles

### 1. Simplicity Over Complexity
- **Maximum 3 core functions** per app (enforced by Pydantic validation)
- Simple, focused tools preferred over complex platforms
- One clear responsibility per module

### 2. Type Safety Everywhere
- Pydantic models validate all data structures
- SQLAlchemy models match Pydantic 1:1
- Full type hints throughout codebase

### 3. Error Handling & Validation
- Reddit API errors with fallbacks
- LLM output validation with Instructor
- Database transaction safety with rollbacks

### 4. Performance & Scalability
- Batch LLM processing
- Database connection pooling
- pgvector for efficient similarity search

## Command Line Options

```bash
# Reddit extraction
--limit N                    # Max submissions to fetch
--subreddits a b c           # Subreddits to fetch from
--sort-by hot|top|new        # Sorting method
--time-filter hour|day|week  # Time filter for top posts

# Quality filtering
--min-score 70.0            # Minimum opportunity score
--min-confidence 60.0        # Minimum confidence score
--validate-quality           # Enable additional validation

# Processing
--batch-size N              # LLM batch size
--test-mode                 # Use mock data
--dry-run                   # Process but don't store

# Output
--log-level DEBUG|INFO|...  # Logging level
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=models --cov=extract --cov=transform --cov=load

# Run specific tests
pytest tests/test_extract.py
pytest tests/test_models.py
```

## Database Schema

The pipeline uses a single `opportunities` table with:

- **Reddit metadata**: submission_id, subreddit, upvotes, comments
- **App analysis**: title, concept, problem, core_functions (JSON)
- **Market metrics**: market_demand, pain_intensity, monetization_potential
- **Scoring**: final_score, confidence_score, trust_level
- **Search**: pgvector embedding for similarity search

## Example Output

```
STEP 1: Extracting Reddit submissions
✓ Extracted 10 submissions in 2.34s

STEP 2: Analyzing submissions with LLM
✓ Analyzed 10 submissions in 45.67s

STEP 3: Validating analysis quality
✓ Filtered to 3 high-quality analyses in 0.12s

STEP 4: Storing analyses to database
✓ Stored 3 analyses in 0.89s

PIPELINE COMPLETION SUMMARY
Total execution time: 48.02s

Step Results:
  1. Extract: 10 submissions
  2. Analyze: 10 analyses
  3. Filter: 3 high-quality
  4. Store: 3 stored, 0 skipped, 0 errors

Quality Metrics:
  - Validation rate: 90.0%
  - High score rate: 30.0%
  - Average score: 75.3
```

## Development

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

### Adding New Features
1. Add Pydantic models in `models/`
2. Implement extraction/transform/load logic
3. Add comprehensive tests
4. Update documentation

## Comparison with Pipeline v2

| Feature | Pipeline v2 | Pipeline v3 |
|---------|-------------|------------|
| Architecture | Complex ETL with conflicts | Clean ELT pattern |
| Type Safety | Partial validation | Full Pydantic validation |
| LLM Integration | Disabled due to conflicts | Instructor + Pydantic |
| Database | DLT SQLAlchemy hybrid | SQLAlchemy only |
| pgvector | Available but unused | Fully integrated |
| Error Handling | Complex workarounds | Clean transaction safety |
| Testing | Limited | Comprehensive |
| Code Quality | Technical debt | Clean, maintainable |

## Next Steps

1. **Add embedding generation** for semantic similarity search
2. **Implement deduplication** using pgvector similarity
3. **Add monitoring** and metrics collection
4. **Expand LLM providers** (Anthropic, Gemini, etc.)
5. **Add API endpoints** for external access