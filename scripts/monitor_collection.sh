#!/bin/bash
# Monitor Enhanced Collection Progress

echo "======================================================================"
echo "📊 RedditHarbor Enhanced Collection Monitor"
echo "======================================================================"
echo ""

# Check if collection is running
if ps aux | grep -v grep | grep enhanced_monetizable_collection > /dev/null; then
    PID=$(ps aux | grep -v grep | grep enhanced_monetizable_collection | awk '{print $2}')
    echo "✅ Collection Status: RUNNING (PID: $PID)"
else
    echo "❌ Collection Status: NOT RUNNING"
    exit 1
fi

echo ""
echo "======================================================================"
echo "📝 Database Statistics"
echo "======================================================================"

docker exec supabase_db_carlos psql -U postgres -d postgres << 'EOF'
-- Overall counts
SELECT
    'Total Submissions' as metric,
    COUNT(*) as count
FROM submissions
UNION ALL
SELECT
    'With Sentiment Score',
    COUNT(*) FILTER (WHERE sentiment_score IS NOT NULL)
FROM submissions
UNION ALL
SELECT
    'With Problem Keywords',
    COUNT(*) FILTER (WHERE problem_keywords IS NOT NULL AND problem_keywords != '')
FROM submissions
UNION ALL
SELECT
    'With Solution Mentions',
    COUNT(*) FILTER (WHERE solution_mentions IS NOT NULL AND solution_mentions != '')
FROM submissions
UNION ALL
SELECT
    'Total Comments',
    COUNT(*)
FROM comments
UNION ALL
SELECT
    'Total Redditors',
    COUNT(*)
FROM redditors;

-- Subreddit distribution
\echo ''
\echo '======================================================================'
\echo '📍 Top 15 Subreddits'
\echo '======================================================================'
SELECT
    subreddit,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM submissions), 0), 2) as percentage
FROM submissions
GROUP BY subreddit
ORDER BY count DESC
LIMIT 15;
EOF

echo ""
echo "======================================================================"
echo "📋 Recent Collection Log (last 20 lines)"
echo "======================================================================"
tail -20 /tmp/enhanced_collection_fresh.log

echo ""
echo "======================================================================"
echo "⏱️  Collection Progress"
echo "======================================================================"
echo "Expected: ~10,950 submissions"
echo "Check progress again in 30-60 minutes"
echo ""
