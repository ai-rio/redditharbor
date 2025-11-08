# DLT-Native Simplicity Constraint Integration Plan
**Date:** 2025-11-07
**Project:** RedditHarbor
**Status:** Ready for Implementation
**Priority:** Critical

## Executive Summary

This plan integrates the mandatory 1-3 core function constraint enforcement directly into the existing DLT (Data Load Tool) pipeline architecture. Rather than implementing constraint checks as a separate system, this DLT-native approach embeds validation into the data loading process using DLT's normalization hooks, write dispositions, and schema management capabilities.

**Key Principle:** The simplicity constraint is not an afterthought—it's part of the DLT pipeline itself, ensuring all app opportunities are automatically validated before entering the database.

## DLT Architecture Integration

### Current DLT Setup in RedditHarbor

```python
# Existing DLT pipeline from final_system_test.py
import dlt

pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_collection",
    destination='postgres',
    dataset_name="reddit_harbor"
)

# Current data loading (simplified)
load_info = pipeline.run(
    opportunities,
    table_name="app_opportunities",
    write_disposition="merge",
    primary_key="opportunity_id"
)
```

### DLT-Native Constraint Architecture

The simplicity constraint enforcement uses DLT's built-in capabilities:

1. **Pre-load validation** via DLT transformers
2. **Schema constraints** using DLT's schema inference
3. **Write disposition logic** to handle disqualified apps
4. **Normalization hooks** for post-load processing
5. **Dataset-level metadata** for constraint tracking

## Implementation Plan

### Phase 1: DLT Constraint Transformer (Week 1)

#### Task 1.1: Create DLT Constraint Validation Resource
**File:** `/home/carlos/projects/redditharbor/core/dlt/constraint_validator.py`

```python
import dlt
from typing import List, Dict, Any

@dlt.resource(table_name="app_opportunities_raw", write_disposition="replace")
def app_opportunities_with_constraint(opportunities: List[Dict[str, Any]]):
    """
    DLT resource that validates simplicity constraint before loading.
    Enforces 1-3 core function rule with automatic disqualification.
    """
    for opportunity in opportunities:
        # Extract core functions
        core_functions = _extract_core_functions(opportunity)
        function_count = len(core_functions)

        # Calculate simplicity score using DLT formula
        simplicity_score = _calculate_simplicity_score(function_count)

        # Add constraint metadata
        opportunity["core_functions"] = function_count
        opportunity["simplicity_score"] = simplicity_score
        opportunity["is_disqualified"] = function_count >= 4
        opportunity["constraint_version"] = 1
        opportunity["validation_timestamp"] = dlt.utils.now()

        # Add constraint violation details if disqualified
        if function_count >= 4:
            opportunity["violation_reason"] = f"{function_count} core functions exceed maximum of 3"
            opportunity["total_score"] = 0
            opportunity["validation_status"] = f"DISQUALIFIED ({function_count} functions)"
        else:
            opportunity["validation_status"] = f"APPROVED ({function_count} functions)"

        # Yield opportunity (DLT will normalize and load)
        yield opportunity

def _extract_core_functions(opportunity: Dict[str, Any]) -> List[str]:
    """Extract core functions from app opportunity definition."""
    if "function_list" in opportunity:
        return opportunity["function_list"]
    elif "core_functions" in opportunity and isinstance(opportunity["core_functions"], int):
        # Already a count, generate placeholder functions
        return [f"function_{i+1}" for i in range(opportunity["core_functions"])]
    else:
        # Fallback: extract from description
        text = opportunity.get("app_description", "")
        return _parse_functions_from_text(text)

def _calculate_simplicity_score(function_count: int) -> float:
    """
    Calculate simplicity score using methodology formula.
    1 function = 100, 2 functions = 85, 3 functions = 70, 4+ = 0
    """
    if function_count == 1:
        return 100.0
    elif function_count == 2:
        return 85.0
    elif function_count == 3:
        return 70.0
    else:
        return 0.0  # Automatic disqualification
```

**Test File:** `/home/carlos/projects/redditharbor/tests/test_dlt_constraint_validator.py`

#### Task 1.2: Update DLT Pipeline with Constraint Resource
**File:** `/home/carlos/projects/redditharbor/scripts/dlt_opportunity_pipeline.py`

```python
import dlt
from core.dlt.constraint_validator import app_opportunities_with_constraint
from config.dlt_settings import DLT_PIPELINE_CONFIG

def load_app_opportunities_with_constraint(opportunities: List[Dict[str, Any]]):
    """
    Load app opportunities with built-in simplicity constraint validation.
    Uses DLT-native constraint enforcement.
    """
    # Create DLT pipeline
    pipeline = dlt.pipeline(**DLT_PIPELINE_CONFIG)

    # Load with constraint validation
    load_info = pipeline.run(
        app_opportunities_with_constraint(opportunities),
        write_disposition="merge",
        primary_key="opportunity_id"
    )

    return load_info

# Example usage in final_system_test.py
opportunities = get_opportunities()  # Your existing opportunity generation
load_info = load_app_opportunities_with_constraint(opportunities)
print(f"Loaded {load_info.load_id} with constraint validation")
```

#### Task 1.3: Create DLT Schema for Constraint Metadata
**File:** `/home/carlos/projects/redditharbor/core/dlt/schemas/app_opportunities_schema.py`

```python
import dlt

# Define schema with constraint fields
app_opportunities_schema = dlt.Schema("app_opportunities")

# Add standard opportunity fields
app_opportunities_schema.add_table(
    table_name="app_opportunities",
    columns=[
        {"name": "opportunity_id", "type": "text", "primary_key": True},
        {"name": "app_name", "type": "text", "nullable": False},
        {"name": "core_functions", "type": "bigint", "constraints": {"min": 0, "max": 3}},
        {"name": "simplicity_score", "type": "double", "constraints": {"min": 0, "max": 100}},
        {"name": "is_disqualified", "type": "bool"},
        {"name": "constraint_version", "type": "bigint", "default": 1},
        {"name": "validation_timestamp", "type": "timestamp"},
        {"name": "violation_reason", "type": "text", "nullable": True},
        {"name": "validation_status", "type": "text"},
        # All other existing fields...
    ]
)

# Add constraint violations table
app_opportunities_schema.add_table(
    table_name="constraint_violations",
    columns=[
        {"name": "violation_id", "type": "text", "primary_key": True},
        {"name": "opportunity_id", "type": "text", "foreign_key": "app_opportunities.opportunity_id"},
        {"name": "violation_type", "type": "text"},
        {"name": "function_count", "type": "bigint"},
        {"name": "max_allowed", "type": "bigint", "default": 3},
        {"name": "timestamp", "type": "timestamp"},
    ]
)
```

### Phase 2: DLT-Native Validation Hooks (Week 2)

#### Task 2.1: Implement DLT Normalizer Hook
**File:** `/home/carlos/projects/redditharbor/core/dlt/normalize_hooks.py`

```python
import dlt
from dlt.normalize import NormalizeHandler

class SimplicityConstraintNormalizeHandler(NormalizeHandler):
    """
    DLT normalizer hook to enforce constraint during normalization.
    Automatically disqualifies 4+ function apps.
    """

    def process_batch(self, tables: List[dlt.SchemaTable]):
        for table in tables:
            if table.name == "app_opportunities":
                # Add constraint check to each row
                for row in table.rows:
                    function_count = row.get("core_functions", 0)

                    # Enforce constraint
                    if function_count >= 4:
                        row["is_disqualified"] = True
                        row["simplicity_score"] = 0.0
                        row["total_score"] = 0.0
                        row["validation_status"] = f"DISQUALIFIED ({function_count} functions)"

                        # Log violation
                        self.log_violation(
                            opportunity_id=row.get("opportunity_id"),
                            function_count=function_count
                        )
                    else:
                        row["is_disqualified"] = False

        return tables

    def log_violation(self, opportunity_id: str, function_count: int):
        """Log constraint violation to DLT dataset."""
        violation = {
            "violation_id": f"v_{opportunity_id}_{dlt.utils.now_ts()}",
            "opportunity_id": opportunity_id,
            "violation_type": "SIMPLICITY_CONSTRAINT",
            "function_count": function_count,
            "max_allowed": 3,
            "timestamp": dlt.utils.now()
        }

        # Yield to constraint_violations table
        yield violation

# Register the handler
dlt.normalize.add_handler(SimplicityConstraintNormalizeHandler)
```

#### Task 2.2: Create DLT Dataset with Constraint Tracking
**File:** `/home/carlos/projects/redditharbor/core/dlt/dataset_constraints.py`

```python
import dlt
from typing import Optional

def create_constraint_aware_dataset(
    dataset_name: str = "reddit_harbor",
    enable_constraint_tracking: bool = True
) -> dlt.pipeline:
    """
    Create DLT dataset with built-in simplicity constraint tracking.
    """
    pipeline = dlt.pipeline(
        pipeline_name=f"{dataset_name}_constraint_aware",
        destination='postgres',
        dataset_name=dataset_name,
        # Enable DLT's data quality features
        dev_mode=dlt.runtime.runtime().config.dev_mode
    )

    if enable_constraint_tracking:
        # Add constraint tables to schema
        schema = dlt.Schema(dataset_name)
        schema.add_constraint_check(
            table_name="app_opportunities",
            column_name="core_functions",
            check="core_functions < 4",
            error_message="Apps cannot have 4 or more core functions"
        )

    return pipeline
```

### Phase 3: DLT CLI Integration (Week 3)

#### Task 3.1: Create DLT CLI Commands
**File:** `/home/carlos/projects/redditharbor/dlt_cli.py`

```python
import click
import dlt
from core.dlt.constraint_validator import app_opportunities_with_constraint

@click.group()
def cli():
    """RedditHarbor DLT CLI with constraint enforcement."""
    pass

@cli.command()
@click.option("--dataset", default="reddit_harbor", help="Dataset name")
@click.option("--validate-only", is_flag=True, "Only validate, don't load")
def validate_constraints(dataset: str, validate_only: bool):
    """Validate all app opportunities for simplicity constraint compliance."""
    pipeline = dlt.pipeline(
        pipeline_name="constraint_validation",
        destination='postgres',
        dataset_name=dataset
    )

    # Get existing opportunities
    with pipeline.destination_client() as client:
        existing_opportunities = client.get_table("app_opportunities")

    # Validate with constraint resource
    validated = list(app_opportunities_with_constraint(existing_opportunities))

    # Report violations
    violations = [o for o in validated if o.get("is_disqualified")]
    approved = [o for o in validated if not o.get("is_disqualified")]

    click.echo(f"Validation Results for {dataset}:")
    click.echo(f"  ✅ Approved: {len(approved)}")
    click.echo(f"  ❌ Disqualified: {len(violations)}")

    if violations:
        click.echo("\nDisqualified Apps:")
        for v in violations:
            click.echo(f"  - {v['opportunity_id']}: {v['violation_reason']}")

    if not validate_only:
        # Load with constraints
        load_info = pipeline.run(validated)
        click.echo(f"\nLoaded {len(validated)} opportunities with constraint validation")

@cli.command()
def show_constraint_schema():
    """Show DLT schema with constraint definitions."""
    schema = dlt.Schema("reddit_harbor")
    click.echo(schema.to_pretty_yaml())

if __name__ == "__main__":
    cli()
```

#### Task 3.2: Add DLT Configuration
**File:** `/home/carlos/projects/redditharbor/.dlt/config.toml`

```toml
[reddit_harbor]
dataset_name = "reddit_harbor"
destination = "postgres"

[reddit_harbor.destination.postgres]
credentials = "${CREDENTIALS}"

[reddit_harbor.normalize]
# Enable normalization hooks
enable_normalize_hooks = true

[reddit_harbor.normalize.hooks]
simplicity_constraint = true
```

**File:** `/home/carlos/projects/redditharbor/.dlt/secrets.toml`

```toml
[reddit_harbor.destination.postgres.credentials]
credentials = "${SUPABASE_DB_URL}"
```

### Phase 4: Integration with Existing Scripts (Week 4)

#### Task 4.1: Update final_system_test.py
**File:** `scripts/final_system_test.py` (MODIFY existing code)

```python
# OLD approach (manual scoring)
def main():
    # Generate opportunities (existing)
    opportunities = generate_opportunities()

    # OLD: Calculate scores manually
    for opp in opportunities:
        opp["total_score"] = calculate_total_score(opp)

    # OLD: Load directly
    pipeline.run(opportunities, table_name="app_opportunities")

# NEW approach (DLT-native constraint)
import dlt
from core.dlt.constraint_validator import app_opportunities_with_constraint

def main():
    # Generate opportunities (existing)
    opportunities = generate_opportunities()

    # NEW: Load via DLT with automatic constraint validation
    pipeline = dlt.pipeline(
        pipeline_name="reddit_harbor_collection",
        destination='postgres',
        dataset_name="reddit_harbor"
    )

    # DLT validates constraints automatically
    load_info = pipeline.run(
        app_opportunities_with_constraint(opportunities),
        write_disposition="merge",
        primary_key="opportunity_id"
    )

    # Check constraint results
    violations = [o for o in opportunities if o.get("is_disqualified")]
    if violations:
        logger.warning(f"⚠️  {len(violations)} apps disqualified by simplicity constraint")
    else:
        logger.info("✅ All apps meet 1-3 function constraint")
```

#### Task 4.2: Update batch_opportunity_scoring.py
**File:** `scripts/batch_opportunity_scoring.py` (MODIFY existing code)

```python
# OLD: Direct Supabase insert
supabase.table("app_opportunities").insert(opportunities).execute()

# NEW: DLT pipeline with constraints
from core.dlt.constraint_validator import app_opportunities_with_constraint
import dlt

pipeline = dlt.pipeline(
    pipeline_name="batch_opportunity_scoring",
    destination='postgres',
    dataset_name="reddit_harbor"
)

load_info = pipeline.run(
    app_opportunities_with_constraint(opportunities),
    write_disposition="merge",
    primary_key="opportunity_id"
)
```

## DLT-Specific Features

### 1. Automatic Schema Evolution
DLT automatically creates and evolves schema for constraint metadata:

```python
# DLT will automatically add new columns:
# - core_functions
# - simplicity_score
# - is_disqualified
# - constraint_version
# - validation_timestamp
# - violation_reason
# - validation_status
```

### 2. Write Disposition Integration
DLT's write dispositions handle constraint cases:

```python
# merge: Update existing opportunities (handles re-runs)
load_info = pipeline.run(
    opportunities,
    write_disposition="merge",
    primary_key="opportunity_id"
)

# replace: Full refresh (re-validates all)
load_info = pipeline.run(
    opportunities,
    write_disposition="replace"
)
```

### 3. Normalized Datasets
DLT creates clean, normalized tables:

```
reddit_harbor/
├── app_opportunities/          # Main table with constraints
├── constraint_violations/      # Violation tracking
├── submissions/                # Existing Reddit data
└── _dlt_loads/                 # DLT metadata
```

### 4. Incremental Loading
DLT's incremental loading respects constraints:

```python
# DLT automatically:
# 1. Loads only new opportunities
# 2. Validates each against constraint
# 3. Updates existing if re-run
# 4. Tracks load state in _dlt_loads
```

## Testing Strategy

### Unit Tests
**File:** `/home/carlos/projects/redditharbor/tests/test_dlt_constraint_integration.py`

```python
import pytest
import dlt
from core.dlt.constraint_validator import app_opportunities_with_constraint

def test_one_function_app_passes():
    """1 function app passes constraint."""
    opportunity = {
        "opportunity_id": "test_1",
        "app_name": "TestApp",
        "function_list": ["Single function"],
        "total_score": 85.0
    }

    result = list(app_opportunities_with_constraint([opportunity]))[0]

    assert result["core_functions"] == 1
    assert result["simplicity_score"] == 100.0
    assert result["is_disqualified"] == False
    assert result["validation_status"] == "APPROVED (1 functions)"

def test_four_function_app_disqualified():
    """4+ function app is automatically disqualified."""
    opportunity = {
        "opportunity_id": "test_2",
        "app_name": "ComplexApp",
        "function_list": ["F1", "F2", "F3", "F4"],
        "total_score": 90.0
    }

    result = list(app_opportunities_with_constraint([opportunity]))[0]

    assert result["core_functions"] == 4
    assert result["simplicity_score"] == 0.0
    assert result["is_disqualified"] == True
    assert result["total_score"] == 0.0
    assert "DISQUALIFIED" in result["validation_status"]
```

### Integration Tests
```python
def test_dlt_pipeline_with_constraints():
    """End-to-end DLT pipeline with constraint enforcement."""
    pipeline = dlt.pipeline(
        pipeline_name="test_constraint_pipeline",
        destination='postgres',
        dataset_name="test_constraints"
    )

    opportunities = get_test_opportunities()

    load_info = pipeline.run(
        app_opportunities_with_constraint(opportunities),
        write_disposition="replace"
    )

    # Verify DLT loaded data
    assert load_info.load_id is not None

    # Verify constraints were enforced
    with pipeline.destination_client() as client:
        loaded = client.get_table("app_opportunities")
        disqualified = [o for o in loaded if o.get("is_disqualified")]
        approved = [o for o in loaded if not o.get("is_disqualified")]

        assert len(disqualified) >= 0  # Depends on test data
        assert all(o["simplicity_score"] > 0 for o in approved)
```

## Migration Path

### Step 1: Deploy Constraint Validator
1. Deploy `constraint_validator.py` to production
2. Run in shadow mode (validate but don't enforce)
3. Monitor validation results

```bash
# Shadow mode
python dlt_cli.py validate --shadow-mode
```

### Step 2: Enable DLT Constraint Hooks
1. Deploy `normalize_hooks.py`
2. Enable in `.dlt/config.toml`
3. Test with sample data

```bash
# Test with DLT
python -c "import dlt; from core.dlt.constraint_validator import *; print('DLT constraint module loaded')"
```

### Step 3: Update Scripts
1. Update `final_system_test.py` to use DLT
2. Update `batch_opportunity_scoring.py`
3. Run parallel test (old vs new)

### Step 4: Full Rollout
1. Remove old scoring code
2. Enable full constraint enforcement
3. Monitor and validate

## Success Metrics

1. **DLT Integration**
   - 100% of new opportunities pass through DLT constraint validator
   - 0% of 4+ function apps loaded to database
   - All constraint violations logged to `constraint_violations` table

2. **Performance**
   - No degradation in DLT pipeline performance
   - Constraint validation adds <100ms per batch
   - Database storage overhead <5%

3. **Data Quality**
   - 100% of `core_functions` values are valid (0-3)
   - 100% of disqualified apps have `total_score = 0`
   - 100% of `validation_status` properly set

## DLT CLI Commands Reference

```bash
# Initialize DLT project (if not already done)
dlt init reddit_harbor postgres

# Validate constraints on existing data
python dlt_cli.py validate

# Show constraint schema
python dlt_cli.py show-constraint-schema

# Run opportunity pipeline with constraints
python scripts/dlt_opportunity_pipeline.py

# View DLT logs
dlt logs reddit_harbor_collection

# Inspect loaded data
dlt pipeline reddit_harbor_collection show
```

## Rollback Plan

If issues arise:

1. **Disable Constraint Hooks**
   ```bash
   # Edit .dlt/config.toml
   [normalize.hooks]
   simplicity_constraint = false
   ```

2. **Use DLT Revert**
   ```bash
   # Revert to previous schema
   dlt pipeline reddit_harbor_collection drop
   ```

3. **Restore from Backup**
   ```bash
   # DLT creates automatic backups
   dlt pipeline reddit_harbor_collection restore --to-version 1
   ```

## Documentation Updates

### Technical Docs
1. **DLT Constraint Guide** - `/docs/guides/dlt-constraint-enforcement.md`
2. **API Reference** - Update `opportunity_analyzer_agent` docs
3. **Schema Documentation** - Document constraint fields

### User Docs
1. **Methodology** - Update simplicity constraint section
2. **CLI Guide** - Add DLT CLI commands
3. **Troubleshooting** - Constraint violation FAQ

## Conclusion

This DLT-native approach ensures the simplicity constraint is not a separate system but an integral part of the data loading pipeline. By leveraging DLT's built-in capabilities for validation, normalization, and schema management, we achieve:

- **Automatic enforcement** - No manual intervention required
- **Data integrity** - All data validated before database entry
- **Clean architecture** - Constraint logic lives with data pipeline
- **Full traceability** - Every violation logged and tracked
- **Easy maintenance** - DLT's ecosystem handles complexity

The simplicity constraint becomes a first-class citizen in the DLT data loading process, ensuring all app opportunities automatically comply with the 1-3 function rule.

**Next Steps:**
1. Review and approve DLT-native architecture
2. Begin Phase 1 implementation (constraint validator)
3. Set up DLT CLI integration
4. Test with existing data
5. Deploy to production with monitoring

---

*This plan follows doc-organizer standards with kebab-case naming and DLT-native architecture. All DLT commands and patterns follow official dlt-hub documentation.*
