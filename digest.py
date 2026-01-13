"""
Daily and weekly digest functions for Second Brain Bot.
"""

from config import logger
from telegram import send_digest_message
from claude_ai import generate_summary, DAILY_PROMPT, WEEKLY_PROMPT
from notion import (
    get_notion_entries,
    format_entries_for_summary,
    format_entries_with_links,
    create_daily_dashboard
)


def send_daily_digest():
    """Send daily digest via Digest Bot."""
    logger.info("Generating daily digest...")
    entries = get_notion_entries(days=1)

    if not entries:
        send_digest_message("*Good Morning!*\n\nNo new entries in the last 24 hours.")
        return

    entries_text = format_entries_for_summary(entries)
    summary = generate_summary(entries_text, DAILY_PROMPT)

    if not summary:
        send_digest_message("*Good Morning!*\n\nCouldn't generate today's digest.")
        return

    # Create daily dashboard in Notion
    dashboard = create_daily_dashboard(entries, summary)
    dashboard_url = dashboard.get("url", "") if dashboard else ""

    # Build message with links to entries
    by_category = format_entries_with_links(entries)

    message = f"*Good Morning!*\n\n{summary}\n\n"
    message += "---\n*Quick Links:*\n"

    # Add top items with links
    for category in ["Tasks", "People", "Research", "Links"]:
        items = by_category.get(category, [])
        for item in items[:2]:  # Top 2 per category
            if item['url']:
                message += f"- [{item['title'][:30]}...]({item['url']})\n"

    # Add dashboard link
    if dashboard_url:
        message += f"\n[Open Daily Dashboard]({dashboard_url})"

    send_digest_message(message)
    logger.info("Daily digest sent via Digest Bot!")


def send_weekly_summary():
    """Send weekly summary via Digest Bot."""
    logger.info("Generating weekly summary...")
    entries = get_notion_entries(days=7)

    if not entries:
        send_digest_message("*Weekly Review*\n\nNo entries this week.")
        return

    entries_text = format_entries_for_summary(entries)
    summary = generate_summary(entries_text, WEEKLY_PROMPT)

    if not summary:
        send_digest_message("*Weekly Review*\n\nCouldn't generate this week's summary.")
        return

    # Stats
    by_category = format_entries_with_links(entries)
    total = len(entries)
    high_priority = sum(1 for e in entries if e.get("properties", {}).get("Priority", {}).get("select", {}).get("name") == "High")

    message = f"*Weekly Review*\n\n{summary}\n\n"
    message += "---\n"
    message += f"*Stats:* {total} entries | {high_priority} high priority\n"
    message += f"- Tasks: {len(by_category.get('Tasks', []))}\n"
    message += f"- People: {len(by_category.get('People', []))}\n"
    message += f"- Research: {len(by_category.get('Research', []))}\n"
    message += f"- Links: {len(by_category.get('Links', []))}"

    send_digest_message(message)
    logger.info("Weekly summary sent via Digest Bot!")
