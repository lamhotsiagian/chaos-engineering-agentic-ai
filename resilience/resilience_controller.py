"""
Resilience Engineering: Unified Resilience Controller.

Aggregates Retry, Timeout, Circuit Breaker, Fallback, Budget,
Kill Switch, and Human Escalation into a single coordinated control plane.
"""

from typing import Optional, Dict, Any, Callable, List, Tuple
from resilience.retry import RetryPolicy, global_idempotency_registry
from resilience.timeout import TimeoutPolicy
from resilience.circuit_breaker import CircuitBreaker
from resilience.fallback import FallbackCascade
from resilience.budget import BudgetController, BudgetConfig
from resilience.kill_switch import KillSwitch, global_kill_switch
from resilience.escalation import HumanEscalationController, SafetyPolicyMode
from observability.logging import logger


class ResilienceController:
    """
    Unified resilience orchestrator guarding agent executions.
    """

    def __init__(
        self,
        name: str = "agent_resilience_controller",
        max_retries: int = 3,
        timeout_seconds: float = 10.0,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: float = 5.0,
        budget_config: Optional[BudgetConfig] = None,
        safety_policy: SafetyPolicyMode = SafetyPolicyMode.FAIL_CLOSED
    ):
        self.name = name
        self.retry_policy = RetryPolicy(max_retries=max_retries)
        self.timeout_policy = TimeoutPolicy(timeout_seconds=timeout_seconds)
        self.circuit_breaker = CircuitBreaker(
            name=f"{name}_breaker",
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_sec=circuit_recovery_timeout
        )
        self.fallback_cascade = FallbackCascade(name=f"{name}_fallback")
        self.budget_controller = BudgetController(config=budget_config or BudgetConfig())
        self.kill_switch = global_kill_switch
        self.escalation_controller = HumanEscalationController(policy_mode=safety_policy)
        self.idempotency_registry = global_idempotency_registry

    def execute_guarded(self, func: Callable, *args, idempotency_key: Optional[str] = None, **kwargs) -> Any:
        """
        Execute a function through the full resilience stack:
        1. Kill Switch Check
        2. Budget Check & Increment
        3. Idempotency Check (if key provided)
        4. Circuit Breaker Guard
        5. Timeout Boundary
        6. Retry Policy with Exponential Backoff
        """
        # 1. Kill switch
        self.kill_switch.verify_safe_to_proceed()

        # 2. Idempotency check
        if idempotency_key and self.idempotency_registry.is_executed(idempotency_key):
            logger.info(f"[IDEMPOTENCY HIT] Returning cached result for key '{idempotency_key}'")
            return self.idempotency_registry.get_result(idempotency_key)

        # 3. Budget tracking
        self.budget_controller.check_and_increment_tool()

        # 4-6. Circuit breaker + Timeout + Retry
        def _timed_call():
            return self.timeout_policy.execute(func, *args, **kwargs)

        def _breaker_call():
            return self.circuit_breaker.execute(_timed_call)

        result = self.retry_policy.execute(_breaker_call)

        # Record idempotency
        if idempotency_key:
            self.idempotency_registry.record_execution(idempotency_key, result)

        return result
