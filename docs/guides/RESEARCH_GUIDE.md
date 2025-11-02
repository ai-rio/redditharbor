# RedditHarbor Research Guide

## Quick Research Workflow

### 1. Basic Research Setup
```python
from config import settings as config
from core.setup import setup_redditharbor
from core.collection import collect_data

# Initialize RedditHarbor
reddit, supabase = setup_redditharbor()

# Collect data from specific subreddits
subreddits = config.DEFAULT_SUBREDDITS  # ["python", "MachineLearning", "datascience", "learnprogramming"]
collect_data(reddit, supabase, subreddits, limit=50)
```

### 2. Using Pre-built Research Projects
```python
from scripts.research import run_research_project

# Available project types:
projects = [
    "programming_trends",           # Analyze programming language discussions
    "tech_industry_sentiment",      # Tech industry sentiment analysis
    "learning_community_analysis",  # How people learn programming
    "ai_ml_monitoring",            # AI/ML discussions monitoring
    "startup_ecosystem",           # Startup and entrepreneurship discussions
    "viral_content_analysis"       # Cross-community viral content analysis
]

# Run a specific research project
run_research_project("programming_trends", subreddits=["python", "MachineLearning"])
```

### 3. Custom Research Project
```python
from scripts.research import custom_research_project

# Define your custom research parameters
custom_params = {
    "subreddits": ["python", "learnprogramming"],
    "keywords": ["asyncio", "fastapi", "django", "flask"],
    "sort_type": "hot",
    "limit": 100,
    "time_filter": "month"
}

custom_research_project(
    name="web_framework_analysis",
    description="Analyze Python web framework discussions",
    **custom_params
)
```

### 4. Quick Demo Research
```python
from scripts.demo import demo_tech_trends_research

# Run a quick demonstration of research capabilities
demo_tech_trends_research()
```

## Research Templates Available

### Template 1: Programming Trends Analysis
```python
from scripts.research import project_1_programming_trends

project_1_programming_trends()
```

### Template 2: Tech Industry Sentiment
```python
from scripts.research import project_2_tech_industry_sentiment

project_2_tech_industry_sentiment()
```

### Template 3: Learning Community Analysis
```python
from scripts.research import project_3_learning_community_analysis

project_3_learning_community_analysis()
```

## Step-by-Step Research Example

Let's say you want to research Python framework discussions:

```python
# Step 1: Import necessary modules
from config import settings as config
from core.setup import setup_redditharbor
from core.collection import collect_data, get_collection_status
from scripts.research import generate_research_report

# Step 2: Setup the connection
reddit, supabase = setup_redditharbor()

# Step 3: Define your research scope
subreddits = ["python", "flask", "django", "fastapi"]
keywords = ["flask", "django", "fastapi", "web framework"]
limit = 100

# Step 4: Collect data
collect_data(reddit, supabase, subreddits, limit=limit)

# Step 5: Check collection status
status = get_collection_status(supabase)
print(f"Collected: {status['total_submissions']} submissions, {status['total_comments']} comments")

# Step 6: Generate research report
generate_research_report(
    title="Python Web Framework Analysis",
    description="Analysis of Python web framework discussions",
    output_format="markdown"
)
```

## Command Line Usage

### Quick Data Collection
```bash
# Run quick collection test
python -m tests.test_quick

# Run full functionality test
python -m tests.test_full
```

### Research Projects
```bash
# Run research projects directly
python -m scripts.research
```

### Demo Research
```bash
# Run demo research
python -m scripts.demo
```

## Configuration Options

Modify `config/settings.py` to customize:

```python
# Custom subreddits for your research
DEFAULT_SUBREDDITS = ["your", "target", "subreddits"]

# Collection parameters
DEFAULT_LIMIT = 200  # Increase for more data
DEFAULT_SORT_TYPES = ["hot", "top", "new"]

# Privacy settings
ENABLE_PII_ANONYMIZATION = True  # Keep True for research ethics
```

## Next Steps

1. **Start with the demo**: Run `python -m scripts.demo` to see how it works
2. **Check collection status**: Use `python -m tests.test_quick` to verify data collection
3. **Run your first research**: Use the templates in `scripts.research`
4. **Customize**: Modify configuration settings for your specific research needs

Happy researching! 🚀