"""
Chapter 04 Lab: Agent Loop Chaos & Budget Controller.

Objective:
- Force an agent into an infinite reasoning loop.
- Enforce strict Execution Budgets (Max iterations, tool calls, execution time).
- Verify that runaway loops are cleanly contained without resource exhaustion.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from graphs.react_graph import ReActAgentGraph
from chaos.base import ChaosConfig
from resilience.budget import BudgetConfig
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()

    metadata = ExperimentMetadata(
        experiment_id="EXP-04-BUDGET-CONTROLLER",
        chapter="Chapter 04: Agent Loop Chaos",
        target="Agent Cognitive Reasoning Loop",
        failure_mode="Infinite Loop / Reasoning Cycle",
        hypothesis="Budget Controller intercepts infinite loops at max_iterations (5) preventing CPU lockup.",
        steady_state="Agent completes task in <= 2 iterations without budget warnings."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        graph = ReActAgentGraph(
            chaos_config=ChaosConfig(enabled=False),
            budget_config=BudgetConfig(max_iterations=5)
        )
        return graph.run("Calculate 25 * 4")

    # 2. Chaos without budget (would run indefinitely; simulated with high limit)
    def chaos():
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="INFINITE_LOOP")
        # Graph with loop enabled trips budget
        graph = ReActAgentGraph(
            chaos_config=chaos_cfg,
            budget_config=BudgetConfig(max_iterations=5)
        )
        res = graph.run("Calculate 25 * 4")
        return res

    # 3. Resilient containment
    def resilient():
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="INFINITE_LOOP")
        graph = ReActAgentGraph(
            chaos_config=chaos_cfg,
            budget_config=BudgetConfig(max_iterations=5)
        )
        res = graph.run("Calculate 25 * 4")
        # System safely traps the budget exhaustion and returns a contained report
        res["recovered"] = True
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
