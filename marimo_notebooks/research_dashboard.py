# marimo_notebooks/research_dashboard.py
import marimo as mo
import pandas as pd
import altair as alt
from .utils import DatabaseConnector
from .config import MarimoConfig

class ResearchDashboard:
    """Main research dashboard for RedditHarbor data visualization"""

    def __init__(self):
        self.config = MarimoConfig()
        self.database_connector = DatabaseConnector()
        self.app = mo.App(app_title="RedditHarbor Research Dashboard")
        self.ui_components = {}
        self._setup_ui_components()

    def _setup_ui_components(self):
        """Setup UI components for the dashboard"""
        # Subreddit selector
        self.ui_components['subreddit'] = mo.ui.dropdown(
            options=['python', 'technology', 'programming', 'startups'],
            value='python',
            label='Select Subreddit'
        )

        # Data type selector
        self.ui_components['data_type'] = mo.ui.dropdown(
            options=['submissions', 'comments', 'both'],
            value='submissions',
            label='Data Type'
        )

        # Date range selector
        self.ui_components['date_range'] = mo.ui.date_range(
            label='Date Range'
        )

    def create_notebook(self):
        """Create the Marimo notebook structure"""
        with self.app.setup:
            import marimo as mo
            import pandas as pd
            import altair as alt
            from datetime import datetime

        @self.app.cell
        def load_data(subreddit, data_type, date_range):
            """Load Reddit data based on selections"""
            # Basic query template
            if data_type == 'submissions':
                query = f"SELECT * FROM submission WHERE subreddit = '{subreddit}'"
            elif data_type == 'comments':
                query = f"SELECT * FROM comment WHERE subreddit = '{subreddit}'"
            else:
                query = f"SELECT * FROM submission WHERE subreddit = '{subreddit}' UNION ALL SELECT * FROM comment WHERE subreddit = '{subreddit}'"

            data = self.database_connector.execute_query(query)
            return data

        @self.app.cell
        def create_visualization(data):
            """Create data visualization"""
            if len(data) > 0:
                # Create basic chart
                chart = alt.Chart(data).mark_bar().encode(
                    x='count()',
                    y=alt.Y('subreddit:N', title='Subreddit')
                ).properties(
                    title=f'Analysis Results ({len(data)} items)'
                )
                return mo.altair(chart)
            else:
                return mo.md("No data available for current selection")

        return self.app