import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Unit tests for BudgetController."""
import unittest
from resilience.budget import BudgetController, BudgetConfig, BudgetExhaustedException


class TestBudgetController(unittest.TestCase):

    def test_budget_iteration_limit(self):
        controller = BudgetController(BudgetConfig(max_iterations=3))
        controller.check_and_increment_iteration()
        controller.check_and_increment_iteration()
        controller.check_and_increment_iteration()

        with self.assertRaises(BudgetExhaustedException):
            controller.check_and_increment_iteration()

    def test_budget_tool_limit(self):
        controller = BudgetController(BudgetConfig(max_tool_calls=2))
        controller.check_and_increment_tool(1)
        controller.check_and_increment_tool(1)

        with self.assertRaises(BudgetExhaustedException):
            controller.check_and_increment_tool(1)


if __name__ == "__main__":
    unittest.main()
