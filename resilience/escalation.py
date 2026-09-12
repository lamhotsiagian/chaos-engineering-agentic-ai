"""
Resilience Engineering: Human Escalation & Fail-Safe Policies.

When automated recovery fails, or when a high-impact action requires confirmation,
the agent must escalate to a human operator. Under failure conditions (e.g. guardrail
outage), the system must adhere to explicit Fail-Closed or Fail-Open safety policies.
"""

from enum import Enum
from typing import Dict, Any, Optional, Callable
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent


class SafetyPolicyMode(str, Enum):
    FAIL_CLOSED = "FAIL_CLOSED"  # High safety: Block action if guardrail/evaluator fails
    FAIL_OPEN = "FAIL_OPEN"      # High availability: Permit action with degraded logging


class EscalationException(RuntimeError):
    """Raised when an action is escalated to a human supervisor and paused."""
    pass


class HumanEscalationController:
    """
    Manages human approval workflows and policy fallback rules.
    """

    def __init__(self, policy_mode: SafetyPolicyMode = SafetyPolicyMode.FAIL_CLOSED):
        self.policy_mode = policy_mode
        self.pending_escalations: Dict[str, Dict[str, Any]] = {}

    def escalate(self, action_id: str, reason: str, payload: Dict[str, Any]) -> None:
        """Trigger an escalation event to human operator."""
        logger.warning(f"[HUMAN ESCALATION] Action: {action_id} Reason: {reason}")
        self.pending_escalations[action_id] = {
            "reason": reason,
            "payload": payload,
            "status": "PENDING"
        }
        global_event_bus.publish(ChaosEvent(
            event_type="HUMAN_ESCALATION",
            component="escalation_controller",
            details={"action_id": action_id, "reason": reason, "policy": self.policy_mode.value}
        ))

    def evaluate_guardrail_failure(self, action_name: str, guardrail_error: Exception) -> bool:
        """
        Determine whether to allow or block an action when a safety guardrail fails.
        
        Returns:
            bool: True if permitted under FAIL_OPEN, False (or raises) if FAIL_CLOSED.
        """
        logger.error(f"[GUARDRAIL FAILURE] Guardrail crashed for action '{action_name}': {guardrail_error}")
        
        if self.policy_mode == SafetyPolicyMode.FAIL_CLOSED:
            logger.critical(f"[FAIL-CLOSED TRIGGERED] Action '{action_name}' BLOCKED for safety.")
            return False
        else:
            logger.warning(f"[FAIL-OPEN TRIGGERED] Action '{action_name}' ALLOWED under degraded availability.")
            return True
