"""
Graphs: Chapter 07 — RAG Knowledge Graph with Chaos Interceptors.

Topology:
  START -> [Retrieve Node] -> [Validate Context Node] -> [Generate Node] -> [Safety Check Node] -> END
"""

import time
from typing import Dict, Any, Optional, List
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from observability.logging import logger
from models.llm import BaseLLMClient, MockLLMClient
from memory.retriever import DocumentRetriever, global_retriever
from chaos.rag_faults import RAGFaultInjector
from chaos.security_faults import SecurityFaultInjector


class RAGAgentGraph:
    """
    RAG Agent workflow with explicit knowledge verification and conflict resilience.
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        retriever: Optional[DocumentRetriever] = None,
        rag_faults: Optional[RAGFaultInjector] = None,
        security_faults: Optional[SecurityFaultInjector] = None
    ):
        self.llm = llm_client or MockLLMClient()
        self.retriever = retriever or global_retriever
        self.rag_faults = rag_faults or RAGFaultInjector()
        self.security_faults = security_faults or SecurityFaultInjector()

    def run(self, query: str) -> Dict[str, Any]:
        """Execute the knowledge-grounded RAG query."""
        start_time = time.time()
        trace_id = global_tracer.start_trace()

        with global_tracer.span("rag_agent_workflow", {"query": query}) as span:
            try:
                # 1. Retrieve Knowledge
                with global_tracer.span("node:retrieve"):
                    docs = self.retriever.retrieve(query)
                    # Security check for poisoned docs
                    docs = self.security_faults.mutate_rag_context(docs)

                # 2. Validate Context
                with global_tracer.span("node:validate_context"):
                    validation = self.retriever.validate_context(docs)
                    if not validation["valid"]:
                        span.set_attribute("context_warning", validation["reason"])
                        logger.warning(f"[RAG CONTEXT WARNING] {validation['reason']}")

                # 3. Generate Answer
                with global_tracer.span("node:generate"):
                    context_str = "\n".join([d["content"] for d in docs]) if docs else "No relevant context found."
                    prompt = f"Context:\n{context_str}\n\nQuestion: {query}\nProvide a precise, grounded answer."
                    raw_answer = self.llm.generate(prompt)

                # 4. Resilience Formatting
                elapsed = time.time() - start_time
                global_metrics.record_request(success=True, latency_sec=elapsed, recovered=not validation["valid"])

                return {
                    "trace_id": trace_id,
                    "status": "SUCCESS",
                    "query": query,
                    "answer": raw_answer,
                    "context_validation": validation,
                    "retrieved_docs_count": len(docs),
                    "latency_sec": round(elapsed, 4)
                }

            except Exception as exc:
                elapsed = time.time() - start_time
                global_metrics.record_request(success=False, latency_sec=elapsed)
                logger.error(f"[RAG GRAPH ERROR] {exc}", extra={"trace_id": trace_id})
                return {
                    "trace_id": trace_id,
                    "status": "FAILED",
                    "error": str(exc),
                    "latency_sec": round(elapsed, 4)
                }
