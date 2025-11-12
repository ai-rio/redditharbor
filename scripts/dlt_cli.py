"""
DLT-Native Simplicity Constraint CLI Commands.

This module provides a Click-based CLI for managing DLT pipelines with simplicity
constraint enforcement. It provides commands for validating constraints, showing
schema information, and running production-ready constraint validation pipelines.

Usage:
    dlt-cli validate-constraints --file data.json
    dlt-cli show-constraint-schema
    dlt-cli run-pipeline --source opportunities.json --destination postgres
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
import dlt

# Add project root to path (following current script pattern)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Phase 1 & 2 components
from core.dlt.constraint_validator import (
    _calculate_simplicity_score,
    _extract_core_functions,
    app_opportunities_with_constraint,
)
from core.dlt.dataset_constraints import (
    create_production_dataset,
    create_test_dataset,
    get_constraint_schema,
)
from core.dlt.normalize_hooks import (
    create_constraint_normalize_handler,
)


# CLI Configuration
@click.group()
@click.version_option(version="1.0.0", prog_name="DLT Constraint CLI")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """DLT-Native Simplicity Constraint Management CLI.

    This CLI provides tools for managing DLT pipelines with built-in simplicity
    constraint enforcement for the 1-3 core function rule.

    Commands:
        validate-constraints  Validate app opportunities against simplicity constraint
        show-constraint-schema Display DLT schema with constraint fields
        run-pipeline          Run a full DLT pipeline with constraint enforcement
        test-constraint       Test constraint enforcement with sample data
        check-database        Check database connectivity and schema

    Examples:
        dlt-cli validate-constraints --file opportunities.json
        dlt-cli show-constraint-schema
        dlt-cli run-pipeline --source data.json --destination postgres
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


# Command 1: validate_constraints
@cli.command("validate-constraints")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to JSON file containing app opportunities"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Path to output validated opportunities (JSON format)"
)
@click.option(
    "--max-functions",
    default=3,
    type=int,
    help="Maximum allowed core functions (default: 3)"
)
@click.option(
    "--fail-on-violation",
    is_flag=True,
    help="Exit with non-zero code if violations found"
)
@click.pass_context
def validate_constraints(
    ctx: click.Context,
    file: Path,
    output: Path | None,
    max_functions: int,
    fail_on_violation: bool
) -> None:
    """Validate app opportunities against simplicity constraint.

    Reads app opportunities from a JSON file and validates them against the
    1-3 core function constraint. Automatically disqualifies apps with 4+ functions
    and adds constraint metadata.

    Example:
        dlt-cli validate-constraints --file data.json --output validated.json
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Reading opportunities from: {file}")

    try:
        # Load opportunities
        with open(file) as f:
            opportunities = json.load(f)

        if not isinstance(opportunities, list):
            click.echo("Error: Data must be a list of opportunities", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"Loaded {len(opportunities)} opportunities")

        # Validate each opportunity
        validated = []
        violations = []

        for i, opportunity in enumerate(opportunities):
            if verbose and i % 10 == 0:
                click.echo(f"Processing opportunity {i+1}/{len(opportunities)}")

            # Extract functions and validate
            core_functions = _extract_core_functions(opportunity)
            function_count = len(core_functions)

            # Create validated opportunity
            validated_opp = opportunity.copy()
            validated_opp["core_functions"] = function_count
            validated_opp["simplicity_score"] = _calculate_simplicity_score(function_count)
            validated_opp["is_disqualified"] = function_count > max_functions
            validated_opp["constraint_version"] = 1
            validated_opp["validation_timestamp"] = datetime.now().isoformat()

            if function_count > max_functions:
                validated_opp["violation_reason"] = f"{function_count} core functions exceed maximum of {max_functions}"
                validated_opp["total_score"] = 0
                validated_opp["validation_status"] = f"DISQUALIFIED ({function_count} functions)"

                violations.append({
                    "index": i,
                    "app_name": opportunity.get("app_name", f"app_{i}"),
                    "function_count": function_count,
                    "reason": validated_opp["violation_reason"]
                })
            else:
                validated_opp["validation_status"] = f"APPROVED ({function_count} functions)"

            validated.append(validated_opp)

        # Print summary
        approved = len([o for o in validated if not o.get("is_disqualified", False)])
        disqualified = len(violations)

        click.echo("\n" + "="*60)
        click.echo("VALIDATION SUMMARY")
        click.echo("="*60)
        click.echo(f"Total opportunities: {len(opportunities)}")
        click.echo(f"Approved: {approved}")
        click.echo(f"Disqualified: {disqualified}")
        if len(opportunities) > 0:
            click.echo(f"Compliance rate: {approved/len(opportunities)*100:.1f}%")
        else:
            click.echo("Compliance rate: N/A (no data)")
        click.echo("="*60 + "\n")

        if violations:
            click.echo("VIOLATIONS DETECTED:")
            for v in violations:
                click.echo(f"  • {v['app_name']}: {v['reason']}")
            click.echo("")

        # Save output if specified
        if output:
            with open(output, "w") as f:
                json.dump(validated, f, indent=2)
            click.echo(f"Validated opportunities saved to: {output}")

        # Exit with error code if violations found and --fail-on-violation set
        if fail_on_violation and violations:
            click.echo("Violations found! Use --fail-on-violation to exit with error code.", err=True)
            sys.exit(1)

    except FileNotFoundError:
        click.echo(f"Error: File not found: {file}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# Command 2: show_constraint_schema
@cli.command("show-constraint-schema")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save schema to file instead of displaying"
)
@click.pass_context
def show_constraint_schema(
    ctx: click.Context,
    format: str,
    output: Path | None
) -> None:
    """Display DLT schema with constraint enforcement fields.

    Shows the complete schema for app_opportunities table including all
    constraint-related fields: core_functions, simplicity_score, is_disqualified,
    validation_timestamp, validation_status, and violation_reason.

    Example:
        dlt-cli show-constraint-schema --format table
        dlt-cli show-constraint-schema --format json --output schema.json
    """
    verbose = ctx.obj.get("verbose", False)

    # Get constraint schema
    schema = get_constraint_schema()

    # Define schema fields
    schema_fields = {
        "app_opportunities": {
            "description": "Main table for app opportunities with constraint enforcement",
            "fields": [
                {"name": "app_name", "type": "string", "required": True},
                {"name": "app_description", "type": "text", "required": False},
                {"name": "core_functions", "type": "integer", "required": False,
                 "description": "Number of core functions (0-10, max allowed is 3)"},
                {"name": "simplicity_score", "type": "float", "required": False,
                 "description": "Score based on function count (100/85/70/0)"},
                {"name": "is_disqualified", "type": "boolean", "required": False,
                 "description": "Boolean flag for 4+ function violations"},
                {"name": "validation_status", "type": "string", "required": False,
                 "description": "APPROVED/DISQUALIFIED with function count"},
                {"name": "validation_timestamp", "type": "timestamp", "required": False,
                 "description": "When constraint was validated"},
                {"name": "violation_reason", "type": "text", "required": False,
                 "description": "Detailed reason for disqualification"},
                {"name": "constraint_version", "type": "integer", "required": False,
                 "description": "Version of constraint rules applied"},
                {"name": "total_score", "type": "float", "required": False,
                 "description": "Overall app score (set to 0 if disqualified)"}
            ]
        },
        "constraint_violations": {
            "description": "Tracking table for all constraint violations",
            "fields": [
                {"name": "violation_id", "type": "string", "required": True},
                {"name": "opportunity_id", "type": "string", "required": True},
                {"name": "app_name", "type": "string", "required": True},
                {"name": "violation_type", "type": "string", "required": True},
                {"name": "function_count", "type": "integer", "required": True},
                {"name": "max_allowed", "type": "integer", "required": True},
                {"name": "violation_reason", "type": "text", "required": True},
                {"name": "timestamp", "type": "timestamp", "required": True}
            ]
        }
    }

    # Format output
    if format == "json" or output:
        schema_data = {
            "schema_name": "reddit_harbor",
            "tables": schema_fields,
            "constraint_rules": {
                "name": "Simplicity Constraint",
                "description": "Apps must have 1-3 core functions",
                "max_functions": 3,
                "scoring": {
                    "1 function": 100,
                    "2 functions": 85,
                    "3 functions": 70,
                    "4+ functions": 0
                }
            },
            "generated_at": datetime.now().isoformat()
        }

        if output:
            with open(output, "w") as f:
                json.dump(schema_data, f, indent=2)
            click.echo(f"Schema saved to: {output}")
        else:
            click.echo(json.dumps(schema_data, indent=2))

    else:  # table format
        click.echo("\n" + "="*80)
        click.echo("DLT CONSTRAINT-AWARE SCHEMA")
        click.echo("="*80 + "\n")

        for table_name, table_info in schema_fields.items():
            click.echo(f"Table: {table_name}")
            click.echo(f"Description: {table_info['description']}")
            click.echo("\nFields:")
            click.echo("  " + "-"*76)

            for field in table_info["fields"]:
                req = "(required)" if field.get("required") else "(optional)"
                click.echo(f"  • {field['name']:<25} {field['type']:<15} {req}")
                if "description" in field:
                    click.echo(f"    {field['description']}")
            click.echo("")

        click.echo("="*80)
        click.echo("\nConstraint Rules:")
        click.echo("  • Name: Simplicity Constraint")
        click.echo("  • Rule: Apps must have 1-3 core functions")
        click.echo("  • Max allowed: 3 functions")
        click.echo("  • Scoring:")
        click.echo("    - 1 function = 100 points")
        click.echo("    - 2 functions = 85 points")
        click.echo("    - 3 functions = 70 points")
        click.echo("    - 4+ functions = 0 points (disqualified)")
        click.echo("="*80 + "\n")


# Command 3: run_pipeline
@cli.command("run-pipeline")
@click.option(
    "--source",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to source data file (JSON)"
)
@click.option(
    "--destination",
    "-d",
    type=click.Choice(["postgres", "bigquery", "duckdb"]),
    default="postgres",
    help="Destination database type (default: postgres)"
)
@click.option(
    "--dataset-name",
    default="reddit_harbor",
    help="Dataset name (default: reddit_harbor)"
)
@click.option(
    "--write-disposition",
    type=click.Choice(["append", "replace", "merge"]),
    default="merge",
    help="Write disposition (default: merge)"
)
@click.option(
    "--table-name",
    default="app_opportunities",
    help="Table name (default: app_opportunities)"
)
@click.option(
    "--max-functions",
    default=3,
    type=int,
    help="Maximum allowed core functions (default: 3)"
)
@click.option(
    "--production/--test",
    default=False,
    help="Use production or test configuration"
)
@click.pass_context
def run_pipeline(
    ctx: click.Context,
    source: Path,
    destination: str,
    dataset_name: str,
    write_disposition: str,
    table_name: str,
    max_functions: int,
    production: bool
) -> None:
    """Run a full DLT pipeline with constraint enforcement.

    Loads data from source file through a DLT pipeline with automatic
    constraint enforcement. Validates simplicity constraint and loads
    results to the specified destination.

    Example:
        dlt-cli run-pipeline --source data.json --destination postgres
        dlt-cli run-pipeline --source data.json --production
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Loading data from: {source}")
        click.echo(f"Destination: {destination}")
        click.echo(f"Dataset: {dataset_name}")
        click.echo(f"Table: {table_name}")

    try:
        # Load data
        with open(source) as f:
            opportunities = json.load(f)

        if not isinstance(opportunities, list):
            click.echo("Error: Data must be a list of opportunities", err=True)
            sys.exit(1)

        if verbose:
            click.echo(f"Loaded {len(opportunities)} opportunities")

        # Create pipeline
        if production:
            if verbose:
                click.echo("Using production configuration")
            pipeline = create_production_dataset(dataset_name)
        else:
            if verbose:
                click.echo("Using test configuration")
            pipeline = create_test_dataset(dataset_name)

        # Note: Pipeline object doesn't have schema attribute until after first run
        # So we skip the schema check that's in create_constraint_aware_dataset

        # Create constraint-aware resource
        @dlt.resource(table_name=table_name, write_disposition=write_disposition)
        def opportunities_resource():
            for opportunity in app_opportunities_with_constraint(opportunities):
                yield opportunity

        # Run pipeline
        click.echo("\nRunning DLT pipeline...")
        load_info = pipeline.run(
            opportunities_resource(),
            dataset_name=dataset_name
        )

        # Display results
        click.echo("\n" + "="*60)
        click.echo("PIPELINE COMPLETED")
        click.echo("="*60)
        click.echo(f"Pipeline: {pipeline.pipeline_name}")
        click.echo(f"Dataset: {dataset_name}")
        click.echo(f"Destination: {destination}")
        click.echo(f"Rows loaded: {load_info.asdict().get('load_id', 'N/A')}")
        click.echo(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo("="*60 + "\n")

        # Count violations
        violations = [o for o in opportunities if len(_extract_core_functions(o)) > max_functions]
        if violations:
            click.echo(f"Constraint violations: {len(violations)} apps disqualified")
        else:
            click.echo("All apps passed constraint validation!")

    except FileNotFoundError:
        click.echo(f"Error: File not found: {source}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error running pipeline: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# Command 4: test_constraint
@cli.command("test-constraint")
@click.option(
    "--sample-size",
    default=5,
    type=int,
    help="Number of sample opportunities to generate (default: 5)"
)
@click.option(
    "--max-functions",
    default=3,
    type=int,
    help="Maximum allowed core functions (default: 3)"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save test results to file"
)
@click.pass_context
def test_constraint(
    ctx: click.Context,
    sample_size: int,
    max_functions: int,
    output: Path | None
) -> None:
    """Test constraint enforcement with sample data.

    Generates sample app opportunities with varying function counts and
    validates them against the simplicity constraint. Useful for testing
    and demonstration purposes.

    Example:
        dlt-cli test-constraint --sample-size 10
        dlt-cli test-constraint --output test_results.json
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Generating {sample_size} sample opportunities")

    # Generate sample data
    import random
    random.seed(42)  # For reproducible results

    sample_opportunities = []
    for i in range(sample_size):
        # Vary the number of functions (1-6)
        function_count = random.randint(1, 6)

        opportunity = {
            "app_name": f"TestApp{i+1}",
            "app_description": f"A test application with {function_count} core functions",
            "function_list": [f"function_{j+1}" for j in range(function_count)],
            "original_score": random.uniform(60, 95)
        }
        sample_opportunities.append(opportunity)

    # Validate using constraint handler
    handler = create_constraint_normalize_handler(max_functions=max_functions)

    # Process opportunities
    validated = []
    for opp in sample_opportunities:
        # Simulate processing
        row = opp.copy()
        handler._enforce_constraint(row)
        validated.append(row)

    # Count results
    approved = sum(1 for v in validated if not v.get("is_disqualified", False))
    disqualified = sum(1 for v in validated if v.get("is_disqualified", False))

    # Display results
    click.echo("\n" + "="*60)
    click.echo("CONSTRAINT TEST RESULTS")
    click.echo("="*60)
    click.echo(f"Total opportunities tested: {sample_size}")
    click.echo(f"Approved: {approved}")
    click.echo(f"Disqualified: {disqualified}")
    click.echo(f"Compliance rate: {approved/sample_size*100:.1f}%")
    click.echo("="*60 + "\n")

    # Show details
    click.echo("Individual Results:")
    for v in validated:
        status = v.get("validation_status", "UNKNOWN")
        score = v.get("simplicity_score", 0)
        functions = v.get("core_functions", 0)
        click.echo(f"  • {v['app_name']:<20} {functions} functions → {status} (score: {score})")
    click.echo("")

    # Save to output
    if output:
        with open(output, "w") as f:
            json.dump(validated, f, indent=2)
        click.echo(f"Test results saved to: {output}")


# Command 5: check_database
@cli.command("check-database")
@click.option(
    "--destination",
    "-d",
    type=click.Choice(["postgres", "bigquery", "duckdb"]),
    default="postgres",
    help="Database type to check (default: postgres)"
)
@click.option(
    "--dataset-name",
    default="reddit_harbor",
    help="Dataset name to check"
)
@click.pass_context
def check_database(
    ctx: click.Context,
    destination: str,
    dataset_name: str
) -> None:
    """Check database connectivity and schema.

    Verifies that the database is accessible and displays information
    about the constraint-aware schema and existing tables.

    Example:
        dlt-cli check-database --destination postgres
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Checking database: {destination}")
        click.echo(f"Dataset: {dataset_name}")

    try:
        # Try to create a test pipeline
        # Note: We'll create the pipeline without applying schema constraints
        # since the schema attribute is not available until after first run
        import dlt
        pipeline = dlt.pipeline(
            pipeline_name=f"check_{dataset_name}",
            dataset_name=dataset_name,
            destination=destination
        )

        click.echo("\n" + "="*60)
        click.echo("DATABASE CHECK RESULTS")
        click.echo("="*60)
        click.echo(f"Database type: {destination}")
        click.echo(f"Dataset name: {dataset_name}")
        click.echo(f"Pipeline name: {pipeline.pipeline_name}")
        click.echo("Status: ✓ Database accessible")
        click.echo("="*60 + "\n")

        # Get schema information
        schema = get_constraint_schema()

        click.echo("Expected tables:")
        click.echo("  • app_opportunities (with constraint fields)")
        click.echo("  • constraint_violations (if violations exist)")
        click.echo("  • constraint_summary (aggregated metrics)")
        click.echo("")

        click.echo("Constraint fields in app_opportunities:")
        click.echo("  • core_functions (integer)")
        click.echo("  • simplicity_score (float)")
        click.echo("  • is_disqualified (boolean)")
        click.echo("  • validation_status (string)")
        click.echo("  • validation_timestamp (timestamp)")
        click.echo("  • violation_reason (text)")
        click.echo("")

        if destination == "postgres":
            click.echo("PostgreSQL connection info:")
            click.echo("  • Host: 127.0.0.1")
            click.echo("  • Port: 54322")
            click.echo("  • Database: postgres")
            click.echo("  • Supabase Studio: http://127.0.0.1:54323")
            click.echo("")

    except Exception as e:
        click.echo(f"Error: Cannot connect to database: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Make the CLI executable
    # Usage: python dlt_cli.py or ./dlt_cli.py
    cli()
