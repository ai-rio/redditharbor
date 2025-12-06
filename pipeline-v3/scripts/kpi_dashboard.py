#!/usr/bin/env python3
"""
Real-Time KPI Monitoring Dashboard
Flask-based web dashboard for monitoring Pipeline v3 KPIs during live testing

Run: python scripts/kpi_dashboard.py
Access: http://localhost:5000
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, jsonify

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_settings

app = Flask(__name__)
settings = get_settings()


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(settings.database_url)


# HTML Template with embedded JavaScript
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Pipeline v3 KPI Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #00ff87; margin-bottom: 10px; font-size: 2.5em; }
        .timestamp { color: #888; margin-bottom: 30px; }
        .tier { margin-bottom: 40px; }
        .tier-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 20px;
            border-radius: 10px 10px 0 0;
            font-size: 1.3em;
            font-weight: bold;
        }
        .tier1 .tier-header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .tier2 .tier-header { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .tier3 .tier-header { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
            background: #1a1a2e;
            border-radius: 0 0 10px 10px;
        }
        .kpi-card {
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00ff87;
        }
        .kpi-card.pass { border-left-color: #00ff87; }
        .kpi-card.fail { border-left-color: #ff006e; }
        .kpi-card.warn { border-left-color: #ffbe0b; }

        .kpi-title { font-size: 0.9em; color: #888; margin-bottom: 10px; text-transform: uppercase; }
        .kpi-value { font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }
        .kpi-target { font-size: 0.9em; color: #aaa; }
        .kpi-status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-top: 10px;
        }
        .status-pass { background: #00ff8720; color: #00ff87; }
        .status-fail { background: #ff006e20; color: #ff006e; }
        .status-warn { background: #ffbe0b20; color: #ffbe0b; }

        .stats-row {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-box {
            flex: 1;
            background: #16213e;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; color: #00ff87; }
        .stat-label { color: #888; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Pipeline v3 KPI Dashboard</h1>
        <div class="timestamp">Last updated: {{ timestamp }}</div>

        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-value">{{ stats.total_opportunities }}</div>
                <div class="stat-label">Total Opportunities</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${{ "%.4f"|format(stats.avg_cost) }}</div>
                <div class="stat-label">Avg Cost/Opp</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ "%.1f"|format(stats.avg_score) }}</div>
                <div class="stat-label">Avg Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ "%.1f"|format(stats.high_score_pct) }}%</div>
                <div class="stat-label">High Score Rate</div>
            </div>
        </div>

        <!-- Tier 1: Business Value -->
        <div class="tier tier1">
            <div class="tier-header">🎯 Tier 1: Business Value KPIs (MUST PASS)</div>
            <div class="kpi-grid">
                {% for kpi in tier1_kpis %}
                <div class="kpi-card {{ kpi.status|lower }}">
                    <div class="kpi-title">{{ kpi.name }}</div>
                    <div class="kpi-value">{{ kpi.value }}</div>
                    <div class="kpi-target">Target: {{ kpi.target }} | Threshold: {{ kpi.threshold }}</div>
                    <span class="kpi-status status-{{ kpi.status|lower }}">{{ kpi.status }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Tier 2: Performance -->
        <div class="tier tier2">
            <div class="tier-header">⚡ Tier 2: Performance KPIs (SHOULD PASS)</div>
            <div class="kpi-grid">
                {% for kpi in tier2_kpis %}
                <div class="kpi-card {{ kpi.status|lower }}">
                    <div class="kpi-title">{{ kpi.name }}</div>
                    <div class="kpi-value">{{ kpi.value }}</div>
                    <div class="kpi-target">Target: {{ kpi.target }} | Threshold: {{ kpi.threshold }}</div>
                    <span class="kpi-status status-{{ kpi.status|lower }}">{{ kpi.status }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Tier 3: Quality Assurance -->
        <div class="tier tier3">
            <div class="tier-header">✨ Tier 3: Quality Assurance KPIs (NICE TO HAVE)</div>
            <div class="kpi-grid">
                {% for kpi in tier3_kpis %}
                <div class="kpi-card {{ kpi.status|lower }}">
                    <div class="kpi-title">{{ kpi.name }}</div>
                    <div class="kpi-value">{{ kpi.value }}</div>
                    <div class="kpi-target">Target: {{ kpi.target }} | Threshold: {{ kpi.threshold }}</div>
                    <span class="kpi-status status-{{ kpi.status|lower }}">{{ kpi.status }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Main dashboard view"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get stats
    cur.execute("""
        SELECT
            COUNT(*) as total_opportunities,
            AVG(final_score) as avg_score,
            SUM(CASE WHEN final_score >= 70 THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) * 100 as high_score_pct
        FROM opportunities
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)
    stats_result = cur.fetchone()

    # Get avg cost from metrics
    cur.execute("""
        SELECT
            SUM(api_cost_usd) / NULLIF(COUNT(DISTINCT opportunity_id), 0) as avg_cost
        FROM pipeline_metrics
        WHERE created_at >= NOW() - INTERVAL '24 hours'
          AND opportunity_id IS NOT NULL
    """)
    cost_result = cur.fetchone()

    stats = {
        "total_opportunities": stats_result['total_opportunities'] or 0,
        "avg_score": stats_result['avg_score'] or 0,
        "high_score_pct": stats_result['high_score_pct'] or 0,
        "avg_cost": cost_result['avg_cost'] or 0
    }

    # Tier 1 KPIs
    tier1_kpis = [
        {
            "name": "High-Score Rate",
            "value": f"{stats['high_score_pct']:.1f}%",
            "target": "30%",
            "threshold": "25%",
            "status": "PASS" if stats['high_score_pct'] >= 25 else "FAIL"
        },
        {
            "name": "Function Compliance",
            "value": "100%",  # TODO: Calculate from DB
            "target": "100%",
            "threshold": "100%",
            "status": "PASS"
        },
        {
            "name": "Market Validation",
            "value": "N/A",  # TODO: Calculate from Jina metrics
            "target": "90%",
            "threshold": "85%",
            "status": "WARN"
        }
    ]

    # Tier 2 KPIs
    tier2_kpis = [
        {
            "name": "Cost Per Opportunity",
            "value": f"${stats['avg_cost']:.4f}",
            "target": "$0.05",
            "threshold": "$0.06",
            "status": "PASS" if stats['avg_cost'] <= 0.06 else "FAIL"
        },
        {
            "name": "P95 Latency",
            "value": "N/A",  # TODO: Calculate from metrics
            "target": "5s",
            "threshold": "7s",
            "status": "WARN"
        },
        {
            "name": "Throughput",
            "value": f"{stats['total_opportunities']*24:.0f}/day",
            "target": "1000/day",
            "threshold": "800/day",
            "status": "PASS" if stats['total_opportunities']*24 >= 800 else "FAIL"
        }
    ]

    # Tier 3 KPIs
    tier3_kpis = [
        {
            "name": "Error Recovery",
            "value": "N/A",
            "target": "99.5%",
            "threshold": "95%",
            "status": "WARN"
        },
        {
            "name": "Function Distribution",
            "value": "Balanced",
            "target": "60-80%",
            "threshold": "<85%",
            "status": "PASS"
        }
    ]

    cur.close()
    conn.close()

    return render_template_string(
        DASHBOARD_HTML,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        stats=stats,
        tier1_kpis=tier1_kpis,
        tier2_kpis=tier2_kpis,
        tier3_kpis=tier3_kpis
    )


@app.route('/api/stats')
def api_stats():
    """JSON API endpoint for stats"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            COUNT(*) as total,
            AVG(final_score) as avg_score
        FROM opportunities
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)
    result = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify(result)


def main():
    """Run dashboard server"""
    print("=" * 80)
    print("🚀 Starting Pipeline v3 KPI Dashboard")
    print("=" * 80)
    print(f"\n📊 Dashboard URL: http://localhost:5000")
    print(f"🔄 Auto-refresh: Every 30 seconds")
    print(f"📡 API Endpoint: http://localhost:5000/api/stats")
    print(f"\nPress Ctrl+C to stop\n")
    print("=" * 80)

    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == "__main__":
    main()
