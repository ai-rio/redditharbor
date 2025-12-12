#!/bin/bash
# Quick start script for RedditHarbor Pipeline-V4 Dashboard

echo "Starting RedditHarbor Dashboard..."
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f .env ] && [ ! -f .env.local ]; then
    echo "Warning: No .env or .env.local file found."
    echo "Make sure DATABASE_URL is configured."
    echo ""
fi

# Test database connection
echo "Testing database connection..."
uv run python -c "
from database import get_db_session
from models.analysis import Opportunity
from sqlmodel import func, select

try:
    with get_db_session() as session:
        count = session.exec(select(func.count(Opportunity.id))).one()
        print(f'✓ Database connected: {count} opportunities found')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    exit(1)
" || exit 1

echo ""
echo "Launching dashboard..."
echo "Access it at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

# Run streamlit with UV
echo "Launching with UV..."
uv run streamlit run dashboard/app.py
