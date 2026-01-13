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
    "Save an entry to the Second Brain Notion database",
    {
        "title": str,
        "category": str,  # People, Research, Links, Tasks
        "description": str,
        "priority": str,  # High, Medium, Low
        "tags": list,
        "source_url": str,
    }
)
async def save_to_notion(args: dict[str, Any]) -> dict[str, Any]:
    """Save a new entry to Notion."""
    url = "https://api.notion.com/v1/pages"

    properties = {
        "Name": {"title": [{"text": {"content": args.get("title", "Untitled")}}]},
        "Category": {"select": {"name": args.get("category", "Research")}},
        "Description": {"rich_text": [{"text": {"content": args.get("description", "")[:2000]}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": args.get("priority", "Medium")}},
    }

    if args.get("tags"):
        properties["Tags"] = {"multi_select": [{"name": tag} for tag in args["tags"][:5]]}

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
    "save_document_to_notion",
    "Save a document/paper analysis to Notion with rich content",
    {
        "title": str,
        "summary": str,
        "key_insights": list,
        "actionable_takeaways": list,
        "priority": str,
        "tags": list,
        "source_url": str,
        "time_estimates": dict,
    }
)
async def save_document_to_notion(args: dict[str, Any]) -> dict[str, Any]:
    """Save document analysis with rich page content."""
    url = "https://api.notion.com/v1/pages"

    properties = {
        "Name": {"title": [{"text": {"content": args.get("title", "Untitled")}}]},
        "Category": {"select": {"name": "Research"}},
        "Description": {"rich_text": [{"text": {"content": args.get("summary", "")[:2000]}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": args.get("priority", "Medium")}},
    }

    if args.get("tags"):
        properties["Tags"] = {"multi_select": [{"name": tag} for tag in args["tags"][:5]]}

    if args.get("source_url"):
        properties["Source"] = {"url": args["source_url"]}

    # Build page content
    children = []

    # Summary
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Summary"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": args.get("summary", "")}}]}
    })

    # Key Insights
    if args.get("key_insights"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Key Insights"}}]}
        })
        for insight in args["key_insights"]:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": insight}}]}
            })

    # Actionable Takeaways
    if args.get("actionable_takeaways"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Actionable Takeaways"}}]}
        })
        for action in args["actionable_takeaways"]:
            children.append({
                "object": "block",
                "type": "to_do",
                "to_do": {"rich_text": [{"type": "text", "text": {"content": action}}], "checked": False}
            })

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children": children
    }

    try:
        response = requests.post(url, headers=_notion_headers(), json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return {
                "content": [{
                    "type": "text",
                    "text": f"Document saved to Notion: {args['title']}\nURL: {result.get('url', 'N/A')}"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error saving document: {response.status_code}"
                }]
            }
    except Exception as e:
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
# Create MCP Server
# =============================================================================

def create_second_brain_server():
    """Create the Second Brain MCP server with all tools."""
    return create_sdk_mcp_server(
        name="second-brain",
        version="1.0.0",
        tools=[
            save_to_notion,
            save_document_to_notion,
            search_notion,
            get_recent_entries,
            send_telegram_message,
        ]
    )
