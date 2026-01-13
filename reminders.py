"""
Task Reminders for Second Brain

Handles:
- Natural language date parsing
- Reminder scheduling and sending
- Notion due date queries
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path

import dateparser
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_CODE")
CHAT_ID = os.environ.get("CHAT_ID")

# File to track sent reminders (prevents duplicates)
REMINDER_TRACKING_FILE = Path("/tmp/second_brain_reminders.json")

# Reminder intervals (minutes before due time)
REMINDER_INTERVALS = [
    1440,  # 1 day before
    60,    # 1 hour before
    0,     # At due time
]


def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


def parse_due_date(text: str) -> Tuple[Optional[datetime], str]:
    """
    Extract due date from task text using natural language.
    Returns (parsed_datetime, cleaned_text).

    Examples:
    - "Review proposal by Friday 3pm" → (datetime, "Review proposal")
    - "Call John in 2 hours" → (datetime, "Call John")
    - "Submit report tomorrow morning" → (datetime, "Submit report")
    """
    import re

    if not text:
        return None, text

    # dateparser settings
    settings = {
        'PREFER_DATES_FROM': 'future',
        'RETURN_AS_TIMEZONE_AWARE': False,
        'RELATIVE_BASE': datetime.now(),
    }

    # Patterns to extract date/time expressions
    # Each tuple is (pattern, group_index for date_str)
    patterns = [
        # "by Friday 3pm", "by Jan 20", "by next Monday" - capture just the date part
        (r'\bby\s+(.+)$', 1),
        # "at 3pm", "at 5:30"
        (r'\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)$', 1),
        # "in 2 hours", "in 3 days"
        (r'\b(in\s+\d+\s+(?:hour|minute|day|week|month)s?)$', 1),
        # "tomorrow morning/afternoon/evening" (with time context)
        (r'\b(tomorrow\s+(?:morning|afternoon|evening|night))$', 1),
        # "tomorrow" alone
        (r'\b(tomorrow)$', 1),
        # "today at 5pm"
        (r'\b(today(?:\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)?)$', 1),
        # "next Monday", "next week"
        (r'\b(next\s+\w+(?:\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)?)$', 1),
    ]

    for pattern, group_idx in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(group_idx)

            # Try to parse the extracted date string
            parsed = dateparser.parse(date_str, settings=settings)

            if parsed:
                # Extract clean text (everything before the full match)
                clean_text = text[:match.start()].strip()

                # Remove trailing prepositions (may be multiple)
                while True:
                    trimmed = False
                    for prep in ['by', 'at', 'on', 'before', 'until', 'due']:
                        if clean_text.lower().endswith(f' {prep}'):
                            clean_text = clean_text[:-len(prep)-1].strip()
                            trimmed = True
                            break
                    if not trimmed:
                        break

                return parsed, clean_text

    # Fallback: try parsing the last few words
    words = text.split()
    for i in range(min(5, len(words)), 0, -1):
        candidate = ' '.join(words[-i:])

        # Replace time-of-day words with actual times
        time_replacements = {
            'morning': '9am',
            'afternoon': '2pm',
            'evening': '6pm',
            'night': '9pm',
        }
        parsed_candidate = candidate
        for time_word, time_val in time_replacements.items():
            if time_word in parsed_candidate.lower():
                parsed_candidate = re.sub(rf'\b{time_word}\b', time_val, parsed_candidate, flags=re.IGNORECASE)

        # Try the modified candidate first, then original
        parsed = dateparser.parse(parsed_candidate, settings=settings)
        if not parsed:
            parsed = dateparser.parse(candidate, settings=settings)

        # If parsing fails and candidate starts with "next", try without it
        # (dateparser handles "Monday" but not "next Monday" well)
        if not parsed and candidate.lower().startswith('next '):
            parsed = dateparser.parse(candidate[5:], settings=settings)

        if parsed:
            clean_text = ' '.join(words[:-i]).strip()
            # Remove trailing prepositions (may be multiple)
            while True:
                trimmed = False
                for prep in ['by', 'at', 'on', 'before', 'until', 'due', 'next']:
                    if clean_text.lower().endswith(f' {prep}'):
                        clean_text = clean_text[:-len(prep)-1].strip()
                        trimmed = True
                        break
                if not trimmed:
                    break
            return parsed, clean_text

    return None, text


def format_due_date(dt: datetime) -> str:
    """Format datetime for display in Telegram."""
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)

    if dt.date() == today:
        return f"Today {dt.strftime('%I:%M %p')}"
    elif dt.date() == tomorrow:
        return f"Tomorrow {dt.strftime('%I:%M %p')}"
    else:
        return dt.strftime('%a %b %d, %I:%M %p')


def get_tasks_due_soon(hours: int = 25) -> list:
    """
    Query Notion for tasks due within N hours.
    Returns list of tasks with title, due_date, url, id.
    """
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    now = datetime.now()
    future = now + timedelta(hours=hours)

    payload = {
        "filter": {
            "and": [
                {
                    "property": "Category",
                    "select": {"equals": "Tasks"}
                },
                {
                    "property": "Status",
                    "select": {"does_not_equal": "Done"}
                },
                {
                    "property": "Due Date",
                    "date": {"is_not_empty": True}
                },
                {
                    "property": "Due Date",
                    "date": {"on_or_before": future.isoformat()}
                }
            ]
        },
        "sorts": [{"property": "Due Date", "direction": "ascending"}]
    }

    try:
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=15)
        if response.status_code == 200:
            results = response.json().get("results", [])
            tasks = []

            for entry in results:
                props = entry.get("properties", {})

                # Extract title
                title = ""
                if props.get("Name", {}).get("title"):
                    title = props["Name"]["title"][0]["text"]["content"]

                # Extract due date
                due_date = None
                if props.get("Due Date", {}).get("date"):
                    due_str = props["Due Date"]["date"].get("start", "")
                    if due_str:
                        try:
                            due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                            due_date = due_date.replace(tzinfo=None)  # Make naive
                        except:
                            pass

                if title and due_date:
                    tasks.append({
                        "id": entry["id"],
                        "title": title,
                        "due_date": due_date,
                        "url": entry.get("url", "")
                    })

            return tasks
    except Exception as e:
        print(f"Error fetching tasks: {e}")

    return []


def load_sent_reminders() -> dict:
    """Load tracking of sent reminders."""
    if REMINDER_TRACKING_FILE.exists():
        try:
            return json.loads(REMINDER_TRACKING_FILE.read_text())
        except:
            pass
    return {}


def save_sent_reminders(data: dict):
    """Save tracking of sent reminders."""
    try:
        REMINDER_TRACKING_FILE.write_text(json.dumps(data))
    except Exception as e:
        print(f"Error saving reminder tracking: {e}")


def send_reminder(task_title: str, due_date: datetime, notion_url: str, reminder_type: str):
    """Send a reminder via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Format the reminder message
    time_str = due_date.strftime('%I:%M %p')

    if reminder_type == "1d":
        emoji = "📅"
        timing = "tomorrow"
    elif reminder_type == "1h":
        emoji = "⏰"
        timing = "in 1 hour"
    else:  # at due time
        emoji = "🔔"
        timing = "now"

    message = f"{emoji} *Task Reminder*\n\n"
    message += f"*{task_title}*\n"
    message += f"Due: {timing} ({time_str})\n\n"
    message += f"[Open in Notion]({notion_url})"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending reminder: {e}")
        return False


def check_and_send_reminders():
    """
    Main reminder check function.
    Called by scheduler every 15 minutes.
    """
    now = datetime.now()
    tasks = get_tasks_due_soon(hours=25)
    sent_reminders = load_sent_reminders()

    # Clean old entries (older than 2 days)
    cutoff = (now - timedelta(days=2)).isoformat()
    sent_reminders = {k: v for k, v in sent_reminders.items() if v.get("date", "") > cutoff}

    for task in tasks:
        task_id = task["id"]
        due_date = task["due_date"]
        minutes_until_due = (due_date - now).total_seconds() / 60

        # Check each reminder interval
        for interval in REMINDER_INTERVALS:
            # Determine reminder type
            if interval == 1440:
                reminder_type = "1d"
                window_start = interval - 30  # 23.5 hours to 24 hours
                window_end = interval + 30
            elif interval == 60:
                reminder_type = "1h"
                window_start = interval - 15  # 45 min to 75 min
                window_end = interval + 15
            else:  # at due time
                reminder_type = "now"
                window_start = -15  # up to 15 min after due
                window_end = 15  # up to 15 min before due

            # Check if we're in the reminder window
            if window_start <= minutes_until_due <= window_end:
                reminder_key = f"{task_id}_{reminder_type}"

                # Check if already sent
                if reminder_key not in sent_reminders:
                    # Send the reminder
                    success = send_reminder(
                        task["title"],
                        due_date,
                        task["url"],
                        reminder_type
                    )

                    if success:
                        sent_reminders[reminder_key] = {
                            "date": now.isoformat(),
                            "task": task["title"]
                        }
                        print(f"Sent {reminder_type} reminder for: {task['title']}")

    # Save updated tracking
    save_sent_reminders(sent_reminders)


def get_upcoming_tasks_formatted() -> str:
    """
    Get formatted list of upcoming tasks for /reminders command.
    Groups by Today, Tomorrow, This Week.
    """
    tasks = get_tasks_due_soon(hours=168)  # Next 7 days

    if not tasks:
        return "No upcoming tasks with due dates."

    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)

    today_tasks = []
    tomorrow_tasks = []
    week_tasks = []

    for task in tasks:
        due = task["due_date"]
        time_str = due.strftime('%I:%M %p')

        if due.date() == today:
            today_tasks.append(f"• {task['title']} ({time_str})")
        elif due.date() == tomorrow:
            tomorrow_tasks.append(f"• {task['title']} ({time_str})")
        elif due.date() <= week_end:
            day_str = due.strftime('%a')
            week_tasks.append(f"• {task['title']} ({day_str} {time_str})")

    message = "*📋 Upcoming Tasks*\n\n"

    if today_tasks:
        message += "*Today:*\n" + "\n".join(today_tasks) + "\n\n"

    if tomorrow_tasks:
        message += "*Tomorrow:*\n" + "\n".join(tomorrow_tasks) + "\n\n"

    if week_tasks:
        message += "*This Week:*\n" + "\n".join(week_tasks) + "\n"

    if not (today_tasks or tomorrow_tasks or week_tasks):
        message = "No upcoming tasks with due dates in the next 7 days."

    return message.strip()


if __name__ == "__main__":
    # Test date parsing
    test_cases = [
        "Review proposal by Friday 3pm",
        "Call John in 2 hours",
        "Submit report tomorrow morning",
        "Fix bug by Jan 20",
        "Meeting at 5pm",
        "Finish slides by next Monday",
    ]

    print("Testing date parsing:\n")
    for text in test_cases:
        due, clean = parse_due_date(text)
        print(f"Input: '{text}'")
        print(f"  Due: {due}")
        print(f"  Clean: '{clean}'")
        print()
