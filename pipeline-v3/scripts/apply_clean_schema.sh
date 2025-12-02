#!/bin/bash
# Apply clean schema to database
# Destroys all existing data

set -e

echo "🚨 WARNING: This will destroy ALL existing data in opportunities tables!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo "📦 Applying clean schema migration..."

# Apply SQL migration
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f "$(dirname "$0")/reset_to_clean_schema.sql"

echo ""
echo "✅ Clean schema applied successfully!"
echo ""
echo "📊 Schema verification:"
psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -c "SELECT COUNT(*) as total_opportunities FROM opportunities;"
