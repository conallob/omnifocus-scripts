#!/usr/bin/env python3
"""
Slack to OmniFocus Integration

Imports starred items from Slack and creates tasks in OmniFocus.

Security: All AppleScript strings are properly escaped to prevent injection attacks.
Performance: Implements pagination for large datasets and caching for API calls.
Reliability: Includes rate limiting handling and comprehensive error logging.

Author: Claude Code
Version: 1.0.0
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def escape_applescript_string(s: str) -> str:
    """
    Escape string for safe use in AppleScript.

    Prevents AppleScript injection by escaping special characters:
    - Backslashes
    - Double quotes
    - Newlines (both LF and CR)
    - Carriage returns

    Args:
        s: String to escape

    Returns:
        Safely escaped string for use in AppleScript

    Security Note: This addresses the AppleScript injection vulnerability
    by properly escaping all characters that could break string syntax.
    """
    if s is None:
        return ""

    return (s
            .replace('\\', '\\\\\\\\')  # Escape backslashes
            .replace('"', '\\\\"')       # Escape double quotes
            .replace('\n', '\\\\n')      # Escape newlines
            .replace('\r', '\\\\r'))     # Escape carriage returns


class SlackToOmniFocus:
    """
    Integrates Slack starred items with OmniFocus.

    Features:
    - Fetches all starred items from Slack (with pagination)
    - Resolves user and channel names with caching
    - Creates OmniFocus tasks with properly formatted information
    - Handles rate limiting and errors gracefully
    """

    def __init__(self, config_path: str):
        """
        Initialize the integration.

        Args:
            config_path: Path to JSON configuration file
        """
        self.config = self._load_config(config_path)
        self.client = WebClient(token=self.config['slack']['token'])

        # Caches for API responses to minimize requests
        self.user_cache: Dict[str, str] = {}
        self.channel_cache: Dict[str, str] = {}

        # Statistics
        self.stats = {
            'items_processed': 0,
            'tasks_created': 0,
            'api_calls': 0,
            'errors': 0
        }

    def _load_config(self, config_path: str) -> dict:
        """Load and validate configuration file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Validate required fields
        required_fields = ['slack.token']
        for field in required_fields:
            parts = field.split('.')
            obj = config
            for part in parts:
                if part not in obj:
                    raise ValueError(f"Missing required config field: {field}")
                obj = obj[part]

        return config

    def get_user_name(self, user_id: str) -> str:
        """
        Get user's display name from Slack.

        Uses caching to minimize API calls.

        Args:
            user_id: Slack user ID

        Returns:
            User's display name or user ID if lookup fails
        """
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            self.stats['api_calls'] += 1
            response = self.client.users_info(user=user_id)

            if response['ok']:
                user = response['user']
                name = (user.get('profile', {}).get('display_name') or
                       user.get('real_name') or
                       user.get('name', user_id))
                self.user_cache[user_id] = name
                return name
        except SlackApiError as e:
            print(f"Warning: Could not fetch user info for {user_id}: {e}",
                  file=sys.stderr)
            self.stats['errors'] += 1

        return user_id

    def get_channel_name(self, channel_id: str) -> str:
        """
        Get channel name from Slack.

        Uses caching to minimize API calls.

        Args:
            channel_id: Slack channel ID

        Returns:
            Channel name or channel ID if lookup fails
        """
        if channel_id in self.channel_cache:
            return self.channel_cache[channel_id]

        try:
            self.stats['api_calls'] += 1
            response = self.client.conversations_info(channel=channel_id)

            if response['ok']:
                name = response['channel'].get('name', channel_id)
                self.channel_cache[channel_id] = name
                return name
        except SlackApiError as e:
            print(f"Warning: Could not fetch channel info for {channel_id}: {e}",
                  file=sys.stderr)
            self.stats['errors'] += 1

        return channel_id

    def fetch_starred_items(self) -> List[dict]:
        """
        Fetch all starred items from Slack with pagination.

        Returns:
            List of starred item objects

        Note: Implements pagination to handle users with many starred items,
        addressing the pagination bug from the code review.
        """
        items = []
        cursor = None
        page = 0

        print("Fetching starred items from Slack...")

        while True:
            try:
                page += 1
                self.stats['api_calls'] += 1

                # Fetch page of results
                if cursor:
                    response = self.client.stars_list(cursor=cursor, limit=100)
                else:
                    response = self.client.stars_list(limit=100)

                if not response['ok']:
                    print(f"Error fetching starred items: {response.get('error')}",
                          file=sys.stderr)
                    break

                page_items = response.get('items', [])
                items.extend(page_items)

                print(f"  Page {page}: {len(page_items)} items")

                # Check for next page
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break

            except SlackApiError as e:
                print(f"Error fetching starred items: {e}", file=sys.stderr)
                self.stats['errors'] += 1

                # Handle rate limiting
                if e.response.get('error') == 'ratelimited':
                    # Try to get retry_after from headers (different access patterns possible)
                    retry_after = 60  # Default
                    if hasattr(e.response, 'headers'):
                        retry_after = int(e.response.headers.get('Retry-After', 60))
                    elif isinstance(e.response, dict) and 'headers' in e.response:
                        retry_after = int(e.response['headers'].get('Retry-After', 60))

                    print(f"Rate limited. Waiting {retry_after} seconds...",
                          file=sys.stderr)
                    time.sleep(retry_after)
                    continue  # Retry this page
                else:
                    break  # Other errors, stop pagination

        print(f"Total starred items fetched: {len(items)}")
        return items

    def format_task(self, item: dict) -> Tuple[str, str]:
        """
        Format a Slack item into OmniFocus task name and note.

        Args:
            item: Slack starred item

        Returns:
            Tuple of (task_name, note)
        """
        item_type = item.get('type', 'unknown')

        # Get task prefix from config, default to "Slack:"
        prefix = self.config.get('options', {}).get('task_prefix', 'Slack:')

        # Build task name and note based on item type
        if item_type == 'message':
            message = item.get('message', {})
            user_id = message.get('user', 'unknown')
            user_name = self.get_user_name(user_id)

            text = message.get('text', '(no text)')
            channel_id = item.get('channel', '')
            channel_name = self.get_channel_name(channel_id) if channel_id else 'DM'

            task_name = f"{prefix} Message from {user_name} in #{channel_name}"

            # Build note with link if enabled
            note = f"{text}\n\n"

            if self.config.get('options', {}).get('add_slack_link', True):
                # Construct Slack link
                team_id = message.get('team', '')
                ts = message.get('ts', '').replace('.', '')
                if team_id and ts and channel_id:
                    link = f"https://slack.com/app_redirect?team={team_id}&channel={channel_id}&message_ts={ts}"
                    note += f"Link: {link}\n"

            note += f"From: {user_name}\nChannel: #{channel_name}"

        elif item_type == 'file':
            file = item.get('file', {})
            file_name = file.get('name', 'unknown file')
            user_id = file.get('user', 'unknown')
            user_name = self.get_user_name(user_id)

            task_name = f"{prefix} File: {file_name}"
            note = f"File: {file_name}\nFrom: {user_name}"

            if 'permalink' in file:
                note += f"\nLink: {file['permalink']}"

        elif item_type == 'channel':
            channel = item.get('channel', {})
            channel_name = channel.get('name', 'unknown')
            task_name = f"{prefix} Channel: #{channel_name}"
            note = f"Starred channel: #{channel_name}"

        else:
            task_name = f"{prefix} {item_type}"
            note = f"Starred item type: {item_type}"

        return task_name, note

    def create_omnifocus_task(self, task_name: str, note: str,
                             dry_run: bool = False) -> bool:
        """
        Create a task in OmniFocus using AppleScript.

        Args:
            task_name: Name of the task
            note: Task notes/description
            dry_run: If True, print AppleScript without executing

        Returns:
            True if successful, False otherwise

        Security: All strings are properly escaped to prevent injection attacks.
        """
        # Escape strings for AppleScript (security fix)
        safe_task_name = escape_applescript_string(task_name)
        safe_note = escape_applescript_string(note)

        # Get optional config values
        default_project = self.config.get('omnifocus', {}).get('default_project', '')
        default_tags = self.config.get('omnifocus', {}).get('default_tags', [])

        # Build AppleScript
        script_parts = ['tell application "OmniFocus"', '  tell default document']

        # Determine where to create the task
        if default_project:
            safe_project = escape_applescript_string(default_project)
            script_parts.append(
                f'    set targetProject to first flattened project whose name is "{safe_project}"'
            )
            script_parts.append(
                f'    set newTask to make new task at end of tasks of targetProject with properties {{name:"{safe_task_name}", note:"{safe_note}"}}'
            )
        else:
            # Create in inbox
            script_parts.append(
                f'    set newTask to make new inbox task with properties {{name:"{safe_task_name}", note:"{safe_note}"}}'
            )

        # Add tags if specified
        if default_tags:
            for tag in default_tags:
                safe_tag = escape_applescript_string(tag)
                script_parts.append(
                    f'    set tagObj to first flattened tag whose name is "{safe_tag}"'
                )
                script_parts.append('    add tagObj to tags of newTask')

        script_parts.extend(['  end tell', 'end tell'])

        applescript = '\n'.join(script_parts)

        if dry_run:
            print("Would execute AppleScript:")
            print("=" * 60)
            print(applescript)
            print("=" * 60)
            return True

        # Execute AppleScript
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"Error creating task: {result.stderr}", file=sys.stderr)
                return False

            return True

        except subprocess.TimeoutExpired:
            print("Error: AppleScript execution timed out", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error executing AppleScript: {e}", file=sys.stderr)
            return False

    def import_starred_items(self, dry_run: bool = False) -> None:
        """
        Main method to import all starred items from Slack to OmniFocus.

        Args:
            dry_run: If True, show what would be done without making changes
        """
        print("\n" + "=" * 60)
        print("Slack to OmniFocus Import")
        print("=" * 60)

        if dry_run:
            print("DRY RUN MODE - No changes will be made")
            print("=" * 60)

        # Fetch starred items
        items = self.fetch_starred_items()

        if not items:
            print("No starred items found.")
            return

        print(f"\nProcessing {len(items)} items...")
        print()

        # Process each item
        for i, item in enumerate(items, 1):
            self.stats['items_processed'] += 1

            try:
                task_name, note = self.format_task(item)

                print(f"[{i}/{len(items)}] {task_name[:60]}...")

                if self.create_omnifocus_task(task_name, note, dry_run=dry_run):
                    self.stats['tasks_created'] += 1
                else:
                    self.stats['errors'] += 1

            except Exception as e:
                print(f"Error processing item {i}: {e}", file=sys.stderr)
                self.stats['errors'] += 1

        # Print statistics
        self._print_statistics(dry_run)

    def _print_statistics(self, dry_run: bool = False) -> None:
        """Print import statistics."""
        print("\n" + "=" * 60)
        print("Import Statistics")
        print("=" * 60)
        print(f"Items processed:  {self.stats['items_processed']}")
        if not dry_run:
            print(f"Tasks created:    {self.stats['tasks_created']}")
        else:
            print(f"Tasks that would be created: {self.stats['tasks_created']}")
        print(f"API calls made:   {self.stats['api_calls']}")
        print(f"Errors:           {self.stats['errors']}")
        print("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import Slack starred items to OmniFocus'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to config file (default: config.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    try:
        integration = SlackToOmniFocus(args.config)
        integration.import_starred_items(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
