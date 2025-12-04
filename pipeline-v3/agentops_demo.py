#!/usr/bin/env python3
"""
Demonstration of Phase 2 AgentOps integration for Pipeline v3
Shows production monitoring, session management, and cost tracking
"""

import sys
import os
import time
import random
sys.path.append('.')

from monitoring.agentops_tracker import AgentOpsTracker, AgentOpsConfig
from monitoring.agentops_decorators import trace, tool, llm_call
from models.cost_tracking import CostTracking, CostSummary
from datetime import datetime

def demonstrate_agentops_integration():
    """Demonstrate AgentOps monitoring capabilities"""
    print("🎯 Phase 2 AgentOps Integration Demo")
    print("=" * 50)

    # 1. Configuration from Environment
    print("\n1️⃣ AgentOps Configuration")
    print("-" * 30)

    config = AgentOpsConfig.from_environment()
    print(f"✅ AgentOps Available: {config.enabled}")
    print(f"✅ Project Name: {config.project_name}")
    print(f"✅ Session Tags: {', '.join(config.session_tags)}")
    print(f"✅ Auto Start Session: {config.auto_start_session}")
    print(f"✅ Fallback to Local: {config.fallback_to_local_tracking}")

    # 2. Session Management
    print("\n2️⃣ Session Management")
    print("-" * 25)

    tracker = AgentOpsTracker(config)

    # Start a monitoring session
    session_id = tracker.start_session("demo_batch_analysis")
    print(f"🚀 Session Started: {session_id[:8]}...")

    # Simulate some analysis work
    print("   ⏳ Simulating Reddit analysis...")
    time.sleep(0.5)

    # Track some costs
    for i in range(3):
        cost_data = CostTracking(
            model_used="openai/gpt-4o-mini",
            provider="openrouter",
            prompt_tokens=100 + i * 50,
            completion_tokens=50 + i * 25,
            total_tokens=150 + i * 75,
            input_cost_usd=0.000015 + i * 0.00001,
            output_cost_usd=0.000030 + i * 0.00002,
            total_cost_usd=0.000045 + i * 0.00003,
            latency_seconds=1.0 + i * 0.2,
            prompt_length_chars=500 + i * 100,
            model_pricing_per_m_tokens={"input": 0.15, "output": 0.60},
            request_success=True
        )
        tracker.track_cost(cost_data, f"analysis_{i+1}")
        time.sleep(0.1)

    # End session with summary
    summary = tracker.end_session("success", "Completed demo analysis")
    print(f"   ✅ Session Summary: {summary['total_cost_usd']:.6f} total cost")
    print(f"   📊 Operations Tracked: {summary['operations_count']}")

    # 3. Decorator Usage
    print("\n3️⃣ Decorator-Based Tracking")
    print("-" * 30)

    @trace("reddit_analysis", tags=["production"])
    @tool("opportunity_analyzer")
    def analyze_reddit_post(post_data):
        """Simulate Reddit post analysis with tracking"""
        print(f"   🔍 Analyzing: {post_data['title'][:30]}...")

        # Simulate LLM call
        time.sleep(0.2)

        return {
            "opportunity_score": random.uniform(60, 95),
            "app_concept": f"AI-powered {post_data['subreddit']} tool",
            "functions": ["analyze", "optimize", "track"]
        }

    @llm_call(track_cost=True)
    def llm_cost_example():
        """Demonstrate LLM cost tracking"""
        return "Simulated LLM response with cost tracking"

    # Execute decorated functions
    post_data = {
        "title": "Looking for better task management app",
        "subreddit": "productivity"
    }

    result = analyze_reddit_post(post_data)
    print(f"   📈 Analysis Score: {result['opportunity_score']:.1f}")

    llm_result = llm_cost_example()
    print(f"   💰 LLM Response: {llm_result[:40]}...")

    # 4. Performance Metrics
    print("\n4️⃣ Performance Metrics")
    print("-" * 25)

    # Get current session metrics
    if hasattr(tracker, 'current_session'):
        metrics = tracker.get_session_metrics()
        print(f"   ⚡ Average Latency: {metrics.get('avg_latency', 0):.3f}s")
        print(f"   🎯 Success Rate: {metrics.get('success_rate', 0):.1%}")
        print(f"   💸 Total Cost: ${metrics.get('total_cost', 0):.6f}")
        print(f"   📋 Operations: {metrics.get('operations_count', 0)}")

    # 5. Production Benefits
    print("\n5️⃣ Production Benefits")
    print("-" * 23)

    benefits = [
        "✅ Real-time cost monitoring and budget control",
        "✅ Performance SLA tracking and alerting",
        "✅ Multi-agent workflow coordination",
        "✅ Error classification and debugging support",
        "✅ Session-level analytics and reporting",
        "✅ Graceful fallback when AgentOps unavailable",
        "✅ Zero-breaking-changes to existing code",
        "✅ Thread-safe production deployment"
    ]

    for benefit in benefits:
        print(f"   {benefit}")

    # 6. Analytics Dashboard Integration
    print("\n6️⃣ Analytics Dashboard")
    print("-" * 24)

    print("📊 AgentOps Dashboard Features:")
    print("   🎯 Real-time session monitoring")
    print("   💰 Cost tracking by model and provider")
    print("   📈 Performance trends and benchmarks")
    print("   🔍 Error analysis and debugging tools")
    print("   📋 Custom tags and filtering")
    print("   📥 Export capabilities for reporting")

    print(f"\n🎉 Phase 2 AgentOps Integration Complete!")
    print(f"⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show environment setup
    print(f"\n🔧 Environment Setup:")
    print(f"   export AGENTOPS_API_KEY=your_key_here")
    print(f"   export AGENTOPS_PROJECT_NAME=pipeline-v3-production")
    print(f"   export AGENTOPS_ENABLED=true")
    print(f"   export AGENTOPS_TAGS=production,pipeline-v3")


if __name__ == "__main__":
    demonstrate_agentops_integration()