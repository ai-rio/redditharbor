from typing import Any
import uuid

from agno.workflow import Workflow


class TrackedWorkflow(Workflow):
    """Minimal TrackedWorkflow implementation for TDD"""

    def __init__(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        enable_agentops: bool = False,
        cost_tracker=None
    ):
        """Initialize TrackedWorkflow"""
        self.name = name
        self.config = config or {}
        self.enable_agentops = enable_agentops
        self.cost_tracker = cost_tracker

        # Generate unique session ID
        self.session_id = str(uuid.uuid4())

        # Initialize session state
        self.session_state = "initialized"

        # Initialize AgentOps tracker if enabled
        if self.enable_agentops:
            self.agentops_tracker = None

    def track_cost(self, amount: float, category: str = "general") -> None:
        """Track a cost amount"""
        if self.cost_tracker:
            self.cost_tracker.track_cost(amount, category)

    def run(self):
        session_id = None
        try:
            if self.enable_agentops and hasattr(self, 'agentops_tracker') and self.agentops_tracker:
                session_id = self.agentops_tracker.start_session(
                    session_name=self.name,
                    tags=["workflow", "tracked_workflow"]
                )
            return super().run()
        except Exception:
            raise
        finally:
            if session_id and self.enable_agentops and hasattr(self, 'agentops_tracker') and self.agentops_tracker:
                self.agentops_tracker.end_session(
                    status="success",
                    metadata={"workflow_name": self.name}
                )
