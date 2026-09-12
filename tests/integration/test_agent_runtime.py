import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Integration tests for basic and ReAct agent graphs."""
import unittest
from agents.basic_agent import BasicAgent
from agents.tool_agent import ToolAgent


class TestAgentRuntime(unittest.TestCase):

    def test_basic_agent_steady_state(self):
        agent = BasicAgent(use_mock=True)
        res = agent.ask("Hello agent!")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("output", res)

    def test_react_tool_agent_execution(self):
        agent = ToolAgent(use_mock=True)
        res = agent.execute("Calculate 25 * 4")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreaterEqual(res["iterations"], 1)


if __name__ == "__main__":
    unittest.main()
