#!/bin/bash

# RedditHarbor Linting Script
# Runs ruff to check and fix code quality issues

echo "🔍 RedditHarbor Code Quality Check"
echo "================================="

# Activate virtual environment
source .venv/bin/activate

# Check if ruff is installed
if ! command -v ruff &> /dev/null; then
    echo "❌ Ruff not found. Installing..."
    pip install ruff
fi

echo -e "\n📋 Running Ruff checks..."
echo "Current issues found:"
ruff check . --exclude ".venv" --statistics

echo -e "\n🔧 Auto-fixing available issues..."
ruff check . --exclude ".venv" --fix

echo -e "\n📊 Final check:"
final_issues=$(ruff check . --exclude ".venv" 2>/dev/null | grep "Found " | sed 's/Found //;s/ errors.*//')

if [ -z "$final_issues" ]; then
    echo "✅ No critical issues found!"
else
    echo "⚠️  $final_issues issues remaining (mostly formatting and long lines)"
fi

echo -e "\n💡 Tips:"
echo "   • Use 'ruff format .' to format code automatically"
echo "   • See ruff.toml for configuration"
echo "   • Run this script before commits"

echo -e "\n✨ RedditHarbor linting complete!"