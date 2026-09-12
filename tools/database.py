"""
Tools: Database Query & Transaction Tool.

Simulates a key-value or relational store with query and write operations.
Supports idempotency key tracking to test against duplicate records.
"""

from typing import Dict, Any, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from chaos.tool_faults import ToolFaultInjector
from resilience.retry import global_idempotency_registry


class DatabaseTool:
    """In-memory key-value database simulator."""

    def __init__(self):
        self._data: Dict[str, Any] = {
            "user:101": {"id": "101", "name": "Alice Smith", "tier": "PREMIUM", "balance": 450.0},
            "user:102": {"id": "102", "name": "Bob Jones", "tier": "STANDARD", "balance": 50.0},
            "order:5001": {"id": "5001", "user_id": "101", "amount": 120.0, "status": "COMPLETED"}
        }

    def query(self, key: str, fault_injector: Optional[ToolFaultInjector] = None) -> Dict[str, Any]:
        """Query a record by key."""
        with global_tracer.span("tool:database_query", {"key": key}) as span:
            global_metrics.record_tool_call()

            if fault_injector:
                fault_override = fault_injector.intercept("database_query", {"key": key})
                if fault_override is not None:
                    span.set_attribute("fault_injected", True)
                    return {"result": fault_override}

            if key in self._data:
                return {"status": "SUCCESS", "key": key, "data": self._data[key]}
            return {"status": "NOT_FOUND", "key": key, "data": None}

    def write(
        self,
        key: str,
        value: Any,
        idempotency_key: Optional[str] = None,
        fault_injector: Optional[ToolFaultInjector] = None
    ) -> Dict[str, Any]:
        """Write or update a record."""
        with global_tracer.span("tool:database_write", {"key": key, "idempotency_key": idempotency_key}) as span:
            global_metrics.record_tool_call()

            # Check idempotency registry
            if idempotency_key and global_idempotency_registry.is_executed(idempotency_key):
                span.set_attribute("idempotency_hit", True)
                return global_idempotency_registry.get_result(idempotency_key)

            if fault_injector:
                fault_override = fault_injector.intercept("database_write", {"key": key, "value": value})
                if fault_override is not None:
                    span.set_attribute("fault_injected", True)
                    return {"result": fault_override}

            self._data[key] = value
            result = {"status": "WRITTEN", "key": key, "data": value}

            if idempotency_key:
                global_idempotency_registry.record_execution(idempotency_key, result)

            return result


# Global singleton instance
global_db_tool = DatabaseTool()
