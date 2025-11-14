#!/usr/bin/env python3
"""
RedditHarbor Hybrid Strategy Monitoring Dashboard

Provides real-time insights into both Option A (LLM monetization analysis)
and Option B (customer lead generation) performance.

Usage:
    python scripts/monitor_hybrid_strategy.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client

def get_monitoring_stats(supabase) -> Dict[str, any]:
    """
    Get comprehensive monitoring stats for the hybrid strategy
    """
    stats = {}

    try:
        # Option B: Customer Leads Overview
        print("🔍 Fetching customer leads overview...")
        leads_response = supabase.table('customer_leads').select('count', count='exact').execute()
        stats['total_leads'] = leads_response.count if leads_response.data else 0

        # Hot leads (high urgency + high score)
        hot_leads_response = supabase.table('hot_leads').select('*').limit(10).execute()
        stats['hot_leads'] = hot_leads_response.data or []
        stats['hot_leads_count'] = len(stats['hot_leads'])

        # Leads by competitor
        competitor_response = supabase.table('leads_by_competitor').select('*').limit(10).execute()
        stats['leads_by_competitor'] = competitor_response.data or []

        # Leads by urgency
        urgency_response = supabase.table('customer_leads').select('urgency_level', count='exact').execute()
        urgency_counts = {}
        for record in urgency_response.data or []:
            urgency = record.get('urgency_level', 'unknown')
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        stats['leads_by_urgency'] = urgency_counts

        # Option A: LLM Monetization Analysis Overview
        print("💰 Fetching LLM monetization overview...")
        llm_response = supabase.table('llm_monetization_analysis').select('count', count='exact').execute()
        stats['total_llm_analyses'] = llm_response.count if llm_response.data else 0

        # High monetization opportunities
        high_mon_response = supabase.table('high_monetization_opportunities').select('*').limit(10).execute()
        stats['high_monetization_opportunities'] = high_mon_response.data or []
        stats['high_mon_count'] = len(stats['high_monetization_opportunities'])

        # Segment performance
        segment_response = supabase.table('segment_performance').select('*').execute()
        stats['segment_performance'] = segment_response.data or []

        # Cost tracking
        cost_response = supabase.table('llm_analysis_cost_stats').select('*').execute()
        stats['cost_stats'] = cost_response.data or []

        # Recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent_leads = supabase.table('customer_leads').select('*').gte('created_at', week_ago).execute()
        stats['recent_leads'] = recent_leads.data or []

        recent_llm = supabase.table('llm_monetization_analysis').select('*').gte('analyzed_at', week_ago).execute()
        stats['recent_llm_analyses'] = recent_llm.data or []

    except Exception as e:
        print(f"⚠️  Error fetching monitoring data: {e}")
        stats['error'] = str(e)

    return stats

def print_dashboard(stats: Dict[str, any]):
    """
    Print a formatted monitoring dashboard
    """
    print("\n" + "="*80)
    print("🎯 REDDITHARBOR HYBRID STRATEGY MONITORING DASHBOARD")
    print("="*80)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Error handling
    if 'error' in stats:
        print(f"\n❌ Error: {stats['error']}")
        return

    # Option B: Customer Leads Summary
    print(f"\n👥 OPTION B: CUSTOMER LEAD GENERATION")
    print(f"   Total Leads Extracted: {stats.get('total_leads', 0):,}")
    print(f"   Hot Leads (High Urgency): {stats.get('hot_leads_count', 0):,}")
    print(f"   Recent Leads (7 days): {len(stats.get('recent_leads', [])):,}")

    # Top competitors mentioned
    if stats.get('leads_by_competitor'):
        print(f"\n🏢 TOP COMPETITORS MENTIONED:")
        for comp in stats['leads_by_competitor'][:5]:
            print(f"   • {comp.get('competitor_mentioned', 'Unknown')}: {comp.get('lead_count', 0)} leads")

    # Urgency breakdown
    if stats.get('leads_by_urgency'):
        print(f"\n🔥 LEADS BY URGENCY:")
        for urgency, count in stats['leads_by_urgency'].items():
            emoji = {"critical": "🚨", "high": "🔥", "medium": "⚡", "low": "📋"}.get(urgency, "❓")
            print(f"   {emoji} {urgency.capitalize()}: {count}")

    # Option A: LLM Monetization Analysis Summary
    print(f"\n💰 OPTION A: LLM MONETIZATION ANALYSIS")
    print(f"   Total LLM Analyses: {stats.get('total_llm_analyses', 0):,}")
    print(f"   High Monetization Opportunities: {stats.get('high_mon_count', 0):,}")
    print(f"   Recent Analyses (7 days): {len(stats.get('recent_llm_analyses', [])):,}")

    # Segment performance
    if stats.get('segment_performance'):
        print(f"\n📊 SEGMENT PERFORMANCE:")
        for segment in stats['segment_performance']:
            print(f"   • {segment.get('customer_segment', 'Unknown')}: "
                  f"Avg Score {segment.get('avg_monetization_score', 0):.1f} "
                  f"({segment.get('analysis_count', 0)} analyses)")

    # Cost summary
    if stats.get('cost_stats'):
        total_cost = sum(stat.get('total_cost', 0) for stat in stats['cost_stats'])
        total_tokens = sum(stat.get('total_tokens', 0) for stat in stats['cost_stats'])
        print(f"\n💸 COST TRACKING (Last 30 days):")
        print(f"   Total LLM Cost: ${total_cost:.6f}")
        print(f"   Total Tokens: {total_tokens:,}")
        print(f"   Avg Cost per Analysis: ${total_cost/max(total_tokens/1000, 1):.6f}" if total_tokens > 0 else "")

    # Hot leads details
    if stats.get('hot_leads'):
        print(f"\n🔥 TOP HOT LEADS:")
        for i, lead in enumerate(stats['hot_leads'][:3], 1):
            print(f"   {i}. u/{lead.get('reddit_username', 'unknown')} | "
                  f"Score: {lead.get('lead_score', 0)}/100 | "
                  f"Budget: ${lead.get('budget_amount', 0):.0f}/{lead.get('budget_period', 'mo')} | "
                  f"Competitor: {lead.get('competitor_mentioned', 'Unknown')}")

    # High monetization opportunities details
    if stats.get('high_monetization_opportunities'):
        print(f"\n💰 TOP MONETIZATION OPPORTUNITIES:")
        for i, opp in enumerate(stats['high_monetization_opportunities'][:3], 1):
            print(f"   {i}. Score: {opp.get('llm_monetization_score', 0):.1f}/100 | "
                  f"Segment: {opp.get('customer_segment', 'Unknown')} | "
                  f"WTP: {opp.get('willingness_to_pay_score', 0):.1f}/100 | "
                  f"Confidence: {opp.get('confidence', 0):.1f}")

    print(f"\n" + "="*80)
    print("📈 RECOMMENDATIONS")

    # Generate recommendations based on data
    recommendations = []

    if stats.get('hot_leads_count', 0) > 5:
        recommendations.append("🔥 HIGH PRIORITY: Contact hot leads immediately - multiple high-urgency opportunities")

    if stats.get('total_leads', 0) > 50 and stats.get('total_llm_analyses', 0) < 10:
        recommendations.append("⚖️  BALANCE: Consider running Option A (LLM analysis) on more leads")

    if stats.get('total_llm_analyses', 0) > 100:
        cost_stats = stats.get('cost_stats', [])
        if cost_stats:
            avg_cost = sum(stat.get('total_cost', 0) for stat in cost_stats) / len(cost_stats)
            if avg_cost > 0.02:  # $0.02 per analysis
                recommendations.append("💡 COST OPTIMIZATION: Consider raising threshold or using cheaper model")

    if not recommendations:
        recommendations.append("🎯 NORMAL: System is operating as expected")

    for rec in recommendations:
        print(f"   {rec}")

    print("="*80)

def main():
    """Main monitoring function"""
    print("🔍 Connecting to Supabase...")

    try:
        # Initialize Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Test connection
        print("✅ Connected successfully!")

        # Get monitoring stats
        stats = get_monitoring_stats(supabase)

        # Print dashboard
        print_dashboard(stats)

    except Exception as e:
        print(f"❌ Failed to connect or fetch data: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check Supabase is running: supabase start")
        print("   2. Check environment variables in .env.local")
        print("   3. Verify database migrations were applied")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())