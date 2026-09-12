import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Unit tests for RetryPolicy & IdempotencyRegistry."""
import unittest
from resilience.retry import RetryPolicy, IdempotencyRegistry


class TestRetryAndIdempotency(unittest.TestCase):

    def test_retry_success_after_failure(self):
        attempts = 0

        def flaky_func():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RuntimeError("Transient glitch")
            return "SUCCESS"

        policy = RetryPolicy(max_retries=3, initial_backoff_sec=0.01)
        result = policy.execute(flaky_func)
        self.assertEqual(result, "SUCCESS")
        self.assertEqual(attempts, 3)

    def test_retry_exhaustion_raises(self):
        def failing_func():
            raise ValueError("Permanent failure")

        policy = RetryPolicy(max_retries=2, initial_backoff_sec=0.01)
        with self.assertRaises(ValueError):
            policy.execute(failing_func)

    def test_idempotency_registry_caching(self):
        registry = IdempotencyRegistry()
        self.assertFalse(registry.is_executed("req-1"))

        registry.record_execution("req-1", {"status": "OK"})
        self.assertTrue(registry.is_executed("req-1"))
        self.assertEqual(registry.get_result("req-1"), {"status": "OK"})


if __name__ == "__main__":
    unittest.main()
