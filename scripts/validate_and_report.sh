#!/bin/bash
# RedditHarbor Schema Validation and Reporting Script
#
# This script runs automated schema validation and provides a summary report.
# Use this as part of your development workflow before commits.
#
# Usage: ./scripts/validate_and_report.sh

set -e

echo "🚀 RedditHarbor Schema Validation Workflow"
echo "============================================"

# Change to project directory
cd "$(dirname "$0")/.."

# Run automated schema validator
echo "📊 Running automated schema validation..."
python3 scripts/database/automated_schema_validator.py

# Exit with appropriate code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 VALIDATION SUCCESSFUL!"
    echo "✅ Schema is synchronized with migrations"
    echo "✅ Field coverage maintained at 96.9%+"
    echo "✅ No schema drift detected"
    echo ""
    echo "💡 Ready to commit changes!"
    exit 0
else
    echo ""
    echo "❌ VALIDATION FAILED!"
    echo "🔧 Please fix the issues above before committing"
    echo ""
    echo "📋 Common fixes:"
    echo "  • Run: python3 scripts/database/validate_schema_sync.py --fix"
    echo "  • Check: supabase migration files"
    echo "  • Verify: database table structures"
    exit 1
fi