#!/bin/bash

# RedditHarbor Schema Dumps Update Script using Docker
# Updates existing schema dump files using Docker database access

set -e

echo "🐳 Updating RedditHarbor schema dumps using Docker..."

# Configuration
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_PORT="54322"
DB_HOST="127.0.0.1"

# Timestamp for new dumps
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📊 Using timestamp: $TIMESTAMP"

# Check if local Supabase is running and get container
if ! supabase status > /dev/null 2>&1; then
    echo "❌ Supabase is not running. Please start it with:"
    echo "   supabase start"
    exit 1
fi

# Get the actual container name from Supabase
CONTAINER_NAME=$(docker ps --format "table {{.Names}}" | grep "supabase_db" | head -1)
if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Could not find Supabase Docker container"
    exit 1
fi

echo "✅ Found Supabase container: $CONTAINER_NAME"

# Function to run SQL query via Docker
run_docker_query() {
    local query="$1"
    echo "🔍 Running: $query"
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "$query"
}

# Function to dump schema component
dump_schema_component() {
    local component="$1"
    local filename="${component}_${TIMESTAMP}.txt"

    echo "📋 Dumping $component..."

    case "$component" in
        "tables")
            run_docker_query "
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
                ORDER BY schemaname, tablename
            " > "current_tables_list_$TIMESTAMP.txt"
            ;;
        "views")
            run_docker_query "
                SELECT
                    schemaname,
                    viewname,
                    viewowner,
                    definition
                FROM pg_views
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, viewname
            " > "current_views_list_$TIMESTAMP.txt"
            ;;
        "indexes")
            run_docker_query "
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename, indexname
            " > "current_indexes_list_$TIMESTAMP.txt"
            ;;
        "structure")
            run_docker_query "
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
                ORDER BY c.table_schema, c.table_name, c.ordinal_position
            " > "current_table_structure_$TIMESTAMP.txt"
            ;;
    esac

    echo "✅ $component dump saved"
}

echo "🐳 Using Docker container: $CONTAINER_NAME"

# Update schema dumps using Docker
dump_schema_component "tables"
dump_schema_component "views"
dump_schema_component "indexes"
dump_schema_component "structure"

# Generate full schema dump
echo "🗄️ Generating full schema dump..."
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" \
    --schema-only \
    --no-owner \
    --no-privileges \
    > "unified_schema_v3.0.0_complete_$TIMESTAMP.sql"

# Add header to SQL dump
echo "-- RedditHarbor Database Schema Dump" > temp_header.txt
echo "-- Generated: $(date)" >> temp_header.txt
echo "-- Schema Version: v3.0.0" >> temp_header.txt
echo "-- Tool: Docker pg_dump via Supabase" >> temp_header.txt
echo "" >> temp_header.txt

cat temp_header.txt "unified_schema_v3.0.0_complete_$TIMESTAMP.sql" > temp_schema.sql
rm temp_header.txt
mv temp_schema.sql "unified_schema_v3.0.0_complete_$TIMESTAMP.sql"

echo "✅ Full schema dump completed"

# Generate summary
cat > "schema_dump_summary_$TIMESTAMP.md" << EOF
# RedditHarbor Schema Dump Summary

**Generated**: $(date)
**Tool**: Docker + pg_dump via Supabase
**Container**: $CONTAINER_NAME
**Timestamp**: $TIMESTAMP

## Generated Files

- \`current_tables_list_$TIMESTAMP.txt\` - All tables in database
- \`current_views_list_$TIMESTAMP.txt\` - All views in database
- \`current_indexes_list_$TIMESTAMP.txt\` - All indexes in database
- \`current_table_structure_$TIMESTAMP.txt\` - Detailed column structure
- \`unified_schema_v3.0.0_complete_$TIMESTAMP.sql\` - Complete schema dump

## Usage Examples

### View tables list
\`\`\`bash
cat current_tables_list_$TIMESTAMP.txt
\`\`\`

### View schema structure
\`\`\`bash
cat current_table_structure_$TIMESTAMP.txt | grep -A 10 "opportunities_unified"
\`\`\`

### Restore schema (if needed)
\`\`\`bash
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f unified_schema_v3.0.0_complete_$TIMESTAMP.sql
\`\`\`

---
*Generated by RedditHarbor Docker-based Schema Dump Utility*
EOF

echo "✅ Summary report created: schema_dump_summary_$TIMESTAMP.md"

# Display results
echo ""
echo "🎉 Schema dump completed successfully!"
echo ""
echo "📁 Generated files:"
ls -la current_*_$TIMESTAMP.txt unified_schema_v3.0.0_complete_$TIMESTAMP.sql schema_dump_summary_$TIMESTAMP.md
echo ""
echo "📊 Quick stats:"
echo "  Tables: $(cat current_tables_list_$TIMESTAMP.txt | grep -c "tablename")"
echo "  Views: $(cat current_views_list_$TIMESTAMP.txt | grep -c "viewname")"
echo "  Indexes: $(cat current_indexes_list_$TIMESTAMP.txt | grep -c "indexname")"
echo "  Schema size: $(du -h unified_schema_v3.0.0_complete_$TIMESTAMP.sql | cut -f1)"

echo ""
echo "💡 Use 'cat schema_dump_summary_$TIMESTAMP.md' for full details"