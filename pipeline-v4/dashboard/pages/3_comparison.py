"""
Comparison Page - Side-by-side comparison of multiple opportunities
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import pandas as pd
import streamlit as st
from sqlmodel import select

from database import get_db_session
from models.analysis import Opportunity

# Page configuration
st.set_page_config(
    page_title="Comparison - RedditHarbor Dashboard",
    page_icon=":balance_scale:",
    layout="wide",
)

# Header
st.title(":balance_scale: Opportunity Comparison")
st.markdown("Compare 2-3 opportunities side-by-side to identify the best options.")


def load_all_opportunities() -> list[tuple[int, str, float]]:
    """Load all opportunities for selection"""
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


def load_opportunities_by_ids(ids: list[int]) -> list[dict]:
    """Load multiple opportunities by their IDs and convert to dicts"""
    try:
        with get_db_session() as session:
            opportunities = session.exec(
                select(Opportunity).where(Opportunity.id.in_(ids))
            ).all()

            # Convert to dicts while session is active
            opp_dicts = []
            for opp in opportunities:
                opp_dicts.append({
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
                })

            # Sort by the order of input ids
            sorted_opps = sorted(opp_dicts, key=lambda x: ids.index(x["id"]))
            return sorted_opps
    except Exception as e:
        st.error(f"Error loading opportunities: {e}")
        return []


def compare_field(values: list, label: str = ""):
    """Helper to highlight differences in field values"""
    unique_values = len(set(values))
    if unique_values > 1:
        return f"{label} ⚠️"  # Different values
    else:
        return f"{label} ✓"  # Same values


# Sidebar - Opportunity selection
st.sidebar.header("Select Opportunities to Compare")

# Load all opportunities
all_opportunities = load_all_opportunities()

if not all_opportunities:
    st.error("No opportunities found in the database.")
    st.stop()

# Filter options
show_high_scoring = st.sidebar.checkbox("Show only high-scoring (70+)", value=True)

if show_high_scoring:
    filtered_opportunities = [
        (id, name, score) for id, name, score in all_opportunities if score >= 70
    ]
else:
    filtered_opportunities = all_opportunities

# Multi-select for opportunities (limit to 3)
st.sidebar.markdown("Select 2-3 opportunities to compare:")

selected_opportunities = st.sidebar.multiselect(
    "Opportunities",
    options=filtered_opportunities,
    format_func=lambda x: x[1],
    max_selections=3,
    help="Select 2-3 opportunities for side-by-side comparison",
)

# Extract IDs
selected_ids = [opp[0] for opp in selected_opportunities]

# Validate selection
if len(selected_ids) < 2:
    st.warning("Please select at least 2 opportunities to compare.")
    st.info("Use the sidebar to select opportunities from the list.")
    st.stop()

# Load selected opportunities
opportunities = load_opportunities_by_ids(selected_ids)

if not opportunities:
    st.error("Could not load selected opportunities.")
    st.stop()

# Display comparison
st.markdown(f"### Comparing {len(opportunities)} Opportunities")

# Create columns for side-by-side comparison
cols = st.columns(len(opportunities))

# Helper function to get nested values safely
def get_nested(data: dict, *keys, default="N/A"):
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data if data else default


# 1. Header section with scores
for idx, (col, opp) in enumerate(zip(cols, opportunities)):
    with col:
        st.markdown(f"#### Opportunity {idx + 1}")
        st.markdown(f"**ID:** {opp['id']}")

        # Score badges
        score_color = "🟢" if opp['final_score'] >= 85 else "🟡" if opp['final_score'] >= 70 else "🔴"
        st.metric(
            label="Final Score",
            value=f"{opp['final_score']:.1f}",
            delta=f"{score_color}",
        )

        st.metric(label="WTP Score", value=f"{opp['wtp_score']:.1f}")

        trust_emoji = "🟢" if opp['trust_level'] == "HIGH" else "🟡" if opp['trust_level'] == "MEDIUM" else "🔴"
        st.metric(label="Trust", value=f"{trust_emoji} {opp['trust_level']}")

st.markdown("---")

# 2. App Idea Comparison
st.markdown("### App Idea Comparison")

for idx, (col, opp) in enumerate(zip(cols, opportunities)):
    with col:
        app_idea = opp['analysis'].get("app_idea", {})

        st.markdown(f"**Title:**")
        st.info(get_nested(app_idea, "title"))

        st.markdown(f"**Concept:**")
        concept = get_nested(app_idea, "app_concept")
        st.caption(concept[:150] + "..." if len(str(concept)) > 150 else concept)

        st.markdown(f"**Target Audience:**")
        audience = get_nested(app_idea, "target_audience")
        st.caption(audience[:100] + "..." if len(str(audience)) > 100 else audience)

st.markdown("---")

# 3. Core Functions Comparison
st.markdown("### Core Functions Comparison")

# Check compliance
function_counts = []
for opp in opportunities:
    core_functions = get_nested(opp['analysis'], "app_idea", "core_functions", default=[])
    function_counts.append(len(core_functions) if isinstance(core_functions, list) else 0)

# Highlight compliance differences
compliance_status = [1 <= count <= 3 for count in function_counts]
if all(compliance_status):
    st.success("✓ All opportunities are compliant (1-3 functions)")
elif any(compliance_status):
    st.warning("⚠️ Some opportunities are not compliant with the 1-3 function rule")
else:
    st.error("✗ None of the opportunities are compliant")

for idx, (col, opp) in enumerate(zip(cols, opportunities)):
    with col:
        core_functions = get_nested(opp['analysis'], "app_idea", "core_functions", default=[])

        if isinstance(core_functions, list) and core_functions:
            func_count = len(core_functions)
            compliant = 1 <= func_count <= 3

            if compliant:
                st.success(f"✓ {func_count} functions")
            else:
                st.error(f"✗ {func_count} functions")

            for i, func in enumerate(core_functions, 1):
                st.markdown(f"{i}. {func}")
        else:
            st.warning("No functions defined")

st.markdown("---")

# 4. Metrics Comparison
st.markdown("### Market Metrics Comparison")

# Create comparison table for metrics
metrics_data = []
metric_names = [
    "market_demand",
    "pain_intensity",
    "monetization_potential",
    "technical_feasibility",
    "competition_level",
]

for metric in metric_names:
    row = {"Metric": metric.replace("_", " ").title()}
    for idx, opp in enumerate(opportunities):
        value = opp['metrics'].get(metric, 0)
        row[f"Opp {idx + 1}"] = f"{value:.1f}"
    metrics_data.append(row)

metrics_df = pd.DataFrame(metrics_data)

# Display as table
st.dataframe(metrics_df, hide_index=True, use_container_width=True)

# Visualize metrics comparison
st.markdown("#### Visual Comparison")

# Prepare data for chart
chart_data = {}
for idx, opp in enumerate(opportunities):
    app_title = get_nested(opp['analysis'], "app_idea", "title", default=f"Opp {idx + 1}")
    chart_data[app_title] = [
        opp['metrics'].get(metric, 0) for metric in metric_names
    ]

chart_df = pd.DataFrame(chart_data, index=[m.replace("_", " ").title() for m in metric_names])
st.bar_chart(chart_df)

st.markdown("---")

# 5. Pain Points Comparison
st.markdown("### Pain Points Comparison")

for idx, (col, opp) in enumerate(zip(cols, opportunities)):
    with col:
        pain_points = get_nested(opp['analysis'], "pain_points", default=[])

        if isinstance(pain_points, list) and pain_points:
            st.markdown(f"**{len(pain_points)} Pain Points:**")
            for i, pain in enumerate(pain_points[:3], 1):  # Show first 3
                st.markdown(f"{i}. {pain[:100]}...")
        else:
            st.caption("No pain points identified")

st.markdown("---")

# 6. Source Information
st.markdown("### Source Information")

for idx, (col, opp) in enumerate(zip(cols, opportunities)):
    with col:
        st.markdown(f"**Subreddit:** r/{opp['subreddit']}")
        st.markdown(f"**Submission ID:** `{opp['submission_id']}`")
        st.markdown(f"**Created:** {opp['created_at'].strftime('%Y-%m-%d')}")

st.markdown("---")

# 7. Summary Comparison Table
st.markdown("### Summary Comparison")

summary_data = []
for idx, opp in enumerate(opportunities):
    app_title = get_nested(opp['analysis'], "app_idea", "title", default=f"Opportunity {idx + 1}")
    core_functions = get_nested(opp['analysis'], "app_idea", "core_functions", default=[])
    func_count = len(core_functions) if isinstance(core_functions, list) else 0

    summary_data.append(
        {
            "Opportunity": app_title[:30] + "..." if len(app_title) > 30 else app_title,
            "Final Score": f"{opp['final_score']:.1f}",
            "WTP Score": f"{opp['wtp_score']:.1f}",
            "Functions": func_count,
            "Compliant": "✓" if 1 <= func_count <= 3 else "✗",
            "Trust": opp['trust_level'],
            "Subreddit": opp['subreddit'],
        }
    )

summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, hide_index=True, use_container_width=True)

# 8. Recommendation
st.markdown("### Recommendation")

# Find highest scoring opportunity
highest_score_opp = max(opportunities, key=lambda x: x['final_score'])
highest_idx = opportunities.index(highest_score_opp)

# Check compliance
highest_score_compliant = (
    1 <= len(get_nested(highest_score_opp['analysis'], "app_idea", "core_functions", default=[])) <= 3
)

if highest_score_compliant:
    st.success(
        f"🏆 **Recommended:** Opportunity {highest_idx + 1} - "
        f"{get_nested(highest_score_opp['analysis'], 'app_idea', 'title')} "
        f"(Score: {highest_score_opp['final_score']:.1f}, Compliant)"
    )
else:
    # Find highest compliant opportunity
    compliant_opps = [
        opp for opp in opportunities
        if 1 <= len(get_nested(opp['analysis'], "app_idea", "core_functions", default=[])) <= 3
    ]

    if compliant_opps:
        best_compliant = max(compliant_opps, key=lambda x: x['final_score'])
        compliant_idx = opportunities.index(best_compliant)
        st.warning(
            f"⚠️ Highest score is non-compliant. "
            f"Best compliant option: Opportunity {compliant_idx + 1} - "
            f"{get_nested(best_compliant['analysis'], 'app_idea', 'title')} "
            f"(Score: {best_compliant['final_score']:.1f})"
        )
    else:
        st.error("⚠️ None of the selected opportunities are compliant with the 1-3 function rule.")

# Export comparison
st.markdown("---")
st.markdown("### Export Comparison")

col1, col2 = st.columns(2)

with col1:
    csv = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Summary as CSV",
        data=csv,
        file_name="comparison_summary.csv",
        mime="text/csv",
    )

with col2:
    # Export detailed comparison as JSON
    comparison_dict = {
        "comparison_date": pd.Timestamp.now().isoformat(),
        "opportunities": [
            {
                "id": opp['id'],
                "title": get_nested(opp['analysis'], "app_idea", "title"),
                "final_score": opp['final_score'],
                "wtp_score": opp['wtp_score'],
                "trust_level": opp['trust_level'],
                "subreddit": opp['subreddit'],
                "core_functions": get_nested(opp['analysis'], "app_idea", "core_functions", default=[]),
                "metrics": opp['metrics'],
            }
            for opp in opportunities
        ],
    }

    import json
    json_str = json.dumps(comparison_dict, indent=2)

    st.download_button(
        label="Download Detailed Comparison as JSON",
        data=json_str,
        file_name="comparison_detailed.json",
        mime="application/json",
    )

# Navigation hint
st.markdown("---")
st.info("Navigate to the **Detailed View** page to explore individual opportunities in depth.")
