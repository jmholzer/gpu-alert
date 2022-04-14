import inspect
import sys
import unittest

sys.path.append("../..")
from mailer import EmailManager


class TestEmailManager(unittest.TestCase):
    def test_read_recipients(self):
        email_manager = EmailManager("test_read_recipients") 
        
        expected = [
            "a@example.com",
            "a@example.com",
            "b@example.com",
            "c@example.eu"
        ]

        results = list(email_manager.read_recipients())

        self.assertEqual(expected, results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
