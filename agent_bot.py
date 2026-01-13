"""
Second Brain Telegram Bot - Agent SDK Version

Uses Claude Agent SDK with custom MCP tools for Notion integration.
Skills-based architecture for intelligent message processing.

Usage:
    python agent_bot.py
"""

import os
import asyncio
import logging
from pathlib import Path

import requests
import schedule
import time
import threading
from dotenv import load_dotenv

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

from tools import create_second_brain_server

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_CODE")
DIGEST_BOT_TOKEN = os.environ.get("TELEGRAM_DIGEST_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("second_brain_agent")

# Track last processed message
last_update_id = 0

# Create MCP server
mcp_server = create_second_brain_server()

# System prompt for the agent
SYSTEM_PROMPT = """You are a Second Brain assistant integrated with Telegram and Notion.

Your capabilities:
1. **Categorize messages** into Tasks, People, Research, or Links
2. **Analyze URLs and documents** - fetch content, extract insights
3. **Save to Notion** - store entries with proper categorization
4. **Search knowledge base** - query saved entries
5. **Generate digests** - daily and weekly summaries

Quick Prefixes:
- t: or task: → Tasks
- p: or person: → People
- r: or research: → Research
- l: or link: → Links
- d: or deep: → Deep paper analysis
- ! → High priority
- ? → Query knowledge base

Always:
- Be concise (Telegram limit)
- Use markdown formatting
- Confirm saves with Notion URL
- Extract key insights from content

When analyzing URLs/documents:
- Provide summary, key insights, actionable takeaways
- Estimate reading time
- Assign appropriate priority and tags
"""


def send_telegram_message(text, bot_token):
    """Send a message via Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # Split long messages
    max_len = 4000
    chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]

    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Error sending message: {e}")


def send_capture_message(text):
    """Send via Capture Bot."""
    send_telegram_message(text, TELEGRAM_BOT_TOKEN)


def send_digest_message(text):
    """Send via Digest Bot."""
    send_telegram_message(text, DIGEST_BOT_TOKEN)


def get_telegram_updates(offset=None):
    """Get new messages from Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return None


async def process_with_agent(message_text: str, context: str = "") -> str:
    """Process a message using Claude Agent SDK."""

    # Build the prompt with context
    prompt = message_text
    if context:
        prompt = f"{context}\n\nUser message: {message_text}"

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"second-brain": mcp_server},
        allowed_tools=[
            "mcp__second-brain__save_to_notion",
            "mcp__second-brain__save_document_to_notion",
            "mcp__second-brain__search_notion",
            "mcp__second-brain__get_recent_entries",
            "mcp__second-brain__send_telegram_message",
            "WebFetch",  # Built-in URL fetching
        ],
        max_turns=10,
        cwd=str(Path(__file__).parent),
    )

    response_text = ""

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
    except Exception as e:
        logger.error(f"Agent error: {e}")
        response_text = f"Error processing message: {str(e)}"

    return response_text


async def handle_message(message_text: str):
    """Handle an incoming Telegram message."""
    logger.info(f"Processing: {message_text[:50]}...")

    # Handle commands
    if message_text.startswith("/"):
        cmd = message_text.lower().strip().split()[0]

        if cmd == "/help":
            help_text = """*Second Brain Agent Bot*

*Prefixes:*
`t:` Task | `p:` Person | `r:` Research | `l:` Link
`d:` Deep analysis | `!` High priority | `?` Query

*Commands:*
`/daily` - Today's digest
`/weekly` - Weekly summary
`/help` - This message

*Features:*
- Send URLs → Auto-analyze
- Send PDFs → Extract & summarize
- Ask questions about your knowledge

*Examples:*
`t: Review proposal by Friday`
`d: https://arxiv.org/abs/...`
`? What do I know about AI?`
"""
            send_capture_message(help_text)
            return

        elif cmd in ["/daily", "/today"]:
            send_capture_message("Generating daily digest...")
            response = await process_with_agent(
                "Generate a daily digest of entries from the last 24 hours. "
                "Use get_recent_entries with days=1, then summarize by category."
            )
            send_digest_message(response)
            return

        elif cmd in ["/weekly", "/week"]:
            send_capture_message("Generating weekly summary...")
            response = await process_with_agent(
                "Generate a weekly summary of entries from the last 7 days. "
                "Use get_recent_entries with days=7, then provide insights and recommendations."
            )
            send_digest_message(response)
            return

        elif cmd == "/start":
            send_capture_message(
                "*Welcome to Second Brain Agent!*\n\n"
                "Send me anything to save it to your knowledge base.\n"
                "Type /help for more info."
            )
            return

    # Process with agent
    send_capture_message("Processing...")

    # Determine context based on prefix
    context = ""
    if message_text.startswith("?"):
        context = "The user is querying their knowledge base. Search Notion and synthesize an answer."
    elif message_text.lower().startswith(("d:", "deep:")):
        context = "The user wants deep paper/document analysis. Provide comprehensive academic and practical breakdown."
    elif "http" in message_text:
        context = "The user shared a URL. Fetch the content, analyze it, and save to Notion with proper categorization."

    response = await process_with_agent(message_text, context)

    # Send response (agent may have already sent via tool)
    if response and not response.startswith("Message sent"):
        send_capture_message(response)


def run_scheduler():
    """Run scheduled tasks."""
    while True:
        schedule.run_pending()
        time.sleep(60)


async def main_loop():
    """Main async bot loop."""
    global last_update_id

    logger.info("=" * 50)
    logger.info("Second Brain Agent Bot Starting...")
    logger.info("=" * 50)

    # Setup scheduled digests
    def sync_daily():
        asyncio.run(process_with_agent(
            "Generate daily digest for the last 24 hours and send via Telegram."
        ))

    def sync_weekly():
        asyncio.run(process_with_agent(
            "Generate weekly summary for the last 7 days and send via Telegram."
        ))

    schedule.every().day.at("08:00").do(sync_daily)
    schedule.every().sunday.at("18:00").do(sync_weekly)

    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Startup messages
    send_capture_message("*Agent Bot is online!*\n\nPowered by Claude Agent SDK.\nType /help for commands.")

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Main polling loop
    while True:
        try:
            updates = get_telegram_updates(
                offset=last_update_id + 1 if last_update_id else None
            )

            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    last_update_id = update["update_id"]

                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))

                    if chat_id == CHAT_ID:
                        # Handle document
                        document = message.get("document")
                        if document:
                            file_name = document.get("file_name", "unknown")
                            caption = message.get("caption", "")
                            await handle_message(
                                f"Analyze this document: {file_name}. Caption: {caption}"
                            )
                            continue

                        # Handle text
                        text = message.get("text", "")
                        if text:
                            await handle_message(text)

        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            send_capture_message("_Agent Bot is offline._")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)


def main():
    """Entry point."""
    # Validate config
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_CODE")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if not os.environ.get("NOTION_TOKEN"):
        missing.append("NOTION_TOKEN")
    if not os.environ.get("NOTION_DATABASE_ID"):
        missing.append("NOTION_DATABASE_ID")

    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        return

    asyncio.run(main_loop())


if __name__ == "__main__":
    main()
