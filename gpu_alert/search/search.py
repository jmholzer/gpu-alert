import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from requests import Session

from gpu_alert.mailer import Mailer
from gpu_alert.product import Product
from gpu_alert.utils import generate_time_stamp


class Search(ABC):
    """
    A `Search` object controls the update loop for one product at one retailer.
    It constructs the http requests needed to check for product availability
    when initialised and continuously executes these requests and parses
    the response. If availability is found, a `Product` object is created,
    which executes a focussed search on the product by interacting with the
    product page itself, rather than the website's search functionality.

    `Search` objects specific to the retailer being searched inherit from this class.

    Attributes:
        _vendor -- the name of the vendor to search the given product for.
        _product -- the name of the product to search for.
        _email_manager -- an interface to AWS SES used to send alert emails.
        _profile -- a dict containing data on variants of the product being
            searched for and a timestamp of the last update to this data.
        _products -- a dict containing only the product data stored in profile.

    Methods:
        __init__
        _read_profile
        _read_requests
        _create_session
        _update_profile
        _update_products
        _update_alert_status
        _generate_email_alert
        _generate_alerts
        _start_product_watcher
        _get_product_watcher
        update
    """

    def __init__(self, vendor: str, product: str, email_manager: Mailer) -> None:
        """
        Initializes the Search object with vendor, product, and email manager.

        Args:
            vendor (str): The name of the vendor to search the given product for.
            product (str): The name of the product to search for.
            email_manager (Mailer): An interface to AWS SES used to send alert emails.
        """
        # Set object values by argument
        self._vendor = vendor
        self._product = product
        self._email_manager = email_manager

        self._profile = self._read_profile()
        self._products = self._profile["products"]
        self._requests = self._read_requests()
        self._session = self._create_session()

    def _read_profile(self) -> Dict[str, Any]:
        """
        Reads the profile data of the product from the file system.

        Returns:
            dict: The profile data.
        """
        self._profile_file_path = Path(__file__).parents[2] / Path(
            f"resources/retailers/{self._vendor}/data/{self._product}.json"
        )
        with open(self._profile_file_path, "r") as in_:
            return json.load(in_)

    def _read_requests(self) -> Dict[str, Any]:
        """
        Reads the http request data for the product from the file system.

        Returns:
            dict: The http request data.
        """
        requests_file_path = Path(__file__).parents[2] / Path(
            f"resources/retailers/{self._vendor}/requests/search/{self._product}.json"
        )

        with open(requests_file_path, "r") as in_:
            return json.load(in_)

    def _create_session(self) -> Session:
        """
        Initializes the session object by making a GET request to the cookies URL.
        """
        session = Session()
        session.get(
            self._requests["cookies"]["url"],
            headers=self._requests["cookies"]["headers"],
        )
        return session

    def _update_profile(self) -> None:
        """
        Updates the profile data of the product and writes it to the file system.
        """
        self._profile["time_updated"] = generate_time_stamp()
        self._profile["products"] = self._products
        with open(self._profile_file_path, "w") as out:
            json.dump(self._profile, out, indent=4)

    @abstractmethod
    def _update_products(self) -> None:
        """
        Updates the product data. This method should be implemented by subclasses.
        """
        pass

    def _update_alert_status(self, id: str, last_stock_state: bool) -> None:
        """
        Updates the alert status of the product.

        Args:
            id (str): The id of the product.
            last_stock_state (bool): The last known stock state of the product.
        """
        if not last_stock_state and self._products[id]["stock"]:
            self._products[id]["alert"] = True
        else:
            self._products[id]["alert"] = False

    def _generate_email_alert(self, id: str) -> None:
        """
        Generates an email alert for the product.

        Args:
            id (str): The id of the product.
        """
        self._email_manager.send_to_all(
            "stock_alert",
            self._product,
            self._vendor,
            self._products[id]["url"],
            self._products[id]["name"],
            self._products[id]["price"],
            self._products[id]["time_updated"],
        )

    def _generate_alerts(self) -> None:
        """
        Checks all products for alerts and starts the product watcher if any are found.
        """
        if any((self._products[id]["alert"] for id in self._products)):
            self._start_product_watcher()

    def _start_product_watcher(self) -> None:
        """
        Starts the product watcher for target products that have alerts.
        """
        found_targets = [
            p for p in self._products.values() if p["target"] and p["alert"]
        ]

        if found_targets:
            found_targets.sort(key=lambda x: x["priority"])
            target_product = found_targets[0]
            product_watcher = self._create_product_watcher(target_product)

            # Check the product page of the chosen target product for give minutes or
            # until availability is found and an alert is sent, whichever is first.
            print(
                f"Found stock for target product {target_product['name']} via search."
                + " Starting product page watcher."
            )

            result = product_watcher.auto_update()
            if result:
                self._generate_email_alert(target_product["id"])

    @abstractmethod
    def _create_product_watcher(self, product: Dict[str, Any]) -> Product:
        """
        Returns the product watcher for the retailer being searched.
        """
        pass

    def update(self) -> None:
        """
        Updates the product data, profile, and alerts.
        """
        time = generate_time_stamp()
        try:
            self._update_products()
            print(
                f"Successfully downloaded product data for {self._product} at {time}."
            )
        except Exception as e:
            print(f"Error downloading product data for {self._product} at {time}.")
            print(e)
        self._update_profile()
        self._generate_alerts()
