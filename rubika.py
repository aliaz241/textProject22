# soroush.py
import requests
import json

def send_to_soroush(text):
    session = json.load(open("soroush_session.json"))

    url = "https://sapp.ir/api/v1/messages/send"

    payload = {
        "receiver": session["chat_id"],
        "text": text
    }

    headers = {
        "Authorization": f"Bearer {session['token']}"
    }

    requests.post(url, json=payload, headers=headers)
