
import requests

RUBIKA_TOKEN = "YOUR_RUBIKA_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_message(text):
    url = "https://bot.rubika.ir/v1/bot/sendMessage"

    headers = {
        "Authorization": f"Bot {RUBIKA_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    requests.post(url, json=payload, headers=headers)
