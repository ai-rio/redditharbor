#!/usr/bin/env python3
"""
Test script to generate sample pipeline metrics for dashboard testing
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_settings
import psycopg2
from psycopg2.extras import RealDictCursor

def generate_test_metrics():
    """Generate sample pipeline metrics for testing"""

    settings = get_settings()
    conn = psycopg2.connect(settings.database_url)
    cur = conn.cursor()

    # Generate test metrics for the last 2 hours
    phases = ['extract', 'transform', 'load', 'end_to_end']
    agents = ['wtp', 'segment', 'price', 'payment', 'market', 'consensus']

    # Generate 20 test metrics entries
    for i in range(20):
        opportunity_id = f"test-opp-{i+1:03d}"
        phase = random.choice(phases)
        agent_name = random.choice(agents)
        duration_seconds = random.uniform(0.1, 3.0)
        api_cost_usd = random.uniform(0.001, 0.01)
        success = random.choice([True, True, True, False])  # 75% success rate
        error_message = None if success else random.choice([
            "API timeout", "Rate limit exceeded", "Invalid response", "Connection error"
        ])

        # Random timestamp within last 2 hours
        minutes_ago = random.randint(0, 120)
        created_at = datetime.now() - timedelta(minutes=minutes_ago)

        cur.execute("""
            INSERT INTO pipeline_metrics
            (opportunity_id, phase, agent_name, duration_seconds, api_cost_usd,
             success, error_message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (opportunity_id, phase, agent_name, duration_seconds, api_cost_usd,
              success, error_message, created_at))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✓ Generated 20 test pipeline metrics entries")

if __name__ == "__main__":
    generate_test_metrics()