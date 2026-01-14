"""
Second Brain - Notion Database Setup Script

This script creates your Second Brain database with all properties configured.

Usage:
1. Get your Notion Integration Token from https://notion.so/my-integrations
2. Get a parent page ID (create a blank page, copy the ID from URL)
3. Create .env file with NOTION_TOKEN and NOTION_PAGE_ID
4. Run: python scripts/setup_notion.py
"""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configuration - loaded from .env file
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
PARENT_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


def create_database():
    """Create the Second Brain database with all properties."""

    url = f"{BASE_URL}/databases"

    payload = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
        "title": [{"type": "text", "text": {"content": "Second Brain"}}],
        "properties": {
            "Name": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "People", "color": "blue"},
                        {"name": "Research", "color": "purple"},
                        {"name": "Links", "color": "green"},
                        {"name": "Tasks", "color": "orange"},
                        {"name": "Articles", "color": "pink"},
                    ]
                }
            },
            "Description": {"rich_text": {}},
            "Source": {"url": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "New", "color": "gray"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Done", "color": "green"},
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"},
                    ]
                }
            },
            "Due Date": {"date": {}},
            "Person Name": {"rich_text": {}},
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "follow-up", "color": "red"},
                        {"name": "networking", "color": "blue"},
                        {"name": "learning", "color": "purple"},
                        {"name": "tool", "color": "green"},
                        {"name": "article", "color": "orange"},
                        {"name": "idea", "color": "pink"},
                        {"name": "urgent", "color": "red"},
                        {"name": "reference", "color": "gray"},
                    ]
                }
            },
        },
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        print("Database created successfully!")
        print(f"\nDatabase ID: {data['id']}")
        print(f"URL: {data['url']}")
        print("\nSave the Database ID - you'll need it for Zapier!")
        return data
    else:
        print(f"Error creating database: {response.status_code}")
        print(response.json())
        return None


def add_sample_entries(database_id):
    """Add sample entries to demonstrate the database."""

    url = f"{BASE_URL}/pages"

    samples = [
        {
            "Name": "John Smith - Met at Tech Conference",
            "Category": "People",
            "Description": "CTO at StartupXYZ. Interested in AI partnerships. Follow up next week.",
            "Status": "New",
            "Priority": "High",
            "Person Name": "John Smith",
            "Tags": ["networking", "follow-up"],
        },
        {
            "Name": "Research: Vector Databases",
            "Category": "Research",
            "Description": "Look into Pinecone, Weaviate, and Chroma for embedding storage.",
            "Status": "New",
            "Priority": "Medium",
            "Tags": ["learning", "idea"],
        },
        {
            "Name": "Zapier Automation Guide",
            "Category": "Links",
            "Description": "Comprehensive guide on advanced Zapier workflows.",
            "Source": "https://zapier.com/learn",
            "Status": "New",
            "Priority": "Low",
            "Tags": ["tool", "reference"],
        },
        {
            "Name": "Set up weekly review process",
            "Category": "Tasks",
            "Description": "Configure the weekly email summary and test it.",
            "Status": "In Progress",
            "Priority": "High",
            "Tags": ["urgent"],
        },
    ]

    for sample in samples:
        properties = {
            "Name": {"title": [{"text": {"content": sample["Name"]}}]},
            "Category": {"select": {"name": sample["Category"]}},
            "Description": {"rich_text": [{"text": {"content": sample["Description"]}}]},
            "Status": {"select": {"name": sample["Status"]}},
            "Priority": {"select": {"name": sample["Priority"]}},
            "Tags": {"multi_select": [{"name": tag} for tag in sample.get("Tags", [])]},
        }

        if sample.get("Person Name"):
            properties["Person Name"] = {"rich_text": [{"text": {"content": sample["Person Name"]}}]}

        if sample.get("Source"):
            properties["Source"] = {"url": sample["Source"]}

        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"  Added: {sample['Name']}")
        else:
            print(f"  Error adding {sample['Name']}: {response.text}")


def main():
    print("=" * 50)
    print("Second Brain - Notion Database Setup")
    print("=" * 50)

    # Check configuration
    if not NOTION_TOKEN or not PARENT_PAGE_ID:
        print("\nPlease configure your credentials first!")
        print("\n1. Get your Integration Token:")
        print("   → Go to https://notion.so/my-integrations")
        print("   → Create new integration")
        print("   → Copy the 'Internal Integration Token'")
        print("\n2. Get a Parent Page ID:")
        print("   → Create a new blank page in Notion")
        print("   → Copy the page URL")
        print("   → The ID is the 32-character string after workspace name")
        print("   → Example: notion.so/workspace/PAGE_ID_HERE")
        print("\n3. Create a .env file in the project root with:")
        print("   NOTION_TOKEN=secret_xxx")
        print("   NOTION_PAGE_ID=abc123...")
        print("\n4. Run this script again: python scripts/setup_notion.py")
        return

    print("\nCreating database...")
    result = create_database()

    if result:
        print("\nAdding sample entries...")
        add_sample_entries(result["id"])
        print("\nSetup complete!")
        print("\nNext steps:")
        print("1. Open the database in Notion")
        print("2. Add the integration via ... → Connections")
        print("3. Copy the Database ID for Zapier")


if __name__ == "__main__":
    main()
