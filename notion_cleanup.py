#!/usr/bin/env python3
"""
Notion Cleanup Script for Second Brain

Provides utilities to clean up the Notion database:
- Remove duplicate entries (by title similarity)
- Remove test data (entries with "test" in title)
- Archive completed tasks

Usage:
    python notion_cleanup.py duplicates [--dry-run]
    python notion_cleanup.py test-data [--dry-run]
    python notion_cleanup.py completed-tasks [--dry-run]
    python notion_cleanup.py all [--dry-run]
    python notion_cleanup.py stats
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from difflib import SequenceMatcher

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")


def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


def get_all_entries(limit: int = 500) -> list[dict]:
    """Fetch all entries from Notion database."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

    all_entries = []
    has_more = True
    start_cursor = None

    while has_more and len(all_entries) < limit:
        payload = {
            "page_size": 100,
            "sorts": [{"timestamp": "created_time", "direction": "descending"}]
        }
        if start_cursor:
            payload["start_cursor"] = start_cursor

        try:
            response = requests.post(url, headers=_notion_headers(), json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                for entry in results:
                    props = entry.get("properties", {})

                    # Extract title
                    title = ""
                    if props.get("Name", {}).get("title"):
                        title = props["Name"]["title"][0]["text"]["content"]

                    # Extract category
                    category = props.get("Category", {}).get("select", {}).get("name", "")

                    # Extract status
                    status = props.get("Status", {}).get("select", {}).get("name", "")

                    # Extract description
                    description = ""
                    if props.get("Description", {}).get("rich_text"):
                        description = props["Description"]["rich_text"][0]["text"]["content"]

                    # Extract created time
                    created_time = entry.get("created_time", "")

                    all_entries.append({
                        "id": entry["id"],
                        "title": title,
                        "category": category,
                        "status": status,
                        "description": description,
                        "created_time": created_time,
                        "url": entry.get("url", "")
                    })

                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
            else:
                print(f"Error fetching entries: {response.status_code}")
                break
        except Exception as e:
            print(f"Error: {e}")
            break

    return all_entries


def archive_entry(page_id: str) -> bool:
    """Archive (soft delete) a Notion page."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"archived": True}

    try:
        response = requests.patch(url, headers=_notion_headers(), json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error archiving {page_id}: {e}")
        return False


def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio (0-1)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# =============================================================================
# Cleanup Functions
# =============================================================================

def find_duplicates(entries: list[dict], threshold: float = 0.85) -> list[tuple]:
    """
    Find duplicate entries based on title similarity.
    Returns list of (original, duplicate) tuples.
    """
    duplicates = []
    seen = []

    for entry in entries:
        title = entry["title"]
        if not title:
            continue

        # Check against all previously seen titles
        for seen_entry in seen:
            sim = similarity(title, seen_entry["title"])
            if sim >= threshold:
                # Keep the older one (later in sorted list = older)
                duplicates.append((seen_entry, entry))
                break
        else:
            seen.append(entry)

    return duplicates


def find_test_data(entries: list[dict]) -> list[dict]:
    """
    Find entries that appear to be test data.
    Criteria:
    - Title contains "test" (case insensitive)
    - Title contains "sample", "example", "demo"
    - Description contains "[test]" or "[TEST]"
    """
    test_keywords = ["test", "sample", "example", "demo", "dummy", "placeholder"]
    test_entries = []

    for entry in entries:
        title_lower = entry["title"].lower()
        desc_lower = entry["description"].lower()

        is_test = False
        reason = ""

        for keyword in test_keywords:
            if keyword in title_lower:
                is_test = True
                reason = f"Title contains '{keyword}'"
                break

        if not is_test and "[test]" in desc_lower:
            is_test = True
            reason = "Description contains [test]"

        if is_test:
            entry["test_reason"] = reason
            test_entries.append(entry)

    return test_entries


def find_completed_tasks(entries: list[dict], days_old: int = 30) -> list[dict]:
    """
    Find completed tasks that are older than N days.
    """
    completed = []
    cutoff_date = datetime.now() - timedelta(days=days_old)

    for entry in entries:
        if entry["category"] != "Tasks":
            continue

        if entry["status"] != "Done":
            continue

        # Check age
        created_str = entry.get("created_time", "")
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if created.replace(tzinfo=None) < cutoff_date:
                    entry["age_days"] = (datetime.now() - created.replace(tzinfo=None)).days
                    completed.append(entry)
            except:
                pass

    return completed


def get_stats(entries: list[dict]) -> dict:
    """Get statistics about the Notion database."""
    stats = {
        "total": len(entries),
        "by_category": defaultdict(int),
        "by_status": defaultdict(int),
        "empty_titles": 0,
        "this_week": 0,
        "this_month": 0,
    }

    week_ago = datetime.now() - timedelta(days=7)
    month_ago = datetime.now() - timedelta(days=30)

    for entry in entries:
        stats["by_category"][entry["category"] or "Unknown"] += 1
        stats["by_status"][entry["status"] or "Unknown"] += 1

        if not entry["title"]:
            stats["empty_titles"] += 1

        created_str = entry.get("created_time", "")
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                created_naive = created.replace(tzinfo=None)
                if created_naive > week_ago:
                    stats["this_week"] += 1
                if created_naive > month_ago:
                    stats["this_month"] += 1
            except:
                pass

    return stats


# =============================================================================
# CLI Commands
# =============================================================================

def cmd_duplicates(args):
    """Handle duplicates command."""
    print("Fetching entries from Notion...")
    entries = get_all_entries()
    print(f"Found {len(entries)} entries\n")

    print(f"Finding duplicates (threshold: {args.threshold})...")
    duplicates = find_duplicates(entries, threshold=args.threshold)

    if not duplicates:
        print("No duplicates found!")
        return

    print(f"\nFound {len(duplicates)} potential duplicates:\n")

    for i, (original, dupe) in enumerate(duplicates, 1):
        sim = similarity(original["title"], dupe["title"])
        print(f"{i}. Duplicate: \"{dupe['title'][:50]}\"")
        print(f"   Original:  \"{original['title'][:50]}\"")
        print(f"   Similarity: {sim:.1%}")
        print(f"   Category: {dupe['category']}")
        print(f"   ID: {dupe['id'][:8]}...")
        print()

    if args.dry_run:
        print("[DRY RUN] No entries were deleted.")
        return

    # Confirm deletion
    confirm = input(f"\nArchive {len(duplicates)} duplicate entries? [y/N]: ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    deleted = 0
    for original, dupe in duplicates:
        if archive_entry(dupe["id"]):
            deleted += 1
            print(f"  Archived: {dupe['title'][:40]}...")
        else:
            print(f"  Failed: {dupe['title'][:40]}...")

    print(f"\nArchived {deleted}/{len(duplicates)} duplicates.")


def cmd_test_data(args):
    """Handle test-data command."""
    print("Fetching entries from Notion...")
    entries = get_all_entries()
    print(f"Found {len(entries)} entries\n")

    print("Finding test data...")
    test_entries = find_test_data(entries)

    if not test_entries:
        print("No test data found!")
        return

    print(f"\nFound {len(test_entries)} test entries:\n")

    for i, entry in enumerate(test_entries, 1):
        print(f"{i}. \"{entry['title'][:50]}\"")
        print(f"   Reason: {entry.get('test_reason', 'N/A')}")
        print(f"   Category: {entry['category']}")
        print(f"   ID: {entry['id'][:8]}...")
        print()

    if args.dry_run:
        print("[DRY RUN] No entries were deleted.")
        return

    confirm = input(f"\nArchive {len(test_entries)} test entries? [y/N]: ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    deleted = 0
    for entry in test_entries:
        if archive_entry(entry["id"]):
            deleted += 1
            print(f"  Archived: {entry['title'][:40]}...")
        else:
            print(f"  Failed: {entry['title'][:40]}...")

    print(f"\nArchived {deleted}/{len(test_entries)} test entries.")


def cmd_completed_tasks(args):
    """Handle completed-tasks command."""
    print("Fetching entries from Notion...")
    entries = get_all_entries()
    print(f"Found {len(entries)} entries\n")

    print(f"Finding completed tasks older than {args.days} days...")
    completed = find_completed_tasks(entries, days_old=args.days)

    if not completed:
        print("No old completed tasks found!")
        return

    print(f"\nFound {len(completed)} completed tasks to archive:\n")

    for i, entry in enumerate(completed, 1):
        print(f"{i}. \"{entry['title'][:50]}\"")
        print(f"   Age: {entry.get('age_days', 'N/A')} days")
        print(f"   ID: {entry['id'][:8]}...")
        print()

    if args.dry_run:
        print("[DRY RUN] No entries were deleted.")
        return

    confirm = input(f"\nArchive {len(completed)} old completed tasks? [y/N]: ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    deleted = 0
    for entry in completed:
        if archive_entry(entry["id"]):
            deleted += 1
            print(f"  Archived: {entry['title'][:40]}...")
        else:
            print(f"  Failed: {entry['title'][:40]}...")

    print(f"\nArchived {deleted}/{len(completed)} completed tasks.")


def cmd_stats(args):
    """Handle stats command."""
    print("Fetching entries from Notion...")
    entries = get_all_entries()

    stats = get_stats(entries)

    print(f"\n{'='*50}")
    print("SECOND BRAIN DATABASE STATISTICS")
    print(f"{'='*50}\n")

    print(f"Total entries: {stats['total']}")
    print(f"Created this week: {stats['this_week']}")
    print(f"Created this month: {stats['this_month']}")
    print(f"Empty titles: {stats['empty_titles']}")

    print(f"\nBy Category:")
    for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print(f"\nBy Status:")
    for status, count in sorted(stats["by_status"].items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")

    # Quick health check
    print(f"\n{'='*50}")
    print("HEALTH CHECK")
    print(f"{'='*50}\n")

    duplicates = find_duplicates(entries)
    test_data = find_test_data(entries)
    completed = find_completed_tasks(entries)

    if duplicates:
        print(f"⚠️  Found {len(duplicates)} potential duplicates")
    else:
        print("✓  No duplicates found")

    if test_data:
        print(f"⚠️  Found {len(test_data)} test data entries")
    else:
        print("✓  No test data found")

    if completed:
        print(f"📋 Found {len(completed)} old completed tasks (30+ days)")
    else:
        print("✓  No old completed tasks")

    if stats["empty_titles"]:
        print(f"⚠️  Found {stats['empty_titles']} entries with empty titles")

    print()


def cmd_all(args):
    """Handle all command - run all cleanups."""
    print("Fetching entries from Notion...")
    entries = get_all_entries()
    print(f"Found {len(entries)} entries\n")

    # Find all issues
    duplicates = find_duplicates(entries)
    test_data = find_test_data(entries)
    completed = find_completed_tasks(entries, days_old=args.days)

    total_issues = len(duplicates) + len(test_data) + len(completed)

    if total_issues == 0:
        print("Database is clean! No issues found.")
        return

    print(f"Found {total_issues} items to clean up:")
    print(f"  - {len(duplicates)} duplicates")
    print(f"  - {len(test_data)} test data entries")
    print(f"  - {len(completed)} old completed tasks")
    print()

    if args.dry_run:
        print("[DRY RUN] Showing what would be cleaned up:\n")

        if duplicates:
            print("DUPLICATES:")
            for orig, dupe in duplicates[:5]:
                print(f"  • {dupe['title'][:50]}")
            if len(duplicates) > 5:
                print(f"  ... and {len(duplicates) - 5} more")
            print()

        if test_data:
            print("TEST DATA:")
            for entry in test_data[:5]:
                print(f"  • {entry['title'][:50]}")
            if len(test_data) > 5:
                print(f"  ... and {len(test_data) - 5} more")
            print()

        if completed:
            print("COMPLETED TASKS:")
            for entry in completed[:5]:
                print(f"  • {entry['title'][:50]} ({entry.get('age_days', '?')} days old)")
            if len(completed) > 5:
                print(f"  ... and {len(completed) - 5} more")

        print("\n[DRY RUN] No entries were deleted.")
        return

    if not args.yes:
        confirm = input(f"\nArchive all {total_issues} entries? [y/N]: ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return

    deleted = 0

    # Archive duplicates
    for orig, dupe in duplicates:
        if archive_entry(dupe["id"]):
            deleted += 1

    # Archive test data
    for entry in test_data:
        if archive_entry(entry["id"]):
            deleted += 1

    # Archive completed tasks
    for entry in completed:
        if archive_entry(entry["id"]):
            deleted += 1

    print(f"\nArchived {deleted}/{total_issues} entries.")


def main():
    parser = argparse.ArgumentParser(
        description="Notion Cleanup Script for Second Brain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python notion_cleanup.py stats                    Show database statistics
  python notion_cleanup.py duplicates --dry-run    Preview duplicates
  python notion_cleanup.py test-data               Remove test data
  python notion_cleanup.py completed-tasks --days 60   Archive tasks >60 days old
  python notion_cleanup.py all --dry-run           Preview all cleanup
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Cleanup command")

    # Duplicates
    dup_parser = subparsers.add_parser("duplicates", help="Find and remove duplicates")
    dup_parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    dup_parser.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold (0-1)")

    # Test data
    test_parser = subparsers.add_parser("test-data", help="Find and remove test data")
    test_parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")

    # Completed tasks
    completed_parser = subparsers.add_parser("completed-tasks", help="Archive old completed tasks")
    completed_parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    completed_parser.add_argument("--days", type=int, default=30, help="Age threshold in days")

    # All
    all_parser = subparsers.add_parser("all", help="Run all cleanups")
    all_parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    all_parser.add_argument("--days", type=int, default=30, help="Age threshold for completed tasks")
    all_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # Stats
    subparsers.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        print("Error: NOTION_TOKEN and NOTION_DATABASE_ID must be set in .env")
        sys.exit(1)

    commands = {
        "duplicates": cmd_duplicates,
        "test-data": cmd_test_data,
        "completed-tasks": cmd_completed_tasks,
        "all": cmd_all,
        "stats": cmd_stats,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
