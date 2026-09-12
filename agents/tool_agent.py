"""
Agents: Tool-Equipped ReAct Agent.

Executes autonomous tool calling with budget and idempotency protection.
"""

from typing import Dict, Any, Optional
from graphs.react_graph import ReActAgentGraph
from models.llm import BaseLLMClient, get_llm
from chaos.base import ChaosConfig
from resilience.budget import BudgetConfig


class ToolAgent:
    """Tool-enabled agent capable of ReAct reasoning loops."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        use_mock: bool = True,
        chaos_config: Optional[ChaosConfig] = None,
        budget_config: Optional[BudgetConfig] = None
    ):
        self.llm = get_llm(model_name=model_name, use_mock=use_mock)
        self.graph = ReActAgentGraph(
            llm_client=self.llm,
            chaos_config=chaos_config,
            budget_config=budget_config
        )

    def execute(self, objective: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Execute autonomous task."""
        return self.graph.run(objective=objective, idempotency_key=idempotency_key)
