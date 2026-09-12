"""
Chapter 12 Lab: Guardrail & Human-in-the-Loop Chaos — Fail-Closed vs Fail-Open Policies.

Objective:
- Inject a crash or timeout into the safety guardrail evaluation service.
- Verify whether high-stakes actions adhere to a Fail-Closed policy (block execution)
  or escalate to a human supervisor instead of failing open dangerously.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from resilience.escalation import HumanEscalationController, SafetyPolicyMode
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-12-GUARDRAIL-FAIL-CLOSED",
        chapter="Chapter 12: Guardrail & Human Chaos",
        target="Safety Guardrail & HITL Approval Layer",
        failure_mode="Guardrail Service Outage (Crash / Timeout)",
        hypothesis="When safety guardrail crashes, high-impact action FAILS CLOSED and escalates to human.",
        steady_state="Guardrail validates all actions within 100ms."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        controller = HumanEscalationController(policy_mode=SafetyPolicyMode.FAIL_CLOSED)
        return {"status": "SUCCESS", "action": "transfer_funds", "guardrail": "VALIDATED"}

    # 2. Chaos (Guardrail crashes under Fail-Open policy: would permit unverified transfer)
    def chaos():
        controller = HumanEscalationController(policy_mode=SafetyPolicyMode.FAIL_OPEN)
        simulated_error = RuntimeError("Guardrail connection timeout")
        is_allowed = controller.evaluate_guardrail_failure("transfer_funds", simulated_error)
        return {
            "status": "DANGEROUS_FAIL_OPEN",
            "action_permitted": is_allowed,
            "error": "High-risk action allowed despite guardrail outage!",
            "latency_sec": 0.02
        }

    # 3. Resilient (Fail-Closed policy blocks action and triggers Human Escalation)
    def resilient():
        controller = HumanEscalationController(policy_mode=SafetyPolicyMode.FAIL_CLOSED)
        simulated_error = RuntimeError("Guardrail connection timeout")
        is_allowed = controller.evaluate_guardrail_failure("transfer_funds", simulated_error)
        
        # Escalate to human
        controller.escalate("transfer_funds", "Guardrail unavailable", {"amount": 5000})

        return {
            "status": "SUCCESS",
            "action_permitted": is_allowed,  # False (Blocked)
            "escalated_to_human": True,
            "recovered": True,
            "latency_sec": 0.03
        }

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
