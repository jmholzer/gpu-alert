import json
from typing import Dict

import boto3
from botocore.exceptions import ClientError

from utility import generate_absolute_path


class EmailManager:
    """
    An object of EmailManager provides an interface for the sending
    of alert emails via AWS SES.

    Attributes:
        recipient_group -- the name of a group of recipients of alert emails.
        sender -- the SES-enabled email to use to send alerts.
        ses_client -- an object enabling send-email requests to be sent to SES.

    Methods:
        __init__
        init_sender
        init_ses_client
        read_recipients
        send_email
        send_to_all
    """

    def __init__(self, recipient_group: str) -> None:
        # Set object values by argument
        self.recipient_group = recipient_group
        # Set object values with function calls
        self.init_ses_client()
        self.init_sender()

    def init_sender(self) -> None:
        relative_file_path = f"resources/email/senders/me.json"
        absolute_file_path = generate_absolute_path(relative_file_path)

        with open(absolute_file_path, "r") as in_:
            self.sender = json.load(in_)["sender"]

    def init_ses_client(self) -> None:
        self.ses_client = boto3.client("ses", region_name="eu-central-1")

    def read_recipients(self) -> None:
        relative_file_path = f"resources/email/recipients/{self.recipient_group}.json"
        absolute_file_path = generate_absolute_path(relative_file_path)

        with open(absolute_file_path, "r") as in_:
            recipients = json.load(in_)

        return (recipients[id]["email"] for id in recipients)

    def send_email(
        self, recipient_email: str, alert_type: str, template_data: Dict[str, str]
    ) -> None:
        try:
            self.ses_client.send_templated_email(
                Source=self.sender,
                Destination={"ToAddresses": [recipient_email]},
                Template=alert_type,
                TemplateData=template_data,
            )
        except ClientError as e:
            print(e.response["Error"]["Message"])

    def send_to_all(
        self: str,
        alert_type: str,
        product: str,
        retailer: str,
        url: str,
        name: str,
        price: str,
        time: str,
    ) -> None:
        recipient_emails = self.read_recipients()

        template_data = json.dumps(
            {
                "product": product,
                "retailer": retailer,
                "url": url,
                "name": name,
                "price": price,
                "time": time,
            }
        )

        for recipient_email in recipient_emails:
            self.send_email(recipient_email, alert_type, template_data)
