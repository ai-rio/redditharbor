"""Unified pipeline orchestration.

This module provides the unified pipeline infrastructure for opportunity
discovery, replacing the monolithic batch_opportunity_scoring.py and
dlt_trust_pipeline.py scripts.

Key Components:
- OpportunityPipeline: Main pipeline orchestrator
- ServiceFactory: Service creation and dependency injection
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
from core.pipeline.factory import ServiceFactory

__all__ = [
    "OpportunityPipeline",
    "ServiceFactory",
    "PipelineConfig",
    "DataSource",
    "ServiceType",
]
