"""Supabase client configuration with timeout management.

This module provides a centralized Supabase client factory with proper timeout
configuration for database operations. Extends default timeouts to handle
large data fetches and batch processing operations.

Usage:
    from core.clients import get_supabase_client
    client = get_supabase_client()
"""

from typing import Any

from supabase.client import ClientOptions

# Import configuration with fallback for different import contexts
try:
    from config.settings import SUPABASE_KEY, SUPABASE_URL
except ImportError:
    # Fallback for direct execution
    import os
    from dotenv import load_dotenv
    load_dotenv('/home/carlos/projects/redditharbor-core-functions-fix/.env.local')
    SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54330")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your_supabase_service_role_key_here")

from supabase import create_client


def get_supabase_client(
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    postgrest_timeout: int = 180,
    storage_timeout: int = 30,
    schema: str = "public"
) -> Any:
    """
    Create a Supabase client with extended timeout configuration.

    Provides timeout-configured Supabase client to prevent connection timeouts
    during database operations, especially for batch processing and large data
    fetches. Uses extended PostgREST timeout (3 minutes) instead of default 60s.

    Args:
        supabase_url: Supabase URL (defaults to config setting)
        supabase_key: Supabase API key (defaults to config setting)
        postgrest_timeout: PostgREST client timeout in seconds (default: 180)
        storage_timeout: Storage client timeout in seconds (default: 30)
        schema: Database schema to use (default: "public")

    Returns:
        Configured Supabase client instance

    Raises:
        ValueError: If required configuration is missing

    Examples:
        >>> from core.clients import get_supabase_client
        >>> client = get_supabase_client()
        >>> # Custom timeout settings
        >>> client = get_supabase_client(postgrest_timeout=300)
    """
    # Use provided values or fall back to config
    url = supabase_url or SUPABASE_URL
    key = supabase_key or SUPABASE_KEY

    # Validate configuration
    if not url:
        raise ValueError("Supabase URL is required. Set SUPABASE_URL in config or provide as parameter.")

    if not key:
        raise ValueError("Supabase key is required. Set SUPABASE_KEY in config or provide as parameter.")

    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid Supabase URL format: {url}")

    # Create client options with extended timeouts
    client_options = ClientOptions(
        postgrest_client_timeout=postgrest_timeout,  # Extended for large queries
        storage_client_timeout=storage_timeout,      # Standard timeout for storage
        schema=schema                                 # Use specified schema
    )

    # Create and return the configured client
    client = create_client(url, key, options=client_options)

    return client


def get_default_client() -> Any:
    """
    Get a Supabase client with default timeout settings.

    Convenience function that returns a Supabase client with the recommended
    timeout configuration for most use cases (3-minute PostgREST timeout).

    Returns:
        Configured Supabase client instance

    Examples:
        >>> from core.clients import get_default_client
        >>> client = get_default_client()
        >>> response = client.table('submissions').select('*').execute()
    """
    return get_supabase_client()


def create_test_client() -> Any:
    """
    Create a Supabase client optimized for testing environments.

    Uses shorter timeouts suitable for test environments while still preventing
    timeout failures during database operations.

    Returns:
        Configured Supabase client instance for testing

    Examples:
        >>> from core.clients import create_test_client
        >>> client = create_test_client()
        >>> # Use in test scenarios
    """
    return get_supabase_client(
        postgrest_timeout=120,  # 2 minutes for testing
        storage_timeout=15      # Faster storage timeout for tests
    )


def validate_client_connection(client: Any) -> bool:
    """
    Validate that the Supabase client can connect to the database.

    Performs a simple connectivity check to ensure the client is properly
    configured and can reach the Supabase instance.

    Args:
        client: Supabase client instance to validate

    Returns:
        True if connection is successful, False otherwise

    Examples:
        >>> from core.clients import get_supabase_client, validate_client_connection
        >>> client = get_supabase_client()
        >>> if validate_client_connection(client):
        ...     print("Database connection successful")
    """
    try:
        # Simple ping to check connection
        response = client.table('_temp_connection_check').select('1').limit(1).execute()
        return True
    except Exception:
        # Try alternative connection check
        try:
            # Use a simple count query as fallback
            response = client.rpc('version').execute()
            return True
        except Exception:
            return False
