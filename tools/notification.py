"""
Tools: External Notification & Side-Effect Tool.

Simulates email/SMS/Webhook dispatching. Crucial for Chapter 05 Chaos testing:
Demonstrates how duplicate tool retries cause unwanted multiple customer alerts
unless idempotency keys and registries are enforced.
"""

from typing import Dict, Any, List, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from chaos.tool_faults import ToolFaultInjector
from resilience.retry import global_idempotency_registry


class NotificationService:
    """Simulated notification dispatcher with side-effect tracking."""

    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []

    def send_notification(
        self,
        recipient: str,
        message: str,
        idempotency_key: Optional[str] = None,
        fault_injector: Optional[ToolFaultInjector] = None
    ) -> Dict[str, Any]:
        """
        Dispatch a notification to a recipient.
        """
        with global_tracer.span("tool:notification", {"recipient": recipient, "idempotency_key": idempotency_key}) as span:
            global_metrics.record_tool_call()

            # 1. Check idempotency registry
            if idempotency_key and global_idempotency_registry.is_executed(idempotency_key):
                span.set_attribute("idempotency_hit", True)
                return global_idempotency_registry.get_result(idempotency_key)

            # 2. Check fault injection
            if fault_injector:
                fault_override = fault_injector.intercept(
                    "notification",
                    {"recipient": recipient, "message": message},
                    lambda **kwargs: self.send_notification(**kwargs)
                )
                if fault_override is not None:
                    span.set_attribute("fault_injected", True)
                    return {"result": fault_override}

            # 3. Perform side effect
            record = {
                "recipient": recipient,
                "message": message,
                "idempotency_key": idempotency_key,
                "status": "SENT"
            }
            self.sent_notifications.append(record)

            result = {"status": "SUCCESS", "details": record}

            if idempotency_key:
                global_idempotency_registry.record_execution(idempotency_key, result)

            return result

    def clear(self) -> None:
        """Clear notification dispatch history."""
        self.sent_notifications.clear()


# Global singleton instance
global_notification_service = NotificationService()
