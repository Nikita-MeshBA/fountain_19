import requests
from requests.auth import HTTPBasicAuth

AUTHENTICATE_URL = "https://app.sendsms.co.ke/api/send-sms-v1"


class SENDSMSBase:
    def __init__(
        self,
        apiClientID=None,
        key=None,
        secret=None,
        serviceID=None,
        texMessage="",
        MSISDN="",
    ):
        self.apiClientID = apiClientID
        self.key = key
        self.secret = secret
        self.serviceID = serviceID
        self.texMessage = texMessage
        self.MSISDN = MSISDN

    def test_send_sms(self):
        payload = {
            "apiClientID": self.apiClientID,
            "key": self.key,
            "secret": self.secret,
            "txtMessage": self.texMessage,
            "MSISDN": self.MSISDN,
            "serviceID": self.serviceID,
        }
        response = requests.post(AUTHENTICATE_URL, data=payload, timeout=30)
        return response

    def send_sms(self, body, to_number):
        payload = {
            "apiClientID": self.apiClientID,
            "key": self.key,
            "secret": self.secret,
            "txtMessage": body,
            "MSISDN": to_number,
            "serviceID": self.serviceID,
        }
        response = requests.post(AUTHENTICATE_URL, data=payload, timeout=30)
        return response
