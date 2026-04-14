import requests

BOT_TOKEN = "7810023171:AAGBtujYuGY0inhiSefujYOh2ONaPfLyb6w"

def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    res = requests.get(url).json()
    return res.get("result", [])

def fetch_messages():
    updates = get_updates()
    messages = []

    for u in updates:
        msg = u.get("channel_post")
        if msg and "text" in msg:
            messages.append(msg["text"])

    return messages[-5:]
