from bot import fetch_messages
from rubika import send_to_rubika

def main():
    messages = fetch_messages()

    for m in messages:
        send_to_rubika(m)

if __name__ == "__main__":
    main()
