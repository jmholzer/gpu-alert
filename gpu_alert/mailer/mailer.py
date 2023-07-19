import json
from pathlib import Path
from typing import Any, Dict, Iterable

import boto3
from botocore.exceptions import ClientError

"""
CODE REVIEW

1. Hardcoding paths and variables, should use config or env vars.
2. Using `print` for displaying output, should use logging.
3. Refactor send_email for reuse in send_to_all to avoid duplication.
4. Inefficient to use loop to send many emails, should use batch API.
5. Excessive use of disk I/O to read static data, should load into memory once.
"""


class Mailer:
    """
    An object of `Mailer` provides an interface for the sending
    of alert emails via AWS SES.

    Attributes:
        _recipient_group -- the name of a group of recipients of alert emails.
        _sender -- the SES-enabled email to use to send alerts.
        _ses_client -- an object enabling send-email requests to be sent to SES.

    Methods:
        __init__
        _read_sender
        _create_ses_client
        _read_recipients
        send_email
        send_to_all
    """

    def __init__(self, recipient_group: str) -> None:
        """
        Initialize the Mailer object by setting the recipient group and initializing
        the SES client and the sender's email address.

        Args:
            recipient_group (str): The name of a group of recipients of alert emails.
        """
        self._recipient_group = recipient_group
        self._ses_client = self._create_ses_client()
        self._sender = self._read_sender()

    def _read_sender(self) -> Any:
        """
        Reads the sender's email from a configuration file.

        Returns:
            str: The sender's email address.
        """
        alert_profile_path = Path(__file__).parents[2] / Path(
            "resources/email/senders/me.json"
        )

        with open(alert_profile_path, "r") as in_:
            return json.load(in_)["sender"]

    def _create_ses_client(self) -> Any:
        """
        Creates an Amazon SES client in the eu-central-1 region.

        Returns:
            A boto3 SES client object.
        """
        return boto3.client("ses", region_name="eu-central-1")

    def _read_recipients(self) -> Iterable[str]:
        """
        Reads the email addresses of the recipients from a configuration file.

        Returns:
            Iterable[str]: An iterable object of recipient email addresses.
        """
        recipients_file_path = Path(__file__).parents[2] / Path(
            f"resources/email/recipients/{self._recipient_group}.json"
        )

        with open(recipients_file_path, "r") as in_:
            recipients = json.load(in_)

        return (recipients[id]["email"] for id in recipients)

    def send_email(
        self, recipient_email: str, alert_type: str, template_data: Dict[str, str]
    ) -> None:
        """
        Sends an email using a specified template and data.

        Args:
            recipient_email (str): The recipient's email address.
            alert_type (str): The type of the alert (used to select the email template).
            template_data (Dict[str, str]): The data to use in the template.
        """
        try:
            self._ses_client.send_templated_email(
                Source=self._sender,
                Destination={"ToAddresses": [recipient_email]},
                Template=alert_type,
                TemplateData=template_data,
            )
        except ClientError as e:
            print(e.response["Error"]["Message"])

    def send_to_all(
        self,
        alert_type: str,
        product: str,
        retailer: str,
        url: str,
        name: str,
        price: str,
        time: str,
    ) -> None:
        """
        Sends an email alert to all the recipients in the recipient group.

        Args:
            alert_type (str): The type of the alert (used to select the email template).
            product (str): The name of the product.
            retailer (str): The name of the retailer.
            url (str): The URL of the product.
            name (str): The name of the product.
            price (str): The price of the product.
            time (str): The time of the alert.
        """
        recipient_emails = self._read_recipients()

        template_data = {
            "product": product,
            "retailer": retailer,
            "url": url,
            "name": name,
            "price": price,
            "time": time,
        }

        for recipient_email in recipient_emails:
            self.send_email(recipient_email, alert_type, template_data)
