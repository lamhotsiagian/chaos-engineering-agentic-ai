"""
Tools: Information Search Tool.

Provides web/document search mock capabilities with simulated latency,
result ranking, and fault injection points.
"""

from typing import Dict, Any, List, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from chaos.tool_faults import ToolFaultInjector


def search(query: str, fault_injector: Optional[ToolFaultInjector] = None) -> Dict[str, Any]:
    """Execute a search query across indexed documents."""
    with global_tracer.span("tool:search", {"query": query}) as span:
        global_metrics.record_tool_call()

        if fault_injector:
            fault_override = fault_injector.intercept("search", {"query": query}, lambda **kwargs: search(**kwargs))
            if fault_override is not None:
                span.set_attribute("fault_injected", True)
                return {"result": fault_override}

        # Deterministic search index results
        q_lower = query.lower()
        results: List[Dict[str, str]] = []

        if "refund" in q_lower or "policy" in q_lower:
            results.append({
                "title": "Return & Refund Policy 2026",
                "snippet": "Customers may request a full refund within 30 days of purchase for unused products.",
                "url": "https://company.internal/policies/refund-2026"
            })
        elif "contact" in q_lower or "support" in q_lower:
            results.append({
                "title": "Support Center",
                "snippet": "Contact customer support 24/7 at support@company.internal or +1-800-555-0199.",
                "url": "https://company.internal/support"
            })
        else:
            results.append({
                "title": f"General results for '{query}'",
                "snippet": f"Found reference documentation matching query criteria for {query}.",
                "url": f"https://company.internal/search?q={query}"
            })

        return {"status": "SUCCESS", "query": query, "results": results}
