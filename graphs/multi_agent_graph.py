"""
Graphs: Chapter 09 — Multi-Agent Team Orchestration Graph.

Topology:
                  Supervisor (Qwen 3B)
                 /        |        \
                ↓         ↓         ↓
          Researcher   Analyst   Executor
          (Qwen 1.7B) (Qwen 1.7B) (Qwen 1.7B)
"""

import time
from typing import Dict, Any, Optional, List
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from observability.logging import logger
from models.llm import BaseLLMClient, MockLLMClient
from chaos.base import ChaosConfig
from chaos.agent_faults import AgentFaultInjector


class MultiAgentGraph:
    """
    Multi-Agent team runtime with fault isolation and worker fallback recovery.
    """

    def __init__(
        self,
        supervisor_llm: Optional[BaseLLMClient] = None,
        worker_llm: Optional[BaseLLMClient] = None,
        chaos_config: Optional[ChaosConfig] = None
    ):
        self.supervisor_llm = supervisor_llm or MockLLMClient(model_name="qwen2.5:3b")
        self.worker_llm = worker_llm or MockLLMClient(model_name="qwen3:1.7b")
        self.emergency_llm = MockLLMClient(model_name="llama3.2:1b")
        self.chaos_config = chaos_config or ChaosConfig()
        self.agent_faults = AgentFaultInjector(self.chaos_config)

    def run(self, mission: str) -> Dict[str, Any]:
        """
        Execute multi-agent collaboration with supervisor failure recovery.
        """
        start_time = time.time()
        trace_id = global_tracer.start_trace()
        recovered_workers = []

        with global_tracer.span("multi_agent_team", {"mission": mission}):
            try:
                # 1. Supervisor Plans Task Delegation
                with global_tracer.span("supervisor:plan"):
                    plan = f"Supervisor plan: Decompose mission '{mission}' into Research -> Analyze -> Execute."

                # 2. Researcher Worker
                research_output = self._run_worker(
                    worker_name="researcher",
                    prompt=f"Research data for: {mission}",
                    recovered_list=recovered_workers
                )

                # 3. Analyst Worker
                analyst_output = self._run_worker(
                    worker_name="analyst",
                    prompt=f"Analyze data: {research_output}",
                    recovered_list=recovered_workers
                )

                # 4. Executor Worker
                execution_output = self._run_worker(
                    worker_name="executor",
                    prompt=f"Execute action based on analysis: {analyst_output}",
                    recovered_list=recovered_workers
                )

                # 5. Supervisor Synthesis
                with global_tracer.span("supervisor:synthesize"):
                    final_synthesis = (
                        f"Mission Completed.\n"
                        f"- Research: {research_output}\n"
                        f"- Analysis: {analyst_output}\n"
                        f"- Result: {execution_output}"
                    )

                elapsed = time.time() - start_time
                global_metrics.record_request(
                    success=True,
                    latency_sec=elapsed,
                    recovered=len(recovered_workers) > 0
                )

                return {
                    "trace_id": trace_id,
                    "status": "SUCCESS",
                    "mission": mission,
                    "synthesis": final_synthesis,
                    "recovered_workers": recovered_workers,
                    "latency_sec": round(elapsed, 4)
                }

            except Exception as exc:
                elapsed = time.time() - start_time
                global_metrics.record_request(success=False, latency_sec=elapsed)
                logger.error(f"[MULTI-AGENT ERROR] {exc}", extra={"trace_id": trace_id})
                return {
                    "trace_id": trace_id,
                    "status": "FAILED",
                    "error": str(exc),
                    "recovered_workers": recovered_workers,
                    "latency_sec": round(elapsed, 4)
                }

    def _run_worker(self, worker_name: str, prompt: str, recovered_list: List[str]) -> str:
        """Run a worker agent with emergency model fallback."""
        with global_tracer.span(f"worker:{worker_name}"):
            # Check for simulated worker fault
            if (
                self.chaos_config.should_inject("agent")
                and self.chaos_config.agent_fault == f"{worker_name.upper()}_FAILURE"
            ):
                logger.warning(f"[WORKER CRASH] Worker '{worker_name}' crashed. Invoking emergency fallback model.")
                recovered_list.append(worker_name)
                # Fallback to emergency worker
                return self.emergency_llm.generate(f"[EMERGENCY BACKUP WORKER] {prompt}")

            return self.worker_llm.generate(prompt)
