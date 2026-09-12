import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Regression test: Prompt injection attempt blocked."""
import unittest
from chaos.security_faults import SecurityFaultInjector, SecurityPolicyViolation
from chaos.base import ChaosConfig


class TestSecurityInjection(unittest.TestCase):

    def test_unauthorized_tool_blocked_by_security(self):
        injector = SecurityFaultInjector(ChaosConfig(enabled=True, security_fault="RESTRICTED_TOOL"))
        with self.assertRaises(SecurityPolicyViolation):
            injector.check_tool_authorization("drop_tables", ["calculator", "search"])


if __name__ == "__main__":
    unittest.main()
