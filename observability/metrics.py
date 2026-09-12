"""
Observability: Metrics Collection Engine for Agentic AI.

Tracks real-time telemetry, quantitative resilience indicators,
and Prometheus-compatible metrics across baseline and chaos runs.
"""

import time
import math
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class MetricsSnapshot:
    """Snapshot of current agentic system reliability metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    recovered_requests: int = 0
    total_tool_calls: int = 0
    total_model_calls: int = 0
    total_faults_injected: int = 0
    circuit_breaker_trips: int = 0
    budget_exhaustions: int = 0
    latencies: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Percentage of successfully completed user requests (including recovered)."""
        if self.total_requests == 0:
            return 100.0
        return ((self.successful_requests + self.recovered_requests) / self.total_requests) * 100.0

    @property
    def recovery_rate(self) -> float:
        """Percentage of faulted requests that successfully recovered via resilience controls."""
        if self.total_faults_injected == 0:
            return 100.0
        return (self.recovered_requests / self.total_faults_injected) * 100.0

    @property
    def failure_rate(self) -> float:
        """Percentage of unhandled failures."""
        return max(0.0, 100.0 - self.success_rate)

    @property
    def p50_latency_sec(self) -> float:
        """Median latency in seconds."""
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.50)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    @property
    def p95_latency_sec(self) -> float:
        """95th percentile latency in seconds (critical for tail latency analysis under chaos)."""
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]


class MetricsCollector:
    """
    Thread-safe in-memory metric accumulator for chaos experiments and dashboards.
    """

    def __init__(self):
        self._snapshot = MetricsSnapshot()

    def reset(self) -> None:
        """Reset all metrics to initial state for a new experiment run."""
        self._snapshot = MetricsSnapshot()

    def record_request(self, success: bool, latency_sec: float, recovered: bool = False) -> None:
        """Record the final outcome of an agent execution request."""
        self._snapshot.total_requests += 1
        self._snapshot.latencies.append(latency_sec)
        if recovered:
            self._snapshot.recovered_requests += 1
        elif success:
            self._snapshot.successful_requests += 1
        else:
            self._snapshot.failed_requests += 1

    def record_tool_call(self, count: int = 1) -> None:
        """Increment total tool execution invocations."""
        self._snapshot.total_tool_calls += count

    def record_model_call(self, count: int = 1) -> None:
        """Increment total LLM inference queries."""
        self._snapshot.total_model_calls += count

    def record_fault_injected(self, count: int = 1) -> None:
        """Record an intentional chaos fault injection."""
        self._snapshot.total_faults_injected += count

    def record_circuit_trip(self) -> None:
        """Record when a circuit breaker trips into OPEN state."""
        self._snapshot.circuit_breaker_trips += 1

    def record_budget_exhaustion(self) -> None:
        """Record when an execution budget halts an runaway agent loop."""
        self._snapshot.budget_exhaustions += 1

    def get_snapshot(self) -> MetricsSnapshot:
        """Return the current metrics snapshot."""
        return self._snapshot

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary suitable for Streamlit display and JSON serialization."""
        snap = self._snapshot
        return {
            "total_requests": snap.total_requests,
            "success_rate_pct": round(snap.success_rate, 2),
            "recovery_rate_pct": round(snap.recovery_rate, 2),
            "failure_rate_pct": round(snap.failure_rate, 2),
            "p50_latency_sec": round(snap.p50_latency_sec, 3),
            "p95_latency_sec": round(snap.p95_latency_sec, 3),
            "total_tool_calls": snap.total_tool_calls,
            "total_model_calls": snap.total_model_calls,
            "faults_injected": snap.total_faults_injected,
            "circuit_breaker_trips": snap.circuit_breaker_trips,
            "budget_exhaustions": snap.budget_exhaustions
        }


# Global singleton instance
global_metrics = MetricsCollector()
