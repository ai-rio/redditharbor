"""Unified pipeline orchestration.

This module provides the unified pipeline infrastructure for opportunity
discovery, replacing the monolithic batch_opportunity_scoring.py and
dlt_trust_pipeline.py scripts.

Key Components:
- OpportunityPipeline: Main pipeline orchestrator
- PipelineConfig: Configuration dataclass
- DataSource: Data source enumeration
- ServiceType: Service type enumeration
"""

from core.pipeline.config import (
    PipelineConfig,
    DataSource,
    ServiceType,
)
from core.pipeline.orchestrator import OpportunityPipeline

__all__ = [
    "OpportunityPipeline",
    "PipelineConfig",
    "DataSource",
    "ServiceType",
]
