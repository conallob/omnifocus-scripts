#!/usr/bin/env python3

"""
Slack Saved Messages to OmniFocus Inbox

This script fetches messages from your Slack "Saved Items" and adds them
to your OmniFocus Inbox, then optionally removes them from Slack saved items.

Requirements:
    pip install slack-sdk

Setup:
    1. Create a Slack App at https://api.slack.com/apps
    2. Add the following OAuth scopes to your User Token:
       - stars:read (to read saved items)
       - stars:write (to remove saved items - optional)
    3. Install the app to your workspace
    4. Copy your User OAuth Token
    5. Create a .env file or export SLACK_USER_TOKEN environment variable

Usage:
    python3 slack_to_omnifocus.py [--remove] [--limit N]

    --remove: Remove items from Slack after adding to OmniFocus
    --limit N: Only process the first N saved items (default: 50)
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Optional

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("Error: slack-sdk is not installed.")
    print("Please install it with: pip install slack-sdk")
    sys.exit(1)


class SlackToOmniFocus:
    def __init__(self, slack_token: str):
        """Initialize with Slack token."""
        self.client = WebClient(token=slack_token)
        self.user_id = None

    def get_saved_messages(self, limit: int = 50) -> List[Dict]:
        """Fetch saved messages from Slack."""
        try:
            # Get starred items (saved messages)
            response = self.client.stars_list(limit=limit)

            if not response["ok"]:
                print(f"Error fetching saved items: {response.get('error', 'Unknown error')}")
                return []

            saved_items = []
            for item in response.get("items", []):
                parsed_item = self._parse_saved_item(item)
                if parsed_item:
                    saved_items.append(parsed_item)

            return saved_items

        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
            return []

    def _parse_saved_item(self, item: Dict) -> Optional[Dict]:
        """Parse a saved item into a structured format."""
        item_type = item.get("type")

        if item_type == "message":
            message = item.get("message", {})
            return {
                "type": "message",
                "text": message.get("text", ""),
                "user": message.get("user", "Unknown"),
                "timestamp": message.get("ts", ""),
                "channel": item.get("channel", ""),
                "permalink": message.get("permalink", ""),
                "date_created": item.get("date_create", 0),
            }

        elif item_type == "file":
            file_info = item.get("file", {})
            return {
                "type": "file",
                "text": f"File: {file_info.get('name', 'Unknown file')}",
                "title": file_info.get("title", ""),
                "url": file_info.get("permalink", ""),
                "date_created": item.get("date_create", 0),
            }

        elif item_type == "file_comment":
            comment = item.get("comment", {})
            return {
                "type": "file_comment",
                "text": comment.get("comment", ""),
                "timestamp": comment.get("timestamp", ""),
                "date_created": item.get("date_create", 0),
            }

        return None

    def remove_saved_item(self, item: Dict) -> bool:
        """Remove an item from Slack saved items."""
        try:
            # Unstar the item
            if item["type"] == "message":
                response = self.client.stars_remove(
                    channel=item["channel"],
                    timestamp=item["timestamp"]
                )
            elif item["type"] == "file":
                response = self.client.stars_remove(
                    file=item.get("file_id")
                )
            else:
                return False

            return response["ok"]

        except SlackApiError as e:
            print(f"Error removing item from Slack: {e.response['error']}")
            return False

    def add_to_omnifocus(self, items: List[Dict]) -> int:
        """Add items to OmniFocus Inbox using AppleScript."""
        if not items:
            return 0

        added_count = 0

        for item in items:
            title = self._create_title(item)
            note = self._create_note(item)

            # Create AppleScript to add task to OmniFocus
            applescript = f'''
            tell application "OmniFocus"
                tell default document
                    set newTask to make new inbox task with properties {{name:"{self._escape_quotes(title)}"}}
                    set note of newTask to "{self._escape_quotes(note)}"
                end tell
            end tell
            '''

            try:
                subprocess.run(
                    ['osascript', '-e', applescript],
                    check=True,
                    capture_output=True,
                    text=True
                )
                added_count += 1
                print(f"✓ Added: {title}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to add: {title}")
                print(f"  Error: {e.stderr}")

        return added_count

    def _create_title(self, item: Dict) -> str:
        """Create a title for the OmniFocus task."""
        text = item.get("text", "").strip()

        # Use first line or first 100 characters as title
        if "\n" in text:
            title = text.split("\n")[0]
        else:
            title = text[:100]

        # Add prefix based on item type
        if item["type"] == "file":
            return f"[Slack File] {title}"
        else:
            return f"[Slack] {title}" if title else "[Slack] Saved Message"

    def _create_note(self, item: Dict) -> str:
        """Create a note for the OmniFocus task."""
        note_parts = []

        # Add full text
        if item.get("text"):
            note_parts.append(item["text"])

        # Add metadata
        note_parts.append("\n---")
        note_parts.append(f"Source: Slack Saved Items")
        note_parts.append(f"Type: {item['type']}")

        if item.get("timestamp"):
            note_parts.append(f"Timestamp: {item['timestamp']}")

        if item.get("permalink"):
            note_parts.append(f"Link: {item['permalink']}")

        if item.get("url"):
            note_parts.append(f"URL: {item['url']}")

        date_created = item.get("date_created", 0)
        if date_created:
            dt = datetime.fromtimestamp(date_created)
            note_parts.append(f"Saved on: {dt.strftime('%Y-%m-%d %H:%M')}")

        return "\n".join(note_parts)

    def _escape_quotes(self, text: str) -> str:
        """Escape quotes for AppleScript."""
        return text.replace('"', '\\"').replace('\\', '\\\\')


def load_slack_token() -> Optional[str]:
    """Load Slack token from environment or .env file."""
    # Try environment variable first
    token = os.environ.get("SLACK_USER_TOKEN")
    if token:
        return token

    # Try loading from .env file
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("SLACK_USER_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"\'')

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Import Slack saved messages to OmniFocus Inbox"
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove items from Slack after adding to OmniFocus"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of saved items to process (default: 50)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually doing it"
    )

    args = parser.parse_args()

    # Load Slack token
    slack_token = load_slack_token()
    if not slack_token:
        print("Error: SLACK_USER_TOKEN not found.")
        print("")
        print("Please set the SLACK_USER_TOKEN environment variable or create a .env file with:")
        print("SLACK_USER_TOKEN=xoxp-your-token-here")
        print("")
        print("To get a token:")
        print("1. Go to https://api.slack.com/apps")
        print("2. Create a new app or select an existing one")
        print("3. Add OAuth scopes: stars:read and stars:write (optional)")
        print("4. Install the app to your workspace")
        print("5. Copy the User OAuth Token")
        sys.exit(1)

    # Initialize
    slack_to_of = SlackToOmniFocus(slack_token)

    print("Fetching saved messages from Slack...")
    saved_items = slack_to_of.get_saved_messages(limit=args.limit)

    if not saved_items:
        print("No saved messages found.")
        return

    print(f"\nFound {len(saved_items)} saved item(s)")
    print("")

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print("")
        for i, item in enumerate(saved_items, 1):
            title = slack_to_of._create_title(item)
            print(f"{i}. {title}")
        return

    # Add to OmniFocus
    print("Adding items to OmniFocus Inbox...")
    added_count = slack_to_of.add_to_omnifocus(saved_items)

    print(f"\nSuccessfully added {added_count}/{len(saved_items)} item(s) to OmniFocus")

    # Optionally remove from Slack
    if args.remove and added_count > 0:
        print("\nRemoving items from Slack saved messages...")
        removed_count = 0
        for item in saved_items[:added_count]:
            if slack_to_of.remove_saved_item(item):
                removed_count += 1

        print(f"Removed {removed_count}/{added_count} item(s) from Slack")


if __name__ == "__main__":
    main()
