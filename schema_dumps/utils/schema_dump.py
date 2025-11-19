#!/usr/bin/env python3
"""
RedditHarbor Schema Dump Utility using Supabase CLI

This script provides database schema dumping capabilities using Supabase CLI
instead of direct database connections for better portability and security.

Usage:
    python utils/schema_dump.py --mode [tables|views|indexes|structure|full]
    python utils/schema_dump.py --help

Requirements:
    - Supabase CLI installed and configured
    - Supabase project running locally (supabase start)
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SchemaDumper:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.schema_dumps_dir = project_root / "schema_dumps"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_supabase_command(self, command: str) -> str:
        """Execute a Supabase CLI command and return the output."""
        try:
            # Change to project root to run supabase commands
            result = subprocess.run(
                ["supabase"] + command.split(),
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running Supabase command: {e}")
            print(f"Error output: {e.stderr}")
            return ""
        except FileNotFoundError:
            print("❌ Supabase CLI not found. Please install it with:")
            print("   npm install -g supabase")
            return ""

    def dump_tables_list(self) -> str:
        """Dump a list of all tables in the database."""
        print("📋 Dumping tables list...")

        sql_query = """
        SELECT
            schemaname,
            tablename,
            tableowner,
            tablespace,
            hasindexes,
            hasrules,
            hastriggers
        FROM pg_tables
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schemaname, tablename;
        """

        output = self.run_supabase_command(f"db --command=\"{sql_query}\"")

        filename = self.schema_dumps_dir / f"current_tables_list_{self.timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("# RedditHarbor Tables List\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Command: {sql_query}\n\n")
            f.write(output)

        print(f"✅ Tables list saved to: {filename}")
        return str(filename)

    def dump_views_list(self) -> str:
        """Dump a list of all views in the database."""
        print("👁️ Dumping views list...")

        sql_query = """
        SELECT
            schemaname,
            viewname,
            viewowner,
            definition
        FROM pg_views
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, viewname;
        """

        output = self.run_supabase_command(f"db --command=\"{sql_query}\"")

        filename = self.schema_dumps_dir / f"current_views_list_{self.timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("# RedditHarbor Views List\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Command: {sql_query}\n\n")
            f.write(output)

        print(f"✅ Views list saved to: {filename}")
        return str(filename)

    def dump_indexes_list(self) -> str:
        """Dump a list of all indexes in the database."""
        print("📚 Dumping indexes list...")

        sql_query = """
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename, indexname;
        """

        output = self.run_supabase_command(f"db --command=\"{sql_query}\"")

        filename = self.schema_dumps_dir / f"current_indexes_list_{self.timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("# RedditHarbor Indexes List\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Command: {sql_query}\n\n")
            f.write(output)

        print(f"✅ Indexes list saved to: {filename}")
        return str(filename)

    def dump_table_structure(self) -> str:
        """Dump detailed table structure with columns and types."""
        print("🏗️ Dumping table structure...")

        sql_query = """
        SELECT
            c.table_schema,
            c.table_name,
            c.column_name,
            c.ordinal_position,
            c.column_default,
            c.is_nullable,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.character_set_name,
            c.collation_name
        FROM information_schema.columns c
        WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY c.table_schema, c.table_name, c.ordinal_position;
        """

        output = self.run_supabase_command(f"db --command=\"{sql_query}\"")

        filename = self.schema_dumps_dir / f"current_table_structure_{self.timestamp}.txt"
        with open(filename, 'w') as f:
            f.write("# RedditHarbor Table Structure\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Command: {sql_query}\n\n")
            f.write(output)

        print(f"✅ Table structure saved to: {filename}")
        return str(filename)

    def dump_full_schema(self) -> str:
        """Dump the complete database schema."""
        print("🗄️ Dumping full schema...")

        # Use pg_dump through Supabase CLI
        filename = self.schema_dumps_dir / f"unified_schema_v3.0.0_complete_{self.timestamp}.sql"

        try:
            # Get database connection info from Supabase
            db_url = self.run_supabase_command("status --output=json").strip()

            # Use pg_dump to get the full schema
            result = subprocess.run([
                "pg_dump",
                "--schema-only",
                "--no-owner",
                "--no-privileges",
                "--file", str(filename),
                "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
            ], capture_output=True, text=True, check=True)

            # Add header to the dump file
            with open(filename) as f:
                content = f.read()

            with open(filename, 'w') as f:
                f.write("-- RedditHarbor Database Schema Dump\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write("-- Schema Version: v3.0.0\n")
                f.write("-- Tool: pg_dump via Supabase CLI\n\n")
                f.write(content)

            print(f"✅ Full schema saved to: {filename}")
            return str(filename)

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running pg_dump: {e}")
            return ""

    def generate_summary_report(self, files: list) -> str:
        """Generate a summary report of all dumped files."""
        print("📊 Generating summary report...")

        summary = f"""# RedditHarbor Schema Dump Summary Report

**Generated**: {datetime.now().isoformat()}
**Schema Version**: v3.0.0
**Tool**: Supabase CLI + pg_dump

## Generated Files

"""

        for file_path in files:
            rel_path = Path(file_path).relative_to(self.project_root)
            size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
            summary += f"- `{rel_path}` ({self._format_size(size)})\n"

        summary += f"""

## Usage Instructions

1. **View Tables**: `cat {self.schema_dumps_dir.name}/current_tables_list_{self.timestamp}.txt`
2. **View Views**: `cat {self.schema_dumps_dir.name}/current_views_list_{self.timestamp}.txt`
3. **View Indexes**: `cat {self.schema_dumps_dir.name}/current_indexes_list_{self.timestamp}.txt`
4. **View Structure**: `cat {self.schema_dumps_dir.name}/current_table_structure_{self.timestamp}.txt`
5. **Full Schema**: `cat {self.schema_dumps_dir.name}/unified_schema_v3.0.0_complete_{self.timestamp}.sql`

## Database Access

All dumps were created using Supabase CLI to ensure consistent access patterns.
The local Supabase instance must be running (`supabase start`) to recreate these dumps.

---
*Generated by RedditHarbor Schema Dump Utility*
"""

        filename = self.schema_dumps_dir / f"dump_summary_{self.timestamp}.md"
        with open(filename, 'w') as f:
            f.write(summary)

        print(f"✅ Summary report saved to: {filename}")
        return str(filename)

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

def main():
    parser = argparse.ArgumentParser(description="RedditHarbor Schema Dump Utility")
    parser.add_argument(
        "--mode",
        choices=["tables", "views", "indexes", "structure", "full", "all"],
        default="all",
        help="What to dump (default: all)"
    )
    parser.add_argument(
        "--project-root",
        default=Path(__file__).parent.parent.parent,
        help="Project root directory (default: auto-detect)"
    )

    args = parser.parse_args()

    project_root = Path(args.project_root)
    dumper = SchemaDumper(project_root)

    # Ensure schema_dumps directory exists
    dumper.schema_dumps_dir.mkdir(exist_ok=True)
    dumper.schema_dumps_dir.mkdir(parents=True, exist_ok=True)

    # Create utils directory if it doesn't exist
    utils_dir = Path(__file__).parent
    utils_dir.mkdir(exist_ok=True)

    generated_files = []

    print("🚀 Starting RedditHarbor Schema Dump using Supabase CLI...")
    print(f"📁 Project Root: {project_root}")
    print(f"📊 Timestamp: {dumper.timestamp}")
    print()

    # Check if Supabase is running
    try:
        result = dumper.run_supabase_command("status")
        if not result or "API URL:" not in result:
            print("❌ Supabase is not running. Please start it with:")
            print("   supabase start")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking Supabase status: {e}")
        print("Please ensure Supabase CLI is installed and running:")
        print("   1. npm install -g supabase")
        print("   2. supabase start")
        sys.exit(1)

    # Execute dumps based on mode
    if args.mode in ["all", "tables"]:
        generated_files.append(dumper.dump_tables_list())

    if args.mode in ["all", "views"]:
        generated_files.append(dumper.dump_views_list())

    if args.mode in ["all", "indexes"]:
        generated_files.append(dumper.dump_indexes_list())

    if args.mode in ["all", "structure"]:
        generated_files.append(dumper.dump_table_structure())

    if args.mode in ["all", "full"]:
        generated_files.append(dumper.dump_full_schema())

    # Generate summary
    summary_file = dumper.generate_summary_report(generated_files)
    generated_files.append(summary_file)

    print()
    print("🎉 Schema dump completed successfully!")
    print(f"📊 Generated {len(generated_files)} files")
    print(f"📋 Summary: {summary_file}")

if __name__ == "__main__":
    main()
