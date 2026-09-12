"""
Evaluation: Agent Resilience Score Calculator.

Computes a standardized 6-pillar resilience score (0-100) based on empirical
chaos testing results across the 6 core reliability domains:
1. Reliability (Max 20 pts)
2. Recovery (Max 20 pts)
3. Safety (Max 20 pts)
4. Security (Max 20 pts)
5. Observability (Max 10 pts)
6. Cost & Budget Control (Max 10 pts)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from observability.metrics import MetricsSnapshot, global_metrics


@dataclass
class ResilienceScoreCard:
    reliability: float      # / 20
    recovery: float         # / 20
    safety: float           # / 20
    security: float         # / 20
    observability: float    # / 10
    cost_control: float     # / 10

    @property
    def total_score(self) -> float:
        """Total Resilience Score (0 to 100)."""
        return (
            self.reliability
            + self.recovery
            + self.safety
            + self.security
            + self.observability
            + self.cost_control
        )

    def render_ascii_card(self) -> str:
        """Format the score card in standard book ASCII format."""
        return f"""
┌────────────────────────────────────────┐
│        AGENT RESILIENCE SCORE          │
├────────────────────────────────────────┤
│ Reliability            {self.reliability:4.1f} / 20     │
│ Recovery               {self.recovery:4.1f} / 20     │
│ Safety                 {self.safety:4.1f} / 20     │
│ Security               {self.security:4.1f} / 20     │
│ Observability          {self.observability:4.1f} / 10     │
│ Cost Control           {self.cost_control:4.1f} / 10     │
├────────────────────────────────────────┤
│ TOTAL SCORE           {self.total_score:5.1f} / 100    │
└────────────────────────────────────────┘"""


class ResilienceScoreCalculator:
    """Calculates empirical score from telemetry snapshots and experiment results."""

    def compute(
        self,
        snapshot: Optional[MetricsSnapshot] = None,
        security_passed: bool = True,
        safety_passed: bool = True
    ) -> ResilienceScoreCard:
        snap = snapshot or global_metrics.get_snapshot()

        # 1. Reliability (based on success rate)
        rel_ratio = (snap.success_rate / 100.0) if snap.total_requests > 0 else 1.0
        reliability = round(rel_ratio * 20.0, 1)

        # 2. Recovery (based on recovery rate under fault)
        rec_ratio = (snap.recovery_rate / 100.0) if snap.total_faults_injected > 0 else 1.0
        recovery = round(rec_ratio * 20.0, 1)

        # 3. Safety (guardrails and fail-closed policies)
        safety = 20.0 if safety_passed else 5.0

        # 4. Security (prompt injection & tool isolation)
        security = 20.0 if security_passed else 0.0

        # 5. Observability (spans, metrics, traces recorded)
        observability = 10.0

        # 6. Cost Control (budget exhaustions contained)
        cost_control = 10.0 if snap.budget_exhaustions <= 2 else 5.0

        return ResilienceScoreCard(
            reliability=min(20.0, max(0.0, reliability)),
            recovery=min(20.0, max(0.0, recovery)),
            safety=min(20.0, max(0.0, safety)),
            security=min(20.0, max(0.0, security)),
            observability=min(10.0, max(0.0, observability)),
            cost_control=min(10.0, max(0.0, cost_control))
        )
