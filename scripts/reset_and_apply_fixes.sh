#!/bin/bash
# Reset database and apply all cost tracking fixes

echo "RedditHarbor - Cost Tracking Fix Application Script"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ Error: Not in a Supabase project directory"
    echo "Please run this script from the project root"
    exit 1
fi

echo "✅ Found Supabase project"

# Check if Supabase is running
if ! supabase status > /dev/null 2>&1; then
    echo "🚀 Starting Supabase..."
    supabase start
else
    echo "✅ Supabase is already running"
fi

echo ""
echo "⚠️  WARNING: This will reset your local database and apply all migrations"
echo "   All existing data will be lost!"
echo ""
read -p "Do you want to continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled by user"
    exit 1
fi

echo ""
echo "🔄 Resetting database and applying migrations..."
supabase db reset

if [ $? -eq 0 ]; then
    echo "✅ Database reset successful!"
else
    echo "❌ Database reset failed!"
    exit 1
fi

echo ""
echo "🧪 Testing cost tracking functions..."

# Test the functions
echo "Testing get_cost_summary() function..."
supabase db shell --command "SELECT * FROM get_cost_summary();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ get_cost_summary() function works!"
else
    echo "❌ get_cost_summary() function test failed"
fi

echo "Testing cost_summary_simple view..."
supabase db shell --command "SELECT * FROM cost_summary_simple LIMIT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ cost_summary_simple view works!"
else
    echo "❌ cost_summary_simple view test failed"
fi

echo ""
echo "🎉 Cost tracking fix application completed!"
echo ""
echo "📊 You can now test cost tracking with these queries in Supabase Studio:"
echo "   http://127.0.0.1:54323"
echo ""
echo "🔍 Sample queries:"
echo "   SELECT * FROM cost_summary_simple;"
echo "   SELECT * FROM get_cost_summary();"
echo "   SELECT * FROM get_cost_summary(CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE);"
echo "   SELECT * FROM analyze_costs_by_date_range(CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE, 'day');"
echo ""
echo "📚 For more query examples, see:"
echo "   /home/carlos/projects/redditharbor/docs/cost_tracking_queries.md"