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
import time
import logging
from typing import List, Dict, Any, Tuple, Set

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("Error: slack-sdk not installed. Install with: pip install slack-sdk")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


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
        self.slack_token = self._get_slack_token()

        if not self.slack_token:
            raise ValueError("Slack token not found in configuration, keychain, or 1Password")

        # Get configuration options with defaults
        options = self.config.get('options', {})
        self.pagination_delay = options.get('pagination_delay', 0.5)
        self.batch_fetch = options.get('batch_fetch_users_channels', True)
        self.max_retries = options.get('max_api_retries', 3)

        self.client = WebClient(token=self.slack_token)
        self.user_cache = {}
        self.channel_cache = {}

    def _get_slack_token(self) -> str:
        """
        Get Slack token from configuration, keychain, or 1Password.

        Supports three methods:
        1. Direct token in config: {"slack_token": "xoxp-..."}
        2. macOS Keychain: {"slack_token_source": "keychain:<service>:<account>"}
        3. 1Password CLI: {"slack_token_source": "1password:<vault>/<item>/<field>"}

        Returns:
            Slack API token
        """
        # Check for direct token first
        if 'slack_token' in self.config and self.config['slack_token']:
            token = self.config['slack_token']
            # Skip if it's a placeholder
            if not token.startswith('xoxp-your-'):
                return token

        # Check for token source (keychain or 1password)
        token_source = self.config.get('slack_token_source', '')

        if token_source.startswith('keychain:'):
            return self._get_token_from_keychain(token_source)
        elif token_source.startswith('1password:'):
            return self._get_token_from_1password(token_source)

        return ''

    def _get_token_from_keychain(self, source: str) -> str:
        """
        Retrieve token from macOS Keychain.

        Args:
            source: Format "keychain:<service>:<account>"

        Returns:
            Token from keychain, or empty string if not found/invalid
        """
        try:
            parts = source.split(':', 2)
            if len(parts) != 3:
                logger.error(f"Invalid keychain source format: {source}")
                return ''

            service, account = parts[1], parts[2]

            result = subprocess.run(
                ['security', 'find-generic-password', '-s', service, '-a', account, '-w'],
                capture_output=True,
                text=True,
                check=True
            )
            token = result.stdout.strip()

            # Validate token is not empty
            if not token:
                logger.error(f"Empty token retrieved from keychain service '{service}'")
                return ''

            logger.info(f"Retrieved token from keychain service '{service}'")
            return token

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to retrieve token from keychain: {e.stderr}")
            return ''
        except FileNotFoundError:
            logger.error("macOS security command not found. Keychain access requires macOS.")
            return ''

    def _get_token_from_1password(self, source: str) -> str:
        """
        Retrieve token from 1Password CLI.

        Args:
            source: Format "1password:<vault>/<item>/<field>" or "1password:<reference>"

        Returns:
            Token from 1Password, or empty string if not found/invalid
        """
        try:
            # Remove "1password:" prefix
            reference = source.replace('1password:', '', 1)

            result = subprocess.run(
                ['op', 'read', reference],
                capture_output=True,
                text=True,
                check=True
            )
            token = result.stdout.strip()

            # Validate token is not empty
            if not token:
                logger.error("Empty token retrieved from 1Password")
                return ''

            logger.info("Retrieved token from 1Password")
            return token

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to retrieve token from 1Password: {e.stderr}")
            logger.error("Make sure 'op' CLI is installed and you're signed in to 1Password")
            return ''
        except FileNotFoundError:
            logger.error("1Password CLI (op) not found. Install from: https://1password.com/downloads/command-line/")
            return ''

    @staticmethod
    def _escape_applescript_string(s: str) -> str:
        """
        Escape string for safe use in AppleScript.

        Handles backslashes, quotes, newlines, carriage returns, tabs,
        backticks, and dollar signs to prevent AppleScript injection vulnerabilities.

        Args:
            s: String to escape

        Returns:
            Safely escaped string
        """
        # Order matters: escape backslashes first, then other special characters
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        s = s.replace('`', '\\`')
        s = s.replace('$', '\\$')
        return s

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please copy config.example.json to config.json and add your Slack token."
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _api_call_with_retry(self, api_func, **kwargs):
        """
        Call Slack API with automatic retry on rate limiting.

        Args:
            api_func: The API function to call
            **kwargs: Arguments to pass to the API function

        Returns:
            API response

        Raises:
            SlackApiError: If the call fails after all retries
        """
        for attempt in range(self.max_retries):
            try:
                return api_func(**kwargs)
            except SlackApiError as e:
                error_code = e.response.get('error', '') if e.response else ''

                if error_code == 'rate_limited':
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(retry_after)
                else:
                    # Not a rate limit error, raise immediately
                    raise

        # If we've exhausted retries
        logger.error(f"Failed after {self.max_retries} retries due to rate limiting")
        raise SlackApiError("Rate limit exceeded", response={'error': 'rate_limited'})

    def _batch_fetch_users(self, user_ids: Set[str]) -> None:
        """
        Batch fetch user information to populate cache.

        Args:
            user_ids: Set of user IDs to fetch
        """
        if not user_ids:
            return

        logger.info(f"Batch fetching information for {len(user_ids)} users...")
        for user_id in user_ids:
            if user_id in self.user_cache or user_id == 'unknown':
                continue

            try:
                response = self._api_call_with_retry(self.client.users_info, user=user_id)
                user = response['user']
                name = user.get('real_name') or user.get('name') or user_id
                self.user_cache[user_id] = name
            except SlackApiError as e:
                logger.warning(f"Could not fetch user info for {user_id}: {e}")
                self.user_cache[user_id] = user_id

    def _batch_fetch_channels(self, channel_ids: Set[str]) -> None:
        """
        Batch fetch channel information to populate cache.

        Args:
            channel_ids: Set of channel IDs to fetch
        """
        if not channel_ids:
            return

        logger.info(f"Batch fetching information for {len(channel_ids)} channels...")
        for channel_id in channel_ids:
            if channel_id in self.channel_cache or channel_id == 'unknown':
                continue

            try:
                response = self._api_call_with_retry(self.client.conversations_info, channel=channel_id)
                name = response['channel'].get('name') or channel_id
                self.channel_cache[channel_id] = f"#{name}"
            except SlackApiError as e:
                logger.warning(f"Could not fetch channel info for {channel_id}: {e}")
                self.channel_cache[channel_id] = channel_id

    def _get_user_name(self, user_id: str) -> str:
        """Get user's display name from user ID."""
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            response = self._api_call_with_retry(self.client.users_info, user=user_id)
            user = response['user']
            name = user.get('real_name') or user.get('name') or user_id
            self.user_cache[user_id] = name
            return name
        except SlackApiError as e:
            logger.warning(f"Could not fetch user info for {user_id}: {e}")
            return user_id

    def _get_channel_name(self, channel_id: str) -> str:
        """Get channel name from channel ID."""
        if channel_id in self.channel_cache:
            return self.channel_cache[channel_id]

        try:
            response = self._api_call_with_retry(self.client.conversations_info, channel=channel_id)
            name = response['channel'].get('name') or channel_id
            self.channel_cache[channel_id] = f"#{name}"
            return self.channel_cache[channel_id]
        except SlackApiError as e:
            logger.warning(f"Could not fetch channel info for {channel_id}: {e}")
            return channel_id

    def fetch_saved_items(self) -> List[Dict[str, Any]]:
        """
        Fetch all saved/starred items from Slack with pagination support.

        Returns:
            List of saved items with metadata.
        """
        logger.info("Fetching saved items from Slack...")
        saved_items = []
        raw_items = []

        try:
            # Fetch starred items (Slack's "saved" items) with pagination
            cursor = None
            page_count = 0

            while True:
                page_count += 1
                # Add delay between pages to avoid rate limiting
                if cursor:
                    time.sleep(self.pagination_delay)

                response = self._api_call_with_retry(self.client.stars_list, cursor=cursor, limit=100)
                items = response.get('items', [])
                raw_items.extend(items)

                # Check for more pages
                cursor = response.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break

                logger.info(f"  Fetched page {page_count}, continuing...")

            logger.info(f"Found {len(raw_items)} raw items across {page_count} page(s)")

            # Batch fetch users and channels if enabled
            if self.batch_fetch and raw_items:
                user_ids = set()
                channel_ids = set()

                for item in raw_items:
                    if item.get('type') == 'message':
                        message = item.get('message', {})
                        if message.get('user'):
                            user_ids.add(message.get('user'))
                        if item.get('channel'):
                            channel_ids.add(item.get('channel'))
                    elif item.get('type') == 'file':
                        file_data = item.get('file', {})
                        if file_data.get('user'):
                            user_ids.add(file_data.get('user'))

                # Batch fetch before processing items
                self._batch_fetch_users(user_ids)
                self._batch_fetch_channels(channel_ids)

            # Now process items with cached user/channel info
            for item in raw_items:
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

            logger.info(f"Processed {len(saved_items)} items successfully")
            return saved_items

        except SlackApiError as e:
            logger.error(f"Error fetching saved items: {e}")
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
        # Escape strings for safe AppleScript execution
        task_name = self._escape_applescript_string(task_name)
        note = self._escape_applescript_string(note)

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
            logger.error(f"Error adding task to OmniFocus: {e.stderr}")
            return False

    def format_task(self, item: Dict[str, Any]) -> Tuple[str, str]:
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
            logger.error(f"Error removing saved item: {e}")
            return False

    def sync(self, remove_after_import: bool = False):
        """
        Main sync function: fetch saved items and add to OmniFocus.

        Args:
            remove_after_import: If True, remove items from Slack after importing
        """
        saved_items = self.fetch_saved_items()

        if not saved_items:
            logger.info("No saved items to import")
            return

        logger.info(f"\nImporting {len(saved_items)} items to OmniFocus...")

        success_count = 0
        fail_count = 0

        for i, item in enumerate(saved_items, 1):
            task_name, note = self.format_task(item)
            logger.info(f"[{i}/{len(saved_items)}] Adding: {task_name[:60]}...")

            if self.add_to_omnifocus(task_name, note):
                success_count += 1

                if remove_after_import:
                    if self.remove_saved_item(item):
                        logger.info(f"  ✓ Added and removed from Slack")
                    else:
                        logger.warning(f"  ✓ Added (failed to remove from Slack)")
                else:
                    logger.info(f"  ✓ Added")
            else:
                fail_count += 1
                logger.error(f"  ✗ Failed")

        logger.info(f"\n{'='*60}")
        logger.info(f"Import complete: {success_count} succeeded, {fail_count} failed")
        logger.info(f"{'='*60}")


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
            logger.info("DRY RUN MODE - No tasks will be added to OmniFocus\n")
            items = sync_tool.fetch_saved_items()
            for i, item in enumerate(items, 1):
                task_name, note = sync_tool.format_task(item)
                logger.info(f"\n[{i}] {task_name}")
                logger.info(f"    {note[:100]}...")
        else:
            sync_tool.sync(remove_after_import=args.remove_after_import)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
