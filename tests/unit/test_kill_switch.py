import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Unit tests for KillSwitch."""
import unittest
from resilience.kill_switch import KillSwitch, KillSwitchEngagedException


class TestKillSwitch(unittest.TestCase):

    def test_kill_switch_lifecycle(self):
        switch = KillSwitch("test_switch")
        switch.verify_safe_to_proceed()  # No exception

        switch.trip("Manual alert")
        self.assertTrue(switch.is_engaged)

        with self.assertRaises(KillSwitchEngagedException):
            switch.verify_safe_to_proceed()

        switch.reset()
        self.assertFalse(switch.is_engaged)
        switch.verify_safe_to_proceed()  # Safe again


if __name__ == "__main__":
    unittest.main()
