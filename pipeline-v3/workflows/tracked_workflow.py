from typing import Any
import uuid

from agno.workflow import Workflow
from monitoring.agentops_tracker import get_tracker


class TrackedWorkflow(Workflow):
    """
    Workflow with AgentOps tracking and cost monitoring capabilities.

    TrackedWorkflow extends Agno's Workflow class to provide:
    - Optional AgentOps session tracking for observability
    - Cost tracking integration
    - Session lifecycle management

    IMPORTANT: Subclasses that override run() MUST call super().run() to ensure
    proper session tracking and cleanup. Without this, AgentOps sessions will not
    be managed correctly.

    Attributes:
        name: Workflow name
        config: Optional configuration dictionary
        enable_agentops: Enable AgentOps tracking (default: False)
        cost_tracker: Optional cost tracker instance
        session_id: Unique identifier for this workflow session
        session_state: Current state of the workflow session
        agentops_tracker: AgentOps tracker instance (None if disabled or unavailable)
        _workflow_session: Internal session tracking state
    """

    def __init__(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        enable_agentops: bool = False,
        cost_tracker=None
    ):
        """
        Initialize TrackedWorkflow with optional tracking capabilities.
        
        Args:
            name: Workflow name identifier
            config: Optional configuration dictionary
            enable_agentops: Enable AgentOps tracking (default: False)
            cost_tracker: Optional cost tracker instance
        """
        self.name = name
        self.config = config or {}
        self.enable_agentops = enable_agentops
        self.cost_tracker = cost_tracker

        # Generate unique session ID for tracking and correlation
        self.session_id = str(uuid.uuid4())

        # Initialize session state
        self.session_state = "initialized"

        # Initialize workflow session tracking
        self._workflow_session = {"active": False, "session_id": None}

        # Initialize AgentOps tracker if enabled
        # Gracefully degrades to None if tracker unavailable
        if self.enable_agentops:
            try:
                self.agentops_tracker = get_tracker()
            except Exception:
                # Fail gracefully if AgentOps not available
                self.agentops_tracker = None
        else:
            self.agentops_tracker = None

    def track_cost(self, amount: float, category: str = "general") -> None:
        """
        Track a cost amount using the configured cost tracker.
        
        Args:
            amount: Cost amount to track
            category: Cost category for grouping (default: "general")
        """
        if self.cost_tracker:
            self.cost_tracker.track_cost(amount, category)

    def run(self, *args, **kwargs):
        """
        Execute the workflow with optional AgentOps session tracking.

        Manages the complete session lifecycle:
        - Starts an AgentOps session before workflow execution
        - Executes the workflow logic via super().run()
        - Ends the session with appropriate status (success/error)

        NOTE: Subclasses should NOT override this method. Instead, implement
        workflow logic in a separate method and call it from here, or ensure
        super().run() is called if overridden.

        Returns:
            Result from the workflow execution

        Raises:
            Exception: Any exception from workflow execution is re-raised
        """
        session_id = None
        session_success = True

        try:
            # Start AgentOps session if tracking is enabled
            if self.enable_agentops and hasattr(self, 'agentops_tracker') and self.agentops_tracker:
                session_id = self.agentops_tracker.start_session(
                    session_name=self.name,
                    tags=["workflow", "tracked_workflow"]
                )
            # Call the actual workflow run method
            # This will execute the overridden method in subclasses
            result = super().run(*args, **kwargs)
            return result
        except Exception:
            session_success = False
            raise
        finally:
            # End AgentOps session if it was started
            if session_id and self.enable_agentops and hasattr(self, 'agentops_tracker') and self.agentops_tracker:
                status = "success" if session_success else "error"
                self.agentops_tracker.end_session(
                    status=status,
                    metadata={"workflow_name": self.name}
                )
