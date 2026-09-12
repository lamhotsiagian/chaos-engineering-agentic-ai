"""
Chaos Engineering Core: Base Fault Injection Architecture for Agentic AI.

Chaos Engineering in Agentic AI requires controlled, deterministic, or stochastic
interception at the core failure boundaries:
1. LLM / Inference Gateway Boundary
2. Agent Loop / Planning Decision Boundary
3. Tool Execution & Side-Effect Boundary
4. Knowledge / Memory / RAG Boundary
5. Network / Transport Boundary
6. Workflow State & Checkpointing Boundary
7. Security & Guardrail Boundary

This module defines the standardized contracts, configurations, and lifecycle hooks.
"""

import random
import time
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from observability.events import global_event_bus, ChaosEvent
from observability.metrics import global_metrics
from observability.logging import logger


class FaultSeverity(str, Enum):
    """Classification of failure severity."""
    LOW = "LOW"            # e.g., Minor latency jitter
    MEDIUM = "MEDIUM"      # e.g., Rate limit, empty response
    HIGH = "HIGH"          # e.g., Service outage, timeout, invalid JSON
    CRITICAL = "CRITICAL"  # e.g., Process kill, poisoned context, infinite loop


@dataclass
class ChaosConfig:
    """
    Centralized Chaos Configuration for controlling fault injection active states,
    fault types, target scopes, and statistical blast radius.
    """
    enabled: bool = False
    blast_radius: float = 1.0  # Probability of fault triggering (0.0 to 1.0)
    target_model: Optional[str] = None       # If set, only injects fault for this specific model
    target_tool: Optional[str] = None        # If set, only injects fault for this specific tool
    
    # Fault category flags
    llm_fault: Optional[str] = None          # 'TIMEOUT', 'LATENCY', 'ERROR', 'EMPTY', 'MALFORMED', 'RATE_LIMIT'
    tool_fault: Optional[str] = None         # 'TIMEOUT', '500', 'BAD_JSON', 'EMPTY', 'RATE_LIMIT', 'DUPLICATE'
    rag_fault: Optional[str] = None          # 'NO_RETRIEVAL', 'EMPTY_CONTEXT', 'WRONG_CONTEXT', 'STALE_CONTEXT', 'CONFLICTING_CONTEXT', 'VECTOR_DB_FAILURE'
    agent_fault: Optional[str] = None        # 'INFINITE_LOOP', 'PLANNER_FAILURE', 'ROUTER_FAILURE', 'EVALUATOR_FAILURE'
    state_fault: Optional[str] = None        # 'STATE_CORRUPTION', 'EVENT_DUPLICATION', 'PROCESS_KILL'
    network_fault: Optional[str] = None      # 'LATENCY', 'CONNECTION_RESET', 'REQUEST_LOSS', 'SERVICE_UNAVAILABLE'
    security_fault: Optional[str] = None     # 'PROMPT_INJECTION', 'INDIRECT_INJECTION', 'POISONED_DOCUMENT', 'RESTRICTED_TOOL'

    # Fault parameters
    latency_delay_sec: float = 2.0
    timeout_duration_sec: float = 10.0
    rate_limit_retry_after: int = 5
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def should_inject(self, target_domain: str, item_name: Optional[str] = None) -> bool:
        """
        Determine if the specified fault should be injected based on enabled state,
        scoped target matching, and stochastic blast radius sampling.
        """
        if not self.enabled:
            return False
        if target_domain == "llm" and self.target_model and item_name and self.target_model != item_name:
            return False
        if target_domain == "tool" and self.target_tool and item_name and self.target_tool != item_name:
            return False
        if random.random() > self.blast_radius:
            return False
        return True


class BaseFaultInjector:
    """
    Abstract Base Class for all Component Fault Injectors.
    Emits observability events and metrics whenever a failure is injected.
    """

    def __init__(self, config: Optional[ChaosConfig] = None):
        self.config = config or ChaosConfig()

    def record_injection(self, component: str, fault_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Notify event bus, metrics, and structured logs of an injected failure."""
        payload = details or {}
        payload["fault_type"] = fault_type
        
        # Increment global Prometheus metric
        global_metrics.record_fault_injected(1)
        
        # Structured log
        logger.warning(
            f"[CHAOS INJECTED] {component} -> {fault_type}",
            extra={"node": component, "fault_type": fault_type}
        )
        
        # Event bus broadcast
        global_event_bus.publish(ChaosEvent(
            event_type="FAULT_INJECTED",
            component=component,
            details=payload
        ))
