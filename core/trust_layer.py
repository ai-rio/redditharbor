"""Backward compatibility shim - import from core.trust.legacy_layer instead.

DEPRECATED: This module provides backward compatibility for existing code
that imports from core.trust_layer. New code should import from core.trust.
"""
from core.trust.legacy_layer import *  # noqa: F401, F403
