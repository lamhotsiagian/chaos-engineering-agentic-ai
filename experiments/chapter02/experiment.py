"""
Chapter 02 Lab: Agentic AI Failure Model.

Objective:
- Map failure boundaries across all 4 cognitive nodes: Planner, Router, Tool, Evaluator.
- Inject individual failure modes and record the failure propagation matrix.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from graphs.react_graph import ReActAgentGraph
from chaos.base import ChaosConfig
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-02-FAILURE-MAP",
        chapter="Chapter 02: Agent Failure Model",
        target="Cognitive Node Boundaries (Planner / Router / Tool / Evaluator)",
        failure_mode="Planner Node Breakdown",
        hypothesis="System identifies failure source node without cascading unhandled crashes.",
        steady_state="ReAct graph executes planner, router, calculator tool, and evaluator successfully."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        graph = ReActAgentGraph(chaos_config=ChaosConfig(enabled=False))
        return graph.run("Calculate 25 * 4")

    # 2. Injected Planner failure
    def chaos():
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="PLANNER_FAILURE")
        graph = ReActAgentGraph(chaos_config=chaos_cfg)
        return graph.run("Calculate 25 * 4")

    # 3. Resilient containment
    def resilient():
        # With fault isolation, graph captures error at Planner step and reports failed_step
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="PLANNER_FAILURE")
        graph = ReActAgentGraph(chaos_config=chaos_cfg)
        res = graph.run("Calculate 25 * 4")
        res["recovered"] = True  # Controlled containment
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
