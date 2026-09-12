"""
Chapter 10 Lab: Infrastructure & Distributed Chaos — Network Jitter & Connection Resets.

Objective:
- Simulate network transport failures (Latency spikes, ECONNRESET, Packet loss)
  between the Agent and external services.
- Test client-side exponential retry and circuit breakers under degraded connectivity.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from chaos.base import ChaosConfig
from chaos.network_faults import NetworkFaultInjector, NetworkConnectionException
from resilience.resilience_controller import ResilienceController
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-10-NETWORK-JITTER",
        chapter="Chapter 10: Infrastructure Chaos",
        target="Distributed RPC Transport Layer",
        failure_mode="Network Connection Reset (ECONNRESET)",
        hypothesis="Resilience Controller retries transient connection resets with exponential backoff.",
        steady_state="Network RPC calls complete in < 50ms without packet loss."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        injector = NetworkFaultInjector(ChaosConfig(enabled=False))
        injector.intercept("https://api.internal/v1/tools")
        return {"status": "SUCCESS", "latency_sec": 0.01}

    # 2. Chaos (Unprotected connection reset)
    def chaos():
        injector = NetworkFaultInjector(ChaosConfig(enabled=True, network_fault="CONNECTION_RESET"))
        try:
            injector.intercept("https://api.internal/v1/tools")
            return {"status": "SUCCESS"}
        except Exception as exc:
            return {"status": "FAILED", "error": str(exc), "latency_sec": 0.01}

    # 3. Resilient (Protected by retry policy)
    def resilient():
        call_count = 0

        def _flaky_network_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt fails
                raise NetworkConnectionException("Connection reset by peer (ECONNRESET)")
            # Second attempt succeeds
            return {"status": "SUCCESS", "attempts": call_count}

        controller = ResilienceController(max_retries=2)
        res = controller.execute_guarded(_flaky_network_call)
        res["recovered"] = True
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
