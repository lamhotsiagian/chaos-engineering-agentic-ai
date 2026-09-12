import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Chaos test: Multi-agent worker failure handled by supervisor."""
import unittest
from graphs.multi_agent_graph import MultiAgentGraph
from chaos.base import ChaosConfig


class TestMultiAgentFailure(unittest.TestCase):

    def test_multi_agent_swaps_failed_worker(self):
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="RESEARCHER_FAILURE")
        graph = MultiAgentGraph(chaos_config=chaos_cfg)
        res = graph.run("Analyze market growth")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("researcher", res["recovered_workers"])


if __name__ == "__main__":
    unittest.main()
