"""Test Telegram bot by sending a message."""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_CODE")
CHAT_ID = os.environ.get("CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

if __name__ == "__main__":
    message = """*Second Brain Test*

Your Telegram integration is working!

This is where you'll receive:
- Daily morning briefings
- Task reminders
- Important follow-ups
"""

    result = send_message(message)

    if result.get("ok"):
        print("Message sent successfully!")
    else:
        print(f"Error: {result}")
