"""
Resilience Engineering: Strict Timeout & Deadline Controller.

Unbounded latency in LLM generation or downstream tool APIs will freeze
agent loops, tie up worker threads, and degrade system responsiveness.
This module enforces strict wall-clock execution deadlines.
"""

import concurrent.futures
from typing import Callable, Any, Optional
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent


class ExecutionTimeoutException(TimeoutError):
    """Raised when an operation exceeds its configured execution deadline."""
    pass


class TimeoutPolicy:
    """
    Enforces a strict execution deadline on any synchronous function.
    """

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute the target callable inside a thread pool with a timeout boundary.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError:
                func_name = getattr(func, "__name__", "operation")
                logger.error(f"[TIMEOUT EXCEEDED] '{func_name}' exceeded {self.timeout_seconds}s limit")
                global_event_bus.publish(ChaosEvent(
                    event_type="TIMEOUT_TRIGGERED",
                    component=func_name,
                    details={"timeout_seconds": self.timeout_seconds}
                ))
                raise ExecutionTimeoutException(
                    f"Execution of '{func_name}' exceeded deadline of {self.timeout_seconds}s"
                )
