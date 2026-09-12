import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Unit tests for TimeoutPolicy."""
import unittest
import time
from resilience.timeout import TimeoutPolicy, ExecutionTimeoutException


class TestTimeoutPolicy(unittest.TestCase):

    def test_timeout_within_limit(self):
        policy = TimeoutPolicy(timeout_seconds=1.0)
        result = policy.execute(lambda x: x * 2, 5)
        self.assertEqual(result, 10)

    def test_timeout_exceeded(self):
        policy = TimeoutPolicy(timeout_seconds=0.1)

        def slow_func():
            time.sleep(0.5)
            return "DONE"

        with self.assertRaises(ExecutionTimeoutException):
            policy.execute(slow_func)


if __name__ == "__main__":
    unittest.main()
