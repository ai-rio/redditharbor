#!/usr/bin/env python3
"""
RedditHarbor Database Schema Dump Script

This script creates comprehensive database schema dumps without data for:
- Documentation purposes
- Backup and recovery
- Deployment and migrations
- Development environment setup

Features:
- Full schema dump (tables, indexes, constraints, triggers)
- Roles and permissions dump
- Separate files for different components
- Timestamped output files
- Clean organization

Usage:
    python scripts/create_schema_dump.py [--full] [--roles] [--combined]
    python scripts/create_schema_dump.py --help
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, '/home/carlos/projects/redditharbor')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaDumper:
    """Database schema dump manager for RedditHarbor."""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.container_name = "supabase_db_carlos"
        self.output_dir = Path("schema_dumps")
        self.output_dir.mkdir(exist_ok=True)

    def check_supabase_status(self) -> bool:
        """Check if Supabase containers are running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=supabase_db_carlos"],
                capture_output=True,
                text=True
            )
            return "supabase_db_carlos" in result.stdout
        except Exception as e:
            logger.error(f"Failed to check Supabase status: {e}")
            return False

    def dump_roles(self) -> str:
        """Create database roles and permissions dump."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"roles_dump_{timestamp}.sql"

        try:
            logger.info("🔧 Creating roles and permissions dump...")

            cmd = [
                "supabase", "db", "dump",
                "--local",
                "--role-only",
                "-f", str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Roles dump created: {output_file}")
                return str(output_file)
            else:
                logger.error(f"❌ Failed to create roles dump: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating roles dump: {e}")
            return None

    def dump_schema(self) -> str:
        """Create full database schema dump without data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"schema_only_{timestamp}.sql"

        try:
            logger.info("🔧 Creating full schema dump...")

            cmd = [
                "docker", "exec", self.container_name,
                "pg_dump", "-U", "postgres",
                "--schema-only",
                "--no-owner",
                "--no-privileges",
                "--create",
                "--verbose",
                "postgres"
            ]

            with open(output_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                file_size = output_file.stat().st_size
                logger.info(f"✅ Schema dump created: {output_file} ({file_size:,} bytes)")

                # Add header information
                self._add_dump_header(output_file, "schema")
                return str(output_file)
            else:
                logger.error(f"❌ Failed to create schema dump: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating schema dump: {e}")
            return None

    def dump_migrations_only(self) -> str:
        """Create dump of only RedditHarbor migration tables."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"migrations_schema_{timestamp}.sql"

        try:
            logger.info("🔧 Creating migrations-only schema dump...")

            # List of RedditHarbor specific schemas/tables
            schemas = ["public", "extensions", "graphql_public"]
            tables_pattern = [
                "redditor", "submission", "comment", "workflow",
                "problem_metrics", "opportunity", "collection_stats"
            ]

            cmd = [
                "docker", "exec", self.container_name,
                "pg_dump", "-U", "postgres",
                "--schema-only",
                "--no-owner",
                "--no-privileges",
                "--exclude-table-data=*"
            ]

            # Add specific tables if needed
            for table in tables_pattern:
                cmd.extend(["--table", f"*{table}*"])

            cmd.append("postgres")

            with open(output_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                file_size = output_file.stat().st_size
                logger.info(f"✅ Migrations schema dump created: {output_file} ({file_size:,} bytes)")

                self._add_dump_header(output_file, "migrations")
                return str(output_file)
            else:
                logger.error(f"❌ Failed to create migrations dump: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating migrations dump: {e}")
            return None

    def dump_combined(self) -> str:
        """Create combined dump with roles and schema."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"complete_schema_{timestamp}.sql"

        try:
            logger.info("🔧 Creating combined schema and roles dump...")

            # Get individual dumps first
            roles_file = self.dump_roles()
            schema_file = self.dump_schema()

            if roles_file and schema_file:
                # Combine them
                with open(output_file, 'w') as combined:
                    combined.write(self._generate_header("complete"))

                    # Add roles
                    with open(roles_file, 'r') as rf:
                        combined.write("\n-- ===========================================\n")
                        combined.write("-- ROLES AND PERMISSIONS\n")
                        combined.write("-- ===========================================\n\n")
                        combined.write(rf.read())

                    # Add schema
                    with open(schema_file, 'r') as sf:
                        combined.write("\n-- ===========================================\n")
                        combined.write("-- DATABASE SCHEMA\n")
                        combined.write("-- ===========================================\n\n")
                        combined.write(sf.read())

                file_size = output_file.stat().st_size
                logger.info(f"✅ Combined dump created: {output_file} ({file_size:,} bytes)")
                return str(output_file)
            else:
                logger.error("❌ Failed to create combined dump - missing components")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating combined dump: {e}")
            return None

    def _add_dump_header(self, file_path: Path, dump_type: str):
        """Add informational header to dump file."""
        header = self._generate_header(dump_type)

        # Read existing content
        with open(file_path, 'r') as f:
            content = f.read()

        # Write header + content
        with open(file_path, 'w') as f:
            f.write(header)
            f.write(content)

    def _generate_header(self, dump_type: str) -> str:
        """Generate dump file header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = f"""-- ===========================================
-- RedditHarbor Database Schema Dump
-- ===========================================
--
-- Dump Type: {dump_type.upper()}
-- Generated: {timestamp}
-- Project: RedditHarbor
-- Database: PostgreSQL (Supabase)
-- Container: {self.container_name}
--
-- This file contains the database schema structure
-- without any data records. Use this for:
-- - Documentation and reference
-- - Development environment setup
-- - Migration planning
-- - Backup and recovery procedures
--
-- ===========================================

"""
        return header

    def cleanup_old_dumps(self, keep_count: int = 5):
        """Clean up old dump files, keeping only the most recent ones."""
        try:
            logger.info(f"🧹 Cleaning up old dumps (keeping latest {keep_count})...")

            for dump_type in ["roles", "schema_only", "migrations_schema", "complete_schema"]:
                pattern = f"{dump_type}_*.sql"
                files = sorted(self.output_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)

                for old_file in files[keep_count:]:
                    old_file.unlink()
                    logger.info(f"  🗑️  Removed: {old_file.name}")

            logger.info("✅ Cleanup completed")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

    def create_index_file(self):
        """Create an index file listing all available dumps."""
        try:
            index_file = self.output_dir / "README.md"

            with open(index_file, 'w') as f:
                f.write("# RedditHarbor Database Schema Dumps\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Available Dump Files\n\n")

                # List all dump files with info
                for dump_file in sorted(self.output_dir.glob("*.sql")):
                    if dump_file.name != "README.md":
                        size = dump_file.stat().st_size
                        mtime = datetime.fromtimestamp(dump_file.stat().st_mtime)
                        f.write(f"- **{dump_file.name}** ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})\n")

                f.write("\n## Usage\n\n")
                f.write("```bash\n")
                f.write("# Restore schema only\n")
                f.write("psql -h localhost -p 54322 -U postgres -d postgres < schema_only_YYYYMMDD_HHMMSS.sql\n\n")
                f.write("# Restore roles first\n")
                f.write("psql -h localhost -p 54322 -U postgres -d postgres < roles_dump_YYYYMMDD_HHMMSS.sql\n")
                f.write("```\n")

            logger.info(f"✅ Index file created: {index_file}")

        except Exception as e:
            logger.error(f"❌ Error creating index file: {e}")


def main():
    """Main function for schema dumping."""
    parser = argparse.ArgumentParser(
        description="Create RedditHarbor database schema dumps without data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create full schema dump
  python scripts/create_schema_dump.py --full

  # Create roles dump only
  python scripts/create_schema_dump.py --roles

  # Create combined dump with everything
  python scripts/create_schema_dump.py --combined

  # Create all dump types
  python scripts/create_schema_dump.py --all

  # Clean up old dumps (keep latest 3)
  python scripts/create_schema_dump.py --cleanup --keep 3
        """
    )

    # Dump type options
    parser.add_argument(
        "--full",
        action="store_true",
        help="Create full database schema dump"
    )
    parser.add_argument(
        "--roles",
        action="store_true",
        help="Create roles and permissions dump"
    )
    parser.add_argument(
        "--migrations",
        action="store_true",
        help="Create RedditHarbor migrations-only dump"
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Create combined dump with roles and schema"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Create all dump types"
    )

    # Maintenance options
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old dump files"
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=5,
        help="Number of recent dumps to keep (default: 5)"
    )

    args = parser.parse_args()

    # Initialize dumper
    dumper = SchemaDumper()

    # Check Supabase status
    if not dumper.check_supabase_status():
        logger.error("❌ Supabase containers are not running. Please start Supabase first.")
        sys.exit(1)

    logger.info("🚀 Starting RedditHarbor schema dump process...")

    # Perform cleanup if requested
    if args.cleanup:
        dumper.cleanup_old_dumps(args.keep)

    # Create requested dumps
    created_files = []

    if args.all:
        logger.info("📦 Creating all dump types...")
        created_files.append(dumper.dump_roles())
        created_files.append(dumper.dump_schema())
        created_files.append(dumper.dump_migrations_only())
        created_files.append(dumper.dump_combined())
    else:
        if args.full:
            created_files.append(dumper.dump_schema())
        if args.roles:
            created_files.append(dumper.dump_roles())
        if args.migrations:
            created_files.append(dumper.dump_migrations_only())
        if args.combined:
            created_files.append(dumper.dump_combined())

    # Default behavior if no options specified
    if not any([args.full, args.roles, args.migrations, args.combined, args.all, args.cleanup]):
        logger.info("📦 No options specified, creating full schema dump...")
        created_files.append(dumper.dump_schema())

    # Create index file if any dumps were created
    if created_files:
        dumper.create_index_file()

        # Report results
        successful = [f for f in created_files if f]
        failed = [f for f in created_files if not f]

        logger.info("\n📊 DUMP RESULTS:")
        logger.info("=" * 50)

        if successful:
            logger.info(f"✅ Successfully created {len(successful)} dump(s):")
            for file in successful:
                size = Path(file).stat().st_size
                logger.info(f"  • {file} ({size:,} bytes)")

        if failed:
            logger.warning(f"⚠️  Failed to create {len(failed)} dump(s)")

        logger.info("=" * 50)
        logger.info("🎉 Schema dump process completed!")

    else:
        logger.info("✅ No dumps requested, cleanup completed.")


if __name__ == "__main__":
    main()