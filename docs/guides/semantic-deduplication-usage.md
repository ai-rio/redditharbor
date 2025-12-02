# Semantic Deduplication Usage Guide

> **Comprehensive guide for using the RedditHarbor semantic deduplication system**
> Phase 1: String-based deduplication (40-50% duplicate detection)

---

## Quick Start

### Prerequisites

- RedditHarbor project with Python environment
- Supabase local instance running
- Basic understanding of Reddit data collection

### Installation

```bash
# Ensure dependencies are installed
source .venv/bin/activate
uv sync

# Start Supabase if not running
supabase start

# Apply database schema
supabase db reset  # Or apply migration manually
```

### Basic Usage

```python
from core.deduplication import SimpleDeduplicator
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize deduplicator
deduplicator = SimpleDeduplicator(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_KEY')
)

# Process an opportunity
opportunity = {
    'id': 'example-123',
    'app_concept': 'App idea: Food delivery service for local restaurants'
}

result = deduplicator.process_opportunity(opportunity)
print(f"Success: {result['success']}")
print(f"Is duplicate: {result['is_duplicate']}")
print(f"Concept ID: {result['concept_id']}")
```

---

## Integration Examples

### 1. Integration with Reddit Data Collection

```python
# In your data collection pipeline
from core.deduplication import SimpleDeduplicator
import os

# Initialize once
deduplicator = SimpleDeduplicator(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def process_reddit_opportunities(opportunities):
    """Process Reddit opportunities with deduplication."""
    results = []

    for opportunity in opportunities:
        # Add deduplication
        dedup_result = deduplicator.process_opportunity(opportunity)

        # Store result metadata
        opportunity['_deduplication'] = dedup_result

        # Only process unique opportunities for expensive AI enrichment
        if not dedup_result['is_duplicate']:
            # Run AI enrichment, scoring, etc.
            opportunity = enrich_with_ai(opportunity)

        results.append(opportunity)

    return results
```

### 2. Batch Processing Existing Data

```python
# scripts/deduplication/migrate_existing_opportunities.py
from core.deduplication import SimpleDeduplicator
import os
from supabase import create_client

def migrate_existing_opportunities():
    """Process all existing opportunities for deduplication."""
    deduplicator = SimpleDeduplicator(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    # Get all opportunities without deduplication
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    response = supabase.table('opportunities_unified')\
        .select('id, app_concept')\
        .is_('business_concept_id', 'null')\
        .execute()

    for opportunity in response.data:
        result = deduplicator.process_opportunity(opportunity)
        print(f"Processed {opportunity['id']}: {result['message']}")

if __name__ == "__main__":
    migrate_existing_opportunities()
```

### 3. Real-time Integration with DLT Pipeline

```python
# In your DLT resource
from core.deduplication import SimpleDeduplicator
import os

# Global deduplicator instance
deduplicator = SimpleDeduplicator(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

@dlt.resource(write_disposition="merge", merge_key="id")
def app_opportunities():
    """Reddit app opportunities with real-time deduplication."""

    for reddit_post in fetch_reddit_posts():
        opportunity = extract_opportunity(reddit_post)

        # Add deduplication
        dedup_result = deduplicator.process_opportunity(opportunity)

        # Add metadata
        opportunity['_is_duplicate'] = dedup_result['is_duplicate']
        opportunity['_concept_id'] = dedup_result['concept_id']

        yield opportunity
```

---

## Configuration Options

### Environment Variables

```bash
# Required - Supabase configuration
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=your-service-role-key

# Optional - Logging level
LOG_LEVEL=INFO

# Optional - Performance tuning
DEDUPLICATION_BATCH_SIZE=100
DEDUPLICATION_TIMEOUT=30
```

### Custom Normalization Rules

The deduplicator includes built-in normalization, but you can extend it:

```python
class CustomDeduplicator(SimpleDeduplicator):
    def normalize_concept(self, concept: str) -> str:
        # Apply default normalization
        normalized = super().normalize_concept(concept)

        # Add custom rules
        custom_rules = {
            'saas': 'software as a service',
            'ai': 'artificial intelligence',
            'ml': 'machine learning'
        }

        for old, new in custom_rules.items():
            normalized = normalized.replace(old, new)

        return normalized
```

---

## Monitoring and Troubleshooting

### Performance Monitoring

```python
# Monitor deduplication performance
import time
import logging

def monitor_deduplication_performance(opportunities):
    """Track deduplication performance metrics."""
    start_time = time.time()
    total_processed = 0
    duplicates_found = 0

    for opportunity in opportunities:
        process_start = time.time()
        result = deduplicator.process_opportunity(opportunity)
        process_time = time.time() - process_start

        total_processed += 1
        if result['is_duplicate']:
            duplicates_found += 1

        # Log slow operations
        if process_time > 1.0:
            logging.warning(f"Slow deduplication: {process_time:.2f}s for {opportunity['id']}")

    total_time = time.time() - start_time
    dedup_rate = (duplicates_found / total_processed) * 100

    logging.info(f"Processed {total_processed} opportunities in {total_time:.2f}s")
    logging.info(f"Found {duplicates_found} duplicates ({dedup_rate:.1f}% rate)")
```

### Common Issues and Solutions

#### Issue: Database Connection Errors

```python
# Check database connectivity
from supabase import create_client
import os

def test_database_connection():
    try:
        client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

        # Test simple query
        response = client.table('business_concepts').select('count').execute()
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
```

#### Issue: Fingerprint Collisions

```python
# Test fingerprint uniqueness
def test_fingerprint_uniqueness():
    concepts = [
        "App idea: Food delivery service",
        "App idea: Recipe sharing app",
        "App idea: Fitness tracker"
    ]

    fingerprints = []
    for concept in concepts:
        fp = deduplicator.generate_fingerprint(concept)
        if fp in fingerprints:
            print(f"COLLISION DETECTED: {concept}")
        fingerprints.append(fp)

    print(f"Generated {len(fingerprints)} unique fingerprints")
```

#### Issue: Empty Concepts After Normalization

```python
# Debug concept normalization
def debug_concept_normalization():
    test_concepts = [
        "   ",  # Whitespace only
        "",     # Empty string
        "app:", # Prefix only
        "App idea: "  # Empty after prefix
    ]

    for concept in test_concepts:
        normalized = deduplicator.normalize_concept(concept)
        fingerprint = deduplicator.generate_fingerprint(concept)
        print(f"Original: '{concept}' -> Normalized: '{normalized}' -> FP: {fingerprint[:8]}...")
```

### Database Status Queries

```sql
-- Check deduplication statistics
SELECT * FROM deduplication_stats;

-- View most duplicated concepts
SELECT
    concept_name,
    submission_count,
    first_seen_at,
    last_updated_at
FROM business_concepts
WHERE submission_count > 1
ORDER BY submission_count DESC
LIMIT 10;

-- Check processing errors
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN business_concept_id IS NULL THEN 1 END) as unprocessed,
    COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates
FROM opportunities_unified
WHERE app_concept IS NOT NULL;
```

---

## Performance Characteristics

### Expected Performance

- **Processing Speed**: 10-50 opportunities per second
- **Duplicate Detection Rate**: 40-50% for Phase 1
- **Database Queries**: 2-3 queries per opportunity
- **Memory Usage**: Minimal (< 50MB for 10k opportunities)

### Optimization Tips

1. **Batch Processing**: Process opportunities in batches of 50-100
2. **Database Indexing**: Ensure fingerprint indexes exist
3. **Connection Pooling**: Reuse Supabase client instances
4. **Caching**: Cache frequently accessed concepts

```python
# Example of optimized batch processing
def batch_process_opportunities(opportunities, batch_size=100):
    """Process opportunities in optimized batches."""
    for i in range(0, len(opportunities), batch_size):
        batch = opportunities[i:i + batch_size]
        results = []

        for opportunity in batch:
            result = deduplicator.process_opportunity(opportunity)
            results.append(result)

        # Log batch progress
        processed = min(i + batch_size, len(opportunities))
        print(f"Processed {processed}/{len(opportunities)} opportunities")

        # Optional: Add small delay between batches
        time.sleep(0.1)

    return results
```

### Resource Monitoring

```python
import psutil
import time

def monitor_resources_during_processing(opportunities):
    """Monitor system resources during deduplication."""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    for opportunity in opportunities:
        result = deduplicator.process_opportunity(opportunity)

        # Check memory usage every 100 opportunities
        if opportunities.index(opportunity) % 100 == 0:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_growth = current_memory - start_memory

            if memory_growth > 100:  # Alert if > 100MB growth
                logging.warning(f"High memory usage: {current_memory:.1f}MB (+{memory_growth:.1f}MB)")

    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024

    logging.info(f"Processing completed in {end_time - start_time:.2f}s")
    logging.info(f"Memory usage: {start_memory:.1f}MB -> {end_memory:.1f}MB")
```

---

## Advanced Usage

### Custom Deduplication Logic

```python
class BusinessDeduplicator(SimpleDeduplicator):
    """Enhanced deduplicator with business logic."""

    def is_business_concept_similar(self, concept1: str, concept2: str) -> bool:
        """Custom similarity logic beyond fingerprint matching."""
        # Add business-specific rules
        similar_keywords = {
            'delivery': ['shipping', 'courier', 'transport'],
            'social': ['community', 'networking', 'connect'],
            'fitness': ['health', 'workout', 'exercise']
        }

        for main_term, synonyms in similar_keywords.items():
            if main_term in concept1 and any(syn in concept2 for syn in synonyms):
                return True
            if main_term in concept2 and any(syn in concept1 for syn in synonyms):
                return True

        return False

    def process_opportunity(self, opportunity: dict) -> dict:
        """Enhanced processing with custom logic."""
        result = super().process_opportunity(opportunity)

        # Add custom processing
        if result['success'] and not result['is_duplicate']:
            # Check for similar concepts using custom logic
            similar_concepts = self.find_similar_by_keywords(
                result['normalized_concept']
            )

            if similar_concepts:
                result['similar_concepts'] = similar_concepts
                result['needs_review'] = True

        return result
```

### Integration with Analytics

```python
def generate_deduplication_report():
    """Generate comprehensive deduplication analytics."""
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    # Get deduplication stats
    stats = supabase.table('deduplication_stats').select('*').execute()

    # Get top concepts
    top_concepts = supabase.table('business_concepts')\
        .select('concept_name, submission_count')\
        .gte('submission_count', 2)\
        .order('submission_count', desc=True)\
        .limit(20)\
        .execute()

    # Calculate cost savings
    if stats.data:
        total_ops = stats.data[0]['total_opportunities']
        duplicates = stats.data[0]['duplicates']
        cost_per_opportunity = 0.01  # Estimated LLM cost

        total_savings = duplicates * cost_per_opportunity

        report = {
            'total_opportunities': total_ops,
            'duplicates_found': duplicates,
            'deduplication_rate': stats.data[0]['deduplication_rate_percent'],
            'estimated_savings': total_savings,
            'top_concepts': top_concepts.data
        }

        return report

    return None
```

---

## Next Steps for Phase 2

### Preparing for ML Enhancement

1. **Data Collection**: Ensure sufficient unique concepts collected
2. **Embedding Generation**: Install sentence-transformers
3. **Vector Indexing**: Enable pgvector extension
4. **Semantic Search**: Implement similarity functions

```python
# Prepare for Phase 2
def prepare_for_phase_2():
    """Steps to prepare for ML-based deduplication."""

    # Install dependencies
    print("Install ML dependencies:")
    print("pip install sentence-transformers torch")

    # Enable pgvector
    print("Enable pgvector in Supabase:")
    print("CREATE EXTENSION IF NOT EXISTS vector;")

    # Generate embeddings for existing concepts
    print("Generate embeddings script:")
    print("python scripts/deduplication/generate_embeddings.py")
```

### Migration Checklist

- [ ] All existing opportunities processed through Phase 1
- [ ] Deduplication rate meets expectations (40-50%)
- [ ] No processing errors in logs
- [ ] Database indexes optimized
- [ ] Backup of current state created
- [ ] ML dependencies installed
- [ ] pgvector extension enabled

---

## Support and Resources

### Getting Help

1. **Check Logs**: Review `error_log/` directory for processing errors
2. **Database Status**: Use monitoring queries to check system health
3. **Performance**: Monitor processing times and resource usage
4. **Testing**: Run integration tests to verify functionality

### Related Documentation

- [Quick Start Guide](../implementation/semantic-deduplication-guides/deduplication-quick-start.md)
- [API Reference](../api/deduplication-api.md)
- [Implementation Plan](../plans/2025-11-18-semantic-deduplication-implementation.md)
- [Integration Tests](../../tests/test_deduplication_integration.py)

### Best Practices

1. **Always test** with small batches before processing large datasets
2. **Monitor performance** during initial migration
3. **Backup data** before major changes
4. **Validate results** with manual review of samples
5. **Document customizations** for future reference

---

**Remember**: Phase 1 provides solid foundation with 40-50% duplicate detection. Phase 2 will enhance this to 60-80% using ML techniques.