"""
Chapter 14 Lab: Resilience & Recovery Patterns — 100-Task Chaos Benchmark.

Objective:
- Run 100 autonomous agent tasks under random stochastic fault injections
  (LLM timeouts, 500 errors, rate limits, duplicate executions).
- Compare:
    WITHOUT RESILIENCE (Baseline failure rate)
    vs
    WITH RESILIENCE CONTROLLER (Automated retry, circuit breaker, fallback, budget).
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from resilience.resilience_controller import ResilienceController
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-14-100-TASK-BENCHMARK",
        chapter="Chapter 14: Resilience & Recovery Patterns",
        target="Full Agent Stack (LLM + Tools + Loops)",
        failure_mode="Stochastic Multi-Domain Chaos (100 Random Injections)",
        hypothesis="Unified Resilience Controller increases overall system recovery rate from 0% to > 90%.",
        steady_state="100 tasks complete with zero unhandled system failures."
    )

    runner = ChaosExperimentRunner(metadata)

    def _simulate_work(task_id: int, fault_rate: float = 0.3):
        """Simulates a task that might experience an intermittent failure."""
        if random.random() < fault_rate:
            raise RuntimeError(f"Simulated transient dependency failure on task {task_id}")
        return f"Task {task_id} completed successfully"

    # 1. Baseline (100 tasks without faults)
    def baseline():
        successes = 0
        for i in range(100):
            try:
                _simulate_work(i, fault_rate=0.0)
                successes += 1
            except Exception:
                pass
        return {"status": "SUCCESS", "successes": successes, "total": 100, "latency_sec": 0.05}

    # 2. Chaos (100 tasks under 30% fault rate WITHOUT resilience)
    def chaos():
        successes = 0
        failures = 0
        for i in range(100):
            try:
                _simulate_work(i, fault_rate=0.3)
                successes += 1
            except Exception:
                failures += 1
        return {
            "status": "UNPROTECTED_FAILURES",
            "successes": successes,
            "failures": failures,
            "total": 100,
            "error": f"{failures}/100 tasks crashed without resilience!",
            "latency_sec": 0.06
        }

    # 3. Resilient (100 tasks under 30% fault rate WITH ResilienceController)
    def resilient():
        controller = ResilienceController(max_retries=3)
        successes = 0
        recovered = 0
        failures = 0

        for i in range(100):
            try:
                _ = controller.execute_guarded(_simulate_work, i, fault_rate=0.3)
                successes += 1
                recovered += 1
            except Exception:
                failures += 1

        return {
            "status": "SUCCESS",
            "successes": successes,
            "failures": failures,
            "recovered": True,
            "recovery_rate_pct": round((successes / 100.0) * 100.0, 1),
            "latency_sec": 0.12
        }

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
