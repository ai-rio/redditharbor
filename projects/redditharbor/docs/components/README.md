# RedditHarbor Components

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">Component Documentation</h2>
  <p style="color: #004E89;">Detailed documentation for individual components</p>
</div>

## 🏗️ Component Overview

RedditHarbor is composed of several key components that work together to provide a complete Reddit data collection solution. Each component is designed to be modular, testable, and extensible.

---

## 📋 Core Components

### 1. RedditCollector (`redditharbor.collector`)

The main component for collecting Reddit data.

**Purpose:**
- Interact with Reddit API
- Handle rate limiting and retries
- Collect posts, comments, and user data
- Manage authentication and credentials

**Key Classes:**
```python
class RedditCollector:
    """Main collector for Reddit data."""

class RateLimitManager:
    """Manages Reddit API rate limits."""

class AuthManager:
    """Handles Reddit API authentication."""
```

**Usage Example:**
```python
from redditharbor.collector import RedditCollector

collector = RedditCollector(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

posts = collector.collect_subreddit_posts("python", limit=100)
```

### 2. PrivacyProcessor (`redditharbor.privacy`)

Handles data privacy and anonymization.

**Purpose:**
- Anonymize user information
- Detect and redact PII (Personally Identifiable Information)
- Apply privacy rules and policies
- Ensure compliance with privacy regulations

**Key Classes:**
```python
class PrivacyProcessor:
    """Processes data for privacy compliance."""

class PIIDetector:
    """Detects personally identifiable information."""

class Anonymizer:
    """Anonymizes sensitive data."""
```

**Usage Example:**
```python
from redditharbor.privacy import PrivacyProcessor

processor = PrivacyProcessor(
    anonymize_usernames=True,
    redact_emails=True,
    remove_private_info=True
)

anonymized_data = processor.process(raw_data)
```

### 3. DatabaseManager (`redditharbor.database`)

Manages database operations and connections.

**Purpose:**
- Handle database connections
- Manage schema and migrations
- Provide CRUD operations
- Optimize queries and performance

**Key Classes:**
```python
class DatabaseManager:
    """Manages database operations."""

class SchemaManager:
    """Manages database schema."""

class QueryBuilder:
    """Builds optimized database queries."""
```

**Usage Example:**
```python
from redditharbor.database import DatabaseManager

db = DatabaseManager("postgresql://user:pass@localhost/redditharbor")

# Store data
db.store_posts(posts)

# Query data
python_posts = db.get_posts_by_subreddit("python")
```

### 4. DataValidator (`redditharbor.validator`)

Validates collected data for quality and completeness.

**Purpose:**
- Validate data structure and format
- Check for data integrity
- Filter out spam or low-quality content
- Ensure consistency across datasets

**Key Classes:**
```python
class DataValidator:
    """Validates collected data."""

class QualityFilter:
    """Filters data based on quality metrics."""

class ConsistencyChecker:
    """Ensures data consistency."""
```

**Usage Example:**
```python
from redditharbor.validator import DataValidator

validator = DataValidator()

if validator.validate_posts(posts):
    print("Data is valid!")
else:
    print("Data validation failed")
```

### 5. ExportManager (`redditharbor.export`)

Exports data to various formats for analysis and sharing.

**Purpose:**
- Export data to JSON, CSV, Excel
- Create datasets for machine learning
- Generate reports and summaries
- Handle large dataset exports

**Key Classes:**
```python
class ExportManager:
    """Manages data export operations."""

class JSONExporter:
    """Exports data to JSON format."""

class CSVExporter:
    """Exports data to CSV format."""

class ExcelExporter:
    """Exports data to Excel format."""
```

**Usage Example:**
```python
from redditharbor.export import ExportManager

exporter = ExportManager()

# Export to JSON
exporter.to_json(data, "reddit_data.json")

# Export to CSV
exporter.to_csv(data, "reddit_data.csv")

# Export to Excel
exporter.to_excel(data, "reddit_data.xlsx")
```

---

## 🔄 Component Interactions

### Data Flow Diagram

```mermaid
graph LR
    A[RedditCollector] --> B[PrivacyProcessor]
    B --> C[DataValidator]
    C --> D[DatabaseManager]
    D --> E[ExportManager]

    subgraph "External Services"
        F[Reddit API]
        G[Database]
        H[File System]
    end

    A --> F
    D --> G
    E --> H
```

### Component Dependencies

<div style="background: #F5F5F5; padding: 15px; border-radius: 8px; margin: 20px 0;">
  <h4 style="color: #1A1A1A; margin-top: 0;">Dependency Graph</h4>
  <ul style="color: #1A1A1A; padding-left: 20px;">
    <li><strong>RedditCollector</strong> → AuthManager, RateLimitManager</li>
    <li><strong>PrivacyProcessor</strong> → PIIDetector, Anonymizer</li>
    <li><strong>DatabaseManager</strong> → SchemaManager, QueryBuilder</li>
    <li><strong>DataValidator</strong> → QualityFilter, ConsistencyChecker</li>
    <li><strong>ExportManager</strong> → JSONExporter, CSVExporter, ExcelExporter</li>
  </ul>
</div>

---

## ⚙️ Configuration Components

### ConfigManager (`redditharbor.config`)

Manages configuration settings and environment variables.

**Purpose:**
- Load configuration from files and environment
- Validate configuration values
- Provide default settings
- Handle environment-specific configurations

**Key Classes:**
```python
class ConfigManager:
    """Manages configuration settings."""

class EnvironmentConfig:
    """Loads environment-specific configuration."""

class DefaultConfig:
    """Provides default configuration values."""
```

**Configuration Structure:**
```python
# config.yaml example
reddit:
  client_id: ${REDDIT_CLIENT_ID}
  client_secret: ${REDDIT_CLIENT_SECRET}
  user_agent: "RedditHarbor/1.0"

database:
  url: ${DATABASE_URL}
  pool_size: 10
  max_overflow: 20

privacy:
  anonymize_usernames: true
  redact_emails: true
  remove_private_info: true

rate_limits:
  requests_per_minute: 60
  requests_per_second: 1
  burst_size: 10
```

---

## 🔌 Plugin Components

### PluginManager (`redditharbor.plugins`)

Manages plugins for extending functionality.

**Purpose:**
- Load and manage plugins
- Provide plugin interface
- Handle plugin dependencies
- Enable custom functionality

**Key Classes:**
```python
class PluginManager:
    """Manages plugin lifecycle."""

class PluginInterface:
    """Base interface for all plugins."""

class PluginLoader:
    """Loads plugins from various sources."""
```

**Available Plugin Types:**

1. **Data Source Plugins** - Add new social media platforms
2. **Storage Plugins** - Add new database backends
3. **Processor Plugins** - Add custom data processing logic
4. **Export Plugins** - Add new export formats
5. **Analytics Plugins** - Add custom analytics capabilities

**Example Plugin:**
```python
from redditharbor.plugins import PluginInterface

class TwitterPlugin(PluginInterface):
    """Plugin for collecting Twitter data."""

    def collect_data(self, query: str, limit: int = 100):
        """Collect Twitter data based on query."""
        # Implementation here
        pass

    def validate_config(self, config: dict) -> bool:
        """Validate plugin configuration."""
        # Implementation here
        pass
```

---

## 📊 Monitoring Components

### MetricsCollector (`redditharbor.monitoring`)

Collects and reports system metrics.

**Purpose:**
- Monitor system performance
- Track API usage and limits
- Collect business metrics
- Provide health checks

**Key Classes:**
```python
class MetricsCollector:
    """Collects various system metrics."""

class PerformanceMonitor:
    """Monitors system performance."""

class HealthChecker:
    """Performs system health checks."""
```

**Metrics Tracked:**

- **API Metrics**: Request count, response time, error rate
- **Performance Metrics**: CPU usage, memory usage, disk I/O
- **Business Metrics**: Data collection rate, storage usage
- **Health Metrics**: Database connectivity, API availability

---

## 🔧 Utility Components

### Logger (`redditharbor.logging`)

Provides structured logging functionality.

**Purpose:**
- Structured logging with multiple levels
- Log rotation and management
- Integration with monitoring systems
- Debug and troubleshooting support

**Key Classes:**
```python
class StructuredLogger:
    """Provides structured logging."""

class LogManager:
    """Manages log files and rotation."""

class LogFormatter:
    """Formats log messages."""
```

### CacheManager (`redditharbor.cache`)

Manages caching for performance optimization.

**Purpose:**
- Multi-level caching (memory, disk, distributed)
- Cache invalidation and expiration
- Performance optimization
- Rate limiting support

**Key Classes:**
```python
class CacheManager:
    """Manages multi-level caching."""

class MemoryCache:
    """In-memory cache implementation."""

class DiskCache:
    """Persistent disk cache."""

class RedisCache:
    """Distributed Redis cache."""
```

---

## 🧪 Testing Components

### TestDataGenerator (`redditharbor.testing`)

Generates test data for development and testing.

**Purpose:**
- Create realistic test datasets
- Mock Reddit API responses
- Generate edge cases for testing
- Provide test fixtures

**Key Classes:**
```python
class TestDataGenerator:
    """Generates test data."""

class MockRedditAPI:
    """Mocks Reddit API for testing."""

class TestDataFactory:
    """Creates test data instances."""
```

---

## 📚 Component Guides

### Creating Custom Components

To create a custom component:

1. **Inherit from base classes**
2. **Implement required interfaces**
3. **Add proper error handling**
4. **Write comprehensive tests**
5. **Add documentation**

**Example:**
```python
from redditharbor.base import BaseComponent
from redditharbor.exceptions import ComponentError

class CustomProcessor(BaseComponent):
    """Custom data processing component."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.validate_config()

    def process(self, data: dict) -> dict:
        """Process data with custom logic."""
        try:
            # Custom processing logic
            return self.custom_processing(data)
        except Exception as e:
            raise ComponentError(f"Processing failed: {e}")

    def validate_config(self) -> None:
        """Validate component configuration."""
        required_keys = ['custom_setting']
        for key in required_keys:
            if key not in self.config:
                raise ComponentError(f"Missing required config: {key}")
```

### Component Testing

```python
import pytest
from redditharbor.testing import TestDataFactory

class TestCustomProcessor:
    def setup_method(self):
        self.processor = CustomProcessor({'custom_setting': 'value'})
        self.test_data = TestDataFactory.create_post_data()

    def test_process_success(self):
        """Test successful data processing."""
        result = self.processor.process(self.test_data)
        assert result is not None
        assert 'processed_field' in result

    def test_process_invalid_data(self):
        """Test error handling for invalid data."""
        with pytest.raises(ComponentError):
            self.processor.process(None)
```

---

## 🔗 Component References

For detailed API documentation:

- **[RedditCollector API](../api/reddit-collector.md)** - Detailed API reference
- **[PrivacyProcessor API](../api/privacy-processor.md)** - Privacy processing reference
- **[DatabaseManager API](../api/database-manager.md)** - Database operations reference
- **[Configuration Guide](../guides/configuration.md)** - Configuration options
- **[Plugin Development](../guides/plugin-development.md)** - Creating custom plugins

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    For help with specific components, check our <a href="../guides/troubleshooting.md" style="color: #004E89;">Troubleshooting Guide</a>
  </p>
</div>