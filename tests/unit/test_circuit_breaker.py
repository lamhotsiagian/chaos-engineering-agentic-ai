import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Unit tests for CircuitBreaker state transitions."""
import unittest
from resilience.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenException


class TestCircuitBreaker(unittest.TestCase):

    def test_circuit_breaker_trips_to_open(self):
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_sec=0.1)

        def fail():
            raise RuntimeError("Outage")

        # 1st failure
        with self.assertRaises(RuntimeError):
            breaker.execute(fail)
        self.assertEqual(breaker.state, CircuitState.CLOSED)

        # 2nd failure -> Trips OPEN
        with self.assertRaises(RuntimeError):
            breaker.execute(fail)
        self.assertEqual(breaker.state, CircuitState.OPEN)

        # 3rd call fails fast
        with self.assertRaises(CircuitBreakerOpenException):
            breaker.execute(fail)


if __name__ == "__main__":
    unittest.main()
