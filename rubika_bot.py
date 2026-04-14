import json
from rubpy import Bot

TOKEN = "BBBBIG0GRMCCYTXKBTZXPURGJPZEMFGHCGUKGRNYDFHTQXTPCRJIENNLUBISCZOC"
TARGET = "@Ali2gi877"

bot = Bot(token=TOKEN)

def read_data():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = read_data()
message = data.get("message", "")

if message:
    bot.send_message(TARGET, message)
    print("Message sent!")
else:
    print("No message found")
