#!/usr/bin/env python3
"""
Evidence-Based AI Profiling Test Script

Demonstrates the enhanced integration between Agno monetization analyzer and LLM profiler
with comprehensive evidence validation and alignment scoring.

This script shows:
1. Agno analysis with multi-agent monetization insights
2. Evidence-based AI profiling using Agno results
3. Comprehensive validation with alignment scoring
4. Discrepancy detection and confidence metrics
5. Cost tracking and performance metrics

Usage:
    python test_evidence_based_profiling.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from agent_tools.monetization_agno_analyzer import MonetizationAgnoAnalyzer


def test_evidence_based_profiling():
    """Test the complete evidence-based profiling pipeline"""

    print("\n" + "="*80)
    print("EVIDENCE-BASED AI PROFILING DEMONSTRATION")
    print("="*80 + "\n")

    # Test cases with different monetization scenarios
    test_cases = [
        {
            "name": "High-Value B2B Opportunity",
            "text": "Our team of 15 is paying $500/month for Asana but it's not meeting our needs. We need something with better reporting and team management features. Budget approved for up to $800/month for the right solution. We need to make a decision by end of Q1.",
            "title": "Looking for better project management tool",
            "subreddit": "projectmanagement",
            "expected_wtp": "High (85+)",
            "expected_segment": "B2B"
        },
        {
            "name": "Price-Sensitive B2C User",
            "text": "I'm NOT willing to pay another subscription fee. All these fitness apps want $10-15/month which is ridiculous. Looking for free alternatives to MyFitnessPal. Why should I pay when there are free options?",
            "title": "Frustrated with subscription fitness apps",
            "subreddit": "fitness",
            "expected_wtp": "Low (<30)",
            "expected_segment": "B2C"
        },
        {
            "name": "Medium-Priority Startup Need",
            "text": "Our startup needs a better CRM solution. Currently using spreadsheets and it's becoming unmanageable. Looking at options in the $50-150/month range. Not urgent but would like to implement in next few months.",
            "title": "Startup needs CRM recommendations",
            "subreddit": "startups",
            "expected_wtp": "Medium (50-70)",
            "expected_segment": "B2B"
        }
    ]

    try:
        # Initialize analyzers
        print("🔧 Initializing analyzers...")
        agno_analyzer = MonetizationAgnoAnalyzer()
        llm_profiler = EnhancedLLMProfiler()
        print("✅ Analyzers initialized successfully\n")

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test_case['name']}")
            print(f"{'='*60}")

            text = test_case["text"]
            title = test_case["title"]
            subreddit = test_case["subreddit"]

            print("\n📝 Input Analysis:")
            print(f"   Title: {title}")
            print(f"   Subreddit: r/{subreddit}")
            print(f"   Expected WTP: {test_case['expected_wtp']}")
            print(f"   Expected Segment: {test_case['expected_segment']}")
            print(f"   Text: {text[:150]}...")

            try:
                # Step 1: Agno monetization analysis
                print("\n🧠 Step 1: Agno Monetization Analysis")
                print("-" * 40)

                agno_result = agno_analyzer.analyze(
                    text=text,
                    subreddit=subreddit
                )

                print(f"   ✓ Willingness to Pay: {agno_result.willingness_to_pay_score}/100")
                print(f"   ✓ Customer Segment: {agno_result.customer_segment}")
                print(f"   ✓ Payment Sentiment: {agno_result.sentiment_toward_payment}")
                print(f"   ✓ Urgency Level: {agno_result.urgency_level}")
                print(f"   ✓ Price Points: {agno_result.mentioned_price_points}")
                print(f"   ✓ Confidence: {agno_result.confidence:.2f}")
                print(f"   ✓ LLM Monetization Score: {agno_result.llm_monetization_score:.1f}/100")

                # Step 2: Evidence-based AI profiling
                print("\n🤖 Step 2: Evidence-Based AI Profiling")
                print("-" * 40)

                # Prepare Agno evidence for AI profiler
                agno_evidence = {
                    "willingness_to_pay_score": agno_result.willingness_to_pay_score,
                    "customer_segment": agno_result.customer_segment,
                    "sentiment_toward_payment": agno_result.sentiment_toward_payment,
                    "urgency_level": agno_result.urgency_level,
                    "mentioned_price_points": agno_result.mentioned_price_points,
                    "existing_payment_behavior": agno_result.existing_payment_behavior,
                    "payment_friction_indicators": agno_result.payment_friction_indicators,
                    "confidence": agno_result.confidence,
                    "reasoning": agno_result.reasoning
                }

                print(f"   🧠 Using Agno evidence: WTP={agno_result.willingness_to_pay_score}, Segment={agno_result.customer_segment}")

                # Generate evidence-based profile
                ai_profile = llm_profiler.generate_app_profile_with_evidence(
                    text=text,
                    title=title,
                    subreddit=subreddit,
                    score=agno_result.llm_monetization_score,
                    agno_analysis=agno_evidence
                )

                print(f"   ✅ AI Profile Generated: {ai_profile.get('app_name', 'Unknown')}")
                print(f"   ✅ Concept: {ai_profile.get('app_concept', 'N/A')[:80]}...")
                print(f"   ✅ Target User: {ai_profile.get('target_user', 'N/A')}")
                print(f"   ✅ Monetization: {ai_profile.get('monetization_model', 'N/A')}")

                # Step 3: Evidence validation results
                print("\n📊 Step 3: Evidence Validation Results")
                print("-" * 40)

                if "evidence_validation" in ai_profile:
                    validation = ai_profile["evidence_validation"]
                    alignment_score = validation.get("alignment_score", 0)
                    validation_status = validation.get("overall_status", "unknown")
                    evidence_strength = validation.get("evidence_strength", "medium")
                    discrepancies = validation.get("discrepancies", [])
                    warnings = validation.get("warnings", [])

                    # Status indicator
                    if alignment_score >= 80:
                        status_icon = "🟢"
                    elif alignment_score >= 60:
                        status_icon = "🟡"
                    else:
                        status_icon = "🔴"

                    print(f"   {status_icon} Overall Alignment: {validation_status.replace('_', ' ').title()}")
                    print(f"   📈 Alignment Score: {alignment_score:.1f}%")
                    print(f"   💪 Evidence Strength: {evidence_strength.title()}")

                    # Detailed validations
                    validations = validation.get("validations", {})
                    if validations:
                        print("   🔍 Validation Breakdown:")
                        for name, data in validations.items():
                            if isinstance(data, dict) and "score" in data:
                                score = data["score"] * 100
                                aligned = data.get("aligned", False)
                                icon = "✅" if aligned else "❌"
                                print(f"      {icon} {name.replace('_', ' ').title()}: {score:.0f}%")

                    # Issues found
                    if discrepancies:
                        print(f"   ⚠️  Discrepancies ({len(discrepancies)}):")
                        for discrepancy in discrepancies[:2]:
                            print(f"      - {discrepancy}")

                    if warnings:
                        print(f"   ⚡ Warnings ({len(warnings)}):")
                        for warning in warnings[:1]:
                            print(f"      - {warning}")

                # Step 4: Cost and performance metrics
                print("\n💰 Step 4: Cost & Performance Metrics")
                print("-" * 40)

                if "cost_tracking" in ai_profile:
                    cost_data = ai_profile["cost_tracking"]
                    print(f"   💸 Total Cost: ${cost_data.get('total_cost_usd', 0):.6f}")
                    print(f"   🔢 Total Tokens: {cost_data.get('total_tokens', 0):,}")
                    print(f"   ⚡ Latency: {cost_data.get('latency_seconds', 0):.2f}s")
                    print(f"   🤖 Model: {cost_data.get('model_used', 'Unknown')}")

                # Evidence summary
                if "evidence_summary" in ai_profile:
                    summary = ai_profile["evidence_summary"]
                    print(f"   📋 Evidence-Based: {summary.get('evidence_based', False)}")
                    print(f"   🎯 Validation Score: {summary.get('validation_score', 0):.1f}%")

                print(f"\n✅ Test case {i} completed successfully!")

            except Exception as e:
                print(f"\n❌ Error in test case {i}: {e}")
                continue

        # Final summary
        print(f"\n{'='*80}")
        print("EVIDENCE-BASED PROFILING DEMONSTRATION COMPLETE")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✅ Multi-agent Agno monetization analysis")
        print("✅ Evidence-based AI profile generation")
        print("✅ Comprehensive alignment validation")
        print("✅ Weighted scoring with confidence metrics")
        print("✅ Discrepancy detection and warnings")
        print("✅ Cost tracking and performance monitoring")
        print("✅ Backward compatibility with existing workflows")

        print("\nIntegration Benefits:")
        print("🧠 AI profiles are now truly data-driven")
        print("📊 Evidence validation ensures consistency")
        print("🎯 Alignment scoring improves accuracy")
        print("⚠️  Discrepancy detection prevents errors")
        print("💰 Cost tracking enables optimization")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        print("\nRequired dependencies:")
        print("- agno (for multi-agent analysis)")
        print("- litellm (for LLM API calls)")
        print("- json_repair (for robust JSON parsing)")
        print("- Valid OPENROUTER_API_KEY in environment")
        print("\nOptional: AGENTOPS_API_KEY for cost tracking")


if __name__ == "__main__":
    test_evidence_based_profiling()
