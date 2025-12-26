import requests
from decouple import config

def send_sms(mobile: str, message: str):
    payload = {
        "token": config("SPARROW_SMS_TOKEN"),
        "from": config("SPARROW_SMS_FROM"),  # REQUIRED
        "to": mobile,
        "text": message,
    }

    r = requests.post(
        config("SPARROW_SMS_URL"),
        data=payload,
        timeout=10
    )

    return r.status_code, r.text
