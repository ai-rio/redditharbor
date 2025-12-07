from typing import Dict, Any, Optional


class TrackedWorkflow:
    """Minimal TrackedWorkflow implementation for TDD"""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enable_agentops: bool = False,
        cost_tracker=None
    ):
        """Initialize TrackedWorkflow"""
        self.name = name
        self.config = config or {}
        self.enable_agentops = enable_agentops
        self.cost_tracker = cost_tracker

        # Initialize AgentOps tracker if enabled
        if self.enable_agentops:
            self.agentops_tracker = None

    def track_cost(self, amount: float, category: str = "general") -> None:
        """Track a cost amount"""
        if self.cost_tracker:
            self.cost_tracker.track_cost(amount, category)
