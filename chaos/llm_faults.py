"""
Chaos Fault Injection: LLM Gateway & Inference Layer.

Simulates catastrophic and subtle failure modes encountered when communicating
with Foundation Model providers (e.g., Ollama, OpenAI, Anthropic, vLLM):
- TIMEOUT: Exceeds client-side deadline.
- LATENCY: Injects artificial delay/jitter.
- ERROR: Simulates HTTP 500 Internal Server Error / Outage.
- EMPTY: Returns blank response payload.
- MALFORMED: Returns corrupted/truncated JSON structure.
- RATE_LIMIT: Simulates HTTP 429 Too Many Requests.
"""

import time
from typing import Optional, Dict, Any
from chaos.base import BaseFaultInjector, ChaosConfig


class LLMTimeoutException(TimeoutError):
    """Raised when LLM inference exceeds the allowed execution deadline."""
    pass


class LLMRateLimitException(Exception):
    """Raised when LLM returns HTTP 429 Rate Limit Exceeded."""
    pass


class LLMServiceException(RuntimeError):
    """Raised when LLM returns HTTP 500 Internal Server Error."""
    pass


class LLMFaultInjector(BaseFaultInjector):
    """Fault injector intercepting LLM inference calls."""

    def intercept(self, model_name: str, prompt: str) -> Optional[str]:
        """
        Intercept an outgoing LLM request and execute the configured fault.
        """
        if not self.config.should_inject("llm", item_name=model_name):
            return None

        fault = self.config.llm_fault

        if fault == "TIMEOUT":
            self.record_injection("llm", "TIMEOUT", {"model": model_name})
            time.sleep(self.config.timeout_duration_sec)
            raise LLMTimeoutException(f"LLM request to '{model_name}' timed out after {self.config.timeout_duration_sec}s")

        elif fault == "LATENCY":
            self.record_injection("llm", "LATENCY", {"delay_sec": self.config.latency_delay_sec})
            time.sleep(self.config.latency_delay_sec)
            return None

        elif fault == "ERROR":
            self.record_injection("llm", "ERROR", {"model": model_name})
            raise LLMServiceException(f"Simulated HTTP 500 Internal Server Error from LLM provider '{model_name}'")

        elif fault == "RATE_LIMIT":
            self.record_injection("llm", "RATE_LIMIT", {"retry_after": self.config.rate_limit_retry_after})
            raise LLMRateLimitException(f"HTTP 429: Too Many Requests. Retry after {self.config.rate_limit_retry_after}s")

        elif fault == "EMPTY":
            self.record_injection("llm", "EMPTY", {"model": model_name})
            return ""

        elif fault == "MALFORMED":
            self.record_injection("llm", "MALFORMED", {"model": model_name})
            return '{"action": "search", "query": "incomplete_json_error...'

        return None
