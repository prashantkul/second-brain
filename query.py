"""
Knowledge base query functions for Second Brain Bot.
"""

import json

from config import logger
from telegram import send_capture_message
from claude_ai import query_with_claude
from notion import search_notion_entries, format_entries_for_query


def query_knowledge_base(query):
    """Query the knowledge base and return an AI-synthesized answer."""
    logger.info(f"Querying knowledge base: {query}")

    # Fetch recent entries
    entries = search_notion_entries(query, limit=30)

    if not entries:
        return None, []

    # Format entries for context
    formatted = format_entries_for_query(entries)
    entries_text = json.dumps(formatted, indent=2)

    # Query with Claude
    answer = query_with_claude(query, entries_text)

    if not answer:
        return None, []

    # Find relevant entries to link
    relevant_entries = [e for e in formatted if e["title"].lower() in answer.lower()][:3]

    return answer, relevant_entries


def process_query(query_text):
    """Process a knowledge base query and send response."""
    send_capture_message(f"Searching your Second Brain...\n\n_{query_text}_")

    answer, relevant_entries = query_knowledge_base(query_text)

    if not answer:
        send_capture_message("Couldn't search your knowledge base. Please try again.")
        return

    response = f"*From Your Second Brain*\n\n{answer}"

    # Add links to relevant entries if found
    if relevant_entries:
        response += "\n\n*Related entries:*\n"
        for entry in relevant_entries:
            if entry.get("url"):
                response += f"- [{entry['title'][:30]}...]({entry['url']})\n"

    send_capture_message(response)
