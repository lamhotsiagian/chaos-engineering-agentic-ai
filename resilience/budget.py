"""
Resilience Engineering: Agent Execution Budget Controller.

Autonomous agents can enter pathological execution loops (e.g. repeated failed tool
calls, cyclic reasoning, or infinite self-reflections). This module places hard
limits on execution iterations, tool calls, model calls, and total execution time.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent
from observability.metrics import global_metrics


class BudgetExhaustedException(RuntimeError):
    """Raised when an autonomous agent exceeds its allotted execution budget."""
    pass


@dataclass
class BudgetConfig:
    """Configurable limits for an agent execution lifecycle."""
    max_iterations: int = 5
    max_tool_calls: int = 10
    max_model_calls: int = 10
    max_execution_time_sec: float = 30.0


class BudgetController:
    """
    Monitors and enforces resource consumption during an agent loop.
    """

    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        self.iteration_count: int = 0
        self.tool_call_count: int = 0
        self.model_call_count: int = 0
        self.start_time: float = time.time()

    def reset(self) -> None:
        """Reset budget counters for a new execution turn."""
        self.iteration_count = 0
        self.tool_call_count = 0
        self.model_call_count = 0
        self.start_time = time.time()

    @property
    def elapsed_time_sec(self) -> float:
        """Calculate elapsed wall-clock execution time."""
        return time.time() - self.start_time

    def check_and_increment_iteration(self) -> None:
        """Record an iteration cycle and check against limit."""
        self.iteration_count += 1
        self._validate()

    def check_and_increment_tool(self, count: int = 1) -> None:
        """Record tool invocations and check against limit."""
        self.tool_call_count += count
        global_metrics.record_tool_call(count)
        self._validate()

    def check_and_increment_model(self, count: int = 1) -> None:
        """Record model invocations and check against limit."""
        self.model_call_count += count
        global_metrics.record_model_call(count)
        self._validate()

    def _validate(self) -> None:
        """Verify that current usage does not violate budget limits."""
        elapsed = self.elapsed_time_sec

        # Check time budget
        if elapsed > self.config.max_execution_time_sec:
            self._trigger_exhaustion(
                f"Execution time {elapsed:.2f}s exceeded limit of {self.config.max_execution_time_sec}s"
            )

        # Check iteration budget
        if self.iteration_count > self.config.max_iterations:
            self._trigger_exhaustion(
                f"Iterations {self.iteration_count} exceeded limit of {self.config.max_iterations}"
            )

        # Check tool calls budget
        if self.tool_call_count > self.config.max_tool_calls:
            self._trigger_exhaustion(
                f"Tool calls {self.tool_call_count} exceeded limit of {self.config.max_tool_calls}"
            )

        # Check model calls budget
        if self.model_call_count > self.config.max_model_calls:
            self._trigger_exhaustion(
                f"Model calls {self.model_call_count} exceeded limit of {self.config.max_model_calls}"
            )

    def _trigger_exhaustion(self, reason: str) -> None:
        """Log, record metrics, and raise budget exhaustion exception."""
        logger.error(f"[BUDGET EXHAUSTED] {reason}")
        global_metrics.record_budget_exhaustion()
        global_event_bus.publish(ChaosEvent(
            event_type="BUDGET_EXCEEDED",
            component="budget_controller",
            details={
                "reason": reason,
                "iterations": self.iteration_count,
                "tool_calls": self.tool_call_count,
                "model_calls": self.model_call_count,
                "elapsed_sec": round(self.elapsed_time_sec, 2)
            }
        ))
        raise BudgetExhaustedException(f"Agent budget exhausted: {reason}")

    def to_dict(self) -> Dict[str, Any]:
        """Export current budget consumption for telemetry."""
        return {
            "iterations": f"{self.iteration_count} / {self.config.max_iterations}",
            "tool_calls": f"{self.tool_call_count} / {self.config.max_tool_calls}",
            "model_calls": f"{self.model_call_count} / {self.config.max_model_calls}",
            "elapsed_sec": f"{self.elapsed_time_sec:.1f}s / {self.config.max_execution_time_sec:.1f}s"
        }
