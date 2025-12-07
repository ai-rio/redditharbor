from typing import Optional, Dict, Any


class CostTracker:
    """Minimal CostTracker implementation for TDD"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CostTracker"""
        self.config = config or {}
        self.total_cost = 0.0

    def track_cost(self, amount: float, category: str = "general") -> None:
        """Track a cost amount"""
        self.total_cost += amount

    def get_total_cost(self) -> float:
        """Get total tracked cost"""
        return self.total_cost

    def reset(self) -> None:
        """Reset the cost tracker"""
        self.total_cost = 0.0
