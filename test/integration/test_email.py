import sys
import unittest
from datetime import datetime

sys.path.append("../..")
from mailer import EmailManager


class TestEmailManager(unittest.TestCase):
    def test_read_recipients(self):
        email_manager = EmailManager("test_send_to_all") 
       
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       
        email_manager.send_to_all(
            "stock_alert",
            "RTX-3060",
            "Retailer B",
            "example.com",
            time_stamp
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)
