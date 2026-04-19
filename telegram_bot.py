import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

CONFIG_FILE = "config.json"
DATA_FILE = "data.json"


# ================= LOAD CONFIG =================
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ================= LOAD OLD DATA =================
def load_old_data():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("messages", [])
    except:
        return []


# ================= SAVE DATA =================
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"messages": data}, f, ensure_ascii=False, indent=2)


# ================= GET POSTS =================
def get_last_posts(channel):
    url = f"https://t.me/s/{channel}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    posts = soup.find_all("div", class_="tgme_widget_message")

    results = []

    for post in posts[-3:]:
        text_el = post.find("div", class_="tgme_widget_message_text")
        text = text_el.get_text(" ", strip=True) if text_el else ""

        img_el = post.find("img")
        image = img_el["src"] if img_el else None

        time_el = post.find("time")
        time = time_el["datetime"] if time_el else str(datetime.utcnow())

        results.append({
            "channel": channel,
            "text": text,
            "image": image,
            "time": time
        })

    return results


# ================= MAIN =================
def main():
    config = load_config()
    old_messages = load_old_data()    # ← قبلی‌ها را می‌خوانیم
    new_messages = []

    for ch in config["channels"]:
        posts = get_last_posts(ch)
        new_messages.extend(posts)

    # append
    all_messages = old_messages + new_messages
    save_data(all_messages)

    print("----- NEW MESSAGES -----")
    print(json.dumps(new_messages, indent=2, ensure_ascii=False))

    print(f"✅ Added {len(new_messages)} new messages (Total: {len(all_messages)})")


if __name__ == "__main__":
    main()
