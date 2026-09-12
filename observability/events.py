"""
Observability: Event Bus for Agentic AI Chaos Experiments.

Provides an asynchronous/in-process pub-sub event bus enabling decoupled
real-time telemetry between the LangGraph execution runtime, Chaos Injectors,
Resilience Controllers, and the Streamlit Dashboard.
"""

import time
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ChaosEvent:
    """
    Structured telemetry event emitted during agent execution or chaos testing.
    
    Event types:
        - 'NODE_START' / 'NODE_END' / 'NODE_ERROR'
        - 'FAULT_INJECTED'
        - 'FALLBACK_TRIGGERED'
        - 'CIRCUIT_BREAKER_STATE_CHANGE'
        - 'BUDGET_WARNING' / 'BUDGET_EXCEEDED'
        - 'KILL_SWITCH_ENGAGED'
        - 'HUMAN_ESCALATION'
    """
    event_type: str
    component: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    trace_id: Optional[str] = None


class EventBus:
    """In-memory Pub/Sub event dispatcher."""

    def __init__(self):
        self._subscribers: List[Callable[[ChaosEvent], None]] = []
        self._history: List[ChaosEvent] = []

    def subscribe(self, callback: Callable[[ChaosEvent], None]) -> None:
        """Register an event listener callback."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[ChaosEvent], None]) -> None:
        """Unregister an event listener callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, event: ChaosEvent) -> None:
        """Emit an event to all registered subscribers and append to in-memory history."""
        self._history.append(event)
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception:
                # Observers must never crash the primary execution path
                pass

    def get_history(self, limit: int = 50) -> List[ChaosEvent]:
        """Return the most recent emitted events."""
        return self._history[-limit:]

    def clear(self) -> None:
        """Clear all event history."""
        self._history.clear()


# Global singleton instance
global_event_bus = EventBus()
