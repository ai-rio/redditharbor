#!/usr/bin/env python3
"""
Test LLM connection pooling to find the connection limit
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler

def main():
    print("=" * 80)
    print("TESTING LLM CONNECTION POOL LIMITS")
    print("=" * 80)

    profiler = EnhancedLLMProfiler()
    print(f"✓ EnhancedLLMProfiler initialized")
    print(f"  Model: {profiler.model}")
    print(f"  API Key: {'*' * 8}{profiler.api_key[-8:] if profiler.api_key else 'MISSING'}\n")

    # Test data
    test_text = "I need help managing my time"
    test_title = "Time management problem"
    test_subreddit = "productivity"
    test_score = 35.0

    # Try to generate profiles repeatedly to trigger the hang
    max_attempts = 10
    successful = 0

    for i in range(1, max_attempts + 1):
        try:
            print(f"Attempt {i}/{max_attempts}: Generating AI profile...")
            start = time.time()

            profile, cost_data = profiler.generate_app_profile_with_costs(
                text=test_text,
                title=test_title,
                subreddit=test_subreddit,
                score=test_score
            )

            elapsed = time.time() - start
            successful += 1

            print(f"  ✅ Profile {i} generated successfully in {elapsed:.2f}s")
            print(f"     Cost: ${cost_data['total_cost_usd']:.6f}, Tokens: {cost_data['total_tokens']}")

            # Small delay to avoid overwhelming the API
            time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n❌ HANG DETECTED at attempt {i}")
            print(f"   Successful before hang: {successful}/{i-1}")
            print("\n⚠️  CONNECTION POOL EXHAUSTION LIKELY")
            return

        except Exception as e:
            print(f"  ❌ Error on attempt {i}: {e}")
            import traceback
            traceback.print_exc()
            break

    print(f"\n✅ ALL {max_attempts} ATTEMPTS SUCCESSFUL")
    print(f"   Total successful: {successful}")
    print("\n💡 No connection pool issue detected with this test")

if __name__ == "__main__":
    main()
