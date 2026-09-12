"""
Agents: Knowledge-Grounded RAG Agent.

Performs document retrieval, freshness validation, and conflict-aware synthesis.
"""

from typing import Dict, Any, Optional
from graphs.rag_graph import RAGAgentGraph
from models.llm import BaseLLMClient, get_llm
from memory.retriever import DocumentRetriever
from chaos.rag_faults import RAGFaultInjector
from chaos.security_faults import SecurityFaultInjector


class RAGAgent:
    """RAG-enabled agent for Chapter 07 and 11 knowledge experiments."""

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        use_mock: bool = True,
        retriever: Optional[DocumentRetriever] = None,
        rag_faults: Optional[RAGFaultInjector] = None,
        security_faults: Optional[SecurityFaultInjector] = None
    ):
        self.llm = get_llm(model_name=model_name, use_mock=use_mock)
        self.graph = RAGAgentGraph(
            llm_client=self.llm,
            retriever=retriever,
            rag_faults=rag_faults,
            security_faults=security_faults
        )

    def query(self, question: str) -> Dict[str, Any]:
        """Query knowledge base."""
        return self.graph.run(query=question)
