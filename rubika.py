import requests
import json

def send_to_rubika(text):
    with open("rubika_session.json") as f:
        session = json.load(f)

    url = "https://messengerg2c1.iranlms.ir/"

    payload = {
        "api_version": "5",
        "method": "sendMessage",
        "auth": session["auth"],
        "data": {
            "object_guid": "YOUR_GUID",
            "text": text
        }
    }

    requests.post(url, json=payload)
