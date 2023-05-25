import unittest

from gpu_alert.mailer import Mailer
from gpu_alert.search import SearchRetailerA


class TestSearchRetailerA(unittest.TestCase):
    def test_format_price(self):
        email_manager = Mailer("me")
        alert_retailer_a = SearchRetailerA("TEST-RTX-3060", email_manager)

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
            "€ 1.304.00": float("inf"),
        }

        result = {x: alert_retailer_a._format_price(x) for x in expected}

        self.assertEqual(expected, result)
