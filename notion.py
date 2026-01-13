"""
Notion API functions for Second Brain Bot.
"""

from datetime import datetime, timedelta

import requests

from config import NOTION_TOKEN, NOTION_DATABASE_ID, logger


def _get_headers():
    """Get Notion API headers."""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


# =============================================================================
# Save Functions
# =============================================================================

def save_to_notion(data):
    """Save categorized data to Notion database."""
    url = "https://api.notion.com/v1/pages"

    properties = {
        "Name": {"title": [{"text": {"content": data.get("title", "Untitled")}}]},
        "Category": {"select": {"name": data.get("category", "Research")}},
        "Description": {"rich_text": [{"text": {"content": data.get("description", "")[:2000]}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": data.get("priority", "Medium")}},
    }

    # Add optional fields
    if data.get("person_name"):
        properties["Person Name"] = {"rich_text": [{"text": {"content": data["person_name"]}}]}

    if data.get("due_date"):
        properties["Due Date"] = {"date": {"start": data["due_date"]}}

    if data.get("tags"):
        tags = data["tags"] if isinstance(data["tags"], list) else data["tags"].split(",")
        properties["Tags"] = {"multi_select": [{"name": tag.strip()} for tag in tags[:5]]}

    if data.get("source"):
        properties["Source"] = {"url": data["source"]}

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }

    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error saving to Notion: {e}")
        return None


def save_document_analysis_to_notion(data):
    """Save document analysis to Notion with rich content in the page body."""
    url = "https://api.notion.com/v1/pages"

    # Build properties
    properties = {
        "Name": {"title": [{"text": {"content": data.get("title", "Untitled Document")}}]},
        "Category": {"select": {"name": "Research"}},
        "Description": {"rich_text": [{"text": {"content": data.get("summary", "")[:2000]}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": data.get("priority", "Medium")}},
    }

    if data.get("tags"):
        tags = data["tags"] if isinstance(data["tags"], list) else []
        properties["Tags"] = {"multi_select": [{"name": tag.strip()} for tag in tags[:5]]}

    # Build page content with analysis
    children = []

    # Summary section
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Summary"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": data.get("summary", "")}}]}
    })

    # Key Insights
    if data.get("key_insights"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Key Insights"}}]}
        })
        for insight in data.get("key_insights", []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": insight}}]}
            })

    # Actionable Takeaways
    if data.get("actionable_takeaways"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Actionable Takeaways"}}]}
        })
        for action in data.get("actionable_takeaways", []):
            children.append({
                "object": "block",
                "type": "to_do",
                "to_do": {"rich_text": [{"type": "text", "text": {"content": action}}], "checked": False}
            })

    # Relevance
    if data.get("relevance_assessment"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Relevance to Your Work"}}]}
        })
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": data.get("relevance_assessment", "")}}]}
        })

    # Time Estimates
    if data.get("time_estimates"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Time Estimates"}}]}
        })
        estimates = data.get("time_estimates", {})
        for level, estimate in estimates.items():
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": f"{level.replace('_', ' ').title()}: {estimate}"}}]}
            })

    # Follow-up Questions
    if data.get("follow_up_questions"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Questions to Explore"}}]}
        })
        for question in data.get("follow_up_questions", []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": question}}]}
            })

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children": children
    }

    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Notion API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error saving document to Notion: {e}")
        return None


def save_deep_analysis_to_notion(data):
    """Save deep paper analysis to Notion with comprehensive content."""
    url = "https://api.notion.com/v1/pages"

    academic = data.get("academic_analysis", {})
    practical = data.get("practical_analysis", {})
    meta = data.get("meta", {})

    # Build properties
    properties = {
        "Name": {"title": [{"text": {"content": data.get("title", "Untitled Paper")}}]},
        "Category": {"select": {"name": "Research"}},
        "Description": {"rich_text": [{"text": {"content": practical.get("tldr", "")[:2000]}}]},
        "Status": {"select": {"name": "New"}},
        "Priority": {"select": {"name": meta.get("priority", "Medium")}},
    }

    if meta.get("tags"):
        tags = meta["tags"] if isinstance(meta["tags"], list) else []
        properties["Tags"] = {"multi_select": [{"name": tag.strip()} for tag in tags[:5]]}

    if data.get("source"):
        properties["Source"] = {"url": data["source"]}

    # Build comprehensive page content
    children = []

    # TL;DR Section
    children.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": practical.get("tldr", "")}}],
            "icon": {"emoji": "💡"}
        }
    })

    # Academic Analysis Section
    children.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Academic Analysis"}}]}
    })

    # Problem Statement
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Problem Statement"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": academic.get("problem_statement", "")}}]}
    })

    # Methodology
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Methodology"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": academic.get("methodology", "")}}]}
    })

    # Key Contributions
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Key Contributions"}}]}
    })
    for contrib in academic.get("key_contributions", []):
        children.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": contrib}}]}
        })

    # Results Summary
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Results"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": academic.get("results_summary", "")}}]}
    })

    # Limitations
    if academic.get("limitations"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Limitations"}}]}
        })
        for limitation in academic.get("limitations", []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": limitation}}]}
            })

    # Practical Analysis Section
    children.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Practical Analysis"}}]}
    })

    # Why It Matters
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Why It Matters"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": practical.get("why_it_matters", "")}}]}
    })

    # Implementation Notes
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": f"Implementation ({practical.get('implementation_complexity', 'Medium')} complexity)"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": practical.get("implementation_notes", "")}}]}
    })

    # Use Cases
    if practical.get("use_cases"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Use Cases"}}]}
        })
        for use_case in practical.get("use_cases", []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": use_case}}]}
            })

    # Code/Pseudocode
    if practical.get("code_or_pseudocode") and practical.get("code_or_pseudocode") != "N/A":
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Key Algorithm / Pseudocode"}}]}
        })
        children.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": practical.get("code_or_pseudocode", "")}}],
                "language": "plain text"
            }
        })

    # Meta Section
    children.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Meta"}}]}
    })

    time_est = meta.get("time_estimates", {})
    meta_text = f"Paper Type: {meta.get('paper_type', 'N/A')}\n"
    meta_text += f"Field: {meta.get('field', 'N/A')}\n"
    meta_text += f"Technical Depth: {academic.get('technical_depth', 'N/A')}\n\n"
    meta_text += f"Reading Time:\n"
    meta_text += f"  - Skim: {time_est.get('skim', 'N/A')}\n"
    meta_text += f"  - Understand: {time_est.get('understand', 'N/A')}\n"
    meta_text += f"  - Deep Study: {time_est.get('deep_study', 'N/A')}"

    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": meta_text}}]}
    })

    # Prerequisites
    if meta.get("prerequisites"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Prerequisites"}}]}
        })
        for prereq in meta.get("prerequisites", []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": prereq}}]}
            })

    # Questions to Explore
    if data.get("questions_to_explore"):
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Questions to Explore"}}]}
        })
        for question in data.get("questions_to_explore", []):
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": question}}]}
            })

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children": children
    }

    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Notion API error (deep analysis): {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error saving deep analysis to Notion: {e}")
        return None


# =============================================================================
# Query Functions
# =============================================================================

def search_notion_entries(query, limit=20):
    """Search Notion database for entries matching the query."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    # Get recent entries (Notion doesn't have full-text search via API)
    # We'll fetch recent entries and let Claude find relevant ones
    payload = {
        "page_size": limit,
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }

    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("results", [])
        return []
    except Exception as e:
        logger.error(f"Error searching Notion: {e}")
        return []


def get_notion_entries(days=1):
    """Get entries from Notion from the last N days."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    # Calculate date filter
    since_date = (datetime.now() - timedelta(days=days)).isoformat()

    payload = {
        "filter": {
            "timestamp": "created_time",
            "created_time": {"after": since_date}
        },
        "sorts": [{"timestamp": "created_time", "direction": "descending"}]
    }

    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            logger.error(f"Notion query error: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error querying Notion: {e}")
        return []


# =============================================================================
# Formatting Functions
# =============================================================================

def format_entries_for_query(entries):
    """Format entries for the query context."""
    formatted = []
    for entry in entries:
        props = entry.get("properties", {})
        url = entry.get("url", "")

        title = ""
        if props.get("Name", {}).get("title"):
            title = props["Name"]["title"][0]["text"]["content"]

        category = props.get("Category", {}).get("select", {}).get("name", "")

        description = ""
        if props.get("Description", {}).get("rich_text"):
            description = props["Description"]["rich_text"][0]["text"]["content"]

        created = entry.get("created_time", "")[:10]  # Just the date

        formatted.append({
            "title": title,
            "category": category,
            "description": description[:500],
            "date": created,
            "url": url
        })

    return formatted


def format_entries_for_summary(entries):
    """Format Notion entries for AI summarization."""
    formatted = []
    for entry in entries:
        props = entry.get("properties", {})

        title = ""
        if props.get("Name", {}).get("title"):
            title = props["Name"]["title"][0]["text"]["content"]

        category = props.get("Category", {}).get("select", {}).get("name", "")
        priority = props.get("Priority", {}).get("select", {}).get("name", "")
        status = props.get("Status", {}).get("select", {}).get("name", "")

        description = ""
        if props.get("Description", {}).get("rich_text"):
            description = props["Description"]["rich_text"][0]["text"]["content"]

        formatted.append(f"- [{category}] {title} (Priority: {priority}, Status: {status})\n  {description}")

    return "\n".join(formatted) if formatted else "No entries found."


def format_entries_with_links(entries):
    """Format entries with Notion links for the digest message."""
    by_category = {"Tasks": [], "People": [], "Research": [], "Links": []}

    for entry in entries:
        props = entry.get("properties", {})
        url = entry.get("url", "")

        title = ""
        if props.get("Name", {}).get("title"):
            title = props["Name"]["title"][0]["text"]["content"]

        category = props.get("Category", {}).get("select", {}).get("name", "Research")
        priority = props.get("Priority", {}).get("select", {}).get("name", "")

        if category in by_category:
            by_category[category].append({
                "title": title,
                "url": url,
                "priority": priority
            })

    return by_category


# =============================================================================
# Dashboard Functions
# =============================================================================

def create_daily_dashboard(entries, summary_text):
    """Create a daily dashboard page in Notion."""
    url = "https://api.notion.com/v1/pages"

    today = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%A, %B %d, %Y")

    # Build children blocks
    children = []

    # Summary section
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Daily Summary"}}]}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": summary_text[:2000]}}]}
    })

    # Entries by category
    by_category = format_entries_with_links(entries)

    for category, items in by_category.items():
        if items:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": category}}]}
            })
            for item in items:
                # Create a linked mention to the entry
                priority_badge = f" [{item['priority']}]" if item['priority'] == 'High' else ""
                children.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"{item['title']}{priority_badge}", "link": {"url": item['url']} if item['url'] else None}}
                        ]
                    }
                })

    # Stats
    total = len(entries)
    high_priority = sum(1 for e in entries if e.get("properties", {}).get("Priority", {}).get("select", {}).get("name") == "High")

    children.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Total entries: {total} | High priority: {high_priority}"}}]}
    })

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": f"Daily Dashboard - {today_display}"}}]},
            "Category": {"select": {"name": "Research"}},
            "Description": {"rich_text": [{"text": {"content": f"Daily summary for {today}"}}]},
            "Status": {"select": {"name": "Done"}},
            "Priority": {"select": {"name": "Medium"}},
            "Tags": {"multi_select": [{"name": "daily-dashboard"}]}
        },
        "children": children
    }

    try:
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error creating daily dashboard: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating daily dashboard: {e}")
        return None
