import requests


class SENDSMSBase:
    def __init__(
        self,
        sms_url=None,
        text_message=None,
    ):
        self.sms_url = sms_url
        self.text_message = text_message

    def test_send_sms(self, payload, header_vals):
        response = requests.post(
            url=self.sms_url, headers=header_vals, data=payload, timeout=30
        )
        return response
