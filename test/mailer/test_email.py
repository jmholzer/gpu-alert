import unittest
from datetime import datetime
from unittest.mock import patch

from gpu_alert.mailer import Mailer


class TestEmailManager(unittest.TestCase):
    @patch("gpu_alert.mailer.Mailer.send_email")
    def test_send_to_all(self, mock_send_email):
        email_manager = Mailer("test_recipients")
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_manager.send_to_all(
            "stock_alert",
            "RTX-3060",
            "Retailer B",
            "example.com",
            "Jane Doe",
            1000.0,
            time_stamp,
        )
        self.assertEqual(mock_send_email.call_count, 4)

    def test_read_recipients(self):
        email_manager = Mailer("test_recipients")
        expected = ["a@example.com", "a@example.com", "b@example.com", "c@example.eu"]
        result = list(email_manager._read_recipients())
        self.assertEqual(expected, result)
