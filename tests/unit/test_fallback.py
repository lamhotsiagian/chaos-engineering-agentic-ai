import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Unit tests for FallbackCascade."""
import unittest
from resilience.fallback import FallbackCascade


class TestFallbackCascade(unittest.TestCase):

    def test_fallback_cascade_selection(self):
        cascade = FallbackCascade()

        def primary_fail():
            raise RuntimeError("Primary down")

        def secondary_ok():
            return "Secondary response"

        handlers = [
            ("primary", primary_fail),
            ("secondary", secondary_ok)
        ]

        provider, res = cascade.execute(handlers)
        self.assertEqual(provider, "secondary")
        self.assertEqual(res, "Secondary response")


if __name__ == "__main__":
    unittest.main()
