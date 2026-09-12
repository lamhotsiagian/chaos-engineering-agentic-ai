"""
Memory: Document Retriever & Vector Store Interface for RAG.

Provides semantic similarity search over indexed documents with support for
clean embeddings, freshness verification, conflict detection, and RAG chaos injection.
"""

from typing import List, Dict, Any, Optional
from models.embeddings import BaseEmbeddingClient, MockEmbeddingClient, cosine_similarity
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from chaos.rag_faults import RAGFaultInjector


class DocumentRetriever:
    """
    Vector search index supporting RAG knowledge retrieval and chaos interception.
    """

    def __init__(
        self,
        embedding_client: Optional[BaseEmbeddingClient] = None,
        fault_injector: Optional[RAGFaultInjector] = None
    ):
        self.embedding_client = embedding_client or MockEmbeddingClient()
        self.fault_injector = fault_injector or RAGFaultInjector()
        self.documents: List[Dict[str, Any]] = []

    def index_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add and embed a document into the vector index."""
        vector = self.embedding_client.embed_text(content)
        doc_entry = {
            "content": content,
            "metadata": metadata or {},
            "vector": vector
        }
        self.documents.append(doc_entry)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most semantically relevant document chunks.
        """
        with global_tracer.span("rag:retrieve", {"query": query, "top_k": top_k}) as span:
            if not self.documents:
                # Default baseline corporate policy documents
                self.index_document(
                    "Standard Return Policy 2026: Products can be returned within 30 days of purchase for a full refund.",
                    {"source": "policy_2026_v2.txt", "timestamp": "2026-01-15", "version": "2.0"}
                )
                self.index_document(
                    "Premium Member Benefits: 60-day returns and free express shipping on all orders.",
                    {"source": "premium_terms_2026.txt", "timestamp": "2026-01-20", "version": "2.0"}
                )

            # Query embedding
            query_vector = self.embedding_client.embed_text(query)

            # Score documents
            scored_docs = []
            for doc in self.documents:
                score = cosine_similarity(query_vector, doc["vector"])
                scored_docs.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": round(score, 4)
                })

            # Sort descending by similarity score
            scored_docs.sort(key=lambda x: x["score"], reverse=True)
            top_results = scored_docs[:top_k]

            # Intercept with Chaos Fault Injector
            if self.fault_injector:
                fault_override = self.fault_injector.intercept(query, top_results)
                if fault_override is not None:
                    span.set_attribute("fault_injected", True)
                    return fault_override

            return top_results

    def validate_context(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resilience check: Validate retrieved context for stale dates or conflicting assertions.
        """
        if not docs:
            return {"status": "EMPTY", "valid": False, "reason": "No context retrieved."}

        has_stale = False
        versions = set()

        for doc in docs:
            meta = doc.get("metadata", {})
            if "timestamp" in meta and "2018" in str(meta["timestamp"]):
                has_stale = True
            if "version" in meta:
                versions.add(meta["version"])

        if has_stale:
            return {"status": "STALE", "valid": False, "reason": "Retrieved context contains outdated policy records."}
        if len(versions) > 1:
            return {"status": "CONFLICT", "valid": False, "reason": "Retrieved context contains conflicting document versions."}

        return {"status": "VALID", "valid": True, "reason": "Context passed freshness and consistency checks."}


# Global singleton instance
global_retriever = DocumentRetriever()
