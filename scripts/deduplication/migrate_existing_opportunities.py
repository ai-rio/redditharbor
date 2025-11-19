#!/usr/bin/env python3
"""
RedditHarbor Migration Script for Existing Opportunities

This script processes existing opportunities_unified records that don't have
business_concept_id assigned yet, using the SimpleDeduplicator to identify
duplicates and assign business concepts.

Usage:
    python scripts/deduplication/migrate_existing_opportunities.py [options]

Options:
    --output-file FILE     JSON file to save results (default: migration_results.json)
    --batch-size N         Number of records to process in each batch (default: 100)
    --dry-run             Show what would be processed without actually processing
    --verbose             Enable verbose logging
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.deduplication import SimpleDeduplicator
    from supabase import create_client
except ImportError as e:
    print(f"Error: Required dependency not found: {e}")
    print("Please install required packages: pip install supabase")
    sys.exit(1)

# Import configuration
try:
    from config.settings import SUPABASE_KEY, SUPABASE_URL
except ImportError:
    print("Error: Could not import configuration from config.settings")
    sys.exit(1)


class MigrationScript:
    """
    Main migration script class for processing existing opportunities.

    This class handles the complete migration workflow:
    1. Fetch opportunities without business_concept_id
    2. Process each through the deduplication pipeline
    3. Track progress and statistics
    4. Save comprehensive results to JSON file
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize the migration script with Supabase connection.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key

        Raises:
            ImportError: If required dependencies are not available
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

        # Initialize deduplicator
        try:
            self.deduplicator = SimpleDeduplicator(supabase_url, supabase_key)
        except ImportError as err:
            raise ImportError(
                "supabase package is required. Install with: pip install supabase"
            ) from err

        # Initialize statistics
        self.statistics = {
            "total_processed": 0,
            "unique_concepts": 0,
            "duplicates_found": 0,
            "errors": 0,
        }

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def fetch_opportunities_without_concept_id(self) -> list[dict]:
        """
        Fetch opportunities from opportunities_unified table that don't have
        business_concept_id assigned.

        Returns:
            List of opportunity dictionaries, empty list if error occurs
        """
        try:
            supabase = create_client(self.supabase_url, self.supabase_key)

            response = (
                supabase.table("opportunities_unified")
                .select("id, app_concept, title")
                .is_("business_concept_id", "null")
                .execute()
            )

            if response.data:
                self.logger.info(
                    f"Fetched {len(response.data)} opportunities "
                    "without business_concept_id"
                )
                return response.data
            else:
                self.logger.info("No opportunities found without business_concept_id")
                return []

        except Exception as e:
            self.logger.error(f"Error fetching opportunities: {e}")
            print(f"Error fetching opportunities: {e}")
            return []

    def process_opportunities(
        self, opportunities: list[dict], batch_size: int = 100
    ) -> list[dict]:
        """
        Process a list of opportunities through the deduplication pipeline.

        Args:
            opportunities: List of opportunity dictionaries
            batch_size: Number of records to process before showing progress

        Returns:
            List of processing results for each opportunity
        """
        results = []
        total_opportunities = len(opportunities)

        print(f"Starting processing of {total_opportunities} opportunities...")

        for i, opportunity in enumerate(opportunities):
            try:
                # Process individual opportunity
                result = self.deduplicator.process_opportunity(opportunity)
                results.append(result)

                # Update statistics
                self.statistics["total_processed"] += 1

                if result["success"]:
                    if result["is_duplicate"]:
                        self.statistics["duplicates_found"] += 1
                    else:
                        self.statistics["unique_concepts"] += 1
                else:
                    self.statistics["errors"] += 1

                # Show progress every batch_size records
                if (i + 1) % batch_size == 0:
                    self._print_progress(i + 1, total_opportunities)

            except Exception as e:
                # Handle unexpected errors for individual opportunities
                error_result = {
                    "success": False,
                    "opportunity_id": opportunity.get("id"),
                    "error": f"Unexpected error: {e}",
                    "message": "Processing failed: unexpected error",
                }
                results.append(error_result)
                self.statistics["total_processed"] += 1
                self.statistics["errors"] += 1
                self.logger.error(
                    f"Unexpected error processing opportunity "
                    f"{opportunity.get('id')}: {e}"
                )

        # Final progress update
        print(f"\nProcessing complete! Total processed: {total_opportunities}")

        return results

    def _print_progress(self, processed: int, total: int) -> None:
        """Print progress update with current statistics."""
        percentage = (processed / total) * 100
        print(
            f"Progress: {processed}/{total} ({percentage:.1f}%) - "
            f"Unique: {self.statistics['unique_concepts']}, "
            f"Duplicates: {self.statistics['duplicates_found']}, "
            f"Errors: {self.statistics['errors']}"
        )

    def save_results_to_json(self, results: list[dict], output_file: str) -> None:
        """
        Save processing results and statistics to a JSON file.

        Args:
            results: List of processing results
            output_file: Path to output JSON file
        """
        try:
            # Prepare output data
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.statistics,
                "results": results,
            }

            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2, default=str)

            print(f"Results saved to: {output_file}")

            # Print summary
            print("\nMigration Summary:")
            print(f"  Total processed: {self.statistics['total_processed']}")
            print(f"  Unique concepts: {self.statistics['unique_concepts']}")
            print(f"  Duplicates found: {self.statistics['duplicates_found']}")
            print(f"  Errors: {self.statistics['errors']}")

        except Exception as e:
            print(f"Error saving results to JSON file: {e}")
            self.logger.error(f"Error saving results: {e}")
            # Don't re-raise - allow script to continue


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate existing opportunities through semantic deduplication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/deduplication/migrate_existing_opportunities.py
    python scripts/deduplication/migrate_existing_opportunities.py \\
        --output-file custom_results.json --batch-size 50
    python scripts/deduplication/migrate_existing_opportunities.py \\
        --dry-run --verbose
        """,
    )

    parser.add_argument(
        "--output-file",
        default="migration_results.json",
        help="JSON file to save results (default: migration_results.json)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to process before showing progress (default: 100)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def main() -> None:
    """Main entry point for the migration script."""
    # Parse command line arguments
    args = parse_arguments()

    # Setup logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Check configuration
    supabase_url = SUPABASE_URL
    supabase_key = SUPABASE_KEY

    if not supabase_url:
        print("Error: SUPABASE_URL not found in environment variables")
        sys.exit(1)

    if not supabase_key:
        print("Error: SUPABASE_KEY not found in environment variables")
        sys.exit(1)

    try:
        # Initialize migration script
        print("Initializing migration script...")
        migration_script = MigrationScript(supabase_url, supabase_key)

        # Fetch opportunities without business_concept_id
        print("Fetching opportunities without business_concept_id...")
        opportunities = migration_script.fetch_opportunities_without_concept_id()

        if not opportunities:
            print("No opportunities found without business_concept_id")
            return

        print(f"Found {len(opportunities)} opportunities to process")

        if args.dry_run:
            print("DRY RUN MODE - No actual processing will be performed")
            print("Opportunities that would be processed:")
            for i, opp in enumerate(opportunities[:5]):  # Show first 5
                concept_preview = opp.get('app_concept', 'No concept')[:50]
                print(f"  {i + 1}. {opp.get('id')}: {concept_preview}...")
            if len(opportunities) > 5:
                print(f"  ... and {len(opportunities) - 5} more")
            return

        # Process opportunities
        print("Starting deduplication processing...")
        results = migration_script.process_opportunities(opportunities, args.batch_size)

        # Save results to JSON file
        print("Saving results...")
        migration_script.save_results_to_json(results, args.output_file)

        print("\nMigration completed successfully!")

    except KeyboardInterrupt:
        print("\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
