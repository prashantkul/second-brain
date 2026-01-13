"""
Test Harness for Second Brain Bot

Allows Claude Code to test bot functionality without using the main bot.
Uses a dedicated test bot for sending/receiving messages.

Usage:
    python test_harness.py send "t: Test task"
    python test_harness.py test-agent "What is 2+2?"
    python test_harness.py test-jobs "https://job-url"
    python test_harness.py test-deep "https://arxiv.org/abs/..."
    python test_harness.py test-reminder "t: Call John in 2 hours"
    python test_harness.py parse-date "by Friday 3pm"
    python test_harness.py show-reminders
    python test_harness.py check-response
"""

import os
import sys
import asyncio
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Test bot configuration
TEST_BOT_TOKEN = os.environ.get("TELEGRAM_TEST_BOT_TOKEN")
TEST_CHAT_ID = os.environ.get("TEST_CHAT_ID")

# Track last update for response checking
LAST_UPDATE_FILE = Path("/tmp/test_harness_last_update.txt")


def send_message(text: str) -> dict:
    """Send a message via the test bot."""
    url = f"https://api.telegram.org/bot{TEST_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TEST_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        if result.get("ok"):
            print(f"✓ Sent: {text[:50]}...")
            return result
        else:
            print(f"✗ Error: {result.get('description')}")
            return result
    except Exception as e:
        print(f"✗ Failed to send: {e}")
        return {"ok": False, "error": str(e)}


def get_updates(offset=None) -> list:
    """Get updates from the test bot."""
    url = f"https://api.telegram.org/bot{TEST_BOT_TOKEN}/getUpdates"
    params = {"timeout": 5}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        if result.get("ok"):
            return result.get("result", [])
        return []
    except Exception as e:
        print(f"Error getting updates: {e}")
        return []


def get_last_update_id() -> int:
    """Get the last processed update ID."""
    if LAST_UPDATE_FILE.exists():
        return int(LAST_UPDATE_FILE.read_text().strip())
    return 0


def save_last_update_id(update_id: int):
    """Save the last processed update ID."""
    LAST_UPDATE_FILE.write_text(str(update_id))


def check_responses() -> list:
    """Check for new responses from the bot."""
    last_id = get_last_update_id()
    updates = get_updates(offset=last_id + 1 if last_id else None)

    responses = []
    for update in updates:
        update_id = update.get("update_id", 0)
        message = update.get("message", {})
        text = message.get("text", "")

        if text:
            responses.append({
                "update_id": update_id,
                "text": text,
                "from": message.get("from", {}).get("first_name", "Unknown")
            })

        # Update last seen
        if update_id > last_id:
            last_id = update_id

    if last_id:
        save_last_update_id(last_id)

    return responses


async def test_agent_directly(message: str) -> str:
    """Test the agent processing directly without Telegram."""
    # Import from agent_bot
    sys.path.insert(0, str(Path(__file__).parent))
    from agent_bot import process_with_agent

    print(f"Testing agent with: {message[:50]}...")
    print("-" * 50)

    response = await process_with_agent(message)

    print("Response:")
    print(response)
    print("-" * 50)

    return response


async def test_jobs(url_or_text: str) -> str:
    """Test job analysis feature."""
    message = f"j: {url_or_text}"
    return await test_agent_directly(message)


async def test_deep(url: str) -> str:
    """Test deep analysis feature."""
    message = f"d: {url}"
    return await test_agent_directly(message)


async def test_reminder(message: str) -> str:
    """Test task with due date."""
    if not message.lower().startswith("t:"):
        message = f"t: {message}"
    return await test_agent_directly(message)


def parse_date_test(text: str):
    """Test date parsing without saving."""
    sys.path.insert(0, str(Path(__file__).parent))
    from reminders import parse_due_date, format_due_date

    print(f"Input: '{text}'")
    print("-" * 40)

    due_date, clean_text = parse_due_date(text)

    if due_date:
        print(f"✓ Due date: {due_date}")
        print(f"  Formatted: {format_due_date(due_date)}")
        print(f"  Clean text: '{clean_text}'")
    else:
        print("✗ No date found")
        print(f"  Original text: '{clean_text}'")


def show_reminders():
    """Show upcoming tasks with due dates."""
    sys.path.insert(0, str(Path(__file__).parent))
    from reminders import get_upcoming_tasks_formatted, get_tasks_due_soon

    # Show formatted output
    print(get_upcoming_tasks_formatted())
    print()

    # Show raw data
    tasks = get_tasks_due_soon(hours=168)  # Next 7 days
    if tasks:
        print("-" * 40)
        print(f"Raw data ({len(tasks)} tasks):")
        for task in tasks:
            print(f"  • {task['title']}")
            print(f"    Due: {task['due_date']}")
            print(f"    ID: {task['id'][:8]}...")


async def cleanup_notion(hours: int = 1) -> int:
    """Delete test entries from Notion created in the last N hours."""
    sys.path.insert(0, str(Path(__file__).parent))
    from tools import get_recent_page_ids, _notion_headers
    import requests

    page_ids = await get_recent_page_ids(hours)

    if not page_ids:
        print("No recent entries to clean up.")
        return 0

    print(f"Found {len(page_ids)} entries to delete...")

    deleted = 0
    for page_id in page_ids:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"archived": True}
        try:
            response = requests.patch(url, headers=_notion_headers(), json=payload, timeout=10)
            if response.status_code == 200:
                deleted += 1
                print(f"  ✓ Deleted {page_id[:8]}...")
            else:
                print(f"  ✗ Failed {page_id[:8]}: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error {page_id[:8]}: {e}")

    print(f"\nCleanup complete: {deleted}/{len(page_ids)} entries deleted")
    return deleted


def print_help():
    """Print usage help."""
    print("""
Second Brain Test Harness

Commands:
  send <message>          Send a message via test bot
  check-response          Check for new responses
  test-agent <message>    Test agent processing directly
  test-jobs <url/text>    Test job analysis (j: prefix)
  test-deep <url>         Test deep analysis (d: prefix)
  test-reminder <task>    Test task with due date (t: prefix)
  parse-date <text>       Test date parsing without saving
  show-reminders          Show upcoming tasks with due dates
  cleanup [hours]         Delete test entries from Notion (default: 1 hour)

Examples:
  python test_harness.py send "t: Test task for Friday"
  python test_harness.py test-agent "? What tasks do I have?"
  python test_harness.py test-jobs "https://lever.co/job/..."
  python test_harness.py test-deep "https://arxiv.org/abs/2403.05181"
  python test_harness.py test-reminder "Call John in 2 hours"
  python test_harness.py parse-date "by Friday 3pm"
  python test_harness.py show-reminders
  python test_harness.py check-response
  python test_harness.py cleanup 2
""")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "send" and len(sys.argv) > 2:
        message = " ".join(sys.argv[2:])
        send_message(message)

    elif command == "check-response":
        responses = check_responses()
        if responses:
            print(f"Found {len(responses)} new message(s):\n")
            for r in responses:
                print(f"From: {r['from']}")
                print(f"Text: {r['text'][:500]}")
                print("-" * 30)
        else:
            print("No new responses.")

    elif command == "test-agent" and len(sys.argv) > 2:
        message = " ".join(sys.argv[2:])
        asyncio.run(test_agent_directly(message))

    elif command == "test-jobs" and len(sys.argv) > 2:
        url_or_text = " ".join(sys.argv[2:])
        asyncio.run(test_jobs(url_or_text))

    elif command == "test-deep" and len(sys.argv) > 2:
        url = sys.argv[2]
        asyncio.run(test_deep(url))

    elif command == "test-reminder" and len(sys.argv) > 2:
        message = " ".join(sys.argv[2:])
        asyncio.run(test_reminder(message))

    elif command == "parse-date" and len(sys.argv) > 2:
        text = " ".join(sys.argv[2:])
        parse_date_test(text)

    elif command == "show-reminders":
        show_reminders()

    elif command == "cleanup":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        asyncio.run(cleanup_notion(hours))

    elif command in ["help", "-h", "--help"]:
        print_help()

    else:
        print(f"Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
