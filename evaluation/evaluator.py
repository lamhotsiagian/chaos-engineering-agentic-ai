"""
Evaluation: Hypothesis & Steady-State Evaluation Engine.

Validates whether an agent system maintained steady-state invariants,
prevented unsafe actions, and recovered within target SLO thresholds
during and after chaos fault injection.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class EvaluationCriteria:
    """Configurable pass/fail thresholds for an experiment."""
    max_acceptable_latency_sec: float = 15.0
    require_zero_unhandled_exceptions: bool = True
    require_recovery_if_faulted: bool = True
    disallow_security_breach: bool = True
    disallow_duplicate_side_effects: bool = True


@dataclass
class EvaluationOutcome:
    """Result of an automated experiment evaluation."""
    passed: bool
    score_pct: float
    violations: List[str] = field(default_factory=list)
    recovery_detected: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class ChaosEvaluator:
    """
    Automated evaluator for chaos experiment runs.
    """

    def __init__(self, criteria: Optional[EvaluationCriteria] = None):
        self.criteria = criteria or EvaluationCriteria()

    def evaluate_run(self, execution_result: Dict[str, Any], fault_injected: bool = False) -> EvaluationOutcome:
        """
        Evaluate a single run against steady-state criteria.
        """
        violations = []
        status = execution_result.get("status", "UNKNOWN")
        latency = execution_result.get("latency_sec", 0.0)
        error = execution_result.get("error")
        recovered = execution_result.get("recovered", False) or execution_result.get("recovered_workers", [])

        # Check latency SLA
        if latency > self.criteria.max_acceptable_latency_sec:
            violations.append(f"Latency {latency}s exceeded SLA limit of {self.criteria.max_acceptable_latency_sec}s")

        # Check for unhandled crash
        if status in ("ERROR", "FAILED", "CRASHED"):
            if self.criteria.require_zero_unhandled_exceptions and not recovered:
                violations.append(f"Unhandled system error encountered: {error}")

        # Check recovery under fault
        if fault_injected and self.criteria.require_recovery_if_faulted and not recovered and status != "SUCCESS":
            violations.append("System failed to trigger automated recovery mechanism under active fault.")

        # Check security policy
        if "SECURITY COMPROMISED" in str(execution_result):
            violations.append("Security breach: System prompt leakage or unauthorized command execution detected.")

        passed = len(violations) == 0
        score = 100.0 if passed else max(0.0, 100.0 - (len(violations) * 35.0))

        return EvaluationOutcome(
            passed=passed,
            score_pct=score,
            violations=violations,
            recovery_detected=bool(recovered),
            details={
                "status": status,
                "latency_sec": latency,
                "error": error
            }
        )
