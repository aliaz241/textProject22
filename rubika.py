import requests
import json

def send_to_rubika(text):
    session = json.load(open("rubika_session.json"))

    url = "https://messengerg2c169.iranlms.ir/"

    payload = {
        "api_version": "5",
        "method": "sendMessage",
        "auth": session["auth"],
        "data": {
            "object_guid": session["object_guid"],
            "text": text
        }
    }

    requests.post(url, json=payload)
