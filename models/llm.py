"""
Models: LLM Client Interface & Mock Gateway for Local-First Execution.

Provides a unified interface for invoking local foundation models via Ollama
(using httpx or standard urllib) or using a deterministic Mock engine when
running in automated testing or offline environments.
"""

import time
import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from observability.logging import logger
from chaos.llm_faults import LLMFaultInjector


class BaseLLMClient:
    """Base class for LLM client providers."""

    def __init__(self, model_name: str = "qwen2.5:3b", fault_injector: Optional[LLMFaultInjector] = None):
        self.model_name = model_name
        self.fault_injector = fault_injector or LLMFaultInjector()

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from the language model."""
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    Deterministic simulated LLM provider for fast, reliable chaos testing
    without external network or GPU dependencies.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        with global_tracer.span(f"mock_llm:{self.model_name}", {"prompt_length": len(prompt)}) as span:
            global_metrics.record_model_call()

            # Check fault injection
            fault_override = self.fault_injector.intercept(self.model_name, prompt)
            if fault_override is not None:
                span.set_attribute("fault_injected", True)
                return fault_override

            # Simulated reasoning responses
            prompt_lower = prompt.lower()
            if "calculate" in prompt_lower or "25 * 4" in prompt_lower or "10 + 10" in prompt_lower or "math" in prompt_lower:
                return 'Thought: I need to calculate the math expression.\nAction: calculator\nAction Input: {"expression": "25 * 4"}'
            elif "refund" in prompt_lower or "policy" in prompt_lower:
                return 'Thought: I should search the knowledge base for refund terms.\nAction: search\nAction Input: {"query": "refund policy"}'
            elif "notify" in prompt_lower or "alert" in prompt_lower or "email" in prompt_lower:
                return 'Thought: Sending notification to user.\nAction: notification\nAction Input: {"recipient": "user@example.com", "message": "Transaction complete"}'
            elif "database" in prompt_lower or "user" in prompt_lower:
                return 'Thought: Querying database for user record.\nAction: database\nAction Input: {"key": "user:101"}'
            else:
                return f"Response from {self.model_name}: Successfully analyzed request '{prompt[:40]}...' with steady state reliability."


class OllamaLLMClient(BaseLLMClient):
    """
    Live local inference client communicating with the Ollama REST API.
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:3b",
        base_url: Optional[str] = None,
        fault_injector: Optional[LLMFaultInjector] = None,
        timeout_sec: float = 30.0
    ):
        super().__init__(model_name, fault_injector)
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout_sec = timeout_sec

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        with global_tracer.span(f"ollama_llm:{self.model_name}", {"base_url": self.base_url}) as span:
            global_metrics.record_model_call()

            # Check fault injection
            fault_override = self.fault_injector.intercept(self.model_name, prompt)
            if fault_override is not None:
                span.set_attribute("fault_injected", True)
                return fault_override

            url = f"{self.base_url}/api/generate"
            payload = json.dumps({
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt or "You are a reliable, resilient AI assistant.",
                "stream": False
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

            try:
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("response", "")
            except Exception as exc:
                logger.warning(f"Ollama connection failed for model '{self.model_name}': {exc}. Falling back to Mock engine.")
                mock = MockLLMClient(model_name=self.model_name, fault_injector=self.fault_injector)
                return mock.generate(prompt, system_prompt)


def get_llm(model_name: str = "qwen2.5:3b", fault_injector: Optional[LLMFaultInjector] = None, use_mock: bool = False) -> BaseLLMClient:
    """Factory helper to obtain an LLM client."""
    if use_mock:
        return MockLLMClient(model_name=model_name, fault_injector=fault_injector)
    return OllamaLLMClient(model_name=model_name, fault_injector=fault_injector)
