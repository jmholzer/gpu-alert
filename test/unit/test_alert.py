import sys
import unittest

sys.path.append("../..")
from alert import Alert, AlertRetailerA, AlertManager
from mailer import EmailManager


class TestAlertManager(unittest.TestCase):
    def test_generate_time_interval(self):
        alert = AlertManager("alert_profile") 
        for _ in range(60 * 24 * 365 * 5):
            result = alert.generate_time_interval()
            lower_limit = 5
            upper_limit = 105
            self.assertGreater(result, lower_limit)
            self.assertLess(result, upper_limit)


class TestAlert(unittest.TestCase):
    """
    Unit tests for the class Alert in alert.py.
    """
    def test_generate_alerts(self):
        email_manager = EmailManager("me")
        alert = Alert("retailer_a", "TEST-RTX-3060", email_manager)
       
        # Set alert value for some products to True
        alert.products["product00"]["alert"]["delivery"] = True
        alert.products["product01"]["alert"]["store"] = True
        alert.products["product02"]["alert"]["delivery"] = True
        alert.products["product02"]["alert"]["store"] = True

        # Add list to store results to alert
        alert.test_generate_alerts_results = []

        alert.generate_email_alert = generate_email_alert

        expected = [
            "product00",
            "product01",
            "product02"
        ]

        alert.generate_alerts()
        results = alert.test_generate_alerts_results

        self.assertEqual(expected, results)


class TestAlertRetailerA(unittest.TestCase):
    def test_format_price(self):
        email_manager = EmailManager("me")
        alert_retailer_a = AlertRetailerA("TEST-RTX-3060", email_manager)
        
        expected = {
            "€ 1.799,00": 1799.0,
            "€ 1.689,00": 1689.0,
            "€ 1.194,00": 1194.0,
            "€ 10.194,00": 10194.0,
            "€ 599,00": 599.0,
            "€ 23,00": 23.0,
            "100.00": 100.0,
            "€ ": float("inf"),
            "FEHLER": float("inf"),
            "€ 1304.00": float("inf"),
            "€ 1.304.00": float("inf")
        }

        result = {x: alert_retailer_a.format_price(x) for x in expected}

        self.assertEqual(expected, result)


# Change definition of generate_email_alert() to 
# test whether it is being correctly triggered
def generate_email_alert(self, id):
    self.test_generate_alerts_results.append(id)
         

if __name__ == "__main__":
    unittest.main(verbosity=2)
