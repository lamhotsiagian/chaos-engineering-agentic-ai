import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Chaos test: Tool failure recovery via Retry."""
import unittest
from resilience.resilience_controller import ResilienceController


class TestToolFailureRecovery(unittest.TestCase):

    def test_tool_recovers_via_retry(self):
        calls = 0

        def unreliable_tool():
            nonlocal calls
            calls += 1
            if calls < 2:
                raise RuntimeError("Temporary 500 error")
            return {"result": 42}

        controller = ResilienceController(max_retries=2)
        res = controller.execute_guarded(unreliable_tool)
        self.assertEqual(res, {"result": 42})
        self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
