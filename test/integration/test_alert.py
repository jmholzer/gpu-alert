import json
import sys
import unittest

# Local module imports
sys.path.append("../..")
from alert import AlertRetailerA
from mailer import EmailManager


class TestAlertClasses(unittest.TestCase):
    """
    Integration tests for the classes in alert.py.
    """
    
    def test_update_products(self):
        # TODO: Update for filtered search strategy.
        alert_objects = generate_alert_objects()
        for alert in alert_objects:
            with self.subTest(test=alert):
                if isinstance(alert, AlertRetailerA):
                    test_data_file_path = "data/update_products_retailer_a_30_04_21.json"

                with open(test_data_file_path, "r") as in_:
                    expected = json.load(in_).get("products")
                    expected = {
                        id: expected[id]["stock"]
                        for id in expected
                    }

                alert.update_products()
                results = alert.products
                results = {
                    id: results[id]["stock"]
                    for id in results
                }

                self.assertEqual(results, expected)

    def test_update_alert_status(self):
        alert_objects = generate_alert_objects()
        for alert in alert_objects:
            with self.subTest(test=alert):
                test_id = next(iter(alert.products.keys()))
                
                expected = False

                last_stock_state = False

                # Expect alert state to change to True
                alert.products[test_id]["stock"] = True
                alert.update_alert_status(test_id, last_stock_state)
                
                expected = True
                result = alert.products[test_id]["alert"]
                self.assertEqual(expected, result)

                # Expect alert state to change to False
                last_stock_state = True
                alert.products[test_id]["stock"] = True
                alert.update_alert_status(test_id, last_stock_state)

                expected = False
                result = alert.products[test_id]["alert"]
                self.assertEqual(expected, result)

                # Expect alert state to stay False
                last_stock_state = False
                alert.products[test_id]["stock"] = False
                alert.update_alert_status(test_id, last_stock_state)
                
                expected = False
                result = alert.products[test_id]["alert"]
                self.assertEqual(expected, result)

    def test_update(self):
        alert_objects = generate_alert_objects()
        for alert in alert_objects:
            with self.subTest(test=alert):
                # Test that product profile is being correctly updated in memory
                # by checking that time stamp is different between updates.
                initial_time_updated = alert.profile.get("time_updated")
                alert.update()
                new_time_updated = alert.profile.get("time_updated")

                self.assertNotEqual(initial_time_updated, new_time_updated)

                # Test that product profile file is being correctly written.
                with open(alert.profile_file_name, "r") as in_:
                    file_profile = json.load(in_)
                    new_time_updated = file_profile["time_updated"]

                self.assertNotEqual(initial_time_updated, new_time_updated)


def generate_alert_objects():
    # Return a dictionary containing alert classes as key, name of
    # test product (used to open corresponding profile) as key.
    email_manager = EmailManager("me")
    return [
        AlertRetailerA("TEST-RTX-3080", email_manager)
    ]


if __name__ == "__main__":
    unittest.main(verbosity=2)
