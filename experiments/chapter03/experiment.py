"""
Chapter 03 Lab: LLM Chaos Engineering & Model Fallback Controller.

Objective:
- Break primary LLM dependency (Timeout, Error, Rate Limit).
- Validate 3-Tier Model Failover: Qwen 3B -> Qwen 1.7B -> Llama 1B -> Safe Degraded.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from models.fallback import ModelFailoverController
from models.llm import MockLLMClient
from chaos.base import ChaosConfig
from chaos.llm_faults import LLMFaultInjector
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-03-LLM-FAILOVER",
        chapter="Chapter 03: LLM Chaos Engineering",
        target="Foundation Model Gateway",
        failure_mode="Primary Model Timeout / HTTP 500 Outage",
        hypothesis="When Primary model (Qwen 3B) fails, system cascades to Secondary (Qwen 1.7B) transparently.",
        steady_state="Primary model satisfies prompt requests with high reasoning accuracy."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline (Normal LLM call)
    def baseline():
        controller = ModelFailoverController(use_mock=True)
        provider, text = controller.generate_with_fallback("Summarize agent reliability principles.")
        return {"status": "SUCCESS", "provider": provider, "output": text, "latency_sec": 0.05}

    # 2. Chaos (Primary fails, no fallback)
    def chaos():
        fault_cfg = ChaosConfig(enabled=True, llm_fault="ERROR", target_model="qwen2.5:3b")
        injector = LLMFaultInjector(fault_cfg)
        client = MockLLMClient(model_name="qwen2.5:3b", fault_injector=injector)
        try:
            client.generate("Summarize agent reliability principles.")
            return {"status": "SUCCESS"}
        except Exception as exc:
            return {"status": "FAILED", "error": str(exc), "latency_sec": 0.01}

    # 3. Resilient (Failover controller cascades to secondary)
    def resilient():
        fault_cfg = ChaosConfig(enabled=True, llm_fault="ERROR", target_model="qwen2.5:3b")
        injector = LLMFaultInjector(fault_cfg)
        # Controller with Primary faulted will automatically invoke secondary
        controller = ModelFailoverController(use_mock=True, fault_injector=injector)
        provider, text = controller.generate_with_fallback("Summarize agent reliability principles.")
        return {
            "status": "SUCCESS",
            "provider": provider,
            "output": text,
            "recovered": True,
            "latency_sec": 0.08
        }

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
