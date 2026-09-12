"""
Graphs: Chapter 08 — Kill-and-Resume Durable Workflow Graph.

Topology:
  START -> [Research] --(save checkpoint)--> [Analyze] --(save checkpoint)--> [Validate] --(save checkpoint)--> [Execute] -> END
"""

import time
from typing import Dict, Any, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from observability.logging import logger
from memory.long_term import CheckpointStore, global_checkpoint_store
from chaos.state_faults import StateFaultInjector


class DurableWorkflowGraph:
    """
    Multi-stage pipeline that persists intermediate state snapshots to withstand
    abrupt process termination or node failures.
    """

    def __init__(
        self,
        checkpoint_store: Optional[CheckpointStore] = None,
        state_faults: Optional[StateFaultInjector] = None
    ):
        self.checkpoint_store = checkpoint_store or global_checkpoint_store
        self.state_faults = state_faults or StateFaultInjector()

    def run(self, thread_id: str, topic: str, resume: bool = False) -> Dict[str, Any]:
        """
        Execute the workflow from start or resume from latest checkpoint.
        """
        start_time = time.time()
        trace_id = global_tracer.start_trace()

        state: Dict[str, Any] = {
            "topic": topic,
            "research_data": None,
            "analysis_data": None,
            "validation_data": None,
            "execution_result": None,
            "completed_steps": []
        }

        # Check if resuming from prior checkpoint
        if resume:
            latest = self.checkpoint_store.get_latest_checkpoint(thread_id)
            if latest:
                state = latest["state"]
                logger.info(f"[RESUMING WORKFLOW] Resumed thread '{thread_id}' from checkpoint step '{latest['step_name']}'")

        with global_tracer.span("durable_workflow", {"thread_id": thread_id, "resume": resume}):
            try:
                # Step 1: Research
                if "research" not in state["completed_steps"]:
                    with global_tracer.span("step:research"):
                        # Check chaos
                        corrupted = self.state_faults.intercept_state(state, "research")
                        if corrupted:
                            state = corrupted

                        state["research_data"] = f"Comprehensive research findings for: {state['topic']}"
                        state["completed_steps"].append("research")
                        self.checkpoint_store.save_checkpoint(thread_id, "research", state)

                # Step 2: Analyze
                if "analyze" not in state["completed_steps"]:
                    with global_tracer.span("step:analyze"):
                        corrupted = self.state_faults.intercept_state(state, "analyze")
                        if corrupted:
                            state = corrupted

                        state["analysis_data"] = f"Synthesized analysis based on: {state['research_data']}"
                        state["completed_steps"].append("analyze")
                        self.checkpoint_store.save_checkpoint(thread_id, "analyze", state)

                # Step 3: Validate
                if "validate" not in state["completed_steps"]:
                    with global_tracer.span("step:validate"):
                        corrupted = self.state_faults.intercept_state(state, "validate")
                        if corrupted:
                            state = corrupted

                        state["validation_data"] = f"Quality metrics and constraints validated for: {state['analysis_data']}"
                        state["completed_steps"].append("validate")
                        self.checkpoint_store.save_checkpoint(thread_id, "validate", state)

                # Step 4: Execute
                if "execute" not in state["completed_steps"]:
                    with global_tracer.span("step:execute"):
                        corrupted = self.state_faults.intercept_state(state, "execute")
                        if corrupted:
                            state = corrupted

                        state["execution_result"] = f"Action finalized successfully for: {state['topic']}"
                        state["completed_steps"].append("execute")
                        self.checkpoint_store.save_checkpoint(thread_id, "execute", state)

                elapsed = time.time() - start_time
                global_metrics.record_request(success=True, latency_sec=elapsed, recovered=resume)

                return {
                    "thread_id": thread_id,
                    "status": "COMPLETED",
                    "final_state": state,
                    "completed_steps": state["completed_steps"],
                    "latency_sec": round(elapsed, 4)
                }

            except Exception as exc:
                elapsed = time.time() - start_time
                global_metrics.record_request(success=False, latency_sec=elapsed)
                logger.error(f"[WORKFLOW CRASHED] {exc}", extra={"thread_id": thread_id})
                return {
                    "thread_id": thread_id,
                    "status": "CRASHED",
                    "error": str(exc),
                    "last_completed_step": state["completed_steps"][-1] if state["completed_steps"] else "none",
                    "latency_sec": round(elapsed, 4)
                }
