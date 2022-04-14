import datetime
import json
import os.path
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Union

import numpy.random
from bs4 import BeautifulSoup
from requests import Session

from mailer import EmailManager
from utility import generate_absolute_path


class AlertManager:
    """
    An object of AlertManager controls the main execution loop of
    the program. It loads an 'alert profile', containing the names
    of the products to send alerts for and the name of the retailer
    to search for them on. It then creates Alert objects for the
    specified retailers, initialised with the target products
    and continuously updates them.

    Attributes:
        alert_profile_name -- the name of the alert profile to use.
        email_manager -- an interface to AWS SES used to send alert emails.
        alerts -- a list of Alert objects to continuously update.

    Methods:
        __init__
        init_email_manager
        init_alerts
        generate_time_interval
        auto_update
    """

    def __init__(self, alert_profile_name: str) -> None:
        # Set object values by argument
        self.alert_profile_name = alert_profile_name
        # Attach an instance of EmailManager
        self.init_email_manager()
        # Attach
        self.init_alerts()

    def init_email_manager(self) -> None:
        self.email_manager = EmailManager("me")

    def init_alerts(self) -> None:
        relative_path = f"resources/alert/data/{self.alert_profile_name}.json"
        alert_profile_path = generate_absolute_path(relative_path)

        vendor_class_map = {"retailer_a": AlertRetailerA}

        with open(alert_profile_path, "r") as alert_profile:
            self.alerts = [
                vendor_class_map[alert["vendor"]](alert["product"], self.email_manager)
                for alert in json.load(alert_profile)
            ]

    def generate_time_interval(self) -> float:
        # Generate a pseudorandom time interval between requests
        time_interval = numpy.random.uniform(0, 30)
        time_interval += numpy.random.normal(30, 7)
        return 5 + (abs(time_interval) / len(self.alerts))

    def auto_update(self) -> None:
        while True:
            for alert in self.alerts:
                alert.update()
                time.sleep(self.generate_time_interval())


class Alert:
    """
    An Alert object controls the update loop for one product at one retailer.
    It constructs the http requests needed to check for product availability
    when initialised and continuously executes these requests and parses
    the response. If availability is found, a ProductWatcher object is created,
    which executes a focussed search on the product by interacting with the
    product page itself, rather than the website's search functionality.

    Alert objects specific to the retailer being searched inherit from this class.

    Attributes:
        vendor -- the name of the vendor to search the given product for.
        product -- the name of the product to search for.
        email_manager -- an interface to AWS SES used to send alert emails.
        profile -- a dict containing data on variants of the product being
            searched for and a timestamp of the last update to this data.
        products -- a dict containing only the product data stored in profile.

    Methods:
        __init__
        init_profile
        init_requests
        init_session
        read_products
        generate_timetamp
        update_profile
        update_products
        update_alert_status
        generate_email_alert
        generate_alerts
        start_product_watcher
        update
    """

    def __init__(self, vendor: str, product: str, email_manager: EmailManager) -> None:
        # Set object values by argument
        self.vendor = vendor
        self.product = product
        self.email_manager = email_manager

        # Set object values with function calls
        self.init_profile()
        self.read_products()
        self.init_requests()
        self.init_session()

    def init_profile(self):
        directory = os.path.dirname(__file__)
        relative_file_name = f"resources/alert/data/{self.vendor}/{self.product}.json"
        absolute_file_name = os.path.join(directory, relative_file_name)
        self.profile_file_path = absolute_file_name

        with open(self.profile_file_path, "r") as in_:
            self.profile = json.load(in_)

    def init_requests(self) -> None:
        relative_file_path = (
            f"resources/alert/requests/{self.vendor}/search/{self.product}.json"
        )
        requests_file_path = generate_absolute_path(relative_file_path)

        with open(requests_file_path, "r") as in_:
            self.requests = json.load(in_)

    def init_session(self) -> None:
        time.sleep(numpy.random.uniform(5, 10))
        self.session = Session()
        self.session.get(
            self.requests["cookies"]["url"], headers=self.requests["cookies"]["headers"]
        )

    def read_products(self) -> None:
        self.products = self.profile.get("products")

    def generate_time_stamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_profile(self) -> None:
        self.profile["time_updated"] = self.generate_time_stamp()
        self.profile["products"] = self.products
        with open(self.profile_file_path, "w") as out:
            json.dump(self.profile, out, indent=4)

    def update_products(self) -> None:
        # update_products is defined in inheriting classes
        pass

    def update_alert_status(self, id: str, last_stock_state: bool) -> None:
        if not last_stock_state and self.products[id]["stock"]:
            self.products[id]["alert"] = True
        else:
            self.products[id]["alert"] = False

    def generate_email_alert(self, id: str) -> None:
        self.email_manager.send_to_all(
            "stock_alert",
            self.product,
            self.vendor,
            self.products[id]["url"],
            self.products[id]["name"],
            self.products[id]["price"],
            self.products[id]["time_updated"],
        )

    def generate_alerts(self) -> None:
        if any((self.products[id]["alert"] for id in self.products)):
            self.start_product_watcher()

    def start_product_watcher(self) -> None:
        found_targets = []

        # Check if target products have alerts
        for id in self.products:
            product = self.products[id]
            if product["alert"] and product["target"]:
                found_targets.append(product)

        if found_targets:
            found_targets.sort(key=lambda x: x["priority"])
            # This breaks vendor-independence of this class, will need to be fixed
            # if this is ever extended for more vendors.
            target_product = found_targets[0]
            product_watcher = ProductWatcherRetailerA(target_product, self.session)

            # Check the product page of the chosen target product for give minutes or
            # until availability is found and an alert is sent, whichever is first.
            print(
                f"Found stock for target product {target_product['name']} via search."
                + " Starting product page watcher."
            )

            result = product_watcher.auto_update()
            if result:
                self.generate_email_alert(target_product["id"])

    def update(self) -> None:
        time = self.generate_time_stamp()
        try:
            self.update_products()
            print(f"Successfully downloaded product data for {self.product} at {time}.")
        except Exception as e:
            print(f"Error downloading product data for {self.product} at {time}.")
            print(e)
        self.update_profile()
        self.generate_alerts()


class AlertRetailerA(Alert):
    """
    A class inheriting from Alert, containing the specific methods to parse
    the response of search http requests made to retailer A.

    Attributes:
        vendor -- the name of the vendor to search the given product for.
        product -- the name of the product to search for.
        email_manager -- an interface to AWS SES used to send alert emails.
        profile -- a dict containing data on variants of the product being
            searched for and a timestamp of the last update to this data.
        products -- a dict containing only the product data stored in profile.
        stock_regex -- a regex expression used to check for stock availability
            in the response of search http requests.

    Methods:
        __init__
        init_profile
        init_requests
        init_session
        read_products
        generate_timetamp
        update_profile
        update_products
        update_alert_status
        generate_email_alert
        generate_alerts
        start_product_watcher
        update
        init_stock_regex
        format_price
        interpret_stock_message
        update_product_data
        parse_search_results
    """

    def __init__(self, product: str, email_manager: EmailManager) -> None:
        Alert.__init__(self, "retailer_a", product, email_manager)
        self.init_stock_regex()

    def init_stock_regex(self) -> None:
        self.stock_regex = re.compile(
            r"^Auf Lager.*|^Ware neu eingetroffen.*|^Artikel kann.*"
        )

    def format_price(self, price: str) -> float:
        if re.match(r"^[^0-9]+(\d+)\.(\d+),(\d+)", price):
            price = re.sub(r"^[^0-9]+(\d+)\.(\d+),(\d+)", "\g<1>\g<2>.\g<3>", price)
        elif re.match(r"^[^0-9]+(\d+),(\d+)", price):
            price = re.sub(r"^[^0-9]+(\d+),(\d+)", "\g<1>.\g<2>", price)

        try:
            return float(price)
        except ValueError:
            return float("inf")

    def interpret_stock_message(self, message: str) -> bool:
        if self.stock_regex.match(message):
            return True
        else:
            return False

    def update_product_data(
        self, id: str, product_data: Dict[str, Union[str, int, bool, float]]
    ) -> None:
        if product_data:
            # Update timestamp
            self.products[id]["time_updated"] = self.generate_time_stamp()

        for key in product_data:
            self.products[id][key] = product_data[key]

    def parse_search_results(self, search_results) -> Dict[str, Union[str, float]]:
        parsed_search_results = dict()

        for result in search_results:
            name = result.findChild("div", {"class": "product-name"}).text

            stock_message = result.findChild("div", {"class": "delivery-info"}).text
            stock = self.interpret_stock_message(stock_message)

            unformatted_price = result.findChild("span", {"class": "price"}).text
            price = self.format_price(unformatted_price)

            url = result["href"]

            parsed_search_results[name] = {"stock": stock, "price": price, "url": url}

        return parsed_search_results

    def update_products(self) -> None:
        search_response = self.session.post(
            self.requests["search"]["url"],
            headers=self.requests["search"]["headers"],
            data=self.requests["search"]["data"],
        )

        parsed_response = BeautifulSoup(search_response.text, "lxml")

        search_results = parsed_response.find_all("a", {"class", "productBox"})

        parsed_results = self.parse_search_results(search_results)

        for id in self.products:
            name = self.products[id]["name"]

            last_stock_state = self.products[id]["stock"]

            if name in parsed_results:
                self.update_product_data(id, parsed_results[name])
            else:
                self.update_product_data(id, {"stock": False})

            self.update_alert_status(id, last_stock_state)


class ProductWatcher:
    """
    ProductWatcher objects are instantiated when an Alert object finds
    product availability using the sites search functionality. ProductWatchers
    then perform a refined search on a given product using its product page,
    they live for 5 minutes.

    Product watcher classes specific to the retailer inherit from this class.

    Attributes:for
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

    def __init__(self, product_data: Dict[str, Union[str, int, bool, float]]) -> None:
        self.init_stop_time()
        self.init_request_headers()

        self.product_data = product_data
        self.send_alert_flag = False

    def init_stop_time(self) -> None:
        self.stop_time = self.get_current_time() + timedelta(minutes=5)

    def init_request_headers(self) -> None:
        relative_file_path = (
            f"resources/alert/requests/{self.vendor}/product/product_page.json"
        )
        headers_file_path = generate_absolute_path(relative_file_path)

        with open(headers_file_path, "r") as in_:
            self.headers = json.load(in_)

    def get_current_time(self) -> datetime:
        return datetime.now()

    def generate_time_stamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_time_interval(self) -> float:
        time_interval = numpy.random.uniform(0, 8)
        time_interval += numpy.random.normal(8, 2)
        return 5 + abs(time_interval)

    def check_availability(self) -> None:
        # Defined in inheriting class
        pass

    def update(self) -> None:
        time = self.generate_time_stamp()
        try:
            self.check_availability()
            print(
                "Successfully downloaded product availability for "
                + f"{self.product_data['name']} at {time}."
            )

            if self.availability:
                self.send_alert_flag = True
        except Exception as e:
            print(
                "Error reading product availability for "
                f"{self.product_data['name']} at {time}:"
            )
            print(e)

    def auto_update(self) -> bool:
        while True:
            self.update()

            if self.send_alert_flag:
                print(
                    "Generating product availability alert for"
                    + f" {self.product_data['name']}. Returning"
                    + " control to searcher."
                )
                return True

            if self.get_current_time() > self.stop_time:
                print(
                    f"Maximum single-product scan time exceeded."
                    + " Returning control to searcher."
                )
                return False

            time.sleep(self.generate_time_interval())


class ProductWatcherRetailerA(ProductWatcher):
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

    def __init__(
        self, product_data: Dict[str, Union[str, int, bool, float]], session: Session
    ) -> None:
        self.vendor = "retailer_a"
        self.session = session
        ProductWatcher.__init__(self, product_data)

    def check_availability(self) -> None:
        product_page = self.session.get(self.product_data["url"], headers=self.headers)

        parsed_product_page = BeautifulSoup(product_page.text, "html.parser")

        if parsed_product_page.find_all("a", {"title", "In den Warenkorb"}):
            self.availability = True
        else:
            self.availability = False


if __name__ == "__main__":
    alert_manager = AlertManager("alert_profile")
    alert_manager.auto_update()
