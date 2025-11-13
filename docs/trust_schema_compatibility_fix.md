# Trust Schema Compatibility Fix

## Issue Analysis

The RedditHarbor trust pipeline was encountering database schema compatibility errors when trying to load trust validation data.

### The Error
```
invalid input syntax for type double precision: "LOW"
LINE 3: ...LL,NULL,E'low',22.58,E'✅ Active Community',72.74,E'LOW',E'M...
```

### Root Cause
1. **Field Mapping Issue**: The pipeline was trying to insert a `confidence_score` field with string values ('LOW', 'MEDIUM', 'HIGH')
2. **Schema Mismatch**: The `app_opportunities` table didn't have a `confidence_score` column
3. **Data Type Conflict**: String values were being inserted into columns expecting numeric types

## Solution Overview

### Multi-layered Approach
1. **Database Schema Fix**: Add `confidence_score` column with proper data type and automatic synchronization
2. **Pipeline Update**: Fix field mapping to use correct numeric scores
3. **Backward Compatibility**: Maintain both string and numeric representations
4. **Automatic Synchronization**: Use triggers to keep data consistent

## Implementation Details

### 1. Database Migration (`20251112000002_fix_trust_schema_compatibility.sql`)

**What it does:**
- Adds `confidence_score` column as DECIMAL(5,2) for backward compatibility
- Creates conversion function from string levels to numeric scores
- Implements trigger to automatically maintain both fields
- Updates existing records with proper numeric scores
- Adds performance indexes and constraints

**Key features:**
- **Bi-directional compatibility**: Supports both string (`ai_confidence_level`) and numeric (`confidence_score`)
- **Automatic conversion**: Trigger maintains consistency between the two fields
- **Performance optimized**: Composite indexes for efficient queries
- **Data validation**: Constraints ensure valid values

### 2. Trust Layer Enhancement (`core/trust_layer.py`)

**Changes made:**
- Added `get_confidence_score()` method to `TrustIndicators` class
- Returns numeric confidence score (0-100) from AI analysis
- Maintains existing string-based confidence levels

### 3. Pipeline Fix (`scripts/dlt/dlt_trust_pipeline.py`)

**Field mapping correction:**
- **Before**: `'confidence_score': post.get('ai_confidence_level', 'LOW')` (string → numeric error)
- **After**: `'confidence_score': trust_indicators.get_confidence_score()` (numeric → compatible)
- Maintains `ai_confidence_level` for string-based operations

### 4. Schema Compatibility Matrix

| Field | Original Issue | Fixed Value | Database Type | Source |
|-------|----------------|-------------|---------------|---------|
| `confidence_score` | String 'LOW' in numeric field | 25.0 (numeric) | DECIMAL(5,2) | `trust_indicators.get_confidence_score()` |
| `ai_confidence_level` | Working correctly | 'LOW' (string) | VARCHAR | `get_ai_confidence_level()` |
| `trust_level` | Working correctly | 'HIGH' (string) | VARCHAR | `trust_indicators.trust_level.value` |
| `trust_score` | Working correctly | 78.5 (numeric) | DECIMAL(5,2) | `trust_indicators.overall_trust_score` |

## Deployment Instructions

### Prerequisites
1. **Supabase Running**: `supabase start`
2. **Database Access**: Connection to postgres@127.0.0.1:54322/postgres
3. **Dependencies**: Project environment with required packages

### Step-by-Step Deployment

#### 1. Create Backup (Optional but Recommended)
```bash
# Create timestamped backup
pg_dump "postgresql://postgres:postgres@127.0.0.1:54322/postgres" > db_dumps/pre_fix_backup_$(date +%s).sql
```

#### 2. Apply Schema Migration
```bash
# Apply the compatibility fix
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f supabase/migrations/20251112000002_fix_trust_schema_compatibility.sql
```

#### 3. Verify Migration Success
```sql
-- Check columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'app_opportunities'
AND column_name IN ('confidence_score', 'ai_confidence_level');

-- Check data consistency
SELECT confidence_score, ai_confidence_level, COUNT(*)
FROM app_opportunities
GROUP BY confidence_score, ai_confidence_level
LIMIT 10;
```

#### 4. Test Trust Pipeline
```bash
# Run the updated trust pipeline
python scripts/dlt/dlt_trust_pipeline.py --limit 5 --test-mode
```

### Using the Deployment Script
For automated deployment with validation:
```bash
python scripts/deploy_trust_schema_fix.py
```

This script handles:
- Backup creation
- Migration application
- Database verification
- Compatibility testing
- Error handling

## Technical Architecture

### Data Flow Diagram
```
Trust Layer Validation
       ↓
TrustIndicators.get_confidence_score() → Numeric Score (0-100)
       ↓                                    ↓
ai_confidence_level (string)    confidence_score (numeric)
       ↓                                    ↓
String Processing                 Numeric Processing
       ↓                                    ↓
Database: VARCHAR               Database: DECIMAL(5,2)
       ↓                                    ↓
           ↓            ↓
           ↓            ↓
         Trigger Sync (Bi-directional)
           ↓            ↓
        DATABASE (app_opportunities)
```

### Conversion Logic
| String Level | Numeric Score | Use Case |
|--------------|---------------|----------|
| 'VERY_HIGH'  | 90.0          | High confidence AI analysis |
| 'HIGH'       | 75.0          | Good confidence |
| 'MEDIUM'     | 50.0          | Moderate confidence |
| 'LOW'        | 25.0          | Low confidence |
| 'UNKNOWN'    | 0.0           | Default/error case |

### Performance Considerations

**Indexes Added:**
- `idx_app_opportunities_ai_confidence_composite`: `(ai_confidence_level, confidence_score)`
- `idx_app_opportunities_trust_composite`: `(trust_level, trust_score, activity_score)`
- Individual indexes on each trust field for efficient filtering

**Query Optimizations:**
- Composite indexes reduce query planning time
- Proper data types minimize storage overhead
- Trigger-based maintenance eliminates manual synchronization

## Testing and Validation

### Unit Test Structure (`scripts/test_trust_schema_fix.py`)
1. **Trust Layer Data Types**: Verify numeric vs string field mapping
2. **Database Compatibility**: Test field mappings against expected schema
3. **DLT Load Simulation**: Simulate pipeline data loading
4. **Error Prevention**: Confirm no type conflicts

### Integration Testing
Run the full pipeline to test end-to-end:
```bash
python scripts/dlt/dlt_trust_pipeline.py --subreddits productivity --limit 10
```

### Expected Results
- ✅ No more "invalid input syntax for type double precision" errors
- ✅ Trust scores range 22.6-87.6 with proper levels (low, medium, high, very_high)
- ✅ AI confidence maintained as both string and numeric
- ✅ Automatic data synchronization between string and numeric fields

## Troubleshooting

### Common Issues

#### 1. Migration Fails
**Problem**: SQL error during migration
**Solution**: Check database connection and permissions
```bash
# Test connection
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -c "SELECT 1;"
```

#### 2. Pipeline Still Fails
**Problem**: Trust pipeline still shows schema errors
**Solution**: Verify field mapping in pipeline code
```bash
# Check field mapping
grep -n "confidence_score" scripts/dlt/dlt_trust_pipeline.py
```

#### 3. Data Inconsistency
**Problem**: confidence_score and ai_confidence_level don't match
**Solution**: Run trigger manually
```sql
-- Manually update all records
UPDATE app_opportunities
SET confidence_score = convert_ai_confidence_to_score(ai_confidence_level)
WHERE ai_confidence_level IS NOT NULL;
```

### Rollback Procedure
If issues arise, rollback can be done by:
```bash
# Remove trigger
DROP TRIGGER IF EXISTS trigger_update_confidence_score ON app_opportunities;

# Drop new column (data loss warning)
ALTER TABLE app_opportunities DROP COLUMN IF EXISTS confidence_score;
```

## Monitoring and Maintenance

### Health Checks
1. **Data Consistency**: Verify `confidence_score` matches `ai_confidence_level`
2. **Pipeline Success**: Monitor for schema errors in logs
3. **Performance**: Check query performance with new indexes

### Ongoing Maintenance
- **Backward Compatibility**: Maintain both fields during future updates
- **Trigger Performance**: Monitor trigger execution time
- **Index Maintenance**: Rebuild indexes if performance degrades

## Success Criteria

The fix is successful when:
1. ✅ Trust pipeline runs without schema errors
2. ✅ All 6-dimensional trust scores are properly stored
3. ✅ Both string and numeric confidence representations work
4. ✅ Existing functionality remains unaffected
5. ✅ Performance is maintained or improved
6. ✅ Data consistency is automatically maintained

## Future Enhancements

### Potential Improvements
1. **Enhanced Conversion Logic**: More granular numeric scoring
2. **Historical Tracking**: Audit trail for confidence score changes
3. **Performance Monitoring**: Automated performance alerting
4. **Data Validation**: Additional constraints for data quality

### Backward Compatibility Considerations
- Future changes should maintain both string and numeric fields
- Migration scripts should handle both old and new data formats
- API changes should support both representations during transition periods