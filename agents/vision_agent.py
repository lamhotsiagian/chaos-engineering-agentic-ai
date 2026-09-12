"""
Agents: Multimodal Vision Agent.

Supports visual reasoning and image analysis using `qwen2.5vl:3b` with
simulated multimodal fallback capabilities under payload corruption or model unavailability.
"""

from typing import Dict, Any, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from models.llm import BaseLLMClient, get_llm
from chaos.llm_faults import LLMFaultInjector


class VisionAgent:
    """Multimodal agent for visual analysis experiments."""

    def __init__(
        self,
        model_name: str = "qwen2.5vl:3b",
        use_mock: bool = True,
        fault_injector: Optional[LLMFaultInjector] = None
    ):
        self.model_name = model_name
        self.llm = get_llm(model_name=model_name, fault_injector=fault_injector, use_mock=use_mock)

    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Analyze an image with prompt."""
        with global_tracer.span("vision_agent", {"image_path": image_path, "model": self.model_name}) as span:
            global_metrics.record_model_call()
            try:
                # Multimodal prompt format
                full_prompt = f"[IMAGE: {image_path}]\nUser Request: {prompt}"
                output = self.llm.generate(full_prompt)
                return {
                    "status": "SUCCESS",
                    "model": self.model_name,
                    "image_path": image_path,
                    "analysis": output
                }
            except Exception as exc:
                span.set_attribute("error", str(exc))
                return {
                    "status": "FAILED",
                    "error": str(exc),
                    "image_path": image_path
                }
