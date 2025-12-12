"""
Overview Page - High-scoring opportunities table and metrics
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import pandas as pd
import streamlit as st
from sqlmodel import func, select

from database import get_db_session
from models.analysis import Opportunity

# Page configuration
st.set_page_config(
    page_title="Overview - RedditHarbor Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

# Header
st.title(":bar_chart: Opportunities Overview")
st.markdown("View and filter all high-scoring opportunities from the pipeline.")

# Sidebar filters
st.sidebar.header("Filters")

# Score range filter
min_score = st.sidebar.slider(
    "Minimum Score",
    min_value=0,
    max_value=100,
    value=70,
    step=5,
    help="Filter opportunities by minimum final score",
)

max_score = st.sidebar.slider(
    "Maximum Score",
    min_value=min_score,
    max_value=100,
    value=100,
    step=5,
    help="Filter opportunities by maximum final score",
)

# Function count filter
function_counts = st.sidebar.multiselect(
    "Core Functions Count",
    options=[1, 2, 3],
    default=[1, 2, 3],
    help="Filter by number of core functions (1-3 is compliant)",
)

# Subreddit filter (will be populated from database)
try:
    with get_db_session() as session:
        # Get unique subreddits
        subreddits = session.exec(
            select(Opportunity.subreddit)
            .distinct()
            .order_by(Opportunity.subreddit)
        ).all()

        selected_subreddits = st.sidebar.multiselect(
            "Subreddits",
            options=subreddits,
            default=subreddits,
            help="Filter by subreddit",
        )
except Exception as e:
    st.sidebar.error(f"Error loading subreddits: {e}")
    selected_subreddits = []

# Date range filter
st.sidebar.markdown("### Date Range")
use_date_filter = st.sidebar.checkbox("Enable date filter", value=False)

if use_date_filter:
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")
else:
    start_date = None
    end_date = None


def get_core_functions_count(analysis: dict) -> int:
    """Extract core functions count from analysis JSON"""
    try:
        app_idea = analysis.get("app_idea", {})
        core_functions = app_idea.get("core_functions", [])
        return len(core_functions)
    except Exception:
        return 0


def load_opportunities(
    min_score: float,
    max_score: float,
    subreddits: list[str],
    function_counts: list[int],
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    """Load opportunities from database with filters"""
    try:
        with get_db_session() as session:
            # Build query
            query = select(Opportunity).where(
                Opportunity.final_score >= min_score,
                Opportunity.final_score <= max_score,
            )

            # Add subreddit filter
            if subreddits:
                query = query.where(Opportunity.subreddit.in_(subreddits))

            # Add date filter
            if start_date and end_date:
                query = query.where(
                    Opportunity.created_at >= start_date,
                    Opportunity.created_at <= end_date,
                )

            # Execute query
            opportunities = session.exec(query).all()

            # Convert to DataFrame
            data = []
            for opp in opportunities:
                # Get core functions count
                func_count = get_core_functions_count(opp.analysis)

                # Apply function count filter
                if func_count not in function_counts:
                    continue

                # Get app title from analysis
                app_title = opp.analysis.get("app_idea", {}).get("title", "N/A")

                data.append(
                    {
                        "ID": opp.id,
                        "App Title": app_title,
                        "Submission Title": opp.title[:50] + "..." if len(opp.title) > 50 else opp.title,
                        "Subreddit": opp.subreddit,
                        "Final Score": round(opp.final_score, 1),
                        "WTP Score": round(opp.wtp_score, 1),
                        "Functions": func_count,
                        "Trust Level": opp.trust_level,
                        "Created": opp.created_at.strftime("%Y-%m-%d"),
                    }
                )

            return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Error loading opportunities: {e}")
        return pd.DataFrame()


# Load data
df = load_opportunities(
    min_score=min_score,
    max_score=max_score,
    subreddits=selected_subreddits,
    function_counts=function_counts,
    start_date=start_date,
    end_date=end_date,
)

# Display metrics
if not df.empty:
    st.markdown("### Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Opportunities",
            value=len(df),
        )

    with col2:
        compliant = len(df[df["Functions"].isin([1, 2, 3])])
        compliance_rate = (compliant / len(df) * 100) if len(df) > 0 else 0
        st.metric(
            label="Function Compliance",
            value=f"{compliance_rate:.1f}%",
            help="Percentage with 1-3 core functions",
        )

    with col3:
        avg_score = df["Final Score"].mean()
        st.metric(
            label="Average Score",
            value=f"{avg_score:.1f}",
        )

    with col4:
        avg_wtp = df["WTP Score"].mean()
        st.metric(
            label="Average WTP",
            value=f"{avg_wtp:.1f}",
        )

    # Score distribution
    st.markdown("### Score Distribution")

    # Create score bins
    bins = [0, 50, 70, 85, 100]
    labels = ["0-50", "50-70", "70-85", "85-100"]
    df["Score Range"] = pd.cut(df["Final Score"], bins=bins, labels=labels, include_lowest=True)

    score_dist = df["Score Range"].value_counts().sort_index()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.dataframe(
            score_dist.reset_index().rename(columns={"Score Range": "Range", "count": "Count"}),
            hide_index=True,
            use_container_width=True,
        )

    with col2:
        st.bar_chart(score_dist)

    # Opportunities table
    st.markdown("### Opportunities Table")
    st.caption(f"Showing {len(df)} opportunities")

    # Add sorting options
    sort_col = st.selectbox(
        "Sort by",
        options=["Final Score", "WTP Score", "Created", "Subreddit"],
        index=0,
    )

    sort_order = st.radio(
        "Order",
        options=["Descending", "Ascending"],
        horizontal=True,
        index=0,
    )

    # Sort dataframe
    df_sorted = df.sort_values(
        by=sort_col,
        ascending=(sort_order == "Ascending"),
    )

    # Style the dataframe
    def style_score(val):
        """Color code scores"""
        if val >= 85:
            return "background-color: #10b981; color: white;"
        elif val >= 70:
            return "background-color: #f59e0b; color: white;"
        else:
            return "background-color: #ef4444; color: white;"

    styled_df = df_sorted.style.applymap(
        style_score,
        subset=["Final Score", "WTP Score"],
    )

    st.dataframe(
        styled_df,
        hide_index=True,
        use_container_width=True,
        height=400,
    )

    # Export functionality
    st.markdown("### Export Data")

    col1, col2 = st.columns(2)

    with col1:
        csv = df_sorted.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="opportunities.csv",
            mime="text/csv",
        )

    with col2:
        json = df_sorted.to_json(orient="records", indent=2)
        st.download_button(
            label="Download as JSON",
            data=json,
            file_name="opportunities.json",
            mime="application/json",
        )

    # Link to detailed view
    st.markdown("---")
    st.info("Click on an opportunity ID and navigate to the **Detailed View** page to see full details.")

else:
    st.warning("No opportunities found matching your filters. Try adjusting the criteria.")

# Footer
st.markdown("---")
st.caption("Use the sidebar to adjust filters and refine your search.")
