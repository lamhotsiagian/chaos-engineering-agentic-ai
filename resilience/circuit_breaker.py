"""
Resilience Engineering: Circuit Breaker State Machine.

Protects against cascading failures and self-inflicted Denial of Service (DoS)
on struggling dependencies (Ollama LLMs, Vector DBs, External Tool APIs).

States:
- CLOSED: Normal execution. Failures are counted.
- OPEN: Tripped when failure threshold is exceeded. Fails fast immediately.
- HALF_OPEN: Trial period after recovery timeout to probe service recovery.
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent
from observability.metrics import global_metrics


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(RuntimeError):
    """Raised immediately when a call is attempted against an OPEN circuit."""
    pass


class CircuitBreaker:
    """
    Thread-safe implementation of the Circuit Breaker pattern.
    """

    def __init__(
        self,
        name: str = "default_breaker",
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 5.0,
        half_open_success_threshold: int = 1
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.half_open_success_threshold = half_open_success_threshold

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_state_change: float = time.time()
        self._lock = threading.Lock()

    def _transition_to(self, new_state: CircuitState) -> None:
        """Internal helper to transition state and emit events."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = time.time()
        logger.warning(f"[CIRCUIT BREAKER: {self.name}] Transitioned {old_state} -> {new_state}")
        
        global_event_bus.publish(ChaosEvent(
            event_type="CIRCUIT_BREAKER_STATE_CHANGE",
            component=self.name,
            details={"old_state": old_state.value, "new_state": new_state.value}
        ))
        
        if new_state == CircuitState.OPEN:
            global_metrics.record_circuit_trip()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker guard.
        """
        with self._lock:
            now = time.time()

            # Check if OPEN circuit should transition to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if now - self.last_state_change >= self.recovery_timeout_sec:
                    self._transition_to(CircuitState.HALF_OPEN)
                    self.failure_count = 0
                    self.success_count = 0
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit '{self.name}' is OPEN. Fast failing to protect dependency. "
                        f"Retry in {round(self.recovery_timeout_sec - (now - self.last_state_change), 1)}s"
                    )

        # Execute call
        try:
            result = func(*args, **kwargs)
            with self._lock:
                self._on_success()
            return result
        except Exception as exc:
            with self._lock:
                self._on_failure(exc)
            raise exc

    def _on_success(self) -> None:
        """Handle successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self, exc: Exception) -> None:
        """Handle failed execution."""
        self.failure_count += 1
        logger.warning(f"[CIRCUIT BREAKER: {self.name}] Failure {self.failure_count}/{self.failure_threshold} ({type(exc).__name__})")
        
        if self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN):
            if self.failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
