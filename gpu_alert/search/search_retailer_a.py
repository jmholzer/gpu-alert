import re
from typing import Any, Dict, Iterable

from bs4 import BeautifulSoup

from gpu_alert.mailer import Mailer
from gpu_alert.product import Product, ProductRetailerA
from gpu_alert.utils import generate_time_stamp

from .search import Search


"""
CODE REVIEW

1. No exception handling for network and parsing failures
2. Make stock regex configurable rather than hardcoded to adapt to retailer changes
3. Non-parsable prices currently return `inf`, it is not immediately clear why this works,
    this should be explicitly documented
4. Tight coupling with DOM, investigate using an API if possible
"""


class SearchRetailerA(Search):
    """
    A class inheriting from `Search`, containing the specific methods to parse
    the response of search http requests made to retailer A.

    Attributes:
        _vendor -- the name of the vendor to search the given product for.
        _product -- the name of the product to search for.
        _email_manager -- an interface to AWS SES used to send alert emails.
        _profile -- a dict containing data on variants of the product being
            searched for and a timestamp of the last update to this data.
        _products -- a dict containing only the product data stored in profile.
        _stock_regex -- a regex expression used to check for stock availability
            in the response of search http requests.

    Methods:
        __init__
        _format_price
        _interpret_stock_message
        _update_product_data
        _parse_search_results
        _update_products
    """

    def __init__(self, product: str, email_manager: Mailer) -> None:
        """
        Constructs all the necessary attributes for the SearchRetailerA object.

        Args:
            product (str): The name of the product to search for.
            email_manager (Mailer): An interface to AWS SES used to send alert emails.
        """
        Search.__init__(self, "retailer_a", product, email_manager)
        self._stock_regex = re.compile(
            r"^Auf Lager.*|^Ware neu eingetroffen.*|^Artikel kann.*"
        )

    def _format_price(self, price: str) -> float:
        """
        Formats the price into a standard float format.

        Args:
            price (str): The price as a string in the format provided by retailer A.

        Returns:
            float: The price as a float. If price can't be converted to a float, it returns infinity.
        """
        if re.match(r"^[^0-9]+(\d+)\.(\d+),(\d+)", price):
            price = re.sub(r"^[^0-9]+(\d+)\.(\d+),(\d+)", "\g<1>\g<2>.\g<3>", price)
        elif re.match(r"^[^0-9]+(\d+),(\d+)", price):
            price = re.sub(r"^[^0-9]+(\d+),(\d+)", "\g<1>.\g<2>", price)

        try:
            return float(price)
        except ValueError:
            return float("inf")

    def _interpret_stock_message(self, message: str) -> bool:
        """
        Interprets the stock message to determine if the product is in stock or not.

        Args:
            message (str): The stock message from retailer A.

        Returns:
            bool: True if the product is in stock, False otherwise.
        """
        if self._stock_regex.match(message):
            return True
        else:
            return False

    def _update_product_data(self, id: str, product_data: Dict[str, Any]) -> None:
        """
        Updates the product data and the timestamp of the last update for a specific product.

        Args:
            id (str): The id of the product.
            product_data (dict): A dictionary containing the new product data.
        """
        if product_data:
            # Update timestamp
            self._products[id]["time_updated"] = generate_time_stamp()

        for key in product_data:
            self._products[id][key] = product_data[key]

    def _parse_search_results(
        self, search_results: Iterable[Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parses the search results from retailer A.

        Args:
            search_results: The search results from retailer A.

        Returns:
            dict: A dictionary where the keys are product names and the values are
                dictionaries with product data.
        """
        parsed_search_results = dict()

        for result in search_results:
            name = str(result.findChild("div", {"class": "product-name"}).text)

            stock_message = result.findChild("div", {"class": "delivery-info"}).text
            stock = self._interpret_stock_message(stock_message)

            unformatted_price = result.findChild("span", {"class": "price"}).text
            price = self._format_price(unformatted_price)

            url = result["href"]

            parsed_search_results[name] = {"stock": stock, "price": price, "url": url}

        return parsed_search_results

    def _update_products(self) -> None:
        """
        Updates the product data for all products by making a search http request to retailer A,
        parsing the response, and updating the product data accordingly.
        """
        search_response = self._session.post(
            self._requests["search"]["url"],
            headers=self._requests["search"]["headers"],
            data=self._requests["search"]["data"],
        )
        parsed_response = BeautifulSoup(search_response.text, "lxml")
        search_results = parsed_response.find_all("a", {"class", "productBox"})
        parsed_results = self._parse_search_results(search_results)

        for id in self._products:
            name = self._products[id]["name"]

            last_stock_state = self._products[id]["stock"]

            if name in parsed_results:
                self._update_product_data(id, parsed_results[name])
            else:
                self._update_product_data(id, {"stock": False})

            self._update_alert_status(id, last_stock_state)

    def _create_product_watcher(self, product: Dict[str, Any]) -> Product:
        """
        Returns the product watcher for the retailer being searched.
        """
        return ProductRetailerA(product, self._session)
