"""Test agentops_enabled configuration field"""

import sys
from pathlib import Path

# Add pipeline-v3 to path
sys.path.insert(0, str(Path(__file__).parent))

def test_agentops_enabled_field():
    """Test that agentops_enabled field exists with correct defaults"""
    from config.settings import Settings

    settings = Settings.create_for_testing()

    # This will fail initially (RED phase)
    assert hasattr(settings, 'agentops_enabled')
    assert isinstance(settings.agentops_enabled, bool)
    assert settings.agentops_enabled is False