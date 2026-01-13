"""
Telegram API functions for Second Brain Bot.
"""

import os
import tempfile

import requests
from PyPDF2 import PdfReader

from config import (
    CAPTURE_BOT_TOKEN,
    DIGEST_BOT_TOKEN,
    CHAT_ID,
    logger
)


def send_telegram_message(text, bot_token, parse_mode="Markdown"):
    """Send a message via Telegram using specified bot."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return None


def send_capture_message(text):
    """Send message via Capture Bot (confirmations)."""
    return send_telegram_message(text, CAPTURE_BOT_TOKEN)


def send_digest_message(text):
    """Send message via Digest Bot (summaries)."""
    return send_telegram_message(text, DIGEST_BOT_TOKEN)


def get_telegram_updates(offset=None):
    """Get new messages from Capture Bot."""
    url = f"https://api.telegram.org/bot{CAPTURE_BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return None


def download_telegram_file(file_id):
    """Download a file from Telegram and return its content."""
    try:
        # Get file path
        url = f"https://api.telegram.org/bot{CAPTURE_BOT_TOKEN}/getFile"
        response = requests.get(url, params={"file_id": file_id}, timeout=10)
        file_info = response.json()

        if not file_info.get("ok"):
            logger.error(f"Failed to get file info: {file_info}")
            return None

        file_path = file_info["result"]["file_path"]

        # Download file
        download_url = f"https://api.telegram.org/file/bot{CAPTURE_BOT_TOKEN}/{file_path}"
        response = requests.get(download_url, timeout=60)

        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"Failed to download file: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return None


def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file.flush()

            reader = PdfReader(tmp_file.name)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

            # Clean up
            os.unlink(tmp_file.name)

            return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return None
