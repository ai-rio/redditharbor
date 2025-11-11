# test_research_dashboard.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from marimo_notebooks.research_dashboard import ResearchDashboard


def test_dashboard_initialization():
    dashboard = ResearchDashboard()
    assert dashboard.app is not None
    assert dashboard.database_connector is not None
    assert dashboard.ui_components is not None
