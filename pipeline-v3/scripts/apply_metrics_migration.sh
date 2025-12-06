#!/bin/bash
# Apply metrics tracking migration to Supabase database
# Created: 2025-12-05

set -e  # Exit on error

# Database connection details
DB_HOST="127.0.0.1"
DB_PORT="54322"
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting pipeline_metrics migration...${NC}"

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql not found. Please install PostgreSQL client.${NC}"
    exit 1
fi

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to database at $DB_HOST:$DB_PORT${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database connection successful${NC}"

# Check if table already exists
echo -e "${YELLOW}Checking if pipeline_metrics table exists...${NC}"
TABLE_EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='pipeline_metrics');")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo -e "${YELLOW}Warning: pipeline_metrics table already exists.${NC}"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Dropping existing table...${NC}"
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
            "DROP TABLE IF EXISTS pipeline_metrics CASCADE;"
        echo -e "${GREEN}✓ Table dropped${NC}"
    else
        echo -e "${YELLOW}Skipping migration. Table already exists.${NC}"
        exit 0
    fi
fi

# Apply migration
echo -e "${YELLOW}Applying migration...${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    -f "$(dirname "$0")/add_metrics_tracking_migration.sql"

# Verify table creation
echo -e "${YELLOW}Verifying table creation...${NC}"
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='pipeline_metrics';")

if [ "$TABLE_COUNT" = "1" ]; then
    echo -e "${GREEN}✓ pipeline_metrics table created successfully${NC}"
else
    echo -e "${RED}Error: Table creation failed${NC}"
    exit 1
fi

# Verify indexes
echo -e "${YELLOW}Verifying indexes...${NC}"
INDEX_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc \
    "SELECT COUNT(*) FROM pg_indexes WHERE tablename='pipeline_metrics';")

echo -e "${GREEN}✓ Created $INDEX_COUNT indexes${NC}"

# Verify views
echo -e "${YELLOW}Verifying views...${NC}"
VIEW_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -tAc \
    "SELECT COUNT(*) FROM information_schema.views WHERE table_name IN ('pipeline_phase_summary', 'agent_performance_summary', 'cost_analysis');")

echo -e "${GREEN}✓ Created $VIEW_COUNT views${NC}"

# Show table structure
echo -e "${YELLOW}Table structure:${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
    "\\d pipeline_metrics"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Available views:${NC}"
echo -e "  - pipeline_phase_summary"
echo -e "  - agent_performance_summary"
echo -e "  - cost_analysis"
echo -e ""
echo -e "${YELLOW}Example queries:${NC}"
echo -e "  SELECT * FROM pipeline_phase_summary;"
echo -e "  SELECT * FROM agent_performance_summary;"
echo -e "  SELECT * FROM cost_analysis;"
