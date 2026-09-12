"""
Chaos Fault Injection: State, Workflow & Checkpointing Layer.

Tests workflow resilience under process crashes, node interruptions,
checkpoint corruption, and duplicate replayed execution events.
"""

import sys
from typing import Dict, Any, Optional
from chaos.base import BaseFaultInjector, ChaosConfig


class StateCorruptionException(RuntimeError):
    """Raised when an agent state dictionary has been corrupted or truncated."""
    pass


class NodeExecutionException(RuntimeError):
    """Raised when an individual graph node crashes."""
    pass


class StateFaultInjector(BaseFaultInjector):
    """Fault injector intercepting LangGraph state transitions and checkpoints."""

    def intercept_state(self, current_state: Dict[str, Any], node_name: str) -> Optional[Dict[str, Any]]:
        """
        Intercept state before or after a node runs.
        
        Returns:
            Mutated state dict or None.
        """
        if not self.config.should_inject("state"):
            return None

        fault = self.config.state_fault

        if fault == "PROCESS_KILL":
            self.record_injection(f"node:{node_name}", "PROCESS_KILL", {"state_keys": list(current_state.keys())})
            # Simulates an ungraceful SIGKILL / process termination
            raise NodeExecutionException(f"Simulated abrupt process termination at node '{node_name}'")

        elif fault == "STATE_CORRUPTION":
            self.record_injection(f"node:{node_name}", "STATE_CORRUPTION", {"corrupted_keys": ["messages", "plan"]})
            # Injects bad types or deleted fields
            corrupted = dict(current_state)
            corrupted["messages"] = None
            corrupted["corrupted"] = True
            return corrupted

        elif fault == "EVENT_DUPLICATION":
            self.record_injection(f"node:{node_name}", "EVENT_DUPLICATION", {})
            # Duplicates the last message or step
            duplicated = dict(current_state)
            if "messages" in duplicated and isinstance(duplicated["messages"], list) and duplicated["messages"]:
                duplicated["messages"].append(duplicated["messages"][-1])
            return duplicated

        return None
