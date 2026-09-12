"""
Chapter 08 Lab: State & Workflow Chaos — Kill-and-Resume Durable Execution.

Objective:
- Execute a multi-stage pipeline: Research -> Analyze -> Validate -> Execute.
- Simulate an abrupt process termination (SIGKILL) during the Analyze step.
- Verify that resuming from checkpoint completes remaining steps without repeating work.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from graphs.workflow_graph import DurableWorkflowGraph
from memory.long_term import CheckpointStore
from chaos.base import ChaosConfig
from chaos.state_faults import StateFaultInjector
from evaluation.experiment import ChaosExperimentRunner, ExperimentMetadata
from observability.metrics import global_metrics


def run_experiment():
    global_metrics.reset()
    store = CheckpointStore()
    thread_id = "thread_prod_order_99"

    metadata = ExperimentMetadata(
        experiment_id="EXP-08-KILL-RESUME",
        chapter="Chapter 08: Agent State Chaos",
        target="LangGraph Execution Pipeline",
        failure_mode="Simulated Process Crash (SIGKILL) at Step 2 (Analyze)",
        hypothesis="Checkpointing allows workflow to resume from last good state without re-executing step 1.",
        steady_state="Complete 4-stage pipeline executes sequentially in a single pass."
    )

    runner = ChaosExperimentRunner(metadata)

    # 1. Baseline
    def baseline():
        store.clear()
        graph = DurableWorkflowGraph(checkpoint_store=store)
        return graph.run(thread_id=thread_id, topic="Quarterly Risk Assessment")

    # 2. Chaos (Crashes at step 2)
    def chaos():
        store.clear()
        fault_cfg = ChaosConfig(enabled=True, state_fault="PROCESS_KILL")
        graph = DurableWorkflowGraph(checkpoint_store=store, state_faults=StateFaultInjector(fault_cfg))
        return graph.run(thread_id=thread_id, topic="Quarterly Risk Assessment")

    # 3. Resilient (Resume from checkpoint without chaos)
    def resilient():
        # Clean graph picks up saved checkpoint
        graph = DurableWorkflowGraph(checkpoint_store=store)
        res = graph.run(thread_id=thread_id, topic="Quarterly Risk Assessment", resume=True)
        res["recovered"] = True
        return res

    return runner.run(baseline_fn=baseline, chaos_fn=chaos, resilient_fn=resilient)


if __name__ == "__main__":
    run_experiment()
