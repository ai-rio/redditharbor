"""
RedditHarbor Scripts Package

Contains executable scripts for research, demos, and certification.
"""

# Import main functions for easy access (with fallback for missing modules)
try:
    from .research import run_research_project as research_main
except ImportError:
    research_main = None

try:
    from .certification import certify_data_collection as run_certification
except ImportError:
    run_certification = None

try:
    from .demo import demo_tech_trends_research as run_demo
except ImportError:
    run_demo = None

__all__ = ["research_main", "run_certification", "run_demo"]
