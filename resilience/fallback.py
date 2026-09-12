"""
Resilience Engineering: Model & Tool Fallback Cascades.

When a primary model or tool is degraded or unavailable, a resilient agent
gracefully cascades down a pre-defined fallback hierarchy instead of crashing.
"""

from typing import List, Callable, Any, Optional, Dict, Tuple
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent


class FallbackCascade:
    """
    Executes an ordered list of providers/handlers until one succeeds.
    """

    def __init__(self, name: str = "model_fallback_cascade"):
        self.name = name

    def execute(self, handlers: List[Tuple[str, Callable[[], Any]]]) -> Tuple[str, Any]:
        """
        Attempt handlers sequentially.
        
        Args:
            handlers: List of tuples (provider_name, callable_func)
        Returns:
            Tuple of (successful_provider_name, result)
        Raises:
            RuntimeError if all handlers in the cascade fail.
        """
        errors = []

        for provider_name, handler in handlers:
            try:
                logger.info(f"[FALLBACK CASCADE: {self.name}] Attempting provider: {provider_name}")
                result = handler()
                
                # Emit recovery event if we fell back beyond primary
                if provider_name != handlers[0][0]:
                    global_event_bus.publish(ChaosEvent(
                        event_type="FALLBACK_TRIGGERED",
                        component=self.name,
                        details={"selected_provider": provider_name, "failed_providers": [p for p, _ in errors]}
                    ))
                return provider_name, result
            except Exception as exc:
                logger.warning(f"[FALLBACK CASCADE: {self.name}] Provider '{provider_name}' failed: {exc}")
                errors.append((provider_name, exc))

        error_summary = "; ".join(f"{p}: {e}" for p, e in errors)
        raise RuntimeError(f"All fallback providers failed in cascade '{self.name}': {error_summary}")
