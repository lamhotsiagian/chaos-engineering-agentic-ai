"""
Agents: Multi-Agent Coordinator.

Coordinates supervisor and worker teams for Chapter 09 experiments.
"""

from typing import Dict, Any, Optional
from graphs.multi_agent_graph import MultiAgentGraph
from models.llm import BaseLLMClient, get_llm
from chaos.base import ChaosConfig


class MultiAgentTeam:
    """Team coordinator encapsulating Supervisor + Worker graphs."""

    def __init__(
        self,
        supervisor_model: str = "qwen2.5:3b",
        worker_model: str = "qwen3:1.7b",
        use_mock: bool = True,
        chaos_config: Optional[ChaosConfig] = None
    ):
        self.supervisor_llm = get_llm(model_name=supervisor_model, use_mock=use_mock)
        self.worker_llm = get_llm(model_name=worker_model, use_mock=use_mock)
        self.graph = MultiAgentGraph(
            supervisor_llm=self.supervisor_llm,
            worker_llm=self.worker_llm,
            chaos_config=chaos_config
        )

    def execute_mission(self, mission: str) -> Dict[str, Any]:
        """Run team mission."""
        return self.graph.run(mission=mission)
