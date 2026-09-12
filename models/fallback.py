"""
Models: Model Fallback Cascade Controller.

Implements multi-model failover for local-first agentic systems:
1. Primary Agent: `qwen2.5:3b` (High reasoning capacity)
2. Fallback Agent: `qwen3:1.7b` (Faster, lower memory consumption)
3. Emergency Fallback: `llama3.2:1b` (Ultra-low footprint emergency agent)
4. Safe Degraded Mode: Deterministic static completion
"""

from typing import List, Tuple, Optional
from models.llm import BaseLLMClient, get_llm
from observability.logging import logger
from observability.events import global_event_bus, ChaosEvent
from chaos.llm_faults import LLMFaultInjector


class ModelFailoverController:
    """
    Orchestrates sequential model fallback execution.
    """

    def __init__(
        self,
        primary_model: str = "qwen2.5:3b",
        secondary_model: str = "qwen3:1.7b",
        emergency_model: str = "llama3.2:1b",
        use_mock: bool = True,
        fault_injector: Optional[LLMFaultInjector] = None
    ):
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        self.emergency_model = emergency_model
        self.use_mock = use_mock
        self.fault_injector = fault_injector

    def generate_with_fallback(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
        """
        Attempt generation cascading through model tiers.
        
        Returns:
            Tuple[str, str]: (successful_model_name, output_text)
        """
        model_tiers = [self.primary_model, self.secondary_model, self.emergency_model]
        errors = []

        for model_name in model_tiers:
            try:
                logger.info(f"[MODEL FAILOVER] Attempting inference with tier: {model_name}")
                client = get_llm(
                    model_name=model_name,
                    fault_injector=self.fault_injector,
                    use_mock=self.use_mock
                )
                output = client.generate(prompt, system_prompt)
                
                if model_name != self.primary_model:
                    global_event_bus.publish(ChaosEvent(
                        event_type="MODEL_FALLBACK_SUCCESS",
                        component="model_failover_controller",
                        details={"recovered_by": model_name, "failed_tiers": errors}
                    ))
                return model_name, output
            except Exception as exc:
                logger.warning(f"[MODEL FAILOVER] Model tier '{model_name}' failed: {exc}")
                errors.append(model_name)

        # Ultimate degraded fallback
        logger.critical("[MODEL FAILOVER EXHAUSTED] All local model tiers failed. Entering Safe Degraded Mode.")
        global_event_bus.publish(ChaosEvent(
            event_type="SAFE_DEGRADED_MODE",
            component="model_failover_controller",
            details={"failed_models": errors}
        ))
        return (
            "safe_degraded_fallback",
            "System is operating in Safe Degraded Mode. Automated fallback summary: Request queued for human operator review."
        )
