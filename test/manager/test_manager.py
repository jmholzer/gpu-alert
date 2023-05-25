import unittest

from gpu_alert.manager import Manager


class TestManager(unittest.TestCase):
    def test_generate_time_interval(self):
        alert = Manager("alert_profile")
        for _ in range(60 * 24 * 365 * 5):
            result = alert._generate_time_interval()
            lower_limit = 5
            upper_limit = 105
            self.assertGreater(result, lower_limit)
            self.assertLess(result, upper_limit)
