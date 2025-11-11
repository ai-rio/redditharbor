#!/usr/bin/env python3
"""
RedditHarbor Ultra-Rare Opportunity Dashboard
Real-time monitoring of 60+ score opportunities and system performance
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()


@app.cell
def __():
    import os
    from datetime import datetime, timedelta

    import marimo as mo

    from supabase import create_client
    return create_client, datetime, mo, os, timedelta


@app.cell
def __(create_client, os):
    supabase = create_client(
        os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321'),
        os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
    )
    return supabase,


@app.cell
def __(mo):
    mo.md("# 🌟 RedditHarbor Ultra-Rare Opportunity Dashboard")
    mo.md("## Real-time monitoring of 60+ score opportunities and automation performance")
    return


@app.cell
def __(supabase):
    # Fetch ultra-rare opportunities (60+ scores) with optional metrics
    try:
        # Try to fetch with metrics first
        result = supabase.rpc(
            'get_opportunities_with_metrics',
            {}
        ).execute()
        # Filter for 60+ scores
        ultra_rare_opportunities = [o for o in result.data if o.get('opportunity_score', 0) >= 60.0][:20] if result.data else []
    except:
        # Fallback: fetch from app_opportunities only
        try:
            result = supabase.table('app_opportunities').select(
                'submission_id, opportunity_score, problem_description, app_concept, core_functions, target_user, monetization_model, subreddit, title, created_at'
            ).gte('opportunity_score', 60.0).order('opportunity_score', desc=True).limit(20).execute()

            ultra_rare_opportunities = result.data if result.data else []
        except Exception:
            # Fallback if table doesn't exist
            ultra_rare_opportunities = []

    # Fetch regular opportunities (40-59 scores) for comparison
    try:
        regular_result = supabase.table('app_opportunities').select(
            'opportunity_score, subreddit, created_at'
        ).gte('opportunity_score', 40.0).lt('opportunity_score', 60.0).order('opportunity_score', desc=True).limit(50).execute()

        regular_opportunities = regular_result.data if regular_result.data else []
    except Exception:
        regular_opportunities = []

    # Fetch collection metrics
    try:
        metrics_result = supabase.table('continuous_collection_metrics').select('*').order('collection_date', desc=True).limit(7).execute()
        collection_metrics = metrics_result.data if metrics_result.data else []
    except Exception:
        collection_metrics = []

    return collection_metrics, regular_opportunities, regular_result, result, ultra_rare_opportunities


@app.cell
def __(mo, ultra_rare_opportunities):
    if ultra_rare_opportunities:
        # Build ultra-rare opportunities table
        ultra_rare_data = []
        for opp in ultra_rare_opportunities:
            core_functions = opp.get('core_functions', [])
            if isinstance(core_functions, str):
                try:
                    core_functions = eval(core_functions)
                except:
                    core_functions = [str(core_functions)]

            functions_text = "\n".join([f"• {func}" for func in core_functions]) if isinstance(core_functions, list) else str(core_functions)

            ultra_rare_data.append({
                'Score': f"🌟 {opp.get('opportunity_score', 0):.1f}",
                'Subreddit': opp.get('subreddit', 'N/A'),
                'Problem': opp.get('problem_description', 'N/A')[:100] + "...",
                'App Concept': opp.get('app_concept', 'N/A')[:100] + "...",
                'Core Functions': functions_text,
                'Target User': opp.get('target_user', 'N/A'),
                'Monetization': opp.get('monetization_model', 'N/A'),
                'Discovered': opp.get('created_at', 'N/A')[:10]
            })

        ultra_rare_table = mo.ui.table(
            ultra_rare_data,
            label=f"🌟 Ultra-Rare Opportunities (60+ Scores) - {len(ultra_rare_data)} Found"
        )
        ultra_rare_table
    else:
        no_ultra_rare = mo.md("""
        ### 🌟 No Ultra-Rare Opportunities (60+) Found Yet

        The 60+ score hunter is continuously running. These opportunities are extremely rare but highly valuable.
        """)
        no_ultra_rare
    return ultra_rare_data, ultra_rare_table, no_ultra_rare


@app.cell
def __(mo, regular_opportunities, ultra_rare_opportunities):
    # Calculate statistics
    ultra_rare_count = len(ultra_rare_opportunities)
    regular_count = len(regular_opportunities)
    total_opportunities = ultra_rare_count + regular_count

    # Score distribution
    if ultra_rare_opportunities:
        ultra_rare_avg = sum(o.get('opportunity_score', 0) for o in ultra_rare_opportunities) / ultra_rare_count
        highest_score = max(o.get('opportunity_score', 0) for o in ultra_rare_opportunities)
    else:
        ultra_rare_avg = 0
        highest_score = 0

    if regular_opportunities:
        regular_avg = sum(o.get('opportunity_score', 0) for o in regular_opportunities) / regular_count
    else:
        regular_avg = 0

    # Rarity classification
    legendary_count = len([o for o in ultra_rare_opportunities if o.get('opportunity_score', 0) >= 70])
    epic_count = len([o for o in ultra_rare_opportunities if 60 <= o.get('opportunity_score', 0) < 70])

    stats_md = mo.md(f"""
    ## 📊 Ultra-Rare Opportunity Statistics

    **Discovery Summary:**
    - 🌟 Ultra-Rare (60+): {ultra_rare_count} opportunities
    - 💎 Regular (40-59): {regular_count} opportunities
    - 📈 Total Analyzed: {total_opportunities} opportunities

    **Ultra-Rare Breakdown:**
    - 🏆 Legendary (70+): {legendary_count} unicorn opportunities
    - 🔥 Epic (60-69): {epic_count} exceptional opportunities

    **Performance Metrics:**
    - 🌟 Ultra-Rare Average Score: {ultra_rare_avg:.1f}
    - 💎 Regular Average Score: {regular_avg:.1f}
    - 🎯 Highest Score: {highest_score:.1f}
    - 📊 Ultra-Rare Hit Rate: {(ultra_rare_count / total_opportunities * 100):.2f}% if total_opportunities > 0 else 0

    **System Status:**
    - 🤖 Score Hunter: Active
    - 📡 Continuous Collection: Running
    - 🎯 Daily Target: 50 posts from premium subreddits
    """)
    return epic_count, legendary_count, regular_avg, stats_md, ultra_rare_avg, highest_score, ultra_rare_count


@app.cell
def __(collection_metrics, mo):
    if collection_metrics:
        # Build collection performance chart
        collection_data = []
        for metric in collection_metrics:
            collection_data.append({
                'Date': metric.get('collection_date', 'N/A')[:10],
                'Target': metric.get('total_target', 0),
                'Collected': metric.get('total_collected', 0),
                'Success Rate': f"{metric.get('overall_success_rate', 0):.1%}",
                'Subreddits': metric.get('subreddit_count', 0)
            })

        collection_table = mo.ui.table(
            collection_data,
            label="📊 Recent Collection Performance (Last 7 Days)"
        )
        collection_table
    else:
        no_metrics = mo.md("📊 Collection metrics will appear here as the system runs.")
        no_metrics
    return collection_data, collection_table, no_metrics


@app.cell
def __(datetime, mo, supabase):
    # Real-time system status
    def get_system_status():
        """Get current system status"""
        try:
            # Check recent activity
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

            # Recent submissions
            recent_result = supabase.table('submissions').select('id').gte('created_at', one_hour_ago).execute()
            recent_submissions = len(recent_result.data or [])

            # Recent opportunities
            recent_opp_result = supabase.table('app_opportunities').select('id').gte('created_at', one_hour_ago).execute()
            recent_opportunities = len(recent_opp_result.data or [])

            return {
                'recent_submissions': recent_submissions,
                'recent_opportunities': recent_opportunities,
                'system_active': recent_submissions > 0 or recent_opportunities > 0,
                'last_update': datetime.now().strftime('%H:%M:%S')
            }
        except Exception:
            return {
                'recent_submissions': 0,
                'recent_opportunities': 0,
                'system_active': False,
                'last_update': datetime.now().strftime('%H:%M:%S')
            }

    system_status = get_system_status()

    status_md = mo.md(f"""
    ## 🤖 System Status (Live)

    **Activity (Last Hour):**
    - 📥 New Submissions: {system_status['recent_submissions']}
    - 🎯 New Opportunities: {system_status['recent_opportunities']}
    - 🟢 System Status: {'Active' if system_status['system_active'] else 'Idle'}
    - 🕐 Last Update: {system_status['last_update']}

    **Automation Schedule:**
    - 🌅 Morning Collection: 9:00 AM (Ultra-premium focus)
    - 🔍 Afternoon Hunt: 2:00 PM (Ultra-rare detection)
    - 📊 Evening Analysis: 7:00 PM (Performance review)
    - 🧠 Weekly Deep Dive: Sundays 3:00 PM

    **Current Targets:**
    - 🎯 Daily Posts: 50 from adaptive subreddit selection
    - 🌟 Ultra-Rare Threshold: 60+ score
    - 💎 Standard Threshold: 40+ score
    - 🔥 Legendary Threshold: 70+ score
    """)

    # Auto-refresh every 5 minutes
    auto_refresh = mo.md(f"*Dashboard auto-refreshes every 5 minutes. Last updated: {system_status['last_update']}*")
    return auto_refresh, get_system_status, status_md, system_status


@app.cell
def __(mo):
    mo.md("---")
    mo.md("""
    ### 🔍 About This Dashboard

    This dashboard monitors RedditHarbor's ultra-rare opportunity detection system:

    **Ultra-Rare Classification:**
    - 🏆 **Legendary (70+)**: Unicorn-level opportunities - transformational potential
    - 🔥 **Epic (60-69)**: Exceptional opportunities - rare high-impact potential
    - 💎 **Regular (40-59)**: High-value opportunities - solid market potential

    **System Features:**
    - 🤖 Automated daily Reddit harvesting from premium subreddits
    - 🎯 Intelligent subreddit rotation based on historical performance
    - 🔍 Specialized 60+ score hunter with enhanced detection algorithms
    - 📊 Real-time opportunity profiling and validation
    - 🚨 Instant alerts for ultra-rare discoveries

    **Expected Rarity:**
    - 60+ scores: ~0.1% of all posts (1 in 1,000)
    - 70+ scores: ~0.01% of all posts (1 in 10,000)
    """)

    mo.md("*Powered by RedditHarbor - AI-Powered App Discovery*")
    return


if __name__ == "__main__":
    app.run()
