#!/usr/bin/env python3
"""
Explore Pipeline Results with SQLAlchemy

Explore the data stored by the pipeline to validate that everything
is working correctly and understand the current state of the database.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

def main():
    """Explore pipeline results using SQLAlchemy."""
    print("=" * 80)
    print("EXPLORING PIPELINE RESULTS WITH SQLALCHEMY")
    print("=" * 80)

    try:
        from core.db.session import get_db_session
        from core.db.models import Submission, get_all_models
        from sqlalchemy import text, inspect
        import sqlalchemy as sa
        print("✓ Successfully imported SQLAlchemy components")
    except ImportError as e:
        print(f"❌ Failed to import SQLAlchemy components: {e}")
        return 1

    # Get all available models to explore
    try:
        all_models = get_all_models()
        print(f"✓ Found {len(all_models)} database models")

        # Print available models
        print("\nAvailable models:")
        for model_name, model_class in all_models.items():
            print(f"  - {model_name}: {model_class.__name__}")
    except Exception as e:
        print(f"⚠️  Could not get all models: {e}")
        all_models = {}

    # Explore database with SQLAlchemy
    try:
        with get_db_session() as session:
            # Get database inspector
            engine = session.get_bind()
            inspector = inspect(engine)

            # Get all table names
            tables = inspector.get_table_names()
            print(f"\n📊 Database Tables Found ({len(tables)}):")
            for table in sorted(tables):
                try:
                    columns = inspector.get_columns(table)
                    print(f"  📋 {table} ({len(columns)} columns)")
                except Exception as e:
                    print(f"  ❌ {table} (error: {e})")

            # Explore submissions table (main table)
            if 'submissions' in tables:
                print(f"\n" + "=" * 60)
                print("EXPLORING SUBMISSIONS TABLE")
                print("=" * 60)

                # Get table info
                columns = inspector.get_columns('submissions')
                print(f"Columns in submissions table ({len(columns)}):")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")

                # Count submissions
                count_result = session.execute(text("SELECT COUNT(*) FROM submissions"))
                total_count = count_result.scalar()
                print(f"\n📈 Total submissions: {total_count}")

                if total_count > 0:
                    # Sample recent submissions
                    sample_query = text("""
                        SELECT id, title, score, num_comments, created_at, updated_at
                        FROM submissions
                        ORDER BY created_at DESC
                        LIMIT 5
                    """)
                    sample_result = session.execute(sample_query).fetchall()

                    print(f"\n📝 Sample Submissions ({len(sample_result)} most recent):")
                    for i, row in enumerate(sample_result, 1):
                        print(f"  {i}. {row.id[:8]}... - {row.title[:60]}...")
                        print(f"     Score: {row.score}, Comments: {row.num_comments}")
                        print(f"     Created: {row.created_at}")
                        print()

            # Explore app_opportunities table (pipeline results)
            if 'app_opportunities' in tables:
                print(f"\n" + "=" * 60)
                print("EXPLORING APP_OPPORTUNITIES TABLE (Pipeline Results)")
                print("=" * 60)

                # Get table info
                columns = inspector.get_columns('app_opportunities')
                print(f"Columns in app_opportunities table ({len(columns)}):")
                important_cols = ['submission_id', 'app_name', 'value_proposition', 'final_score',
                                'opportunity_score', 'created_at', 'analyzed_at']
                for col in columns:
                    marker = " ⭐" if col['name'] in important_cols else ""
                    print(f"  {marker} {col['name']}: {col['type']} (nullable: {col['nullable']})")

                # Count app_opportunities
                count_result = session.execute(text("SELECT COUNT(*) FROM app_opportunities"))
                opp_count = count_result.scalar()
                print(f"\n📈 Total app opportunities: {opp_count}")

                if opp_count > 0:
                    # Sample recent opportunities
                    sample_query = text("""
                        SELECT
                            submission_id,
                            app_name,
                            value_proposition,
                            final_score,
                            opportunity_score,
                            analyzed_at
                        FROM app_opportunities
                        ORDER BY analyzed_at DESC
                        LIMIT 5
                    """)
                    sample_result = session.execute(sample_query).fetchall()

                    print(f"\n📝 Sample App Opportunities ({len(sample_result)} most recent):")
                    for i, row in enumerate(sample_result, 1):
                        print(f"  {i}. {row.submission_id[:8] if row.submission_id else 'N/A'}...")
                        print(f"     App Name: {row.app_name or 'N/A'}")
                        if row.value_proposition:
                            print(f"     Value Prop: {row.value_proposition[:80]}...")
                        print(f"     Final Score: {row.final_score}, Opportunity Score: {row.opportunity_score}")
                        print(f"     Analyzed: {row.analyzed_at}")
                        print()

            # Check for other pipeline-related tables
            pipeline_tables = [t for t in tables if any(keyword in t.lower()
                            for keyword in ['opportunity', 'score', 'trust', 'market', 'monetization'])]

            if pipeline_tables:
                print(f"\n" + "=" * 60)
                print("OTHER PIPELINE-RELATED TABLES")
                print("=" * 60)

                for table in pipeline_tables:
                    if table != 'app_opportunities':  # Already explored
                        try:
                            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = count_result.scalar()
                            columns = inspector.get_columns(table)

                            print(f"\n📊 {table}")
                            print(f"   Records: {count}")
                            print(f"   Columns: {len(columns)}")

                            # Show key columns
                            key_columns = [col['name'] for col in columns[:5]]  # First 5 columns
                            print(f"   Key columns: {', '.join(key_columns)}")

                            # Sample data if available
                            if count > 0:
                                try:
                                    sample_query = text(f"SELECT * FROM {table} LIMIT 1")
                                    sample = session.execute(sample_query).fetchone()
                                    if sample:
                                        print(f"   Sample data available ✅")
                                except Exception as e:
                                    print(f"   Sample query failed: {e}")

                        except Exception as e:
                            print(f"   ❌ Error exploring {table}: {e}")

            # Check for recent activity
            print(f"\n" + "=" * 60)
            print("RECENT PIPELINE ACTIVITY")
            print("=" * 60)

            # Get timestamps from various tables
            activity_queries = [
                ("Submissions", "SELECT MAX(created_at) as latest FROM submissions"),
                ("App Opportunities", "SELECT MAX(analyzed_at) as latest FROM app_opportunities"),
                ("All Updates", "SELECT MAX(updated_at) as latest FROM submissions"),
            ]

            for name, query in activity_queries:
                try:
                    result = session.execute(text(query)).fetchone()
                    if result and result.latest:
                        print(f"  📅 {name}: {result.latest}")
                    else:
                        print(f"  📅 {name}: No data")
                except Exception as e:
                    print(f"  ❌ {name}: Error - {e}")

        print(f"\n✅ Database exploration completed successfully!")

    except Exception as e:
        print(f"❌ Database exploration failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Exploration interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)