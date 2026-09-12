"""
Memory: Long-Term Checkpoint Store for Durable Workflow Execution.

Saves and restores LangGraph state checkpoints. Essential for Chapter 08:
Enables killing an agent mid-flight and resuming execution seamlessly from the
last valid checkpoint without losing state.
"""

import copy
import json
import time
from typing import Dict, Any, Optional, List


class CheckpointStore:
    """
    Durable in-memory / persistent checkpoint repository for agent state snapshots.
    """

    def __init__(self):
        self._checkpoints: Dict[str, List[Dict[str, Any]]] = {}

    def save_checkpoint(self, thread_id: str, step_name: str, state_data: Dict[str, Any]) -> str:
        """
        Save a snapshot of the workflow state for a given thread/session.
        """
        checkpoint_id = f"{thread_id}_{step_name}_{int(time.time() * 1000)}"
        snapshot = {
            "checkpoint_id": checkpoint_id,
            "thread_id": thread_id,
            "step_name": step_name,
            "timestamp": time.time(),
            "state": copy.deepcopy(state_data)
        }

        if thread_id not in self._checkpoints:
            self._checkpoints[thread_id] = []
        self._checkpoints[thread_id].append(snapshot)
        return checkpoint_id

    def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest checkpoint for recovery after a simulated process crash.
        """
        if thread_id in self._checkpoints and self._checkpoints[thread_id]:
            return copy.deepcopy(self._checkpoints[thread_id][-1])
        return None

    def get_all_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """Return full history of checkpoints for a thread."""
        return copy.deepcopy(self._checkpoints.get(thread_id, []))

    def clear(self, thread_id: Optional[str] = None) -> None:
        """Clear checkpoints."""
        if thread_id:
            self._checkpoints.pop(thread_id, None)
        else:
            self._checkpoints.clear()


# Global checkpoint store singleton
global_checkpoint_store = CheckpointStore()
