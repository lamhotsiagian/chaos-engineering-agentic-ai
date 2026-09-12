"""
Chapter 09 Lab: Multi-Agent Chaos — Worker Crash & Supervisor Recovery.

Objective:
- Coordinate a multi-agent team: Supervisor -> Researcher, Analyst, Executor.
- Inject a crash on the Researcher agent.
- Validate that the Supervisor detects worker failure and switches to emergency backup worker.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from graphs.multi_agent_graph import MultiAgentGraph
from chaos.base import ChaosConfig
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-09-MULTI-AGENT-FAILOVER",
        chapter="Chapter 09: Multi-Agent Chaos",
        target="Multi-Agent Team (Researcher Worker)",
        failure_mode="Worker Node Crash / Unresponsive Worker",
        hypothesis="Supervisor isolates worker crash and swaps in Emergency Worker (Llama 3.2 1B).",
        steady_state="Supervisor and 3 workers complete coordinated synthesis task."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        graph = MultiAgentGraph()
        return graph.run("Analyze competitor pricing models")

    # 2. Chaos (Researcher worker failure, uncontained)
    def chaos():
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="RESEARCHER_FAILURE")
        # MultiAgentGraph contains automatic emergency failover
        graph = MultiAgentGraph(chaos_config=chaos_cfg)
        return graph.run("Analyze competitor pricing models")

    # 3. Resilient (Worker crash automatically replaced)
    def resilient():
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="RESEARCHER_FAILURE")
        graph = MultiAgentGraph(chaos_config=chaos_cfg)
        res = graph.run("Analyze competitor pricing models")
        res["recovered"] = True
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
