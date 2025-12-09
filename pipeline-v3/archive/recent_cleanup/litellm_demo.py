#!/usr/bin/env python3
"""
Demonstration of Phase 1 LiteLLM integration for Pipeline v3
Shows cost tracking capabilities and model management
"""

import sys

sys.path.append('.')

from datetime import datetime

from models.cost_tracking import CostTracking, ModelCostConfig


def demonstrate_cost_tracking():
    """Demonstrate cost tracking functionality"""
    print("🎯 Phase 1 LiteLLM Integration Demo")
    print("=" * 50)

    # 1. Model Cost Configuration
    print("\n1️⃣ Model Cost Configuration")
    print("-" * 30)

    models = [
        ModelCostConfig(
            model_name="openai/gpt-4o-mini",
            provider="openrouter",
            input_cost_per_million=0.15,
            output_cost_per_million=0.60,
            max_tokens=4000,
            supports_json_mode=True
        ),
        ModelCostConfig(
            model_name="anthropic/claude-haiku-4.5",
            provider="openrouter",
            input_cost_per_million=1.0,
            output_cost_per_million=5.0,
            max_tokens=4096,
            supports_json_mode=True
        ),
        ModelCostConfig(
            model_name="meta-llama/llama-3.1-8b-instruct:floor",
            provider="openrouter",
            input_cost_per_million=0.07,  # Floor pricing!
            output_cost_per_million=0.14,
            max_tokens=8192,
            supports_json_mode=True
        )
    ]

    for model in models:
        cost_per_1k_input = (model.input_cost_per_million / 1000000) * 1000
        cost_per_1k_output = (model.output_cost_per_million / 1000000) * 1000
        print(f"✅ {model.model_name}")
        print(f"   💰 Input: ${cost_per_1k_input:.6f} per 1K tokens")
        print(f"   💰 Output: ${cost_per_1k_output:.6f} per 1K tokens")
        print(f"   🎯 JSON Mode: {'✓' if model.supports_json_mode else '✗'}")

    # 2. Cost Tracking Demonstration
    print("\n2️⃣ Cost Tracking Demonstration")
    print("-" * 35)

    # Simulate 3 analysis operations
    cost_data_list = [
        CostTracking(
            model_used="openai/gpt-4o-mini",
            provider="openrouter",
            prompt_tokens=850,
            completion_tokens=315,
            total_tokens=1165,
            input_cost_usd=0.000128,
            output_cost_usd=0.000189,
            total_cost_usd=0.000317,
            latency_seconds=1.23,
            prompt_length_chars=1250,
            model_pricing_per_m_tokens={"input": 0.15, "output": 0.60},
            request_success=True
        ),
        CostTracking(
            model_used="meta-llama/llama-3.1-8b-instruct:floor",
            provider="openrouter",
            prompt_tokens=750,
            completion_tokens=280,
            total_tokens=1030,
            input_cost_usd=0.000053,
            output_cost_usd=0.000039,
            total_cost_usd=0.000092,
            latency_seconds=0.87,
            prompt_length_chars=1100,
            model_pricing_per_m_tokens={"input": 0.07, "output": 0.14},
            request_success=True
        ),
        CostTracking(
            model_used="anthropic/claude-haiku-4.5",
            provider="openrouter",
            prompt_tokens=920,
            completion_tokens=340,
            total_tokens=1260,
            input_cost_usd=0.000920,
            output_cost_usd=0.001700,
            total_cost_usd=0.002620,
            latency_seconds=1.56,
            prompt_length_chars=1400,
            model_pricing_per_m_tokens={"input": 1.0, "output": 5.0},
            request_success=True
        )
    ]

    # Calculate cost summary
    total_cost = sum(cost.total_cost_usd for cost in cost_data_list)
    total_tokens = sum(cost.total_tokens for cost in cost_data_list)
    avg_latency = sum(cost.latency_seconds for cost in cost_data_list) / len(cost_data_list)

    print(f"📊 Analysis Operations: {len(cost_data_list)}")
    print(f"💰 Total Cost: ${total_cost:.6f}")
    print(f"🔢 Total Tokens: {total_tokens:,}")
    print(f"⚡ Average Latency: {avg_latency:.2f}s")
    print(f"💸 Cost per 1K Tokens: ${(total_cost / total_tokens) * 1000:.6f}")

    # 3. Cost Comparison Analysis
    print("\n3️⃣ Cost Efficiency Analysis")
    print("-" * 28)

    for i, cost_data in enumerate(cost_data_list, 1):
        cost_per_1k = (cost_data.total_cost_usd / cost_data.total_tokens) * 1000
        tokens_per_dollar = cost_data.total_tokens / cost_data.total_cost_usd if cost_data.total_cost_usd > 0 else 0

        print(f"🔍 Analysis #{i}")
        print(f"   Model: {cost_data.model_used}")
        print(f"   Cost: ${cost_data.total_cost_usd:.6f} ({cost_data.total_tokens:,} tokens)")
        print(f"   Efficiency: ${cost_per_1k:.6f} per 1K tokens")
        print(f"   Throughput: {tokens_per_dollar:.0f} tokens per $1")
        print(f"   Latency: {cost_data.latency_seconds:.2f}s")
        print()

    # 4. Production Cost Projections
    print("4️⃣ Production Cost Projections")
    print("-" * 31)

    # Project costs for different volumes
    volumes = [100, 1000, 10000, 100000]

    print("Using Llama 3.1 8B (floor pricing):")
    avg_cost_per_analysis = cost_data_list[1].total_cost_usd  # Use cheapest model

    for volume in volumes:
        daily_cost = avg_cost_per_analysis * volume
        monthly_cost = daily_cost * 30
        print(f"   📈 {volume:,} analyses/day:")
        print(f"      Daily: ${daily_cost:.2f}")
        print(f"      Monthly: ${monthly_cost:.2f}")

    print("\n🎉 LiteLLM Integration Benefits:")
    print("✅ Transparent cost tracking")
    print("✅ Model flexibility and switching")
    print("✅ Floor pricing optimization")
    print("✅ Production-ready monitoring")
    print("✅ Detailed performance metrics")
    print("✅ Cost per opportunity calculation")

    print(f"\n⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    demonstrate_cost_tracking()
