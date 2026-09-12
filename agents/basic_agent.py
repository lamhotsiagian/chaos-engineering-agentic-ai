"""
Agents: Basic Agent Wrapper.

Wraps the basic single-node graph and provides clean user-facing invocation.
"""

from typing import Dict, Any, Optional
from graphs.basic_graph import BasicAgentGraph
from models.llm import BaseLLMClient, get_llm


class BasicAgent:
    """Entry point agent for Chapter 01 experiments."""

    def __init__(self, model_name: str = "qwen2.5:3b", use_mock: bool = True):
        self.llm = get_llm(model_name=model_name, use_mock=use_mock)
        self.graph = BasicAgentGraph(llm_client=self.llm)

    def ask(self, prompt: str, chaos_enabled: bool = False, fail_mode: Optional[str] = None) -> Dict[str, Any]:
        """Invoke basic agent."""
        return self.graph.run(input_prompt=prompt, chaos_enabled=chaos_enabled, fail_mode=fail_mode)
