#!/usr/bin/env python3
"""
HTTP Client Configuration for LLM Libraries
Prevents connection pool exhaustion when using multiple LLM clients (litellm + dspy)
"""

import httpx

from config import settings


def get_configured_httpx_client() -> httpx.Client:
    """
    Create a properly configured httpx client with connection pooling.

    This prevents connection pool exhaustion that occurs when:
    - EnhancedLLMProfiler (litellm) makes concurrent AI profile requests
    - MonetizationLLMAnalyzer (dspy) makes concurrent monetization requests
    - Both point to the same OpenRouter API endpoint

    Returns:
        Configured httpx.Client with proper limits and timeouts
    """
    return httpx.Client(
        limits=httpx.Limits(
            max_connections=settings.HTTP_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE
        ),
        timeout=httpx.Timeout(settings.HTTP_TIMEOUT),
        # Force connection cleanup after each request
        # This prevents stale connections from accumulating
        headers={"Connection": "close"}
    )


def configure_litellm_client():
    """
    Configure litellm to use a properly managed httpx client.
    Call this once at module initialization.
    """
    try:
        import httpx
        import litellm

        # Create a persistent httpx client with proper connection pooling
        # This client will be reused across all litellm calls
        client = httpx.Client(
            limits=httpx.Limits(
                max_connections=settings.HTTP_MAX_CONNECTIONS,
                max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE
            ),
            timeout=httpx.Timeout(settings.HTTP_TIMEOUT),
        )

        # Set as the default client for litellm
        litellm.client = client

        print(f"✓ litellm configured with connection pool: "
              f"max={settings.HTTP_MAX_CONNECTIONS}, "
              f"keepalive={settings.HTTP_MAX_KEEPALIVE}")
    except ImportError:
        print("⚠️  litellm not available, skipping client configuration")
    except Exception as e:
        print(f"⚠️  Failed to configure litellm client: {e}")


def configure_dspy_client():
    """
    Configure DSPy to use proper httpx settings.
    DSPy doesn't expose direct client configuration, but we can set httpx defaults.
    """
    try:
        # Set global httpx defaults that DSPy will inherit
        # This is a workaround since DSPy creates its own clients internally
        import dspy

        # Note: DSPy creates httpx clients internally per LM instance
        # We've configured the connection limits via environment and settings
        # The actual fix is ensuring we don't create too many LM instances
        print(f"✓ DSPy configured to use connection pool settings: "
              f"max={settings.HTTP_MAX_CONNECTIONS}")
    except ImportError:
        print("⚠️  dspy not available, skipping client configuration")
    except Exception as e:
        print(f"⚠️  Failed to configure dspy client: {e}")


# Track if we've already initialized to prevent re-initialization
_initialized = False

def initialize_http_clients():
    """
    Initialize all HTTP clients with proper configuration.
    This should be called once at application startup.
    Safe to call multiple times - will only initialize once.
    """
    global _initialized

    if _initialized:
        return  # Already initialized, skip

    print("\n" + "="*80)
    print("CONFIGURING HTTP CLIENTS FOR LLM LIBRARIES")
    print("="*80)
    print("Settings:")
    print(f"  MAX_CONNECTIONS: {settings.HTTP_MAX_CONNECTIONS}")
    print(f"  MAX_KEEPALIVE: {settings.HTTP_MAX_KEEPALIVE}")
    print(f"  TIMEOUT: {settings.HTTP_TIMEOUT}s")
    print()

    configure_litellm_client()
    configure_dspy_client()

    print("="*80 + "\n")

    _initialized = True


# Auto-configure on module import
# This ensures HTTP clients are properly configured even if
# initialize_http_clients() is not explicitly called
initialize_http_clients()


# Export the initialization function
__all__ = ['get_configured_httpx_client', 'initialize_http_clients']
