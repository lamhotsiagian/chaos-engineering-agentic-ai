"""
Evaluation: Standard 10-Step Chaos Experiment Lifecycle Runner.

Automates the complete Chaos Experiment cycle:
1. Define Hypothesis & Steady State
2. Run Baseline (No Chaos)
3. Inject Targeted Fault
4. Observe Failure Impact & Detection
5. Trigger Resilience Controls
6. Validate Recovery & Blast Radius
7. Measure Metrics (Success, Latency, Tool Calls, Model Calls)
8. Evaluate Pass / Fail
9. Output Standardized Experiment Template Report
"""

import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from observability.metrics import global_metrics
from observability.logging import logger
from evaluation.evaluator import ChaosEvaluator, EvaluationOutcome


@dataclass
class ExperimentMetadata:
    experiment_id: str
    chapter: str
    target: str
    failure_mode: str
    hypothesis: str
    steady_state: str
    blast_radius: float = 1.0
    duration_sec: float = 10.0


class ChaosExperimentRunner:
    """
    Standardized executor for chapter lab experiments.
    """

    def __init__(self, metadata: ExperimentMetadata):
        self.metadata = metadata
        self.evaluator = ChaosEvaluator()

    def run(
        self,
        baseline_fn: Callable[[], Dict[str, Any]],
        chaos_fn: Callable[[], Dict[str, Any]],
        resilient_fn: Optional[Callable[[], Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete 10-step experiment lifecycle.
        """
        print(f"\n{'='*70}")
        print(f"🚀 RUNNING CHAOS EXPERIMENT: [{self.metadata.experiment_id}] {self.metadata.chapter}")
        print(f"Target: {self.metadata.target} | Fault: {self.metadata.failure_mode}")
        print(f"Hypothesis: {self.metadata.hypothesis}")
        print(f"{'='*70}\n")

        # Step 1: Baseline Execution
        print("🔹 Step 1: Running Baseline (Steady State)...")
        baseline_res = baseline_fn()
        print(f"   Baseline Status: {baseline_res.get('status')} | Latency: {baseline_res.get('latency_sec', 0.0)}s")

        # Step 2: Fault Injection Run (Without Resilience)
        print("\n🔹 Step 2: Injecting Fault (Without Resilience)...")
        chaos_res = chaos_fn()
        print(f"   Fault Run Status: {chaos_res.get('status')} | Error: {chaos_res.get('error', 'None')}")

        # Step 3: Resilient Run (With Resilience Controls)
        resilient_res = None
        if resilient_fn:
            print("\n🔹 Step 3: Running with Resilience Controls...")
            resilient_res = resilient_fn()
            print(f"   Resilient Status: {resilient_res.get('status')} | Recovered: {resilient_res.get('recovered', True)}")
            # Record recovered metric
            if resilient_res.get("recovered"):
                global_metrics.record_request(
                    success=True,
                    latency_sec=resilient_res.get("latency_sec", 0.01),
                    recovered=True
                )

        # Step 4: Evaluate Outcome
        target_res = resilient_res if resilient_res else chaos_res
        outcome = self.evaluator.evaluate_run(target_res, fault_injected=True)

        result_str = "PASS" if outcome.passed else "FAIL"

        # Generate Standardized Template Report (PART X OF OUTLINE)
        report = self._format_report(baseline_res, chaos_res, target_res, outcome, result_str)
        print(f"\n{report}\n")

        return {
            "metadata": self.metadata,
            "baseline": baseline_res,
            "chaos_unprotected": chaos_res,
            "resilient_protected": resilient_res,
            "evaluation": outcome,
            "result": result_str,
            "report": report
        }

    def _format_report(
        self,
        baseline: Dict[str, Any],
        chaos: Dict[str, Any],
        final: Dict[str, Any],
        outcome: EvaluationOutcome,
        result_str: str
    ) -> str:
        """Format output to match Part X of the book outline."""
        metrics_dict = global_metrics.to_dict()

        return f"""
┌────────────────────────────────────────────────────────────────────────┐
│                      CHAOS EXPERIMENT REPORT                           │
├────────────────────────────────────────────────────────────────────────┤
Experiment ID:      {self.metadata.experiment_id}
Chapter:            {self.metadata.chapter}
Target:             {self.metadata.target}
Failure Mode:       {self.metadata.failure_mode}

Hypothesis:         {self.metadata.hypothesis}
Steady State:       {self.metadata.steady_state}

Fault Injection:    {self.metadata.failure_mode}
Blast Radius:       {self.metadata.blast_radius * 100:.0f}%
Duration:           {self.metadata.duration_sec}s

Expected Behavior:  System detects failure, contains blast radius, and recovers.
Actual Behavior:    {final.get('status', 'N/A')} (Recovered: {outcome.recovery_detected})

Detection:          Trace & Metric event recorded
Recovery:           {'Automated fallback/retry succeeded' if outcome.passed else 'Failed recovery'}

User Impact:        {'Zero unhandled errors' if outcome.passed else 'Degraded experience / unhandled failure'}

Metrics:
  Success Rate:     {metrics_dict['success_rate_pct']}%
  Latency (P95):    {metrics_dict['p95_latency_sec']}s
  Recovery Rate:    {metrics_dict['recovery_rate_pct']}%
  Tool Calls:       {metrics_dict['total_tool_calls']}
  Model Calls:      {metrics_dict['total_model_calls']}

Result:             {result_str}

Lessons Learned:    {('Resilience mechanisms contained the fault predictably.' if outcome.passed else 'Identified failure gap: ' + ', '.join(outcome.violations))}
└────────────────────────────────────────────────────────────────────────┘"""
