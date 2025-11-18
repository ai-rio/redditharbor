#!/usr/bin/env python3
"""
RedditHarbor Database Query Utility using Supabase CLI

A convenient utility for running SQL queries against the local Supabase database
without requiring direct database connections or credentials.

Usage:
    python utils/db_query.py --query "SELECT COUNT(*) FROM opportunities_unified"
    python utils/db_query.py --file queries/active_opportunities.sql
    python utils/db_query.py --interactive

Requirements:
    - Supabase CLI installed and configured
    - Supabase project running locally (supabase start)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class DatabaseQuerier:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.schema_dumps_dir = project_root / "schema_dumps"
        self.results_dir = self.schema_dumps_dir / "query_results"
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_supabase_query(self, sql_query: str, output_format: str = "text") -> str:
        """Execute a SQL query using Supabase CLI."""
        try:
            # Clean up the query for command line
            clean_query = sql_query.strip().replace('"', '\\"').replace('\n', ' ')

            if output_format.lower() == "json":
                command = f"db --command=\"{clean_query}\" --json"
            else:
                command = f"db --command=\"{clean_query}\""

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
            error_msg = f"❌ Error running SQL query: {e}"
            if e.stderr:
                error_msg += f"\nError output: {e.stderr}"
            return error_msg
        except FileNotFoundError:
            return "❌ Supabase CLI not found. Please install it with: npm install -g supabase"

    def save_query_result(self, query: str, result: str, output_format: str = "text") -> str:
        """Save query result to a file."""
        filename = self.results_dir / f"query_result_{self.timestamp}.{'json' if output_format == 'json' else 'txt'}"

        content = f"""# RedditHarbor Database Query Result

**Generated**: {datetime.now().isoformat()}
**Output Format**: {output_format.upper()}
**Database**: Local Supabase Instance

## Query
```sql
{query}
```

## Result
"""

        if output_format.lower() == "json":
            # Try to format JSON nicely
            try:
                json_data = json.loads(result)
                content += "```json\n" + json.dumps(json_data, indent=2) + "\n```"
            except json.JSONDecodeError:
                content += "```\n" + result + "\n```"
        else:
            content += "```\n" + result + "\n```"

        with open(filename, 'w') as f:
            f.write(content)

        print(f"✅ Query result saved to: {filename}")
        return str(filename)

    def interactive_mode(self):
        """Run interactive query mode."""
        print("🔮 RedditHarbor Interactive Database Query Mode")
        print("Type your SQL queries below. Type 'exit' or 'quit' to stop.")
        print("Special commands:")
        print("  \\help      - Show help")
        print("  \\tables    - List all tables")
        print("  \\schema    - Show table schemas")
        print("  \\json      - Toggle JSON output format")
        print()

        json_output = False

        while True:
            try:
                query = input("redditdb> ").strip()

                if query.lower() in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    break

                if query.lower() == '\\help':
                    print("""
Available commands:
  SQL query    - Execute any SQL query
  \\tables     - List all tables
  \\schema     - Show table schemas
  \\json       - Toggle JSON output format
  \\exit/\\quit - Exit interactive mode
  \\help       - Show this help

Examples:
  SELECT COUNT(*) FROM opportunities_unified;
  \\tables
  SELECT * FROM redditors LIMIT 5;
                    """)
                    continue

                if query.lower() == '\\tables':
                    query = "SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('information_schema', 'pg_catalog') ORDER BY schemaname, tablename;"

                if query.lower() == '\\schema':
                    table_name = input("Enter table name: ").strip()
                    if table_name:
                        query = f"""
                        SELECT
                            column_name,
                            data_type,
                            is_nullable,
                            column_default
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        AND table_schema = 'public'
                        ORDER BY ordinal_position;
                        """
                    else:
                        continue

                if query.lower() == '\\json':
                    json_output = not json_output
                    print(f"📊 JSON output: {'ON' if json_output else 'OFF'}")
                    continue

                if not query:
                    continue

                print(f"🔍 Executing: {query[:100]}{'...' if len(query) > 100 else ''}")
                result = self.run_supabase_query(query, "json" if json_output else "text")
                print(result)
                print()

            except KeyboardInterrupt:
                print("\n👋 Interrupted. Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break

    def run_preset_queries(self):
        """Run common preset queries."""
        queries = {
            "table_counts": """
                SELECT
                    schemaname,
                    tablename,
                    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = pg_tables.tablename) as column_count
                FROM pg_tables
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename;
            """,

            "opportunities_summary": """
                SELECT
                    COUNT(*) as total_opportunities,
                    COUNT(CASE WHEN trust_level = 'VERY_HIGH' THEN 1 END) as very_high_trust,
                    COUNT(CASE WHEN trust_level = 'HIGH' THEN 1 END) as high_trust,
                    AVG(opportunity_score) as avg_score,
                    MAX(opportunity_score) as max_score
                FROM opportunities_unified
                WHERE opportunity_score IS NOT NULL;
            """,

            "recent_submissions": """
                SELECT
                    title,
                    subreddit,
                    score,
                    created_at,
                    trust_level
                FROM submissions s
                JOIN opportunities_unified o ON s.id = o.submission_id
                ORDER BY s.created_at DESC
                LIMIT 10;
            """,

            "schema_size": """
                SELECT
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    schemaname,
                    tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20;
            """
        }

        print("📊 Running preset queries...")

        for name, query in queries.items():
            print(f"\n🔍 Running: {name}")
            result = self.run_supabase_query(query)
            print(result)

def main():
    parser = argparse.ArgumentParser(description="RedditHarbor Database Query Utility")
    parser.add_argument("--query", help="SQL query to execute")
    parser.add_argument("--file", help="File containing SQL query")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--preset", action="store_true", help="Run preset queries")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--save", action="store_true", help="Save results to file")
    parser.add_argument("--project-root", help="Project root directory (auto-detected)")

    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else Path(__file__).parent.parent.parent
    querier = DatabaseQuerier(project_root)

    # Check if Supabase is running
    try:
        result = querier.run_supabase_query("SELECT 1", "json")
        if not result:
            print("❌ Supabase is not running. Please start it with:")
            print("   supabase start")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking Supabase status: {e}")
        print("Please ensure Supabase CLI is installed and running:")
        print("   1. npm install -g supabase")
        print("   2. supabase start")
        sys.exit(1)

    if args.interactive:
        querier.interactive_mode()
    elif args.preset:
        querier.run_preset_queries()
    elif args.query:
        result = querier.run_supabase_query(args.query, "json" if args.json else "text")
        print(result)

        if args.save:
            querier.save_query_result(args.query, result, "json" if args.json else "text")
    elif args.file:
        query_file = Path(args.file)
        if not query_file.exists():
            print(f"❌ Query file not found: {args.file}")
            sys.exit(1)

        with open(query_file) as f:
            query = f.read()

        result = querier.run_supabase_query(query, "json" if args.json else "text")
        print(result)

        if args.save:
            querier.save_query_result(query, result, "json" if args.json else "text")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
