""" Firebase Notification python file """
# pylint: disable= E0401, C0116, R0903
import json
import logging
import requests

_logger = logging.getLogger(__name__)


class FireBaseNotificationBase:
    """Firebase Notification class"""

    def __init__(
        self,
        url="https://fcm.googleapis.com/fcm/send",
        server_token="",
    ):
        self.url = url
        self.server_token = server_token

    def send_notification(
        self,
        title=None,
        body=None,
        device_token=None,
        message_id=False,
        channel_id=False,
        partner_id=False,
        sender_partner=False,
    ):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "key=" + self.server_token,
        }
        message_body = {
            "notification": {"title": title, "body": body},
            "to": device_token,
            "priority": "high",
            "data": {
                "title": title,
                "body": body,
                "message_id": message_id,
                "channel_id": channel_id,
                "partner_id": partner_id,
                "sender_partner": sender_partner,
            },
        }
        try:
            response = requests.post(
                self.url, headers=headers, data=json.dumps(message_body)
            )
            _logger.info("__________________response %s", response)
            if response.status_code != 200:
                _logger.error(
                    "Error: Push notification error code is %s , %s",
                    response.status_code,
                    response.text,
                )
            if response.status_code == 200:
                _logger.info(
                    "INFO Push Notification code %s , %s",
                    response.status_code,
                    response.text,
                )
        except Exception as e:
            _logger.error("Error Push Notification %s", e)
