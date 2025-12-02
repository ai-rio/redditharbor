#!/usr/bin/env python3
"""
Debug script to test the RED phase of TDD
"""

from unittest.mock import Mock
from orchestration.pipeline_orchestrator import PipelineOrchestrator, PipelineConfiguration
import pytest

def debug_test():
    """Debug the test method existence"""

    # Mock all dependencies
    mock_reddit_client = Mock()
    mock_analyzer_factory = Mock()
    mock_database_loader = Mock()
    mock_validator = Mock()
    mock_staging_layer = Mock()
    mock_settings = Mock()

    # Create orchestrator with mocked dependencies
    orchestrator = PipelineOrchestrator(
        reddit_client=mock_reddit_client,
        analyzer_factory=mock_analyzer_factory,
        database_loader=mock_database_loader,
        validator=mock_validator,
        staging_layer=mock_staging_layer,
        settings=mock_settings
    )

    print("=== RED Phase Debug ===")
    print("1. Checking if method exists:")
    has_method = hasattr(orchestrator, '_filter_by_quality')
    print(f"   hasattr(orchestrator, '_filter_by_quality') = {has_method}")

    print("2. Testing direct method call:")
    try:
        result = orchestrator._filter_by_quality([], PipelineConfiguration())
        print(f"   Method call succeeded unexpectedly with result: {result}")
    except AttributeError as e:
        print(f"   AttributeError raised as expected: {e}")
        print("   ✓ RED test working correctly - method doesn't exist")
    except Exception as e:
        print(f"   Unexpected exception: {type(e).__name__}: {e}")

    print("3. Testing pytest.raises:")
    try:
        with pytest.raises(AttributeError, match=".*_filter_by_quality.*"):
            orchestrator._filter_by_quality([], PipelineConfiguration())
        print("   ✓ pytest.raises captured the AttributeError correctly")
    except AssertionError as e:
        print(f"   ✗ pytest.raises failed: {e}")
    except Exception as e:
        print(f"   Unexpected exception in pytest.raises: {type(e).__name__}: {e}")

if __name__ == "__main__":
    debug_test()