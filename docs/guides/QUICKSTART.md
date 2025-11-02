# RedditHarbor Quick Start

## New Organized Structure

RedditHarbor has been reorganized for better maintainability and AI-agent compatibility:

### Configuration
```python
from config import settings as config
print(config.REDDIT_USER_AGENT)
```

### Core Functionality
```python
from core.setup import setup_redditharbor
from core.collection import collect_data, get_collection_status
```

### Scripts
```python
from scripts.research import run_research_project
from scripts.demo import demo_tech_trends_research
from scripts.certification import certify_data_collection
```

### Tests
```python
from tests.test_debug import main as debug_main
from tests.test_quick import main as quick_main
from tests.test_full import main as full_main
```

## Directory Structure

- `config/` - Configuration settings and credentials
- `core/` - Core functionality (setup, collection, templates)
- `scripts/` - Executable scripts (research, demo, certification)
- `tests/` - Test suite (debug, quick, full)
- `docs/` - Documentation