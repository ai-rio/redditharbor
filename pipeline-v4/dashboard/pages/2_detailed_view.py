"""
Detailed View Page - Deep dive into individual opportunity details
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import json

import streamlit as st
from sqlmodel import select

from database import get_db_session
from models.analysis import Opportunity

# Page configuration
st.set_page_config(
    page_title="Detailed View - RedditHarbor Dashboard",
    page_icon=":mag:",
    layout="wide",
)

# Header
st.title(":mag: Opportunity Detailed View")
st.markdown("Explore complete details of a single opportunity including all analysis fields.")


def load_opportunity_by_id(opp_id: int) -> dict | None:
    """Load a single opportunity by ID and convert to dict to avoid detached instance issues"""
    try:
        with get_db_session() as session:
            opp = session.exec(
                select(Opportunity).where(Opportunity.id == opp_id)
            ).first()

            if not opp:
                return None

            # Convert to dict while session is still active
            return {
                "id": opp.id,
                "submission_id": opp.submission_id,
                "subreddit": opp.subreddit,
                "title": opp.title,
                "wtp_score": opp.wtp_score,
                "final_score": opp.final_score,
                "confidence_score": opp.confidence_score,
                "trust_level": opp.trust_level,
                "analysis": opp.analysis,
                "metrics": opp.metrics,
                "created_at": opp.created_at,
                "updated_at": opp.updated_at,
            }
    except Exception as e:
        st.error(f"Error loading opportunity: {e}")
        return None


def load_all_opportunities() -> list[tuple[int, str, float]]:
    """Load all opportunities for selection dropdown"""
    try:
        with get_db_session() as session:
            opportunities = session.exec(
                select(Opportunity).order_by(Opportunity.final_score.desc())
            ).all()

            return [
                (
                    opp.id,
                    f"{opp.analysis.get('app_idea', {}).get('title', opp.title[:30])} (Score: {opp.final_score:.1f})",
                    opp.final_score,
                )
                for opp in opportunities
            ]
    except Exception as e:
        st.error(f"Error loading opportunities: {e}")
        return []


# Sidebar - Opportunity selection
st.sidebar.header("Select Opportunity")

# Load all opportunities
opportunities = load_all_opportunities()

if not opportunities:
    st.error("No opportunities found in the database.")
    st.stop()

# Filter options
show_high_scoring = st.sidebar.checkbox("Show only high-scoring (70+)", value=True)

if show_high_scoring:
    opportunities = [(id, name, score) for id, name, score in opportunities if score >= 70]

# Select opportunity
selected = st.sidebar.selectbox(
    "Choose an opportunity",
    options=opportunities,
    format_func=lambda x: x[1],
    help="Select an opportunity to view details",
)

opportunity_id = selected[0] if selected else None

# Load selected opportunity
if opportunity_id:
    opp = load_opportunity_by_id(opportunity_id)

    if not opp:
        st.error(f"Opportunity with ID {opportunity_id} not found.")
        st.stop()

    # Display opportunity details
    st.markdown(f"## {opp['analysis'].get('app_idea', {}).get('title', 'Untitled Opportunity')}")

    # Score badges
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score_color = "🟢" if opp['final_score'] >= 85 else "🟡" if opp['final_score'] >= 70 else "🔴"
        st.metric(
            label="Final Score",
            value=f"{score_color} {opp['final_score']:.1f}",
        )

    with col2:
        st.metric(
            label="WTP Score",
            value=f"{opp['wtp_score']:.1f}",
        )

    with col3:
        st.metric(
            label="Confidence",
            value=f"{opp['confidence_score']:.1f}",
        )

    with col4:
        trust_emoji = "🟢" if opp['trust_level'] == "HIGH" else "🟡" if opp['trust_level'] == "MEDIUM" else "🔴"
        st.metric(
            label="Trust Level",
            value=f"{trust_emoji} {opp['trust_level']}",
        )

    st.markdown("---")

    # Tab navigation for organized content
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["App Idea", "Metrics", "Analysis", "Pain Points", "Raw Data"]
    )

    # Tab 1: App Idea
    with tab1:
        st.markdown("### App Idea Details")

        app_idea = opp['analysis'].get("app_idea", {})

        if app_idea:
            # App title
            st.markdown(f"**Title:** {app_idea.get('title', 'N/A')}")

            # App concept
            st.markdown("**Concept:**")
            st.info(app_idea.get("app_concept", "N/A"))

            # Problem statement
            st.markdown("**Problem Statement:**")
            st.warning(app_idea.get("problem_statement", "N/A"))

            # Core functions
            st.markdown("**Core Functions:**")
            core_functions = app_idea.get("core_functions", [])
            if core_functions:
                for i, func in enumerate(core_functions, 1):
                    st.markdown(f"{i}. {func}")

                # Compliance check
                func_count = len(core_functions)
                if 1 <= func_count <= 3:
                    st.success(f"✓ Compliant: {func_count} core functions (within 1-3 range)")
                else:
                    st.error(f"✗ Non-compliant: {func_count} core functions (should be 1-3)")
            else:
                st.caption("No core functions defined")

            # Target audience
            st.markdown("**Target Audience:**")
            st.markdown(app_idea.get("target_audience", "N/A"))
        else:
            st.warning("No app idea details available.")

    # Tab 2: Metrics
    with tab2:
        st.markdown("### Market Metrics")

        metrics = opp['metrics']

        if metrics:
            # Display metrics as a grid
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Market Demand",
                    value=f"{metrics.get('market_demand', 0):.1f}",
                    help="Score indicating market demand (0-100)",
                )
                st.metric(
                    label="Pain Intensity",
                    value=f"{metrics.get('pain_intensity', 0):.1f}",
                    help="Intensity of the pain point (0-100)",
                )
                st.metric(
                    label="Monetization Potential",
                    value=f"{metrics.get('monetization_potential', 0):.1f}",
                    help="Potential for monetization (0-100)",
                )

            with col2:
                st.metric(
                    label="Technical Feasibility",
                    value=f"{metrics.get('technical_feasibility', 0):.1f}",
                    help="Technical feasibility score (0-100)",
                )
                st.metric(
                    label="Competition Level",
                    value=f"{metrics.get('competition_level', 0):.1f}",
                    help="Competition level (0=high, 100=low)",
                )

            # Metrics visualization
            st.markdown("#### Metrics Overview")
            import pandas as pd

            metrics_df = pd.DataFrame(
                [
                    {"Metric": "Market Demand", "Score": metrics.get("market_demand", 0)},
                    {"Metric": "Pain Intensity", "Score": metrics.get("pain_intensity", 0)},
                    {"Metric": "Monetization", "Score": metrics.get("monetization_potential", 0)},
                    {"Metric": "Technical Feasibility", "Score": metrics.get("technical_feasibility", 0)},
                    {"Metric": "Competition", "Score": metrics.get("competition_level", 0)},
                ]
            )

            st.bar_chart(metrics_df.set_index("Metric"))
        else:
            st.warning("No metrics data available.")

    # Tab 3: Analysis
    with tab3:
        st.markdown("### Analysis Details")

        # Reddit source info
        st.markdown("**Source Information:**")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"- **Subreddit:** r/{opp['subreddit']}")
            st.markdown(f"- **Submission ID:** `{opp['submission_id']}`")

        with col2:
            st.markdown(f"- **Created:** {opp['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"- **Updated:** {opp['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")

        st.markdown("**Submission Title:**")
        st.info(opp['title'])

        # Opportunity summary
        if "opportunity_summary" in opp['analysis']:
            st.markdown("**Opportunity Summary:**")
            st.success(opp['analysis']["opportunity_summary"])

        # Content quality
        if "content_quality_score" in opp['analysis']:
            st.markdown("**Content Quality:**")
            quality_score = opp['analysis']["content_quality_score"]
            st.progress(quality_score / 100)
            st.caption(f"Score: {quality_score:.1f}/100")

        # Spam analysis
        spam_analysis = opp['analysis'].get("spam_analysis", {})
        if spam_analysis:
            st.markdown("**Spam Analysis:**")
            is_spam = spam_analysis.get("is_spam", False)

            if is_spam:
                st.error(f"⚠ Flagged as spam")
                spam_indicators = spam_analysis.get("spam_indicators", [])
                if spam_indicators:
                    st.markdown("**Spam Indicators:**")
                    for indicator in spam_indicators:
                        st.markdown(f"- {indicator}")
            else:
                st.success("✓ Not flagged as spam")

    # Tab 4: Pain Points
    with tab4:
        st.markdown("### Identified Pain Points")

        pain_points = opp['analysis'].get("pain_points", [])

        if pain_points:
            for i, pain in enumerate(pain_points, 1):
                st.markdown(f"**{i}. Pain Point**")
                st.info(pain)
                st.markdown("")
        else:
            st.warning("No pain points identified.")

    # Tab 5: Raw Data
    with tab5:
        st.markdown("### Raw JSON Data")

        st.markdown("**Analysis Data:**")
        st.json(opp['analysis'])

        st.markdown("**Metrics Data:**")
        st.json(opp['metrics'])

        # Export opportunity as JSON
        st.markdown("### Export")

        opportunity_dict = {
            "id": opp['id'],
            "submission_id": opp['submission_id'],
            "subreddit": opp['subreddit'],
            "title": opp['title'],
            "wtp_score": opp['wtp_score'],
            "final_score": opp['final_score'],
            "confidence_score": opp['confidence_score'],
            "trust_level": opp['trust_level'],
            "analysis": opp['analysis'],
            "metrics": opp['metrics'],
            "created_at": opp['created_at'].isoformat(),
            "updated_at": opp['updated_at'].isoformat(),
        }

        json_str = json.dumps(opportunity_dict, indent=2)

        st.download_button(
            label="Download Opportunity as JSON",
            data=json_str,
            file_name=f"opportunity_{opp['id']}.json",
            mime="application/json",
        )

    # Navigation hint
    st.markdown("---")
    st.info("Navigate to the **Comparison** page to compare this opportunity with others side-by-side.")

else:
    st.warning("Please select an opportunity from the sidebar.")
