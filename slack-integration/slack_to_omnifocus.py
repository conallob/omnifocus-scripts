#!/usr/bin/env python3
"""
Slack to OmniFocus Integration Script

This script fetches saved messages from Slack and adds them as tasks
to the OmniFocus inbox for triage.

Requirements:
    - Python 3.7+
    - slack-sdk library (pip install slack-sdk)
    - OmniFocus installed on macOS
    - Slack API token with appropriate permissions

Usage:
    python slack_to_omnifocus.py [--remove-after-import] [--config CONFIG_FILE]
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("Error: slack-sdk not installed. Install with: pip install slack-sdk")
    sys.exit(1)


class SlackToOmniFocus:
    """Handles importing Slack saved items to OmniFocus."""

    def __init__(self, config_path: str = None):
        """
        Initialize the integration.

        Args:
            config_path: Path to configuration file. Defaults to config.json in script directory.
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')

        self.config = self._load_config(config_path)
        self.slack_token = self.config.get('slack_token')

        if not self.slack_token:
            raise ValueError("Slack token not found in configuration")

        self.client = WebClient(token=self.slack_token)
        self.user_cache = {}
        self.channel_cache = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please copy config.example.json to config.json and add your Slack token."
            )

        with open(config_path, 'r') as f:
            return json.load(f)

    def _get_user_name(self, user_id: str) -> str:
        """Get user's display name from user ID."""
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            response = self.client.users_info(user=user_id)
            user = response['user']
            name = user.get('real_name') or user.get('name') or user_id
            self.user_cache[user_id] = name
            return name
        except SlackApiError:
            return user_id

    def _get_channel_name(self, channel_id: str) -> str:
        """Get channel name from channel ID."""
        if channel_id in self.channel_cache:
            return self.channel_cache[channel_id]

        try:
            response = self.client.conversations_info(channel=channel_id)
            name = response['channel'].get('name') or channel_id
            self.channel_cache[channel_id] = f"#{name}"
            return self.channel_cache[channel_id]
        except SlackApiError:
            return channel_id

    def fetch_saved_items(self) -> List[Dict[str, Any]]:
        """
        Fetch all saved/starred items from Slack.

        Returns:
            List of saved items with metadata.
        """
        print("Fetching saved items from Slack...")
        saved_items = []

        try:
            # Fetch starred items (Slack's "saved" items)
            response = self.client.stars_list()
            items = response.get('items', [])

            print(f"Found {len(items)} saved items")

            for item in items:
                item_type = item.get('type')

                if item_type == 'message':
                    message = item.get('message', {})
                    saved_items.append({
                        'type': 'message',
                        'text': message.get('text', ''),
                        'user': self._get_user_name(message.get('user', 'unknown')),
                        'channel': self._get_channel_name(item.get('channel', 'unknown')),
                        'timestamp': message.get('ts', ''),
                        'permalink': message.get('permalink', ''),
                        'item': item
                    })
                elif item_type == 'file':
                    file_data = item.get('file', {})
                    saved_items.append({
                        'type': 'file',
                        'text': file_data.get('title', file_data.get('name', 'Untitled file')),
                        'url': file_data.get('permalink', ''),
                        'user': self._get_user_name(file_data.get('user', 'unknown')),
                        'timestamp': file_data.get('created', ''),
                        'item': item
                    })

            return saved_items

        except SlackApiError as e:
            print(f"Error fetching saved items: {e.response['error']}")
            return []

    def add_to_omnifocus(self, task_name: str, note: str = "") -> bool:
        """
        Add a task to OmniFocus inbox using AppleScript.

        Args:
            task_name: Name of the task
            note: Additional notes for the task

        Returns:
            True if successful, False otherwise
        """
        # Escape quotes and backslashes for AppleScript
        task_name = task_name.replace('\\', '\\\\').replace('"', '\\"')
        note = note.replace('\\', '\\\\').replace('"', '\\"')

        applescript = f'''
        tell application "OmniFocus"
            tell default document
                make new inbox task with properties {{name:"{task_name}", note:"{note}"}}
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
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding task to OmniFocus: {e.stderr}")
            return False

    def format_task(self, item: Dict[str, Any]) -> tuple:
        """
        Format a Slack item as an OmniFocus task.

        Args:
            item: Slack item dictionary

        Returns:
            Tuple of (task_name, note)
        """
        if item['type'] == 'message':
            # Create task name from first line or truncated text
            text = item['text'].strip()
            first_line = text.split('\n')[0][:100]
            task_name = f"Slack: {first_line}"

            # Create detailed note
            note_parts = [
                f"From: {item['user']}",
                f"Channel: {item['channel']}",
                f"",
                text,
            ]

            if item.get('permalink'):
                note_parts.append(f"\nLink: {item['permalink']}")

            note = "\n".join(note_parts)

        elif item['type'] == 'file':
            task_name = f"Slack File: {item['text']}"
            note_parts = [
                f"Shared by: {item['user']}",
                f"URL: {item['url']}"
            ]
            note = "\n".join(note_parts)

        else:
            task_name = f"Slack Item: {item.get('type', 'unknown')}"
            note = str(item)

        return task_name, note

    def remove_saved_item(self, item: Dict[str, Any]) -> bool:
        """
        Remove an item from Slack saved items.

        Args:
            item: The item to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            item_data = item['item']

            # Determine what to unstar based on item type
            if item['type'] == 'message':
                self.client.stars_remove(
                    channel=item_data.get('channel'),
                    timestamp=item_data['message'].get('ts')
                )
            elif item['type'] == 'file':
                self.client.stars_remove(
                    file=item_data['file'].get('id')
                )

            return True

        except SlackApiError as e:
            print(f"Error removing saved item: {e.response['error']}")
            return False

    def sync(self, remove_after_import: bool = False):
        """
        Main sync function: fetch saved items and add to OmniFocus.

        Args:
            remove_after_import: If True, remove items from Slack after importing
        """
        saved_items = self.fetch_saved_items()

        if not saved_items:
            print("No saved items to import")
            return

        print(f"\nImporting {len(saved_items)} items to OmniFocus...")

        success_count = 0
        fail_count = 0

        for i, item in enumerate(saved_items, 1):
            task_name, note = self.format_task(item)
            print(f"[{i}/{len(saved_items)}] Adding: {task_name[:60]}...")

            if self.add_to_omnifocus(task_name, note):
                success_count += 1

                if remove_after_import:
                    if self.remove_saved_item(item):
                        print(f"  ✓ Added and removed from Slack")
                    else:
                        print(f"  ✓ Added (failed to remove from Slack)")
                else:
                    print(f"  ✓ Added")
            else:
                fail_count += 1
                print(f"  ✗ Failed")

        print(f"\n{'='*60}")
        print(f"Import complete: {success_count} succeeded, {fail_count} failed")
        print(f"{'='*60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Import Slack saved messages to OmniFocus inbox'
    )
    parser.add_argument(
        '--config',
        help='Path to configuration file (default: config.json)',
        default=None
    )
    parser.add_argument(
        '--remove-after-import',
        action='store_true',
        help='Remove items from Slack after successfully importing to OmniFocus'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually adding to OmniFocus'
    )

    args = parser.parse_args()

    try:
        sync_tool = SlackToOmniFocus(config_path=args.config)

        if args.dry_run:
            print("DRY RUN MODE - No tasks will be added to OmniFocus\n")
            items = sync_tool.fetch_saved_items()
            for i, item in enumerate(items, 1):
                task_name, note = sync_tool.format_task(item)
                print(f"\n[{i}] {task_name}")
                print(f"    {note[:100]}...")
        else:
            sync_tool.sync(remove_after_import=args.remove_after_import)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
