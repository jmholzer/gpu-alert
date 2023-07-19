import json
import time
from pathlib import Path
from typing import List

import numpy

from gpu_alert.mailer import Mailer
from gpu_alert.search import Search, SearchRetailerA


class Manager:
    """
    An object of `Manager` controls the main execution loop of
    the program. It loads an 'alert profile', containing the names
    of the products to send alerts for and the name of the retailer
    to search for them on. It then creates `Search` objects for the
    specified retailers, initialised with the target products
    and continuously updates them.

    Attributes:
        _alert_profile_name -- the name of the alert profile to use.
        _mailer -- an interface to AWS SES used to send alert emails.
        _searches -- a list of Alert objects to continuously update.

    Methods:
        __init__
        _create_searches
        _generate_time_interval
        auto_update
    """

    def __init__(self, alert_profile_name: str) -> None:
        """
        Initialize a Manager object.

        Args:
            alert_profile_name (str): The name of the alert profile to use.

        Returns:
            None
        """
        self._alert_profile_name = alert_profile_name
        self._mailer = Mailer("me")
        self._searches = self._create_searches()

    def _create_searches(self) -> List[Search]:
        """
        Create searches for the specified retailers, initialized with the target products.

        Returns:
            List[Search]: A list of Search objects.
        """
        alert_profile_path = Path(__file__).parents[2] / Path(
            f"resources/alert_profiles/{self._alert_profile_name}.json"
        )
        vendor_class_map = {"alternate": SearchRetailerA}

        with open(alert_profile_path, "r") as alert_profile:
            self._searches = [
                vendor_class_map[alert["vendor"]](alert["product"], self._mailer)
                for alert in json.load(alert_profile)
            ]
        return self._searches

    def _generate_time_interval(self) -> float:
        """
        Generate a pseudorandom time interval between requests to scrape a bit more ethically.

        Returns:
            float: The generated time interval.
        """
        time_interval = numpy.random.uniform(0, 30)
        time_interval += numpy.random.normal(30, 7)
        return 5 + (abs(time_interval) / len(self._searches))

    def auto_update(self) -> None:
        """
        Continuously update the Search objects with a pseudorandom delay between updates.

        Returns:
            None
        """
        while True:
            for search in self._searches:
                search.update()
                time.sleep(self._generate_time_interval())


if __name__ == "__main__":
    alert_manager = Manager("me")
    alert_manager.auto_update()
