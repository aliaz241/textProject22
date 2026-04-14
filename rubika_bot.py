import json
import requests

# ====== TOKEN ======
TOKEN = "BBBBIG0GRMCCYTXKBTZXPURGJPZEMFGHCGUKGRNYDFHTQXTPCRJIENNLUBISCZOC"
BASE_URL = "https://bot.rubika.ir/v1/bot"

DATA_FILE = "data.json"


# ====== LOAD MESSAGES ======
def load_messages():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)["messages"]
    except:
        return []


# ====== SEND MESSAGE ======
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, json=payload, headers=headers)


# ====== GET UPDATES ======
def get_updates():
    url = f"{BASE_URL}/getUpdates"

    headers = {
        "Authorization": f"Bot {TOKEN}"
    }

    return requests.get(url, headers=headers).json()


# ====== HANDLE USER ======
def handle_message(chat_id, text):
    messages = load_messages()

    if text == "/start":
        if not messages:
            send_message(chat_id, "No news yet ❌")
        else:
            send_message(chat_id, "\n\n".join(messages[-5:]))

    else:
        send_message(chat_id, "Send /start to see latest news")


# ====== MAIN LOOP ======
def main():
    print("Bot started...")

    while True:
        data = get_updates()

        for item in data.get("result", []):
            msg = item.get("message", {})

            chat = msg.get("chat", {})
            chat_id = chat.get("id")

            text = msg.get("text")

            if chat_id and text:
                handle_message(chat_id, text)


if __name__ == "__main__":
    main()
