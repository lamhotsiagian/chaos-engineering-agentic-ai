"""
Observability: Tracing Module for Agentic AI Systems.

In Agentic AI, a single user request can trigger multiple reasoning loops,
nested tool executions, vector queries, and model fallbacks. Traditional
single-span request/response tracing is insufficient.

This module provides OpenTelemetry-compatible tracing infrastructure that tracks:
- Trace ID: Propagated across the entire agent lifecycle.
- Run ID: Identifies a specific execution attempt or retry.
- Spans: Fine-grained measurement of nodes, tools, LLMs, and fault injection events.
- Metadata: Records model names, token counts, fault injections, and recovery actions.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class Span:
    """
    Represents an individual unit of work within an agent execution graph.
    
    Attributes:
        name: Logical name of the operation (e.g., 'llm_call', 'tool:calculator', 'node:planner')
        span_id: Unique identifier for this span
        parent_id: Identifier of the parent span for nested call trees
        start_time: Monotonic start timestamp in seconds
        end_time: Monotonic completion timestamp in seconds
        status: Execution status ('OK', 'ERROR', 'FAULT_INJECTED', 'RECOVERED')
        attributes: Key-value metadata (e.g., model name, token counts, error messages)
        events: Time-stamped milestone markers inside the span
    """
    name: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "OK"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        """Calculate span duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000.0
        return (self.end_time - self.start_time) * 1000.0

    def set_attribute(self, key: str, value: Any) -> None:
        """Attach contextual metadata to the span."""
        self.attributes[key] = value

    def record_event(self, name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Record an in-span event (e.g., retry trigger, fault injection point)."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "payload": payload or {}
        })

    def end(self, status: Optional[str] = None) -> None:
        """Mark span completion and record final status."""
        self.end_time = time.time()
        if status:
            self.status = status


class Tracer:
    """
    In-memory trace collector and context manager for Agentic AI workflows.
    Maintains the active span stack and records historical execution traces.
    """

    def __init__(self, service_name: str = "agent-chaos-platform"):
        self.service_name = service_name
        self.active_trace_id: str = str(uuid.uuid4())
        self.active_spans: List[Span] = []
        self.completed_spans: List[Span] = []

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """Start a new trace context for a user or chaos experiment request."""
        self.active_trace_id = trace_id or str(uuid.uuid4())
        self.active_spans.clear()
        self.completed_spans.clear()
        return self.active_trace_id

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Context manager for instrumenting code blocks with OpenTelemetry-like spans.
        
        Usage:
            with tracer.span("node:planner", {"model": "qwen2.5:3b"}) as s:
                # Do planning work...
                s.set_attribute("plan_steps", 3)
        """
        parent_id = self.active_spans[-1].span_id if self.active_spans else None
        current_span = Span(name=name, parent_id=parent_id)
        if attributes:
            current_span.attributes.update(attributes)

        self.active_spans.append(current_span)
        try:
            yield current_span
            if current_span.end_time is None:
                current_span.end(status="OK")
        except Exception as exc:
            current_span.set_attribute("error.type", type(exc).__name__)
            current_span.set_attribute("error.message", str(exc))
            current_span.end(status="ERROR")
            raise exc
        finally:
            if current_span in self.active_spans:
                self.active_spans.remove(current_span)
            self.completed_spans.append(current_span)

    def get_traces_summary(self) -> List[Dict[str, Any]]:
        """Return a structured summary of all completed spans in the current trace."""
        return [
            {
                "span_id": s.span_id,
                "parent_id": s.parent_id,
                "name": s.name,
                "duration_ms": round(s.duration_ms, 2),
                "status": s.status,
                "attributes": s.attributes,
                "events_count": len(s.events)
            }
            for s in self.completed_spans
        ]


# Global singleton instance for easy import across graphs and nodes
global_tracer = Tracer()
