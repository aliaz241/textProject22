import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

CONFIG_FILE = "config.json"
DATA_FILE = "data.json"


# ================= LOAD CONFIG =================
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


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

        # متن
        text_el = post.find("div", class_="tgme_widget_message_text")
        text = text_el.get_text(" ", strip=True) if text_el else ""

        # عکس
        img_el = post.find("img")
        image = img_el["src"] if img_el else None

        # زمان
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

    all_messages = []

    for ch in config["channels"]:
        posts = get_last_posts(ch)
        all_messages.extend(posts)

    save_data(all_messages)

    print(f"✅ Saved {len(all_messages)} messages")


if __name__ == "__main__":
    main()
