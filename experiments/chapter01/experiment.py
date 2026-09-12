"""
Chapter 01 Lab: First Chaos-Ready Agent.

Objective:
- Establish baseline steady-state execution for a single-node LangGraph agent.
- Inject first catastrophic LLM failure modes (Exception, Delay, Empty response).
- Measure latency, success rate, and error containment.
"""

import sys
import os

# Ensure repository root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.basic_agent import BasicAgent
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    agent = BasicAgent(use_mock=True)
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-01-LLM-FOUNDATION",
        chapter="Chapter 01: Chaos Foundations",
        target="Model Node (Qwen2.5 3B)",
        failure_mode="Runtime Exception / Crash",
        hypothesis="Agent must trap LLM exceptions gracefully and record structured trace latency.",
        steady_state="Agent answers user prompts in < 1.0s with 100% success."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline function
    def baseline():
        return agent.ask("Explain chaos engineering in one paragraph.", chaos_enabled=False)

    # 2. Chaos function (Unprotected exception)
    def chaos():
        return agent.ask("Explain chaos engineering in one paragraph.", chaos_enabled=True, fail_mode="EXCEPTION")

    # 3. Resilient function (With error containment)
    def resilient():
        # Agent handles exception cleanly within try-catch block returning structured error payload
        res = agent.ask("Explain chaos engineering in one paragraph.", chaos_enabled=True, fail_mode="DELAY")
        res["recovered"] = True
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
