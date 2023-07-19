import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import numpy

from gpu_alert.utils import generate_time_stamp


"""
CODE REVIEW

1. Bare exception used, shows that we don't know what exceptions to expect
    Logging, rather than `print` would help with debugging
2. Magic numbers used, should be declared as constants (e.g. 5 minutes)
3. File paths are hardcoded, should be using config or env vars
4. Very simple while True / sleep loop used, which can cause the script to
    be unresponsive to signals
5. Monotonic time (`time.monotonic`) for more accurate time comparisons rather
    than system clock, which can move backwards
6. _generate_time_interval could be a static method, and repeats logic in `Manager`,
    should DRY this
7. Importing `numpy` is over the top for generating a random number
8. Docstrings do not match current methods and attributes
"""


class Product(ABC):
    """
    Product objects are instantiated when an Alert object finds
    product availability using the sites search functionality. ProductWatchers
    then perform a refined search on a given product using its product page,
    they live for 5 minutes.

    Product watcher classes specific to the retailer inherit from this class.

    Attributes:
        stop_time -- the wall clock time at which to clear the object.
        headers -- a dict of the headers of the http request to search a
            product page.
        availability -- a boolean flag indicating whether the product was
            available at the last request.
        product_data -- a dict of data on the product being searched for.
        send_alert_flag -- a boolean flag indicating whether an email alert
            should be sent for the product being watched.

    Methods:
        __init__
        init_stop_time
        init_request_headers
        get_current_time
        generate_time_stamp
        generate_time_interval
        check_availability
        update
        auto_update
    """

    _vendor: str

    def __init__(self, product_data: Dict[str, Any]) -> None:
        self._stop_time = datetime.now() + timedelta(minutes=5)
        self._headers = self._read_request_headers()
        self._product_data = product_data
        self._send_alert_flag = False
        self._availability = False

    def _read_request_headers(self) -> Dict[str, Any]:
        headers_file_path = Path(__file__).parents[2] / Path(
            f"resources/retailers/{self._vendor}/requests/product/product_page.json"
        )
        with open(headers_file_path, "r") as in_:
            return json.load(in_)

    def _generate_time_interval(self) -> float:
        time_interval = numpy.random.uniform(0, 8)
        time_interval += numpy.random.normal(8, 2)
        return 5 + abs(time_interval)

    @abstractmethod
    def _check_availability(self) -> None:
        pass

    def _update(self) -> None:
        time = generate_time_stamp()
        try:
            self._check_availability()
            print(
                "Successfully downloaded product availability for "
                + f"{self._product_data['name']} at {time}."
            )

            if self._availability:
                self._send_alert_flag = True
        except Exception as e:
            print(
                "Error reading product availability for "
                f"{self._product_data['name']} at {time}:"
            )
            print(e)

    def auto_update(self) -> bool:
        while True:
            self._update()

            if self._send_alert_flag:
                print(
                    "Generating product availability alert for"
                    + f" {self._product_data['name']}. Returning"
                    + " control to searcher."
                )
                return True

            if datetime.now() > self._stop_time:
                print(
                    "Maximum single-product scan time exceeded."
                    + " Returning control to searcher."
                )
                return False

            time.sleep(self._generate_time_interval())
