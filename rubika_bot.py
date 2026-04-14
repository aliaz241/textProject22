import json

DATA_FILE = "data.json"


# ===== LOAD MESSAGES =====
def load_messages():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)["messages"]
    except:
        return []


# ===== SIMULATED START =====
def handle_start():
    messages = load_messages()

    if not messages:
        return "No messages yet"

    return "\n\n".join(messages)


# ===== RUN TEST =====
if __name__ == "__main__":
    print(handle_start())
