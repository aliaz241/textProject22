import requests
import json

BOT_TOKEN = "7810023171:AAGBtujYuGY0inhiSefujYOh2ONaPfLyb6w"

CONFIG_FILE = "config.json"
DATA_FILE = "data.json"


# ===== LOAD / SAVE =====
def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ===== GET UPDATES =====
def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    return requests.get(url).json()


# ===== SAVE MESSAGES =====
def save_data(messages):
    with open(DATA_FILE, "w") as f:
        json.dump({"messages": messages}, f, indent=2)


# ===== FETCH CHANNEL POSTS =====
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


# ===== HANDLE COMMANDS =====
def handle_command(text):
    config = load_config()

    if text.startswith("/add"):
        ch = text.replace("/add", "").strip()
        if ch not in config["channels"]:
            config["channels"].append(ch)
            save_config(config)
            return f"Added {ch}"

    elif text.startswith("/remove"):
        ch = text.replace("/remove", "").strip()
        if ch in config["channels"]:
            config["channels"].remove(ch)
            save_config(config)
            return f"Removed {ch}"

    elif text.startswith("/list"):
        return "\n".join(config["channels"]) or "No channels"

    return None


# ===== MAIN =====
def main():
    data = get_updates()

    messages = get_messages()
    save_data(messages)

    for item in data.get("result", []):
        msg = item.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text")

        if not chat_id or not text:
            continue

        result = handle_command(text)

        if result:
            send(chat_id, result)


def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


if __name__ == "__main__":
    main()
