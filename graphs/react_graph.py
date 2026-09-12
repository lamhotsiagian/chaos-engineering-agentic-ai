"""
Graphs: Chapter 02 & 04 & 05 — ReAct Agent Loop with Chaos Failure Boundaries.

Topology:
  START -> [Planner Node] -> [Router Node] -> [Tool Node] -> [Evaluator Node] -> [Decide Edge]
              ^                                                                         |
              └──────────────────────── (If incomplete / looping) ──────────────────────┘
"""

import time
import json
from typing import Dict, Any, Optional, List
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from observability.logging import logger
from models.llm import BaseLLMClient, MockLLMClient
from chaos.base import ChaosConfig
from chaos.agent_faults import AgentFaultInjector
from chaos.tool_faults import ToolFaultInjector
from resilience.budget import BudgetController, BudgetConfig
from tools.calculator import calculate
from tools.search import search
from tools.database import global_db_tool
from tools.notification import global_notification_service


class ReActAgentGraph:
    """
    Modular LangGraph-style ReAct execution engine with granular node-level
    fault injection interceptors and execution budget guards.
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        chaos_config: Optional[ChaosConfig] = None,
        budget_config: Optional[BudgetConfig] = None
    ):
        self.llm = llm_client or MockLLMClient()
        self.chaos_config = chaos_config or ChaosConfig()
        self.agent_faults = AgentFaultInjector(self.chaos_config)
        self.tool_faults = ToolFaultInjector(self.chaos_config)
        self.budget_controller = BudgetController(config=budget_config or BudgetConfig())

    def run(self, objective: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the autonomous ReAct cognitive loop.
        """
        start_time = time.time()
        trace_id = global_tracer.start_trace()
        self.budget_controller.reset()

        state: Dict[str, Any] = {
            "objective": objective,
            "step": 0,
            "plan": None,
            "action": None,
            "tool_args": {},
            "tool_result": None,
            "evaluation": None,
            "final_answer": None,
            "is_complete": False,
            "idempotency_key": idempotency_key
        }

        with global_tracer.span("react_agent_loop", {"objective": objective}) as span:
            try:
                while not state["is_complete"]:
                    # Enforce budget limits per loop iteration
                    self.budget_controller.check_and_increment_iteration()
                    state["step"] += 1

                    # 1. Planner Node
                    state = self._node_planner(state)

                    # 2. Router Node
                    state = self._node_router(state)

                    # 3. Tool Node (if tool requested)
                    if state.get("action") and state["action"] != "final_answer":
                        state = self._node_tool(state)

                    # 4. Evaluator Node
                    state = self._node_evaluator(state)

                    # Chaos check: force infinite loop if configured
                    if self.agent_faults.should_force_loop():
                        state["is_complete"] = False

                elapsed = time.time() - start_time
                global_metrics.record_request(success=True, latency_sec=elapsed)
                return {
                    "trace_id": trace_id,
                    "status": "SUCCESS",
                    "final_answer": state["final_answer"],
                    "iterations": state["step"],
                    "latency_sec": round(elapsed, 4),
                    "budget_telemetry": self.budget_controller.to_dict()
                }

            except Exception as exc:
                elapsed = time.time() - start_time
                global_metrics.record_request(success=False, latency_sec=elapsed)
                logger.error(f"[REACT LOOP ERROR] {exc}", extra={"trace_id": trace_id, "step": state["step"]})
                return {
                    "trace_id": trace_id,
                    "status": "FAILED",
                    "error": str(exc),
                    "failed_step": state["step"],
                    "latency_sec": round(elapsed, 4),
                    "budget_telemetry": self.budget_controller.to_dict()
                }

    def _node_planner(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Planner node: breaks objective into reasoning and next action."""
        with global_tracer.span("node:planner", {"step": state["step"]}):
            self.agent_faults.intercept_planner(state)
            self.budget_controller.check_and_increment_model()

            prompt = f"Objective: {state['objective']}\nHistory: {state.get('tool_result')}"
            llm_output = self.llm.generate(prompt)

            state["plan"] = llm_output
            return state

    def _node_router(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Router node: inspects plan and parses target tool action."""
        with global_tracer.span("node:router", {"step": state["step"]}):
            self.agent_faults.intercept_router(state)

            plan = state.get("plan", "")
            if "Action: calculator" in plan:
                state["action"] = "calculator"
                state["tool_args"] = {"expression": "25 * 4"}
            elif "Action: search" in plan:
                state["action"] = "search"
                state["tool_args"] = {"query": "refund policy"}
            elif "Action: notification" in plan:
                state["action"] = "notification"
                state["tool_args"] = {
                    "recipient": "user@example.com",
                    "message": "Task processed successfully",
                    "idempotency_key": state.get("idempotency_key")
                }
            elif "Action: database" in plan:
                state["action"] = "database"
                state["tool_args"] = {"key": "user:101"}
            else:
                state["action"] = "final_answer"
                state["final_answer"] = plan
                state["is_complete"] = True

            return state

    def _node_tool(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Tool node: executes external action with tool fault injector."""
        action = state["action"]
        args = state.get("tool_args", {})

        with global_tracer.span(f"node:tool:{action}", args):
            self.budget_controller.check_and_increment_tool()

            if action == "calculator":
                state["tool_result"] = calculate(args.get("expression", "0"), fault_injector=self.tool_faults)
            elif action == "search":
                state["tool_result"] = search(args.get("query", ""), fault_injector=self.tool_faults)
            elif action == "database":
                state["tool_result"] = global_db_tool.query(args.get("key", ""), fault_injector=self.tool_faults)
            elif action == "notification":
                state["tool_result"] = global_notification_service.send_notification(
                    recipient=args.get("recipient", "user@example.com"),
                    message=args.get("message", ""),
                    idempotency_key=args.get("idempotency_key"),
                    fault_injector=self.tool_faults
                )
            else:
                state["tool_result"] = {"error": f"Unknown action: {action}"}

            return state

    def _node_evaluator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluator node: validates tool outputs and decides whether objective is satisfied."""
        with global_tracer.span("node:evaluator", {"step": state["step"]}):
            self.agent_faults.intercept_evaluator(state)

            if state.get("tool_result") and not state.get("is_complete"):
                state["final_answer"] = f"Objective accomplished using tool '{state['action']}'. Output: {state['tool_result']}"
                state["is_complete"] = True

            return state
