"""
Custom MCP Tools for Second Brain Agent.
Provides Notion integration and Telegram messaging.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Any

import requests
from dotenv import load_dotenv
from claude_agent_sdk import tool, create_sdk_mcp_server

# Load environment
load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_CODE")
CHAT_ID = os.environ.get("CHAT_ID")


def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


# =============================================================================
# Notion Tools
# =============================================================================

@tool(
    "save_to_notion",
    "Save a QUICK entry to Notion. For simple saves only - NOT for deep paper analysis (use save_deep_analysis for that)",
    {
        "title": str,
        "category": str,  # People, Research, Links, Tasks
        "description": str,
        "priority": str,  # High, Medium, Low
        "tags": str,  # Comma-separated tags like "AI, machine learning, NLP"
        "source_url": str,
    }
)
async def save_to_notion(args: dict[str, Any]) -> dict[str, Any]:
    """Save a new entry to Notion."""
    import logging
    logger = logging.getLogger("second_brain_agent")
    logger.info(f"save_to_notion called (NOT deep analysis) with title: {args.get('title', 'N/A')}")

    url = "https://api.notion.com/v1/pages"

    properties = {
        "Name": {"title": [{"text": {"content": args.get("title", "Untitled")}}]},
        "Category": {"select": {"name": args.get("category", "Research")}},
        "Description": {"rich_text": [{"text": {"content": args.get("description", "")[:2000]}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": args.get("priority", "Medium")}},
    }

    # Handle tags - can be string or list
    tags = args.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if tags:
        properties["Tags"] = {"multi_select": [{"name": tag[:50]} for tag in tags[:5]]}

    if args.get("source_url"):
        properties["Source"] = {"url": args["source_url"]}

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }

    try:
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return {
                "content": [{
                    "type": "text",
                    "text": f"Saved to Notion: {args['title']}\nURL: {result.get('url', 'N/A')}"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error saving to Notion: {response.status_code} - {response.text[:200]}"
                }]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
        }


@tool(
    "save_deep_analysis",
    "REQUIRED for d: prefix deep analysis. Saves comprehensive paper analysis with structured sections to Notion page body",
    {
        "title": str,
        "authors": str,
        "paper_type": str,
        "problem": str,
        "methodology": str,
        "key_contributions": list,
        "results": str,
        "limitations": list,
        "tldr": str,
        "why_it_matters": str,
        "implementation_complexity": str,
        "use_cases": list,
        "reading_time": str,
        "prerequisites": str,
        "priority": str,
        "tags": str,
        "source_url": str,
        "questions_to_explore": list,
    }
)
async def save_deep_analysis(args: dict[str, Any]) -> dict[str, Any]:
    """Save deep document analysis with full structured content."""
    import logging
    logger = logging.getLogger("second_brain_agent")
    logger.info(f"save_deep_analysis called with title: {args.get('title', 'N/A')}")

    url = "https://api.notion.com/v1/pages"

    # Build description from TL;DR and problem
    description = f"{args.get('tldr', '')} | Problem: {args.get('problem', '')}"[:2000]

    properties = {
        "Name": {"title": [{"text": {"content": args.get("title", "Untitled")}}]},
        "Category": {"select": {"name": "Research"}},
        "Description": {"rich_text": [{"text": {"content": description}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": args.get("priority", "Medium")}},
    }

    # Handle tags - can be string or list
    tags = args.get("tags", [])
    if isinstance(tags, str):
        # Split by comma and clean up
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if tags:
        properties["Tags"] = {"multi_select": [{"name": tag[:50]} for tag in tags[:5]]}

    if args.get("source_url"):
        properties["Source"] = {"url": args["source_url"]}

    # Build rich page content
    children = []

    def add_heading(text):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
        })

    def strip_markdown(text):
        """Remove markdown formatting from text."""
        import re
        if not text:
            return text
        text = str(text)
        # Remove bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        # Remove italic: *text* or _text_
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
        # Remove code: `text`
        text = re.sub(r'`(.+?)`', r'\1', text)
        return text.strip()

    def add_paragraph(text):
        if text:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": strip_markdown(text)[:2000]}}]}
            })

    def add_bullet(text):
        if text:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": strip_markdown(text)[:2000]}}]}
            })

    def add_divider():
        children.append({"object": "block", "type": "divider", "divider": {}})

    # TL;DR at top
    add_heading("TL;DR")
    add_paragraph(args.get("tldr", ""))

    add_divider()

    # Meta info
    add_heading("Meta")
    add_paragraph(f"Authors: {args.get('authors', 'Unknown')}")
    add_paragraph(f"Type: {args.get('paper_type', 'Research paper')}")
    add_paragraph(f"Reading Time: {args.get('reading_time', 'N/A')}")
    add_paragraph(f"Prerequisites: {args.get('prerequisites', 'N/A')}")

    add_divider()

    # Academic Analysis
    add_heading("Academic Analysis")

    # Problem with bold label
    if args.get('problem'):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "Problem: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": str(args.get('problem', ''))[:1900]}}
            ]}
        })

    # Methodology with bold label
    if args.get('methodology'):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "Methodology: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": str(args.get('methodology', ''))[:1900]}}
            ]}
        })

    # Helper to parse list items from various formats
    def parse_list_items(items):
        import re
        if isinstance(items, list):
            return items
        if isinstance(items, str):
            # Try newline split first
            if "\n" in items:
                return [i.strip() for i in items.split("\n") if i.strip()]
            # Try numbered format: "1) item 2) item" or "1. item 2. item"
            numbered = re.split(r'\d+[\)\.]\s*', items)
            numbered = [i.strip() for i in numbered if i.strip()]
            if len(numbered) > 1:
                return numbered
            # Try bullet format: "• item • item" or "- item - item"
            bulleted = re.split(r'[•\-]\s*', items)
            bulleted = [i.strip() for i in bulleted if i.strip()]
            if len(bulleted) > 1:
                return bulleted
            # Return as single item if no pattern matched
            return [items.strip()] if items.strip() else []
        return []

    # Handle key_contributions - can be string or list in various formats
    key_contributions = parse_list_items(args.get("key_contributions", []))
    if key_contributions:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Key Contributions:"}, "annotations": {"bold": True}}]}
        })
        for item in key_contributions[:7]:  # Limit to 7
            add_bullet(item)

    # Results with bold label
    if args.get('results'):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "Results: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": str(args.get('results', ''))[:1900]}}
            ]}
        })

    # Handle limitations - can be string or list in various formats
    limitations = parse_list_items(args.get("limitations", []))
    if limitations:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Limitations:"}, "annotations": {"bold": True}}]}
        })
        for item in limitations[:5]:  # Limit to 5
            add_bullet(item)

    add_divider()

    # Practical Analysis
    add_heading("Practical Analysis")
    # Why It Matters with bold label
    if args.get('why_it_matters'):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "Why It Matters: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": str(args.get('why_it_matters', ''))[:1900]}}
            ]}
        })

    # Implementation Complexity with bold label
    if args.get('implementation_complexity'):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [
                {"type": "text", "text": {"content": "Implementation: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": str(args.get('implementation_complexity', ''))[:1900]}}
            ]}
        })

    # Handle use_cases - can be string or list in various formats
    use_cases = parse_list_items(args.get("use_cases", []))
    if use_cases:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Use Cases:"}, "annotations": {"bold": True}}]}
        })
        for item in use_cases[:6]:  # Limit to 6
            add_bullet(item)

    add_divider()

    # Handle questions_to_explore - can be string or list in various formats
    questions = parse_list_items(args.get("questions_to_explore", []))
    if questions:
        add_heading("Questions to Explore")
        for q in questions[:6]:  # Limit to 6
            add_bullet(q)

    # Safety check: Notion allows max 100 children blocks
    if len(children) > 100:
        logger.warning(f"Truncating children from {len(children)} to 100 blocks")
        children = children[:100]

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children": children
    }

    try:
        logger.info(f"Sending to Notion with {len(children)} children blocks")
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=30)
        logger.info(f"Notion response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            return {
                "content": [{
                    "type": "text",
                    "text": f"Deep analysis saved to Notion: {args['title']}\nURL: {result.get('url', 'N/A')}"
                }]
            }
        else:
            error_text = response.text[:500]
            logger.error(f"Notion API error: {response.status_code} - {error_text}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error saving document: {response.status_code} - {error_text}"
                }]
            }
    except Exception as e:
        logger.error(f"Exception in save_deep_analysis: {str(e)}")
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
        }


@tool(
    "search_notion",
    "Search the Second Brain Notion database",
    {
        "query": str,
        "limit": int,
    }
)
async def search_notion(args: dict[str, Any]) -> dict[str, Any]:
    """Search Notion for entries."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    payload = {
        "page_size": args.get("limit", 20),
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }

    try:
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])

            entries = []
            for entry in results:
                props = entry.get("properties", {})
                title = ""
                if props.get("Name", {}).get("title"):
                    title = props["Name"]["title"][0]["text"]["content"]

                category = props.get("Category", {}).get("select", {}).get("name", "")
                description = ""
                if props.get("Description", {}).get("rich_text"):
                    description = props["Description"]["rich_text"][0]["text"]["content"][:200]

                entries.append({
                    "title": title,
                    "category": category,
                    "description": description,
                    "url": entry.get("url", "")
                })

            return {
                "content": [{
                    "type": "text",
                    "text": f"Found {len(entries)} entries:\n{json.dumps(entries, indent=2)}"
                }]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Search error: {response.status_code}"}]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
        }


@tool(
    "get_recent_entries",
    "Get entries from the last N days",
    {
        "days": int,
    }
)
async def get_recent_entries(args: dict[str, Any]) -> dict[str, Any]:
    """Get recent Notion entries for digests."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    since_date = (datetime.now() - timedelta(days=args.get("days", 1))).isoformat()

    payload = {
        "filter": {
            "timestamp": "created_time",
            "created_time": {"after": since_date}
        },
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }

    try:
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])

            by_category = {"Tasks": [], "People": [], "Research": [], "Links": []}

            for entry in results:
                props = entry.get("properties", {})
                title = ""
                if props.get("Name", {}).get("title"):
                    title = props["Name"]["title"][0]["text"]["content"]

                category = props.get("Category", {}).get("select", {}).get("name", "Research")
                priority = props.get("Priority", {}).get("select", {}).get("name", "")

                if category in by_category:
                    by_category[category].append({
                        "title": title,
                        "priority": priority,
                        "url": entry.get("url", "")
                    })

            return {
                "content": [{
                    "type": "text",
                    "text": f"Entries from last {args['days']} days:\n{json.dumps(by_category, indent=2)}"
                }]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Error: {response.status_code}"}]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
        }


# =============================================================================
# Telegram Tools
# =============================================================================

@tool(
    "send_telegram_message",
    "Send a message to the user via Telegram",
    {
        "text": str,
    }
)
async def send_telegram_message(args: dict[str, Any]) -> dict[str, Any]:
    """Send a Telegram message."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": args["text"],
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return {
                "content": [{"type": "text", "text": "Message sent successfully"}]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Send error: {response.status_code}"}]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}]
        }


# =============================================================================
# Cleanup Tools (for testing)
# =============================================================================

@tool(
    "delete_notion_entries",
    "Delete (archive) Notion entries by their page IDs. Used for test cleanup.",
    {
        "page_ids": str,  # Comma-separated page IDs
    }
)
async def delete_notion_entries(args: dict[str, Any]) -> dict[str, Any]:
    """Archive/delete Notion pages by ID."""
    import logging
    logger = logging.getLogger("second_brain_agent")

    page_ids = args.get("page_ids", "")
    if isinstance(page_ids, str):
        page_ids = [p.strip() for p in page_ids.split(",") if p.strip()]

    deleted = []
    failed = []

    for page_id in page_ids:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"archived": True}

        try:
            response = requests.patch(url, headers=_notion_headers(), json=payload, timeout=10)
            if response.status_code == 200:
                deleted.append(page_id)
                logger.info(f"Deleted Notion page: {page_id}")
            else:
                failed.append(page_id)
                logger.error(f"Failed to delete {page_id}: {response.status_code}")
        except Exception as e:
            failed.append(page_id)
            logger.error(f"Error deleting {page_id}: {e}")

    return {
        "content": [{
            "type": "text",
            "text": f"Deleted {len(deleted)} entries. Failed: {len(failed)}"
        }]
    }


async def get_recent_page_ids(hours: int = 1) -> list[str]:
    """Get page IDs of entries created in the last N hours. For test cleanup."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    since_date = (datetime.now() - timedelta(hours=hours)).isoformat()

    payload = {
        "filter": {
            "timestamp": "created_time",
            "created_time": {"after": since_date}
        },
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }

    try:
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            results = response.json().get("results", [])
            return [entry["id"] for entry in results]
    except Exception:
        pass
    return []


# =============================================================================
# Create MCP Server
# =============================================================================

def create_second_brain_server():
    """Create the Second Brain MCP server with all tools."""
    return create_sdk_mcp_server(
        name="second-brain",
        version="1.0.0",
        tools=[
            save_to_notion,
            save_deep_analysis,
            search_notion,
            get_recent_entries,
            send_telegram_message,
            delete_notion_entries,
        ]
    )
