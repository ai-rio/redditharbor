#!/bin/bash

# RedditHarbor Development Environment Startup Script
# Starts Docker daemon and Supabase services

set -e

echo "🚀 Starting RedditHarbor development environment..."

# Start Docker daemon if not already running
if ! docker ps &> /dev/null; then
    echo "🐳 Starting Docker daemon..."
    sudo dockerd > /tmp/docker.log 2>&1 &
    sleep 3
else
    echo "✓ Docker already running"
fi

# Wait for Docker to be fully ready
echo "⏳ Waiting for Docker to be ready..."
for i in {1..30}; do
    if docker ps &> /dev/null; then
        echo "✓ Docker ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Docker failed to start"
        exit 1
    fi
    sleep 1
done

# Start Supabase services
echo "🗄️  Starting Supabase services..."
supabase start --ignore-health-check

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Verify connection
echo "🔍 Verifying connection..."
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate

python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/carlos/projects/redditharbor')

try:
    from supabase import create_client
    from config.settings import SUPABASE_URL, SUPABASE_KEY

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('redditor').select('count', count='exact').execute()
    print(f"✓ Database connected - {response.count} redditors available")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)
PYTHON_EOF

echo ""
echo "✅ Development environment ready!"
echo ""
echo "📡 Service URLs:"
echo "   API:    http://127.0.0.1:54321"
echo "   Studio: http://127.0.0.1:54323"
echo "   DB:     postgresql://postgres:postgres@127.0.0.1:54322/postgres"
echo ""
