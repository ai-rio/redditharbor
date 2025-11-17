#!/usr/bin/env python3
"""
Minimal test to reproduce the connection pool exhaustion with litellm.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

print("Testing litellm connection pool behavior...")
print("="*80)

# Import HTTP client config (triggers auto-init)
import core.http_client_config

# Import litellm
import litellm

print(f"\nlitellm.client configured: {litellm.client is not None}")
if litellm.client:
    print(f"Client type: {type(litellm.client)}")
    if hasattr(litellm.client, '_limits'):
        print(f"Client limits: {litellm.client._limits}")

# Try making multiple sequential calls
print("\nMaking 10 sequential litellm calls...")
for i in range(10):
    try:
        print(f"  Call {i+1}...", end=" ", flush=True)
        response = litellm.completion(
            model="openrouter/anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5,
            timeout=10
        )
        print(f"✓ Success ({response.usage.total_tokens} tokens)")
    except Exception as e:
        print(f"✗ Failed: {e}")
        break

print("\n" + "="*80)
print("Test complete!")
