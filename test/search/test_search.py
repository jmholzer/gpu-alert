import unittest
from unittest.mock import patch

from gpu_alert.mailer import Mailer
from gpu_alert.search import Search


class TestSearch(unittest.TestCase):
    """
    Unit tests for the class Search in alert.py.
    """

    @patch("gpu_alert.search.Search._start_product_watcher")
    def test_generate_alerts(self, mock_start_product_watcher):
        search = Search("retailer_a", "TEST-RTX-3060", Mailer("me"))
        search._products["product0"]["alert"] = True
        search._products["product2"]["alert"] = True
        search._generate_alerts()
        self.assertEqual(mock_start_product_watcher.call_count, 1)
