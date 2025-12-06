#!/bin/bash

# Phase 2 Real-Time KPI Monitoring Script
# Tracks Tier 1 Business Value KPIs with alerting thresholds

set -e

# Database configuration
DB_HOST="127.0.0.1"
DB_PORT="54322"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_NAME="postgres"

# KPI Thresholds
HIGH_SCORE_TARGET=30
HIGH_SCORE_WARNING=25
FUNCTION_COMPLIANCE_TARGET=100
FUNCTION_COMPLIANCE_WARNING=95
MARKET_VALIDATION_TARGET=90
MARKET_VALIDATION_WARNING=85

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to execute SQL query
run_query() {
    local query="$1"
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -A -c "$query" | grep -v '^$' | head -1
}

# Function to determine KPI status
get_kpi_status() {
    local current_value=$1
    local target=$2
    local warning=$3

    if (( $(echo "$current_value >= $target" | bc -l) )); then
        echo "PASS"
    elif (( $(echo "$current_value >= $warning" | bc -l) )); then
        echo "WARNING"
    else
        echo "FAIL"
    fi
}

# Function to get status color
get_status_color() {
    local status="$1"
    case "$status" in
        "PASS") echo -e "$GREEN" ;;
        "WARNING") echo -e "$YELLOW" ;;
        "FAIL") echo -e "$RED" ;;
        *) echo -e "$NC" ;;
    esac
}

# Check if bc is installed (for floating point comparisons)
if ! command -v bc &> /dev/null; then
    echo -e "${RED}ERROR: bc calculator not found. Please install bc for floating point comparisons.${NC}"
    exit 1
fi

# Check if database is accessible
if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" &> /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to database at $DB_HOST:$DB_PORT${NC}"
    exit 1
fi

echo -e "${BLUE}=== PHASE 2 QUALITY VALIDATION - REAL-TIME KPI DASHBOARD ===${NC}"
echo -e "${BLUE}Timestamp: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}Time Window: Last 24 hours${NC}"
echo ""

# Get High-Score Rate KPI
echo -e "${BLUE}--- TIER 1 BUSINESS VALUE KPIS ---${NC}"
printf "%-20s %-10s %-10s %-10s %s\n" "KPI" "Current" "Target" "Status" "Details"
printf "%-70s\n" "----------------------------------------------------------------------"

# High-Score Rate
HIGH_SCORE_QUERY="SELECT ROUND(COUNT(CASE WHEN final_score >= 70 THEN 1 END) * 100.0 / COUNT(*), 2) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours';"
HIGH_SCORE_RATE=$(run_query "$HIGH_SCORE_QUERY")
TOTAL_OPPORTUNITIES=$(run_query "SELECT COUNT(*) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours';")
HIGH_SCORE_COUNT=$(run_query "SELECT COUNT(CASE WHEN final_score >= 70 THEN 1 END) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours';")

HIGH_SCORE_STATUS=$(get_kpi_status $HIGH_SCORE_RATE $HIGH_SCORE_TARGET $HIGH_SCORE_WARNING)
HIGH_SCORE_COLOR=$(get_status_color "$HIGH_SCORE_STATUS")

printf "%-20s ${HIGH_SCORE_COLOR}%-10s${NC} %-10s ${HIGH_SCORE_COLOR}%-10s${NC} %s opportunities\n" \
    "HIGH_SCORE_RATE" "$HIGH_SCORE_RATE%" "$HIGH_SCORE_TARGET%" "$HIGH_SCORE_STATUS" "$TOTAL_OPPORTUNITIES"

# Function Compliance
FUNCTION_QUERY="SELECT ROUND(COUNT(CASE WHEN jsonb_array_length(core_functions) <= 3 THEN 1 END) * 100.0 / COUNT(*), 2) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours' AND core_functions IS NOT NULL;"
FUNCTION_RATE=$(run_query "$FUNCTION_QUERY")
FUNCTION_COMPLIANT=$(run_query "SELECT COUNT(CASE WHEN jsonb_array_length(core_functions) <= 3 THEN 1 END) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours' AND core_functions IS NOT NULL;")

FUNCTION_STATUS=$(get_kpi_status $FUNCTION_RATE $FUNCTION_COMPLIANCE_TARGET $FUNCTION_COMPLIANCE_WARNING)
FUNCTION_COLOR=$(get_status_color "$FUNCTION_STATUS")

printf "%-20s ${FUNCTION_COLOR}%-10s${NC} %-10s ${FUNCTION_COLOR}%-10s${NC} %s compliant\n" \
    "FUNCTION_COMPLIANCE" "$FUNCTION_RATE%" "$FUNCTION_COMPLIANCE_TARGET%" "$FUNCTION_STATUS" "$FUNCTION_COMPLIANT"

# Market Validation (Jina API)
MARKET_QUERY="SELECT ROUND(COUNT(CASE WHEN jina_validation_status = 'completed' THEN 1 END) * 100.0 / COUNT(*), 2) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours' AND jina_validation_status IS NOT NULL;"
MARKET_RATE=$(run_query "$MARKET_QUERY")
MARKET_VALIDATED=$(run_query "SELECT COUNT(CASE WHEN jina_validation_status = 'completed' THEN 1 END) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours' AND jina_validation_status IS NOT NULL;")
MARKET_TOTAL=$(run_query "SELECT COUNT(*) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours' AND jina_validation_status IS NOT NULL;")

MARKET_STATUS=$(get_kpi_status $MARKET_RATE $MARKET_VALIDATION_TARGET $MARKET_VALIDATION_WARNING)
MARKET_COLOR=$(get_status_color "$MARKET_STATUS")

printf "%-20s ${MARKET_COLOR}%-10s${NC} %-10s ${MARKET_COLOR}%-10s${NC} %s/%s validated\n" \
    "MARKET_VALIDATION" "$MARKET_RATE%" "$MARKET_VALIDATION_TARGET%" "$MARKET_STATUS" "$MARKET_VALIDATED" "$MARKET_TOTAL"

echo ""

# Processing Metrics
echo -e "${BLUE}--- PROCESSING METRICS ---${NC}"

# Throughput
THROUGHPUT_COUNT=$(run_query "SELECT COUNT(*) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours';")
THROUGHPUT_SECONDS=$(run_query "SELECT EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours';")

if (( $(echo "$THROUGHPUT_SECONDS > 0" | bc -l) )); then
    THROUGHPUT_PER_HOUR=$(echo "scale=2; $THROUGHPUT_COUNT / $THROUGHPUT_SECONDS * 3600" | bc)
else
    THROUGHPUT_PER_HOUR=0
fi

echo "Throughput: $THROUGHPUT_PER_HOUR opportunities/hour"

# Cost Metrics
COST_QUERY="SELECT COALESCE(SUM(jina_api_cost_usd), 0) FROM opportunities WHERE created_at >= NOW() - INTERVAL '24 hours';"
TOTAL_COST=$(run_query "$COST_QUERY")

if (( $(echo "$THROUGHPUT_COUNT > 0" | bc -l) )); then
    AVG_COST=$(echo "scale=8; $TOTAL_COST / $THROUGHPUT_COUNT" | bc)
else
    AVG_COST=0
fi

echo "Total Cost: \$$TOTAL_COST"
echo "Avg Cost/Opportunity: \$$AVG_COST"

echo ""

# Pipeline Health
echo -e "${BLUE}--- PIPELINE HEALTH ---${NC}"

PIPELINE_QUERY="SELECT phase, COUNT(*), ROUND(COUNT(CASE WHEN success = false THEN 1 END) * 100.0 / COUNT(*), 2) FROM pipeline_metrics WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY phase ORDER BY COUNT(*) DESC;"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -A -c "$PIPELINE_QUERY" | grep -v '^$' | while IFS='|' read -r phase exec_count error_rate; do
    if [[ -n "$phase" && -n "$exec_count" && -n "$error_rate" ]]; then
        # Determine health status
        if (( $(echo "$error_rate < 5" | bc -l) )); then
            health_status="PASS"
            health_color=$GREEN
        elif (( $(echo "$error_rate < 10" | bc -l) )); then
            health_status="WARNING"
            health_color=$YELLOW
        else
            health_status="FAIL"
            health_color=$RED
        fi

        printf "%-12s - ${health_color}%s${NC} (%.1f%% error rate, %s executions)\n" \
            "$phase" "$health_status" "$error_rate" "$exec_count"
    fi
done

echo ""

# Alert Summary
FAILED_KPIS=()
WARNING_KPIS=()

if [[ "$HIGH_SCORE_STATUS" == "FAIL" ]]; then
    FAILED_KPIS+=("HIGH_SCORE_RATE: $HIGH_SCORE_RATE% (threshold: $HIGH_SCORE_WARNING%)")
elif [[ "$HIGH_SCORE_STATUS" == "WARNING" ]]; then
    WARNING_KPIS+=("HIGH_SCORE_RATE: $HIGH_SCORE_RATE% (target: $HIGH_SCORE_TARGET%)")
fi

if [[ "$FUNCTION_STATUS" == "FAIL" ]]; then
    FAILED_KPIS+=("FUNCTION_COMPLIANCE: $FUNCTION_RATE% (threshold: $FUNCTION_COMPLIANCE_WARNING%)")
elif [[ "$FUNCTION_STATUS" == "WARNING" ]]; then
    WARNING_KPIS+=("FUNCTION_COMPLIANCE: $FUNCTION_RATE% (target: $FUNCTION_COMPLIANCE_TARGET%)")
fi

if [[ "$MARKET_STATUS" == "FAIL" ]]; then
    FAILED_KPIS+=("MARKET_VALIDATION: $MARKET_RATE% (threshold: $MARKET_VALIDATION_WARNING%)")
elif [[ "$MARKET_STATUS" == "WARNING" ]]; then
    WARNING_KPIS+=("MARKET_VALIDATION: $MARKET_RATE% (target: $MARKET_VALIDATION_TARGET%)")
fi

# Display alerts
if [[ ${#FAILED_KPIS[@]} -gt 0 ]]; then
    echo -e "${RED}🚨 CRITICAL ALERTS:${NC}"
    for alert in "${FAILED_KPIS[@]}"; do
        echo -e "  • ${RED}$alert${NC}"
    done
    echo ""
fi

if [[ ${#WARNING_KPIS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  WARNINGS:${NC}"
    for alert in "${WARNING_KPIS[@]}"; do
        echo -e "  • ${YELLOW}$alert${NC}"
    done
    echo ""
fi

if [[ ${#FAILED_KPIS[@]} -eq 0 && ${#WARNING_KPIS[@]} -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL KPIS WITHIN ACCEPTABLE RANGES${NC}"
    echo ""
fi

# Additional monitoring information
echo -e "${BLUE}--- ADDITIONAL INFORMATION ---${NC}"
echo "Dashboard API: http://localhost:5000/api/stats"
echo "Supabase Studio: http://127.0.0.1:54323"
echo "API Endpoint: http://127.0.0.1:54321/rest/v1/"

# Exit with appropriate code
if [[ ${#FAILED_KPIS[@]} -gt 0 ]]; then
    exit 2  # Critical failure
elif [[ ${#WARNING_KPIS[@]} -gt 0 ]]; then
    exit 1  # Warning
else
    exit 0  # All good
fi