"""
RedditHarbor Pipeline-V4 Dashboard
Main entry point for multi-page Streamlit application
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="RedditHarbor Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    /* CueTimer brand colors */
    :root {
        --primary-color: #FF6B35;
        --secondary-color: #004E89;
        --accent-color: #F7B801;
    }

    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #004E89;
        margin-bottom: 1rem;
    }

    /* Metric cards */
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B35;
    }

    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        font-size: 0.875rem;
    }

    .score-high {
        background-color: #10b981;
        color: white;
    }

    .score-medium {
        background-color: #f59e0b;
        color: white;
    }

    .score-low {
        background-color: #ef4444;
        color: white;
    }

    /* Table styling */
    .dataframe {
        font-size: 0.9rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main page content
st.markdown('<h1 class="main-header">:chart_with_upwards_trend: RedditHarbor Dashboard</h1>', unsafe_allow_html=True)

st.markdown(
    """
    Welcome to the RedditHarbor Pipeline-V4 Dashboard. This tool helps you analyze and track
    high-scoring opportunities from Reddit data.

    ### Navigation
    Use the sidebar to navigate between pages:

    - **Overview** - View all high-scoring opportunities with key metrics
    - **Detailed View** - Deep dive into individual opportunity details
    - **Comparison** - Compare multiple opportunities side-by-side

    ### Quick Stats
    """
)

# Display quick stats from database
try:
    from sqlmodel import func, select

    from database import get_db_session
    from models.analysis import Opportunity

    with get_db_session() as session:
        # Total opportunities
        total_count = session.exec(
            select(func.count(Opportunity.id))
        ).one()

        # High-scoring opportunities (70+)
        high_score_count = session.exec(
            select(func.count(Opportunity.id)).where(Opportunity.final_score >= 70)
        ).one()

        # Average score
        avg_score = session.exec(
            select(func.avg(Opportunity.final_score))
        ).one() or 0.0

        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Total Opportunities",
                value=f"{total_count:,}",
                delta=None,
            )

        with col2:
            st.metric(
                label="High-Scoring (70+)",
                value=f"{high_score_count:,}",
                delta=f"{(high_score_count/total_count*100):.1f}%" if total_count > 0 else "0%",
            )

        with col3:
            st.metric(
                label="Average Score",
                value=f"{avg_score:.1f}",
                delta=None,
            )

        # Quarterly progress
        st.markdown("### Quarterly Progress")
        progress = min(high_score_count / 50, 1.0)
        st.progress(progress)
        st.caption(f"Target: 50 high-scoring opportunities | Current: {high_score_count} ({progress*100:.1f}%)")

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
    st.info("Make sure the database is configured correctly and contains data.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6c757d; font-size: 0.875rem;">
    RedditHarbor Pipeline-V4 | Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
