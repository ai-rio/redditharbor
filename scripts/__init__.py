"""
RedditHarbor Scripts Package

Contains executable scripts for research, demos, and certification.
"""

# Import main functions for easy access
from .certification import certify_data_collection as run_certification
from .demo import demo_tech_trends_research as run_demo
from .research import run_research_project as research_main

__all__ = ['research_main', 'run_certification', 'run_demo']
