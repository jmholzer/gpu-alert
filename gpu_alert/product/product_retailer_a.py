from typing import Any, Dict

from bs4 import BeautifulSoup
from requests import Session

from .product import Product


"""
CODE REVIEW

1. Check HTTP response status before parsing
2. Handle potential HTTP request exceptions, connection problems currently
    result in a crash
3. Move hardcoded string ('In den Warenkorb') to a class-level constant
4. Use 'super().__init__(product_data)' for parent constructor, more pythonic
5. Update docstring to match class methods and attributes
"""


class ProductRetailerA(Product):
    """
    A product watcher class specific to Retailer A, with methods to parse the
    requested data from the website of Retailer A. Inherits from the ProductWatcher
    class.

    Attributes:
        stop_time -- the wall clock time at which to clear the object.
        headers -- a dict of the headers of the http request to search a
            product page.
        availability -- a boolean flag indicating whether the product was
            available at the last request.
        product_data -- a dict of data on the product being searched for.
        send_alert_flag -- a boolean flag indicating whether an email alert was
            sent for the product being searched for.

    Methods:
        __init__
        init_stop_time
        init_request_headers
        get_current_time
        generate_time_stamp
        generate_time_interval
        check_availability
        generate_alert
        update
        auto_update
        check_availability
    """

    def __init__(self, product_data: Dict[str, Any], session: Session) -> None:
        self._vendor = "retailer_a"
        self._session = session
        Product.__init__(self, product_data)

    def _check_availability(self) -> None:
        product_page = self._session.get(
            self._product_data["url"], headers=self._headers
        )

        parsed_product_page = BeautifulSoup(product_page.text, "html.parser")

        if parsed_product_page.find_all("a", {"title", "In den Warenkorb"}):
            self._availability = True
        else:
            self._availability = False
