"""
Chaos Fault Injection: Tool Execution & External API Layer.

In Agentic AI, tools perform side-effecting operations (e.g. database updates,
API transactions, payment processing, notifications). Breaking tools tests
idempotency, retry budgets, circuit breakers, and human escalation.
"""

import time
from typing import Optional, Dict, Any, Callable
from chaos.base import BaseFaultInjector, ChaosConfig


class ToolTimeoutException(TimeoutError):
    """Raised when an external tool or API takes too long to respond."""
    pass


class ToolAPIException(RuntimeError):
    """Raised when a downstream tool returns an unrecoverable 500 status."""
    pass


class ToolSchemaException(ValueError):
    """Raised when a tool response violates the expected contract schema."""
    pass


class ToolFaultInjector(BaseFaultInjector):
    """Fault injector intercepting Tool invocations."""

    def intercept(self, tool_name: str, args: Dict[str, Any], tool_func: Optional[Callable] = None) -> Optional[Any]:
        """
        Intercept tool execution.
        
        Returns:
            Optional[Any]: Overridden tool response if simulated, or None to proceed.
        Raises:
            ToolTimeoutException, ToolAPIException, ToolSchemaException
        """
        if not self.config.should_inject("tool"):
            return None

        fault = self.config.tool_fault

        if fault == "TIMEOUT":
            self.record_injection(f"tool:{tool_name}", "TIMEOUT", {"args": args})
            time.sleep(self.config.timeout_duration_sec)
            raise ToolTimeoutException(f"Tool '{tool_name}' timed out after {self.config.timeout_duration_sec}s")

        elif fault == "500":
            self.record_injection(f"tool:{tool_name}", "500_ERROR", {"args": args})
            raise ToolAPIException(f"Downstream tool API '{tool_name}' returned 500 Internal Server Error")

        elif fault == "BAD_JSON":
            self.record_injection(f"tool:{tool_name}", "BAD_SCHEMA", {"args": args})
            # Returns an invalid unparseable payload or corrupted schema
            return "<<CORRUPTED_XML_IN_JSON_ENDPOINT>>"

        elif fault == "EMPTY":
            self.record_injection(f"tool:{tool_name}", "EMPTY_RESPONSE", {"args": args})
            return ""

        elif fault == "RATE_LIMIT":
            self.record_injection(f"tool:{tool_name}", "RATE_LIMIT", {"args": args})
            raise ToolAPIException(f"Rate limit exceeded for tool API '{tool_name}'")

        elif fault == "DUPLICATE":
            # Key experiment: execute tool twice to test if side-effects are idempotent
            self.record_injection(f"tool:{tool_name}", "DUPLICATE_EXECUTION", {"args": args})
            if tool_func:
                # First execution
                _ = tool_func(**args)
                # Second execution to test idempotency
                return tool_func(**args)

        return None
