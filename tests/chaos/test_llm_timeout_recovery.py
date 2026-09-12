"""Chaos test: LLM Model Failover on Outage."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import unittest
from models.fallback import ModelFailoverController
from chaos.base import ChaosConfig
from chaos.llm_faults import LLMFaultInjector


class TestLLMTimeoutRecovery(unittest.TestCase):

    def test_llm_failover_cascades_on_primary_error(self):
        # Target only the primary model to simulate primary model outage
        fault_cfg = ChaosConfig(enabled=True, llm_fault="ERROR", target_model="qwen2.5:3b")
        injector = LLMFaultInjector(fault_cfg)
        controller = ModelFailoverController(use_mock=True, fault_injector=injector)
        provider, text = controller.generate_with_fallback("Test failover")
        self.assertEqual(provider, "qwen3:1.7b")  # Cascaded to secondary


if __name__ == "__main__":
    unittest.main()
