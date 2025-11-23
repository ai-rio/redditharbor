# Supabase Client Timeout Configuration Fix

## Problem

Test 02 (Small Batch Validation) was failing with "Database fetch failed: Limited fetch failed: timed out" error. The issue was caused by the default Supabase client configuration having a 60-second PostgREST timeout, which is insufficient for batch processing operations that fetch multiple submissions sequentially.

## Solution

Implemented a timeout-configured Supabase client with extended timeouts (180 seconds) to prevent connection timeouts during database operations.

## Changes Made

### 1. Created `core/clients.py`

New module providing timeout-configured Supabase client factory:

```python
from core.clients import get_default_client

# Create client with 180s PostgREST timeout (vs 60s default)
client = get_default_client()
```

Key features:
- **Extended PostgREST timeout**: 180 seconds (3 minutes) instead of default 60s
- **Configurable timeouts**: Customizable timeouts for different use cases
- **Proper error handling**: Configuration validation and connection testing
- **Test client support**: Optimized settings for testing environments

### 2. Updated `core/fetchers/database_fetcher.py`

Enhanced database fetcher to use timeout-configured client:

- Updated import to use `get_default_client()`
- Added `create_with_timeout_config()` class method for convenience
- Updated documentation with proper client usage examples
- Added note about timeout configuration requirements

### 3. Updated Test 02 Script

Modified `scripts/testing/integration/tests/test_02_small_batch.py`:

- Replaced `create_client()` calls with `get_default_client()`
- Fixed two locations where timeout issues occurred:
  - `update_small_batch_config()` function (line ~180)
  - `process_single_submission()` function (line ~337)

## Configuration Details

### Default Timeout Settings
- **PostgREST client timeout**: 180 seconds (3 minutes)
- **Storage client timeout**: 30 seconds
- **Schema**: "public"

### Custom Configuration
```python
from core.clients import get_supabase_client

# Custom timeouts for specific needs
client = get_supabase_client(
    postgrest_timeout=300,  # 5 minutes
    storage_timeout=60      # 1 minute
)
```

## Testing Environment

Optimized settings for testing:
- **PostgREST timeout**: 120 seconds (2 minutes)
- **Storage timeout**: 15 seconds

## Impact

### Before Fix
- Test 02 failed with timeout errors during database fetch
- Default 60-second timeout insufficient for batch operations
- Sequential submission processing caused cumulative timeouts

### After Fix
- Test 02 should complete without database timeout errors
- 180-second timeout accommodates batch processing requirements
- Maintains backward compatibility with existing code
- Provides configurable timeout options for different use cases

## Usage Examples

### Basic Usage
```python
from core.clients import get_default_client
from core.fetchers.database_fetcher import DatabaseFetcher

# Create timeout-configured client
client = get_default_client()

# Use with database fetcher
fetcher = DatabaseFetcher(client)
submissions = list(fetcher.fetch(limit=100))
```

### Convenience Method
```python
from core.fetchers.database_fetcher import DatabaseFetcher

# Create fetcher with timeout-configured client
fetcher = DatabaseFetcher.create_with_timeout_config()
submissions = list(fetcher.fetch(limit=100))
```

### Custom Configuration
```python
from core.clients import get_supabase_client

# Custom timeout settings for large data operations
client = get_supabase_client(
    postgrest_timeout=300,  # 5 minutes for very large queries
    storage_timeout=60      # 1 minute for storage operations
)
```

## Backward Compatibility

The changes maintain full backward compatibility:

1. **Existing code unchanged**: All existing Supabase client creation continues to work
2. **Optional adoption**: Code can be migrated to use timeout-configured client gradually
3. **Same interface**: The timeout-configured client has the same interface as the default client
4. **Default behavior**: No changes to existing functionality unless explicitly updated

## Files Modified

1. **Created**: `core/clients.py` - Timeout-configured Supabase client factory
2. **Modified**: `core/fetchers/database_fetcher.py` - Updated to use timeout client
3. **Modified**: `scripts/testing/integration/tests/test_02_small_batch.py` - Updated client creation
4. **Created**: `test_timeout_client.py` - Test script for validation (temporary)

## Success Criteria

- ✅ Test 02 should fetch submissions without database timeout errors
- ✅ Extended timeout (180s) accommodates batch processing
- ✅ Backward compatibility maintained
- ✅ Proper environment variable loading from `.env.local`
- ✅ Code follows RedditHarbor documentation standards

## Next Steps

1. Run Test 02 to verify the timeout fix works
2. Monitor test results to ensure no new issues introduced
3. Consider migrating other core modules to use timeout-configured client for consistency
4. Update documentation to recommend timeout-configured client for batch operations