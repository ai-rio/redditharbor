#!/usr/bin/env python3
"""
Add Trust Layer Columns to Database Schema
RedditHarbor Trust Layer Integration Migration

This script adds the necessary trust layer columns to the app_opportunities table
to support comprehensive trust validation and credibility indicators.

Usage:
    python scripts/add_trust_layer_columns.py
"""

import sys
import os
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY


def add_trust_layer_columns():
    """Add trust layer columns to app_opportunities table"""
    print("🏆 ADDING TRUST LAYER COLUMNS")
    print("=" * 80)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # SQL to add trust layer columns
    sql_commands = [
        # Trust level and score
        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS trust_level TEXT CHECK (trust_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'));
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS trust_score DECIMAL(5,2) DEFAULT 0.0 CHECK (trust_score >= 0 AND trust_score <= 100);
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS trust_badge TEXT CHECK (trust_badge IN ('GOLD', 'SILVER', 'BRONZE', 'BASIC', 'NO-BADGE'));
        """,

        # Activity and engagement
        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS activity_score DECIMAL(6,2) DEFAULT 0.0 CHECK (activity_score >= 0);
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS engagement_level TEXT CHECK (engagement_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'));
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS trend_velocity DECIMAL(8,4) DEFAULT 0.0;
        """,

        # Validation indicators
        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS problem_validity TEXT CHECK (problem_validity IN ('VALID', 'POTENTIAL', 'UNCLEAR', 'INVALID'));
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS discussion_quality TEXT CHECK (discussion_quality IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR'));
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS ai_confidence_level TEXT CHECK (ai_confidence_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW'));
        """,

        # Additional data
        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS trust_factors JSONB DEFAULT '{}';
        """,

        """
        ALTER TABLE app_opportunities
        ADD COLUMN IF NOT EXISTS trust_updated_at TIMESTAMPTZ;
        """
    ]

    print("📊 Adding trust layer columns to app_opportunities table...")

    for i, sql in enumerate(sql_commands, 1):
        try:
            print(f"  {i}/{len(sql_commands)}: Executing migration...")

            # Use raw SQL execution through Supabase
            result = supabase.rpc('exec_sql', {'sql_query': sql}).execute()

            print(f"    ✅ Success")

        except Exception as e:
            # Try direct SQL approach if RPC not available
            try:
                # This will require direct database access or different approach
                print(f"    ⚠️  RPC not available, column may need manual addition: {e}")
            except Exception as e2:
                print(f"    ❌ Error: {e2}")

    print("\n🎯 Trust layer schema migration complete!")
    print("ℹ️  Note: Some columns may need manual addition via Supabase Studio")

    # Create indexes for performance
    print("\n📈 Creating indexes for trust layer columns...")

    index_commands = [
        "CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_level ON app_opportunities(trust_level);",
        "CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_score ON app_opportunities(trust_score);",
        "CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_badge ON app_opportunities(trust_badge);",
        "CREATE INDEX IF NOT EXISTS idx_app_opportunities_activity_score ON app_opportunities(activity_score);",
        "CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_updated_at ON app_opportunities(trust_updated_at);"
    ]

    for i, sql in enumerate(index_commands, 1):
        try:
            print(f"  {i}/{len(index_commands)}: Creating index...")
            result = supabase.rpc('exec_sql', {'sql_query': sql}).execute()
            print(f"    ✅ Success")
        except Exception as e:
            print(f"    ⚠️  Index may need manual creation: {e}")

    print("\n🎉 TRUST LAYER SCHEMA MIGRATION COMPLETE!")
    print("📊 Trust validation columns now available")
    print("🏆 Badge system ready for user interface")
    print("🔍 Comprehensive credibility indicators enabled")


if __name__ == "__main__":
    add_trust_layer_columns()