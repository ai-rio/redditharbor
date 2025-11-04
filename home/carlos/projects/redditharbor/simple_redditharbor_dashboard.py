#!/usr/bin/env python3
"""
Simple RedditHarbor Dashboard - Web Version
A basic web dashboard for Reddit data visualization
"""

import sys
import json
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class RedditHarborDashboard:
    def __init__(self):
        self.data = self.generate_demo_data("python", 50)

    def generate_demo_data(self, subreddit, limit):
        """Generate realistic demo Reddit data"""
        num_items = limit
        timestamps = pd.date_range('2024-01-01', periods=num_items, freq='H')

        # Subreddit-specific titles
        if subreddit == 'python':
            titles = [
                "Python 3.12 released with new pattern matching",
                "Django 5.0 brings major improvements",
                "Async Python best practices guide",
                "FastAPI vs Flask: Performance comparison",
                "Python type hints for better code quality"
            ]
        elif subreddit == 'technology':
            titles = [
                "AI breakthrough changes everything we know",
                "Quantum computing reaches new milestone",
                "5G deployment accelerates globally",
                "Cybersecurity threats in 2024",
                "Cloud computing trends and predictions"
            ]
        elif subreddit == 'programming':
            titles = [
                "Clean code principles every developer should know",
                "Git advanced workflows for teams",
                "Microservices architecture patterns",
                "Kubernetes deployment strategies",
                "API design best practices"
            ]
        else:  # startups
            titles = [
                "YC announces new batch of startups",
                "Series B funding rounds this week",
                "Startup failure rates analyzed",
                "Unicorn valuations face reality check",
                "Remote work startup success stories"
            ]

        # Create DataFrame
        data = pd.DataFrame({
            'id': range(1, num_items + 1),
            'title': np.random.choice(titles, num_items, replace=True),
            'score': np.random.randint(10, 1000, num_items),
            'num_comments': np.random.randint(1, 200, num_items),
            'created_utc': timestamps,
            'subreddit': subreddit
        })

        return data

    def get_html_page(self, subreddit='python', limit=50):
        """Generate HTML dashboard page"""
        # Generate data
        self.data = self.generate_demo_data(subreddit, limit)

        # Calculate statistics
        avg_score = self.data['score'].mean()
        avg_comments = self.data['num_comments'].mean()
        total_score = self.data['score'].sum()
        total_comments = self.data['num_comments'].sum()

        # Get top posts
        top_posts = self.data.nlargest(10, 'score')

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RedditHarbor Research Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        .header h1 {{
            color: #FF6B35;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .controls {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .control-group {{
            flex: 1;
            min-width: 200px;
        }}
        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }}
        .control-group select, .control-group input {{
            width: 100%;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        .stats {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        .stats h2 {{
            color: #004E89;
            margin-bottom: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #F7B801;
        }}
        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .stat-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }}
        .posts-table {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}
        .posts-table h2 {{
            color: #004E89;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .title {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .score {{
            font-weight: bold;
            color: #FF6B35;
        }}
        .refresh-btn {{
            background: #004E89;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 20px;
            font-size: 16px;
        }}
        .refresh-btn:hover {{
            background: #003d7a;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RedditHarbor Research Dashboard</h1>
            <p>Interactive Reddit data visualization for r/{subreddit}</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label for="subreddit">Subreddit:</label>
                <select id="subreddit" onchange="refreshDashboard()">
                    <option value="python" {'selected' if subreddit == 'python' else ''}>python</option>
                    <option value="technology" {'selected' if subreddit == 'technology' else ''}>technology</option>
                    <option value="programming" {'selected' if subreddit == 'programming' else ''}>programming</option>
                    <option value="startups" {'selected' if subreddit == 'startups' else ''}>startups</option>
                </select>
            </div>
            <div class="control-group">
                <label for="limit">Number of Posts:</label>
                <input type="number" id="limit" value="{limit}" min="10" max="100" step="10" onchange="refreshDashboard()">
            </div>
        </div>

        <div class="stats">
            <h2>📈 Summary Statistics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Average Score</h3>
                    <div class="value">{avg_score:.1f}</div>
                </div>
                <div class="stat-card">
                    <h3>Average Comments</h3>
                    <div class="value">{avg_comments:.1f}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Score</h3>
                    <div class="value">{total_score:,.0f}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Comments</h3>
                    <div class="value">{total_comments:,.0f}</div>
                </div>
            </div>
        </div>

        <div class="posts-table">
            <h2>📋 Top Posts (Showing {len(top_posts)} of {len(self.data)})</h2>
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Score</th>
                        <th>Comments</th>
                        <th>Posted</th>
                    </tr>
                </thead>
                <tbody>
                    {self.generate_table_rows(top_posts)}
                </tbody>
            </table>
        </div>

        <center>
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Data</button>
        </center>
    </div>

    <script>
        function refreshDashboard() {{
            const subreddit = document.getElementById('subreddit').value;
            const limit = parseInt(document.getElementById('limit').value);
            window.location.href = `?subreddit=${subreddit}&limit=${limit}`;
        }}
    </script>
</body>
</html>
        """
        return html

    def generate_table_rows(self, posts):
        """Generate HTML table rows from DataFrame"""
        rows = ""
        for _, post in posts.iterrows():
            posted_date = post['created_utc'].strftime('%Y-%m-%d %H:%M')
            rows += f"""
                    <tr>
                        <td class="title">{post['title']}</td>
                        <td class="score">{post['score']}</td>
                        <td>{post['num_comments']}</td>
                        <td>{posted_date}</td>
                    </tr>
            """
        return rows

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard

    def do_GET(self):
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        subreddit = params.get('subreddit', ['python'])[0]
        limit = int(params.get('limit', ['50'])[0])

        # Generate and serve HTML
        html = self.dashboard.get_html_page(subreddit, limit)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

def main():
    dashboard = RedditHarborDashboard()
    handler = DashboardHandler(dashboard)

    port = 8080
    with HTTPServer(('localhost', port), handler) as httpd:
        print(f"🚀 RedditHarbor Dashboard running at http://localhost:{port}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")

if __name__ == "__main__":
    main()