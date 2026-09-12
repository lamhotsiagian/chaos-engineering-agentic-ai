import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
"""Regression test: Idempotency keys prevent duplicate side effects."""
import unittest
from tools.notification import NotificationService
from resilience.resilience_controller import ResilienceController


class TestDuplicateToolExecution(unittest.TestCase):

    def test_duplicate_notification_prevented(self):
        service = NotificationService()
        controller = ResilienceController()

        # First send
        r1 = controller.execute_guarded(service.send_notification, "user@test.com", "Alert 1", idempotency_key="msg-101")
        # Duplicate retry
        r2 = controller.execute_guarded(service.send_notification, "user@test.com", "Alert 1", idempotency_key="msg-101")

        self.assertEqual(len(service.sent_notifications), 1)  # Only 1 email sent despite 2 calls!


if __name__ == "__main__":
    unittest.main()
