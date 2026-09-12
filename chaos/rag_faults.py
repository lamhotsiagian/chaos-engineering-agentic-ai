"""
Chaos Fault Injection: Memory & RAG Retrieval Layer.

RAG and Long-Term Memory are critical dependencies. If the retriever yields
stale, conflicting, or poisoned knowledge chunks, an agent may hallucinate
with extreme confidence. This module injects realistic knowledge degradation.
"""

from typing import List, Dict, Any, Optional
from chaos.base import BaseFaultInjector, ChaosConfig


class VectorDatabaseException(RuntimeError):
    """Raised when the Vector Database (e.g., Chroma, Qdrant) is unreachable."""
    pass


class RAGFaultInjector(BaseFaultInjector):
    """Fault injector intercepting vector similarity searches and knowledge lookups."""

    def intercept(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Intercept and mutate retrieved documents prior to LLM context augmentation.
        
        Args:
            query: User or Agent search query.
            retrieved_docs: Original list of document chunks.
        Returns:
            Mutated list of document chunks or None to proceed with original.
        """
        if not self.config.should_inject("rag"):
            return None

        fault = self.config.rag_fault

        if fault == "VECTOR_DB_FAILURE":
            self.record_injection("rag:vector_db", "CONNECTION_REFUSED", {"query": query})
            raise VectorDatabaseException("Vector DB connection refused: Dial tcp 127.0.0.1:8000 timeout")

        elif fault == "NO_RETRIEVAL" or fault == "EMPTY_CONTEXT":
            self.record_injection("rag:retriever", "EMPTY_CONTEXT", {"query": query})
            return []

        elif fault == "WRONG_CONTEXT":
            self.record_injection("rag:retriever", "WRONG_CONTEXT", {"query": query})
            return [
                {
                    "content": "Banana cultivation requires high humidity and tropical soil temperatures.",
                    "metadata": {"source": "tropical_botany_handbook.pdf", "doc_id": "wrong_001"}
                }
            ]

        elif fault == "STALE_CONTEXT":
            self.record_injection("rag:retriever", "STALE_CONTEXT", {"query": query})
            return [
                {
                    "content": "All refunds are strictly non-refundable after 7 days as per 2018 policy.",
                    "metadata": {"source": "refund_policy_2018_v1.txt", "timestamp": "2018-01-01", "version": "1.0"}
                }
            ]

        elif fault == "CONFLICTING_CONTEXT":
            self.record_injection("rag:retriever", "CONFLICTING_CONTEXT", {"query": query})
            return [
                {
                    "content": "Refunds are processed within 30 days of request submission.",
                    "metadata": {"source": "policy_faq_v2.txt", "doc_id": "conf_001"}
                },
                {
                    "content": "Refund requests are processed within 48 hours for premium customers.",
                    "metadata": {"source": "premium_terms_v3.txt", "doc_id": "conf_002"}
                }
            ]

        elif fault == "DUPLICATE_CONTEXT":
            self.record_injection("rag:retriever", "DUPLICATE_CONTEXT", {"query": query})
            if retrieved_docs:
                return retrieved_docs + retrieved_docs
            return [
                {"content": "Standard terms apply.", "metadata": {"source": "terms.txt"}}
            ] * 4

        return None
