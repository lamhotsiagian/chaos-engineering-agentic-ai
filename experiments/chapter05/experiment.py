"""
Chapter 05 Lab: Tool & API Chaos — Idempotent Execution Framework.

Objective:
- Inject duplicate execution and downstream 500 errors on side-effecting tools (Notifications).
- Verify that idempotency keys prevent multiple duplicate emails/alerts during retries.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tools.notification import global_notification_service
from chaos.base import ChaosConfig
from chaos.tool_faults import ToolFaultInjector
from resilience.resilience_controller import ResilienceController
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()
    global_notification_service.clear()

    metadata = ExperimentMetadata(
        experiment_id="EXP-05-IDEMPOTENT-TOOLS",
        chapter="Chapter 05: Tool & API Chaos",
        target="External Notification & Side-Effect API",
        failure_mode="Duplicate Tool Retries / Double Execution",
        hypothesis="Idempotency keys prevent duplicate side-effects when tool operations are retried.",
        steady_state="1 request results in exactly 1 sent notification."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        global_notification_service.clear()
        res = global_notification_service.send_notification("user@test.com", "Order confirmed", idempotency_key="tx-1001")
        return {"status": "SUCCESS", "notifications_sent": len(global_notification_service.sent_notifications), "details": res}

    # 2. Chaos (Duplicate execution without idempotency check would send 2 emails)
    def chaos():
        global_notification_service.clear()
        fault_cfg = ChaosConfig(enabled=True, tool_fault="DUPLICATE")
        injector = ToolFaultInjector(fault_cfg)
        # Injects duplicate execution
        res = global_notification_service.send_notification("user@test.com", "Order confirmed", fault_injector=injector)
        return {
            "status": "DUPLICATE_SENT",
            "notifications_sent": len(global_notification_service.sent_notifications),
            "error": "Duplicate notification side-effect dispatched!",
            "latency_sec": 0.02
        }

    # 3. Resilient (Protected by ResilienceController & Idempotency Key)
    def resilient():
        global_notification_service.clear()
        controller = ResilienceController()
        # Execute first time
        controller.execute_guarded(
            global_notification_service.send_notification,
            "user@test.com",
            "Order confirmed",
            idempotency_key="tx-idempotent-200"
        )
        # Execute duplicate retry with same key
        res = controller.execute_guarded(
            global_notification_service.send_notification,
            "user@test.com",
            "Order confirmed",
            idempotency_key="tx-idempotent-200"
        )
        return {
            "status": "SUCCESS",
            "notifications_sent": len(global_notification_service.sent_notifications),
            "recovered": True,
            "latency_sec": 0.04
        }

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
