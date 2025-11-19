# Deduplication API Reference

> **Complete API documentation for RedditHarbor semantic deduplication system**
> Version: 1.0.0 (Phase 1)

---

## Overview

The `SimpleDeduplicator` class provides string-based deduplication functionality for Reddit opportunity data. It uses SHA256 fingerprinting to identify duplicate business concepts and integrates with Supabase for data persistence.

## Class: SimpleDeduplicator

### Constructor

```python
def __init__(self, supabase_url: str, supabase_key: str)
```

Initialize the deduplicator with Supabase connection parameters.

**Parameters:**
- `supabase_url` (str): Supabase project URL
- `supabase_key` (str): Supabase service role key

**Raises:**
- `ImportError`: If supabase package is not installed
- `Exception`: If Supabase client creation fails

**Example:**
```python
from core.deduplication import SimpleDeduplicator
import os

deduplicator = SimpleDeduplicator(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_KEY')
)
```

---

## Core Methods

### normalize_concept()

```python
def normalize_concept(self, concept: str) -> str
```

Normalize business concept text for consistent fingerprinting.

**Parameters:**
- `concept` (str): Raw business concept text

**Returns:**
- `str`: Normalized concept string

**Processing Steps:**
1. Convert to lowercase
2. Remove common app-related prefixes
3. Normalize whitespace (multiple spaces to single space)
4. Strip leading/trailing spaces

**Example:**
```python
normalized = deduplicator.normalize_concept("App idea: Food delivery service")
# Returns: "idea: food delivery service"
```

### generate_fingerprint()

```python
def generate_fingerprint(self, concept: str) -> str
```

Generate SHA256 fingerprint from normalized concept.

**Parameters:**
- `concept` (str): Business concept text

**Returns:**
- `str`: 64-character SHA256 hash as hexadecimal string

**Example:**
```python
fingerprint = deduplicator.generate_fingerprint("App idea: Food delivery")
# Returns: "a1b2c3d4e5f6..." (64 character string)
```

### validate_and_convert_uuid()

```python
def validate_and_convert_uuid(self, opportunity_id: str) -> str
```

Validate and convert opportunity ID to proper UUID format.

**Parameters:**
- `opportunity_id` (str): Raw opportunity identifier

**Returns:**
- `str`: Valid UUID string

**Raises:**
- `ValueError`: If opportunity_id is empty

**Note:** For testing purposes, generates deterministic UUID for non-UUID strings.

---

## Database Operations

### find_existing_concept()

```python
def find_existing_concept(self, fingerprint: str) -> dict | None
```

Check if business concept already exists in database.

**Parameters:**
- `fingerprint` (str): SHA256 fingerprint to search for

**Returns:**
- `dict | None`: Concept data if found, None otherwise

**Returns Structure:**
```python
{
    "id": int,                    # Business concept ID
    "concept_name": str,          # Normalized concept name
    "concept_fingerprint": str,   # SHA256 fingerprint
    "submission_count": int,      # Number of submissions
    "primary_opportunity_id": str, # UUID of primary opportunity
    "first_seen_at": str,         # ISO timestamp
    "last_updated_at": str,       # ISO timestamp
    "created_at": str            # ISO timestamp
}
```

### create_business_concept()

```python
def create_business_concept(
    self, concept_name: str, fingerprint: str, opportunity_id: str
) -> int | None
```

Create new business concept in database.

**Parameters:**
- `concept_name` (str): Normalized business concept name
- `fingerprint` (str): SHA256 fingerprint of the concept
- `opportunity_id` (str): ID of the opportunity creating this concept

**Returns:**
- `int | None`: ID of created concept if successful, None otherwise

**Database Record Created:**
```sql
INSERT INTO business_concepts (
    concept_name,
    concept_fingerprint,
    primary_opportunity_id,
    submission_count
) VALUES (?, ?, ?, 1);
```

### update_concept_stats()

```python
def update_concept_stats(self, concept_id: int) -> None
```

Update concept statistics in database.

**Parameters:**
- `concept_id` (int): ID of the concept to update

**Action:**
- Increments `submission_count` by 1
- Updates `last_updated_at` timestamp

### mark_as_duplicate()

```python
def mark_as_duplicate(
    self, opportunity_id: str, concept_id: int, primary_opportunity_id: str
) -> bool
```

Mark an opportunity as a duplicate.

**Parameters:**
- `opportunity_id` (str): ID of opportunity to mark as duplicate
- `concept_id` (int): ID of business concept it belongs to
- `primary_opportunity_id` (str): ID of primary/original opportunity

**Returns:**
- `bool`: True if successful, False otherwise

**Database Updates:**
```sql
UPDATE opportunities_unified
SET
    business_concept_id = ?,
    is_duplicate = TRUE,
    duplicate_of_id = ?,
    updated_at = NOW()
WHERE id = ?;
```

### mark_as_unique()

```python
def mark_as_unique(self, opportunity_id: str, concept_id: int) -> bool
```

Mark an opportunity as unique (original).

**Parameters:**
- `opportunity_id` (str): ID of opportunity to mark as unique
- `concept_id` (int): ID of business concept it belongs to

**Returns:**
- `bool`: True if successful, False otherwise

**Database Updates:**
```sql
UPDATE opportunities_unified
SET
    business_concept_id = ?,
    is_duplicate = FALSE,
    duplicate_of_id = NULL,
    updated_at = NOW()
WHERE id = ?;
```

---

## Main Processing Method

### process_opportunity()

```python
def process_opportunity(self, opportunity: dict) -> dict
```

Process single opportunity for deduplication with complete workflow.

**Parameters:**
- `opportunity` (dict): Opportunity data dictionary

**Required Fields:**
```python
{
    "id": str,           # Unique opportunity identifier
    "app_concept": str   # Business concept description
}
```

**Optional Fields:**
```python
{
    "title": str,        # Opportunity title
    "subreddit": str,    # Source subreddit
    "score": int,        # Reddit score
    # ... any other fields
}
```

**Returns:**
- `dict`: Comprehensive processing result

**Return Structure:**
```python
{
    "success": bool,              # Overall processing success
    "is_duplicate": bool,         # Whether opportunity was identified as duplicate
    "concept_id": int | None,     # Business concept ID if successful
    "opportunity_id": str | None, # Opportunity ID (converted to UUID)
    "fingerprint": str | None,    # Generated fingerprint
    "normalized_concept": str | None, # Normalized concept text
    "message": str,               # Success or error message
    "processing_time": float,     # Time taken in seconds
    "error": str | None           # Error details if failed
}
```

**Processing Workflow:**
1. **Validation**: Check required fields (id, app_concept)
2. **Normalization**: Normalize concept and generate fingerprint
3. **Lookup**: Check for existing concepts using fingerprint
4. **Duplicate Handling**: If found, mark as duplicate and update stats
5. **Unique Handling**: If unique, create new concept and mark as unique
6. **Result**: Return comprehensive result with timing

**Example:**
```python
opportunity = {
    "id": "example-123",
    "app_concept": "App idea: Food delivery service for local restaurants",
    "title": "Looking for feedback on delivery app",
    "subreddit": "startups"
}

result = deduplicator.process_opportunity(opportunity)

if result["success"]:
    print(f"Processed successfully: {result['message']}")
    print(f"Is duplicate: {result['is_duplicate']}")
    print(f"Concept ID: {result['concept_id']}")
else:
    print(f"Processing failed: {result['error']}")
```

---

## Database Schema

### business_concepts Table

```sql
CREATE TABLE business_concepts (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    concept_name TEXT NOT NULL,
    concept_fingerprint TEXT UNIQUE NOT NULL,
    embedding VECTOR(384),                    -- Phase 2 (NULL in Phase 1)
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    submission_count INTEGER DEFAULT 1,
    primary_opportunity_id UUID REFERENCES opportunities_unified(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes:**
```sql
CREATE INDEX idx_business_concepts_fingerprint
ON business_concepts(concept_fingerprint);

CREATE INDEX idx_business_concepts_embedding_hnsw
ON business_concepts
USING hnsw (embedding vector_ip_ops)
WITH (m = 16, ef_construction = 64);
```

### opportunities_unified Table (Deduplication Columns)

```sql
ALTER TABLE opportunities_unified
ADD COLUMN business_concept_id BIGINT REFERENCES business_concepts(id),
ADD COLUMN semantic_fingerprint TEXT,          -- Deprecated
ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN duplicate_of_id UUID REFERENCES opportunities_unified(id);
```

**Indexes:**
```sql
CREATE INDEX idx_opportunities_unified_business_concept_id
ON opportunities_unified(business_concept_id);

CREATE INDEX idx_opportunities_unified_is_duplicate
ON opportunities_unified(is_duplicate);
```

### Database Functions

#### increment_concept_count()

```sql
CREATE OR REPLACE FUNCTION increment_concept_count(concept_id BIGINT)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE business_concepts
  SET submission_count = submission_count + 1,
      last_updated_at = NOW()
  WHERE id = concept_id;
END;
$$;
```

#### mark_opportunity_duplicate()

```sql
CREATE OR REPLACE FUNCTION mark_opportunity_duplicate(
    p_opportunity_id UUID,
    p_concept_id BIGINT,
    p_primary_opportunity_id UUID DEFAULT NULL
)
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE
  v_success BOOLEAN := FALSE;
BEGIN
  UPDATE opportunities_unified
  SET
    business_concept_id = p_concept_id,
    is_duplicate = TRUE,
    duplicate_of_id = COALESCE(p_primary_opportunity_id, (
      SELECT primary_opportunity_id
      FROM business_concepts
      WHERE id = p_concept_id
    )),
    updated_at = NOW()
  WHERE id = p_opportunity_id;

  v_success := FOUND;

  IF v_success THEN
    PERFORM increment_concept_count(p_concept_id);
  END IF;

  RETURN v_success;
END;
$$;
```

#### mark_opportunity_unique()

```sql
CREATE OR REPLACE FUNCTION mark_opportunity_unique(
    p_opportunity_id UUID,
    p_concept_id BIGINT
)
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE
  v_success BOOLEAN := FALSE;
BEGIN
  UPDATE opportunities_unified
  SET
    business_concept_id = p_concept_id,
    is_duplicate = FALSE,
    duplicate_of_id = NULL,
    updated_at = NOW()
  WHERE id = p_opportunity_id;

  v_success := FOUND;
  RETURN v_success;
END;
$$;
```

### Views

#### deduplication_stats View

```sql
CREATE VIEW deduplication_stats AS
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates,
    COUNT(CASE WHEN NOT is_duplicate THEN 1 END) as unique,
    COUNT(DISTINCT business_concept_id) as total_concepts,
    ROUND(
        COUNT(CASE WHEN is_duplicate THEN 1 END)::numeric /
        NULLIF(COUNT(*), 0) * 100, 2
    ) as deduplication_rate_percent,
    COUNT(CASE WHEN is_duplicate AND duplicate_of_id IS NOT NULL THEN 1 END) as linked_duplicates,
    COUNT(CASE WHEN is_duplicate AND duplicate_of_id IS NULL THEN 1 END) as unlinked_duplicates
FROM opportunities_unified
WHERE business_concept_id IS NOT NULL;
```

---

## Error Handling

### Error Types

#### ImportError
- **Cause**: Supabase package not installed
- **Solution**: Install with `pip install supabase`

#### ValueError
- **Cause**: Invalid opportunity ID
- **Solution**: Ensure opportunity_id is not empty

#### Database Errors
- **Cause**: Connection issues, constraint violations
- **Solution**: Check database connectivity and schema

#### Processing Errors
- **Cause**: Missing required fields, empty concepts
- **Solution**: Validate input data before processing

### Error Return Values

All error conditions return a structured result:

```python
{
    "success": False,
    "is_duplicate": False,
    "concept_id": None,
    "opportunity_id": str | None,
    "fingerprint": None,
    "normalized_concept": None,
    "message": "Description of error",
    "processing_time": float,
    "error": "Detailed error message"
}
```

### Common Error Messages

- `"Validation failed: empty opportunity"`
- `"Validation failed: missing opportunity ID"`
- `"Validation failed: missing app concept"`
- `"Processing failed: empty normalized concept"`
- `"Processing failed: could not mark as duplicate"`
- `"Processing failed: could not mark as unique"`

---

## Performance Characteristics

### Expected Metrics

| Metric | Expected Range | Notes |
|--------|----------------|-------|
| Processing Speed | 10-50 opportunities/second | Depends on database performance |
| Fingerprint Generation | < 1ms per opportunity | SHA256 is very fast |
| Database Lookup | 10-100ms per query | With proper indexing |
| Duplicate Detection Rate | 40-50% | Phase 1 string-based |

### Resource Usage

- **Memory**: Minimal (< 50MB for 10k opportunities)
- **Database**: 2-3 queries per opportunity processed
- **Network**: Supabase connection overhead
- **CPU**: SHA256 computation (very efficient)

### Optimization Recommendations

1. **Batch Processing**: Process 50-100 opportunities at a time
2. **Connection Reuse**: Maintain single Supabase client instance
3. **Database Indexing**: Ensure fingerprint indexes exist
4. **Error Recovery**: Implement retry logic for transient failures

---

## Integration Examples

### Basic Integration

```python
from core.deduplication import SimpleDeduplicator
import os

# Initialize
dedup = SimpleDeduplicator(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Process single opportunity
result = dedup.process_opportunity({
    'id': 'test-123',
    'app_concept': 'App idea: Food delivery service'
})

if result['success']:
    print(f"Success: {result['message']}")
    print(f"Duplicate: {result['is_duplicate']}")
```

### Batch Processing

```python
def process_opportunities_batch(opportunities):
    """Process multiple opportunities with error handling."""
    results = []
    errors = []

    for opportunity in opportunities:
        try:
            result = deduplicator.process_opportunity(opportunity)
            results.append(result)

            if not result['success']:
                errors.append({
                    'opportunity_id': opportunity.get('id'),
                    'error': result['error']
                })

        except Exception as e:
            errors.append({
                'opportunity_id': opportunity.get('id'),
                'error': str(e)
            })

    return {
        'processed': len(results),
        'successful': sum(1 for r in results if r['success']),
        'duplicates_found': sum(1 for r in results if r.get('is_duplicate')),
        'errors': errors
    }
```

### Error Recovery

```python
def safe_process_opportunity(opportunity, max_retries=3):
    """Process opportunity with retry logic."""
    for attempt in range(max_retries):
        try:
            result = deduplicator.process_opportunity(opportunity)

            if result['success']:
                return result
            elif attempt == max_retries - 1:
                return result

        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    'success': False,
                    'error': f"Failed after {max_retries} attempts: {e}"
                }

            time.sleep(1)  # Wait before retry

    return {'success': False, 'error': 'Unknown error'}
```

---

## Testing

### Unit Test Structure

```python
import pytest
from core.deduplication import SimpleDeduplicator

class TestSimpleDeduplicator:
    @pytest.fixture
    def deduplicator(self):
        return SimpleDeduplicator(
            supabase_url="test_url",
            supabase_key="test_key"
        )

    def test_normalize_concept(self, deduplicator):
        assert deduplicator.normalize_concept("App idea: Test") == "idea: test"

    def test_fingerprint_consistency(self, deduplicator):
        fp1 = deduplicator.generate_fingerprint("Test concept")
        fp2 = deduplicator.generate_fingerprint("Test concept")
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA256 length

    def test_process_opportunity(self, deduplicator):
        opportunity = {
            'id': 'test-123',
            'app_concept': 'App idea: Test concept'
        }
        result = deduplicator.process_opportunity(opportunity)
        assert result['success'] is True
        assert 'concept_id' in result
```

### Integration Test Structure

```python
def test_end_to_end_workflow():
    """Test complete deduplication workflow."""
    # Setup test data
    opportunities = [
        {'id': 'test-1', 'app_concept': 'App idea: Food delivery'},
        {'id': 'test-2', 'app_concept': 'app idea: food delivery'}  # Duplicate
    ]

    # Process both
    results = [dedup.process_opportunity(opp) for opp in opportunities]

    # Verify first is unique, second is duplicate
    assert results[0]['success'] is True
    assert results[0]['is_duplicate'] is False
    assert results[1]['success'] is True
    assert results[1]['is_duplicate'] is True
    assert results[0]['concept_id'] == results[1]['concept_id']
```

---

## Migration to Phase 2

### Preparation Steps

1. **Install ML Dependencies**
```bash
pip install sentence-transformers torch
```

2. **Enable pgvector**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. **Generate Embeddings**
```python
# Phase 2 enhancement (future)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(concept_text)
```

### Expected Phase 2 Changes

- **New Method**: `find_similar_concepts()` for semantic search
- **Enhanced Field**: `embedding` in business_concepts table
- **Improved Detection**: 60-80% duplicate detection rate
- **Vector Operations**: pgvector similarity search

---

## Support and Troubleshooting

### Common Issues

1. **Database Connection**
   - Verify Supabase credentials
   - Check Supabase service status
   - Test network connectivity

2. **Schema Mismatch**
   - Run database migrations
   - Verify table existence
   - Check column names

3. **Performance Issues**
   - Monitor database query times
   - Check index usage
   - Optimize batch sizes

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check deduplicator status
print(f"Supabase URL: {deduplicator.supabase.supabase_url}")
print(f"Connection successful: {deduplicator.supabase.auth.get_session()}")
```

### Getting Help

1. Check application logs for detailed error messages
2. Verify database schema matches documentation
3. Run integration tests to validate functionality
4. Review monitoring queries for system health

---

**Version History:**
- v1.0.0: Initial Phase 1 implementation with string-based deduplication
- v1.1.0: Planned - Phase 2 with ML-based semantic deduplication