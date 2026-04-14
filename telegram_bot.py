import requests
import json

BOT_TOKEN = "7810023171:AAGBtujYuGY0inhiSefujYOh2ONaPfLyb6w"

CONFIG_FILE = "config.json"
DATA_FILE = "data.json"


# ===== CONFIG =====
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {"channels": ["@channel1", "@channel2"], "limit": 5}


def save_data(messages):
    with open(DATA_FILE, "w") as f:
        json.dump({"messages": messages}, f, indent=2)


# ===== GET LAST POSTS =====
def get_messages():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    data = requests.get(url).json()

    config = load_config()
    limit = config["limit"]

    messages = []

    for item in data.get("result", []):
        msg = item.get("channel_post")

        if msg and "text" in msg:
            messages.append(msg["text"])

    return messages[-limit:]


# ===== RUN =====
def main():
    messages = get_messages()
    save_data(messages)
    print(f"Saved {len(messages)} messages")


if __name__ == "__main__":
    main()
