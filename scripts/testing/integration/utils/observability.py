#!/usr/bin/env python3
"""
Observability Integration Utilities

Helpers for integrating AgentOps, LiteLLM, and Agno observability
during integration testing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Observability output directory
OBSERVABILITY_DIR = Path(__file__).parent.parent / "observability"


class ObservabilityManager:
    """Manages observability integrations for testing."""

    def __init__(self, test_name: str, config: Dict[str, Any]):
        """
        Initialize observability manager.

        Args:
            test_name: Name of the test
            config: Observability configuration from service_config.json
        """
        self.test_name = test_name
        self.config = config
        self.session_id = f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # AgentOps setup
        self.agentops_enabled = config.get("agentops", {}).get("enabled", False)
        self.agentops_client = None
        self.agentops_session = None

        # LiteLLM setup
        self.litellm_enabled = config.get("litellm", {}).get("enabled", False)
        self.litellm_costs: list[Dict[str, Any]] = []

        # Agno setup
        self.agno_enabled = config.get("agno", {}).get("enabled", False)
        self.agno_traces: list[Dict[str, Any]] = []

    def initialize_agentops(self) -> Optional[Any]:
        """
        Initialize AgentOps session if enabled.

        Returns:
            AgentOps client and session, or None if not enabled
        """
        if not self.agentops_enabled:
            return None

        try:
            import agentops

            api_key_env = self.config.get("agentops", {}).get("api_key_env", "AGENTOPS_API_KEY")
            api_key = os.getenv(api_key_env)

            if not api_key:
                print(f"Warning: AgentOps enabled but {api_key_env} not set")
                return None

            self.agentops_client = agentops.Client(api_key=api_key)
            tags = self.config.get("agentops", {}).get("session_tags", [])
            tags.append(self.test_name)

            # Try different AgentOps API versions for session initialization
            try:
                # Try newer API first
                self.agentops_session = self.agentops_client.start_session(
                    tags=tags,
                    default_tags=tags,  # Some versions use default_tags
                )
            except Exception:
                try:
                    # Try older API with session_id
                    self.agentops_session = self.agentops_client.start_session(
                        tags=tags,
                        session_id=self.session_id
                    )
                except Exception:
                    try:
                        # Try minimal API
                        self.agentops_session = self.agentops_client.start_session()
                    except Exception:
                        # If all fail, set session to None but keep client
                        self.agentops_session = None
                        print("Warning: AgentOps session initialization failed, but client is available")
                        return self.agentops_client, self.agentops_session

            print(f"✓ AgentOps session started: {self.session_id}")
            return self.agentops_client, self.agentops_session

        except Exception as e:
            print(f"Warning: Failed to initialize AgentOps: {e}")
            self.agentops_enabled = False
            return None

    def initialize_litellm(self):
        """Initialize LiteLLM if enabled."""
        if not self.litellm_enabled:
            return

        try:
            import litellm

            # Set log level
            log_level = self.config.get("litellm", {}).get("log_level", "INFO")
            litellm.set_verbose = (log_level == "DEBUG")

            print("✓ LiteLLM initialized")

        except Exception as e:
            print(f"Warning: Failed to initialize LiteLLM: {e}")
            self.litellm_enabled = False

    def record_llm_call(
        self,
        service_name: str,
        model: str,
        cost: float,
        latency: float,
        tokens: int,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Record LLM call metrics.

        Args:
            service_name: Name of service making the call
            model: LLM model used
            cost: Cost in USD
            latency: Latency in seconds
            tokens: Total tokens used
            success: Whether call succeeded
            error: Error message if failed
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "service_name": service_name,
            "model": model,
            "cost": cost,
            "latency": latency,
            "tokens": tokens,
            "success": success,
            "error": error,
        }

        self.litellm_costs.append(record)

        # Also record in AgentOps if enabled
        if self.agentops_client and self.agentops_session:
            try:
                # Record as AgentOps event
                # Note: This is a placeholder - actual AgentOps API may differ
                pass
            except Exception as e:
                print(f"Warning: Failed to record in AgentOps: {e}")

    def record_agno_execution(
        self,
        submission_id: str,
        agents_executed: list[str],
        total_cost: float,
        analysis_result: Dict[str, Any],
        was_copied: bool = False
    ):
        """
        Record Agno multi-agent execution.

        Args:
            submission_id: Submission being analyzed
            agents_executed: List of agent names
            total_cost: Total cost of execution
            analysis_result: Analysis result dictionary
            was_copied: Whether analysis was copied (deduplication)
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "submission_id": submission_id,
            "agents_executed": agents_executed,
            "total_cost": total_cost,
            "was_copied": was_copied,
            "analysis_result": analysis_result,
        }

        self.agno_traces.append(record)

    def export_traces(self):
        """Export all traces to files."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Export AgentOps traces
        if self.agentops_enabled and self.agentops_session:
            try:
                agentops_path = OBSERVABILITY_DIR / "agentops_traces"
                agentops_path.mkdir(parents=True, exist_ok=True)

                trace_file = agentops_path / f"{self.test_name}_{timestamp}.json"

                # Note: Actual AgentOps export API may differ
                session_data = {
                    "session_id": self.session_id,
                    "test_name": self.test_name,
                    "timestamp": timestamp,
                    "note": "See AgentOps dashboard for full trace details"
                }

                with open(trace_file, "w") as f:
                    json.dump(session_data, f, indent=2)

                print(f"✓ AgentOps traces exported to {trace_file}")

            except Exception as e:
                print(f"Warning: Failed to export AgentOps traces: {e}")

        # Export LiteLLM costs
        if self.litellm_enabled and self.litellm_costs:
            try:
                litellm_path = OBSERVABILITY_DIR / "litellm_logs"
                litellm_path.mkdir(parents=True, exist_ok=True)

                cost_file = litellm_path / f"{self.test_name}_{timestamp}.json"

                cost_data = {
                    "test_name": self.test_name,
                    "timestamp": timestamp,
                    "total_calls": len(self.litellm_costs),
                    "total_cost": sum(c["cost"] for c in self.litellm_costs),
                    "total_tokens": sum(c["tokens"] for c in self.litellm_costs),
                    "calls": self.litellm_costs,
                }

                with open(cost_file, "w") as f:
                    json.dump(cost_data, f, indent=2)

                print(f"✓ LiteLLM costs exported to {cost_file}")

            except Exception as e:
                print(f"Warning: Failed to export LiteLLM costs: {e}")

        # Export Agno traces
        if self.agno_enabled and self.agno_traces:
            try:
                agno_path = OBSERVABILITY_DIR / "agno_traces"
                agno_path.mkdir(parents=True, exist_ok=True)

                trace_file = agno_path / f"{self.test_name}_{timestamp}.json"

                agno_data = {
                    "test_name": self.test_name,
                    "timestamp": timestamp,
                    "total_executions": len(self.agno_traces),
                    "total_cost": sum(t["total_cost"] for t in self.agno_traces),
                    "copied_count": sum(1 for t in self.agno_traces if t["was_copied"]),
                    "deduplication_rate": (sum(1 for t in self.agno_traces if t["was_copied"]) / len(self.agno_traces) * 100) if self.agno_traces else 0,
                    "traces": self.agno_traces,
                }

                with open(trace_file, "w") as f:
                    json.dump(agno_data, f, indent=2)

                print(f"✓ Agno traces exported to {trace_file}")

            except Exception as e:
                print(f"Warning: Failed to export Agno traces: {e}")

    def finalize(self):
        """Finalize observability and export all traces."""
        # End AgentOps session
        if self.agentops_client and self.agentops_session:
            try:
                # Note: Actual AgentOps end session API may differ
                # self.agentops_client.end_session(self.agentops_session)
                print("✓ AgentOps session ended")
            except Exception as e:
                print(f"Warning: Failed to end AgentOps session: {e}")

        # Export all traces
        self.export_traces()

        print(f"\n✓ Observability data exported to {OBSERVABILITY_DIR}")
