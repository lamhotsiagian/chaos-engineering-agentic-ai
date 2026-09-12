"""
Resilience Engineering: Agent Kill Switch.

When an agent exhibits runaway behavior, hallucinated destruction, or security
hijacking, operators must have an instantaneous, guaranteed emergency halt mechanism
that aborts execution regardless of agent state.
"""

from typing import Dict, Any, Optional
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent


class KillSwitchEngagedException(RuntimeError):
    """Raised when an active kill switch immediately aborts execution."""
    pass


class KillSwitch:
    """
    Emergency Stop Controller for Agentic AI runtimes.
    """

    def __init__(self, name: str = "global_kill_switch"):
        self.name = name
        self.is_engaged: bool = False
        self.engagement_reason: Optional[str] = None

    def trip(self, reason: str = "Manual operator override") -> None:
        """Trip the kill switch to immediately block all subsequent actions."""
        self.is_engaged = True
        self.engagement_reason = reason
        logger.critical(f"[KILL SWITCH ENGAGED: {self.name}] Reason: {reason}")
        
        global_event_bus.publish(ChaosEvent(
            event_type="KILL_SWITCH_ENGAGED",
            component=self.name,
            details={"reason": reason}
        ))

    def reset(self) -> None:
        """Reset the kill switch to restore normal operation."""
        self.is_engaged = False
        self.engagement_reason = None
        logger.info(f"[KILL SWITCH RESET: {self.name}] Normal operations restored.")

    def verify_safe_to_proceed(self) -> None:
        """Guard method called before any critical action or loop iteration."""
        if self.is_engaged:
            raise KillSwitchEngagedException(
                f"Emergency Kill Switch '{self.name}' is ENGAGED. "
                f"Execution aborted. Reason: {self.engagement_reason}"
            )


# Global singleton kill switch instance
global_kill_switch = KillSwitch()
