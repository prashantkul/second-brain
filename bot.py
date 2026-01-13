"""
Second Brain Telegram Bot

Two-bot architecture:
- Capture Bot: Receives messages, categorizes with Claude, saves to Notion
- Digest Bot: Sends daily/weekly summaries

Usage:
    python bot.py
"""

import threading
import time

import schedule

from config import CHAT_ID, logger, validate_config
from telegram import (
    send_capture_message,
    send_digest_message,
    get_telegram_updates
)
from processors import (
    parse_prefixes,
    process_document,
    process_text_message,
    extract_urls,
    process_deep_analysis,
    process_deep_document,
    process_paper_question,
    is_deep_analysis_cache_valid,
    clear_deep_analysis_cache
)
from query import process_query
from digest import send_daily_digest, send_weekly_summary


# Track last processed message
last_update_id = 0


# =============================================================================
# Command Handling
# =============================================================================

def handle_command(command):
    """Handle bot commands."""
    cmd_parts = command.strip().split(maxsplit=1)
    cmd = cmd_parts[0].lower()
    args = cmd_parts[1] if len(cmd_parts) > 1 else ""

    if cmd == "/daily" or cmd == "/today":
        send_capture_message("Generating daily digest...")
        send_daily_digest()

    elif cmd == "/weekly" or cmd == "/week":
        send_capture_message("Generating weekly summary...")
        send_weekly_summary()

    elif cmd == "/deep":
        if not args:
            send_capture_message("*Deep Analysis*\n\nUsage: `/deep <url>`\n\nExample:\n`/deep https://arxiv.org/abs/2301.00001`")
            return
        urls = extract_urls(args)
        if urls:
            process_deep_analysis(urls[0])
        else:
            send_capture_message("Please provide a valid URL for deep analysis.")

    elif cmd == "/exit" or cmd == "/done":
        if is_deep_analysis_cache_valid():
            clear_deep_analysis_cache()
            send_capture_message("Exited paper Q&A mode.")
        else:
            send_capture_message("No active Q&A session to exit.")

    elif cmd == "/help":
        help_text = """*Second Brain Capture Bot*

*Quick Prefixes:*
`t:` Task - `t: Review proposal by Friday`
`p:` Person - `p: John, CTO at Acme`
`r:` Research - `r: Ideas about AI agents`
`l:` Link - `l: Check out example.com`
`d:` Deep analysis - `d: arxiv.org/abs/...`
`!` High priority - `!t: Urgent deadline`
`?` Ask brain - `? What do I know about AI?`

*Commands:*
`/deep <url>` - Deep paper analysis + Q&A
`/daily` - Today's digest + dashboard
`/weekly` - Weekly summary
`/exit` - Exit paper Q&A mode
`/help` - Show this message

*Features:*
- Send URLs -> Auto-analyze articles
- Send PDFs -> Extract & summarize
- Upload PDF with caption `d:` -> Deep analysis
- After deep analysis, ask follow-up questions!

*Examples:*
`d: https://arxiv.org/abs/2301.00001`
`!t: Submit report by EOD`
`? What papers have I saved about LLMs?`
"""
        send_capture_message(help_text)

    elif cmd == "/start":
        send_capture_message("*Welcome to Second Brain Capture Bot!*\n\nSend me any message to save it to your knowledge base.\n\nType /help for more info.")

    else:
        send_capture_message(f"Unknown command: {cmd}\n\nType /help for available commands.")


# =============================================================================
# Message Processing
# =============================================================================

def process_message(message_text):
    """Process an incoming message: route to appropriate handler."""
    logger.info(f"Processing message: {message_text[:50]}...")

    # Check for commands
    if message_text.startswith("/"):
        handle_command(message_text)
        return

    # Parse prefixes (t:, p:, r:, l:, d:, !, ?)
    clean_text, category_override, priority_override, is_query = parse_prefixes(message_text)

    # Query mode - ask your brain
    if is_query:
        process_query(clean_text)
        return

    # Deep analysis mode (d: prefix)
    if category_override == "DeepAnalysis":
        urls = extract_urls(clean_text)
        if urls:
            process_deep_analysis(urls[0])
        else:
            send_capture_message("Please provide a URL for deep analysis.\n\nExample: `d: https://arxiv.org/abs/2301.00001`")
        return

    # Check if we're in paper Q&A mode (auto-detect)
    # If no prefix was used and we have a valid cache, treat as paper question
    if is_deep_analysis_cache_valid() and not category_override and not priority_override:
        # Check if message looks like a question or follow-up
        # (not a URL, not very short)
        urls = extract_urls(message_text)
        if not urls and len(message_text.strip()) > 5:
            process_paper_question(message_text.strip())
            return

    # Regular message processing
    process_text_message(clean_text, category_override, priority_override)


# =============================================================================
# Scheduler
# =============================================================================

def run_scheduler():
    """Run the scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(60)


# =============================================================================
# Main Bot Loop
# =============================================================================

def main():
    """Main bot loop."""
    global last_update_id

    # Verify configuration
    if not validate_config():
        return

    logger.info("=" * 50)
    logger.info("Second Brain Bot Starting...")
    logger.info("=" * 50)
    logger.info("Capture Bot: For receiving and saving messages")
    logger.info("Digest Bot: For sending daily/weekly summaries")

    # Setup scheduled tasks
    schedule.every().day.at("08:00").do(send_daily_digest)
    schedule.every().sunday.at("18:00").do(send_weekly_summary)
    logger.info("Scheduled: Daily digest at 8:00 AM (via Digest Bot)")
    logger.info("Scheduled: Weekly summary on Sunday at 6:00 PM (via Digest Bot)")

    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Send startup messages
    send_capture_message("*Capture Bot is online!*\n\nSend me anything to save it.\nType /help for commands.")
    send_digest_message("*Digest Bot is online!*\n\nYou'll receive:\n- Daily briefings at 8:00 AM\n- Weekly summaries on Sunday at 6:00 PM")

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Main polling loop (only for Capture Bot)
    while True:
        try:
            updates = get_telegram_updates(offset=last_update_id + 1 if last_update_id else None)

            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    last_update_id = update["update_id"]

                    # Process only messages from our chat
                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))

                    if chat_id == CHAT_ID:
                        # Check for document upload
                        document = message.get("document")
                        if document:
                            file_id = document.get("file_id")
                            file_name = document.get("file_name", "unknown")
                            caption = message.get("caption", "").strip()

                            # Check if deep analysis requested via caption
                            caption_lower = caption.lower()
                            if caption_lower.startswith("/deep") or caption_lower.startswith("d:") or caption_lower.startswith("deep:"):
                                process_deep_document(file_id, file_name)
                            else:
                                process_document(file_id, file_name, caption)
                            continue

                        # Check for text message
                        text = message.get("text", "")
                        if text:
                            process_message(text)

        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            send_capture_message("_Capture Bot is offline._")
            send_digest_message("_Digest Bot is offline._")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
