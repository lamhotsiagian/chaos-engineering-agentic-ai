"""
Chaos Fault Injection: Agent Loop & Autonomous Decision Failures.

Agentic systems differ from deterministic software because they self-direct.
They can enter infinite reasoning loops, trigger cascading retries, hallucinate
non-existent tools, or fail at intermediate evaluation boundaries.
"""

from typing import Optional, Dict, Any
from chaos.base import BaseFaultInjector, ChaosConfig


class PlannerException(RuntimeError):
    """Raised when the Agent's planning node crashes."""
    pass


class RouterException(RuntimeError):
    """Raised when the Agent's tool routing node fails to select a valid branch."""
    pass


class EvaluatorException(RuntimeError):
    """Raised when the self-reflection / output evaluator node fails."""
    pass


class AgentFaultInjector(BaseFaultInjector):
    """Fault injector targeting cognitive loop nodes in LangGraph."""

    def intercept_planner(self, state: Dict[str, Any]) -> None:
        """Inject failure into the planning/reasoning step."""
        if self.config.should_inject("agent") and self.config.agent_fault == "PLANNER_FAILURE":
            self.record_injection("node:planner", "PLANNER_FAILURE", {"state_step": state.get("step", 0)})
            raise PlannerException("Agent Planner failed: unable to decompose user objective into subtasks")

    def intercept_router(self, state: Dict[str, Any]) -> Optional[str]:
        """Inject failure into the decision router step."""
        if self.config.should_inject("agent") and self.config.agent_fault == "ROUTER_FAILURE":
            self.record_injection("node:router", "ROUTER_FAILURE", {})
            raise RouterException("Router failed: ambiguous decision branch or hallucinated destination node")
        return None

    def intercept_evaluator(self, state: Dict[str, Any]) -> None:
        """Inject failure into the self-evaluation step."""
        if self.config.should_inject("agent") and self.config.agent_fault == "EVALUATOR_FAILURE":
            self.record_injection("node:evaluator", "EVALUATOR_FAILURE", {})
            raise EvaluatorException("Evaluator failed: output validator crashed on semantic check")

    def should_force_loop(self) -> bool:
        """Determine if agent should be forced into an infinite loop repetition."""
        if self.config.should_inject("agent") and self.config.agent_fault == "INFINITE_LOOP":
            self.record_injection("loop:controller", "INFINITE_LOOP_FORCED", {})
            return True
        return False
