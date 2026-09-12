"""
Graphs: Chapter 01 — First Chaos-Ready Agent Graph.

Topology:
  START -> [Model Node] -> END

Instrumented with:
- Request ID & Trace propagation
- Precise Latency measurement
- Direct Fault Injection interceptors
- Steady-state vs Failure tracking
"""

import time
from typing import Dict, Any, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from observability.logging import logger
from models.llm import BaseLLMClient, MockLLMClient


class BasicAgentGraph:
    """
    Minimal LangGraph-compatible state machine for single-turn inference
    with latency profiling and chaos resilience.
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm = llm_client or MockLLMClient()

    def run(self, input_prompt: str, chaos_enabled: bool = False, fail_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the basic agent graph with optional injected failures.
        
        Args:
            input_prompt: User input string.
            chaos_enabled: Whether chaos is active for this invocation.
            fail_mode: 'EXCEPTION', 'DELAY', or 'EMPTY'.
        """
        start_time = time.time()
        trace_id = global_tracer.start_trace()

        with global_tracer.span("basic_agent_graph", {"input_prompt": input_prompt, "chaos": chaos_enabled}) as span:
            try:
                # Chapter 1 Lab Injected Failure Modes
                if chaos_enabled:
                    if fail_mode == "EXCEPTION":
                        span.set_attribute("fault_injected", "EXCEPTION")
                        global_metrics.record_fault_injected()
                        raise RuntimeError("Injected LLM failure: simulated catastrophic crash")
                    elif fail_mode == "DELAY":
                        span.set_attribute("fault_injected", "DELAY")
                        global_metrics.record_fault_injected()
                        time.sleep(2.0)
                    elif fail_mode == "EMPTY":
                        span.set_attribute("fault_injected", "EMPTY")
                        global_metrics.record_fault_injected()
                        elapsed = time.time() - start_time
                        global_metrics.record_request(success=False, latency_sec=elapsed)
                        return {
                            "trace_id": trace_id,
                            "status": "EMPTY_RESPONSE",
                            "output": "",
                            "latency_sec": round(elapsed, 4),
                            "recovered": False
                        }

                # Model Node Execution
                output = self.llm.generate(input_prompt)
                elapsed = time.time() - start_time
                global_metrics.record_request(success=True, latency_sec=elapsed)

                return {
                    "trace_id": trace_id,
                    "status": "SUCCESS",
                    "output": output,
                    "latency_sec": round(elapsed, 4),
                    "recovered": False
                }

            except Exception as exc:
                elapsed = time.time() - start_time
                global_metrics.record_request(success=False, latency_sec=elapsed)
                logger.error(f"[BASIC GRAPH ERROR] {exc}", extra={"trace_id": trace_id})
                return {
                    "trace_id": trace_id,
                    "status": "ERROR",
                    "error": str(exc),
                    "latency_sec": round(elapsed, 4),
                    "recovered": False
                }
