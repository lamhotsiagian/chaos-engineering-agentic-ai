import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Chaos test: Infinite reasoning loop contained by budget."""
import unittest
from graphs.react_graph import ReActAgentGraph
from chaos.base import ChaosConfig
from resilience.budget import BudgetConfig


class TestInfiniteLoopBudget(unittest.TestCase):

    def test_infinite_loop_trapped_by_budget(self):
        chaos_cfg = ChaosConfig(enabled=True, agent_fault="INFINITE_LOOP")
        graph = ReActAgentGraph(
            chaos_config=chaos_cfg,
            budget_config=BudgetConfig(max_iterations=4)
        )
        res = graph.run("Calculate 10 + 10")
        self.assertEqual(res["status"], "FAILED")
        self.assertIn("budget exhausted", res["error"].lower())


if __name__ == "__main__":
    unittest.main()
