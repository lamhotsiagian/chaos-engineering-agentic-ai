"""
Resilience Engineering: Retry Policy & Idempotent Execution.

Retrying in Agentic AI is dangerous without guardrails:
1. Retrying non-idempotent tools causes duplicate transactions (e.g., sending two emails).
2. Retrying without backoff creates 'retry storms' that crash local LLM inference engines.

This module implements Exponential Backoff with Jitter and an Idempotency Registry.
"""

import time
import random
import uuid
from typing import Callable, Any, Optional, Set, Dict, Type, Tuple
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent


class DuplicateExecutionError(RuntimeError):
    """Raised when an operation with the same idempotency key is re-executed dangerously."""
    pass


class IdempotencyRegistry:
    """
    In-memory registry for tracking idempotency keys across tool calls.
    Guarantees that side-effecting operations (e.g. notifications, database writes)
    are executed at most once per unique request.
    """

    def __init__(self):
        self._executed_keys: Dict[str, Any] = {}

    def is_executed(self, key: str) -> bool:
        """Check if an idempotency key has already been processed."""
        return key in self._executed_keys

    def record_execution(self, key: str, result: Any) -> None:
        """Record the successful result of an idempotent operation."""
        self._executed_keys[key] = result

    def get_result(self, key: str) -> Optional[Any]:
        """Retrieve the cached output of an already executed idempotent action."""
        return self._executed_keys.get(key)

    def clear(self) -> None:
        """Clear registry history."""
        self._executed_keys.clear()


# Global idempotency registry singleton
global_idempotency_registry = IdempotencyRegistry()


class RetryPolicy:
    """
    Exponential backoff retry policy with jitter.
    
    Formula:
        sleep_duration = min(max_backoff, initial_backoff * (backoff_factor ** attempt)) + jitter
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_sec: float = 0.5,
        backoff_factor: float = 2.0,
        max_backoff_sec: float = 5.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_retries = max_retries
        self.initial_backoff_sec = initial_backoff_sec
        self.backoff_factor = backoff_factor
        self.max_backoff_sec = max_backoff_sec
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a callable wrapped with the retry policy.
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as exc:
                last_exception = exc
                if attempt == self.max_retries:
                    logger.error(f"[RETRY EXHAUSTED] After {attempt} retries: {exc}")
                    raise exc

                # Calculate exponential backoff
                backoff = min(
                    self.max_backoff_sec,
                    self.initial_backoff_sec * (self.backoff_factor ** attempt)
                )
                if self.jitter:
                    backoff += random.uniform(0.0, 0.2 * backoff)

                logger.warning(
                    f"[RETRY TRIGGERED] Attempt {attempt + 1}/{self.max_retries}. "
                    f"Backing off for {backoff:.2f}s due to: {type(exc).__name__}: {exc}"
                )
                global_event_bus.publish(ChaosEvent(
                    event_type="RETRY_TRIGGERED",
                    component=getattr(func, "__name__", "callable"),
                    details={"attempt": attempt + 1, "backoff_sec": round(backoff, 2), "error": str(exc)}
                ))
                time.sleep(backoff)

        raise last_exception
