#!/usr/bin/env python3
"""
Unit tests for Slack to OmniFocus integration script.

Run tests with:
    python -m pytest test_slack_to_omnifocus.py -v
    or
    python -m unittest test_slack_to_omnifocus.py
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

# Import the module to test
import slack_to_omnifocus
from slack_to_omnifocus import SlackToOmniFocus


class TestConfigLoading(unittest.TestCase):
    """Test configuration file loading."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'slack_token': 'xoxp-test-token-123',
            'omnifocus': {
                'default_project': None,
                'default_tags': []
            }
        }

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            config_path = f.name

        try:
            with patch('slack_to_omnifocus.WebClient'):
                integration = SlackToOmniFocus(config_path=config_path)
                self.assertEqual(integration.slack_token, 'xoxp-test-token-123')
        finally:
            os.unlink(config_path)

    def test_missing_config_file(self):
        """Test error handling when config file is missing."""
        with self.assertRaises(FileNotFoundError):
            SlackToOmniFocus(config_path='/nonexistent/config.json')

    def test_missing_slack_token(self):
        """Test error handling when Slack token is missing from config."""
        config_without_token = {'omnifocus': {}}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_without_token, f)
            config_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                SlackToOmniFocus(config_path=config_path)
            self.assertIn('token', str(context.exception).lower())
        finally:
            os.unlink(config_path)

    def test_invalid_json_config(self):
        """Test error handling with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            config_path = f.name

        try:
            with self.assertRaises(json.JSONDecodeError):
                SlackToOmniFocus(config_path=config_path)
        finally:
            os.unlink(config_path)


class TestSlackAPIInteractions(unittest.TestCase):
    """Test Slack API interactions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'slack_token': 'xoxp-test-token-123',
            'omnifocus': {}
        }

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            self.config_path = f.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    @patch('slack_to_omnifocus.WebClient')
    def test_fetch_saved_messages(self, mock_webclient):
        """Test fetching saved messages from Slack."""
        # Mock Slack API response
        mock_client = MagicMock()
        mock_response = {
            'items': [
                {
                    'type': 'message',
                    'channel': 'C123',
                    'message': {
                        'text': 'Test message',
                        'user': 'U456',
                        'ts': '1234567890.123456',
                        'permalink': 'https://slack.com/archives/C123/p1234567890'
                    }
                }
            ]
        }
        mock_client.stars_list.return_value = mock_response
        mock_client.users_info.return_value = {
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        }
        mock_client.conversations_info.return_value = {
            'channel': {'name': 'general'}
        }
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)
        saved_items = integration.fetch_saved_items()

        self.assertEqual(len(saved_items), 1)
        self.assertEqual(saved_items[0]['type'], 'message')
        self.assertEqual(saved_items[0]['text'], 'Test message')
        self.assertEqual(saved_items[0]['user'], 'Test User')
        self.assertEqual(saved_items[0]['channel'], '#general')

    @patch('slack_to_omnifocus.WebClient')
    def test_fetch_saved_files(self, mock_webclient):
        """Test fetching saved files from Slack."""
        mock_client = MagicMock()
        mock_response = {
            'items': [
                {
                    'type': 'file',
                    'file': {
                        'title': 'Test Document.pdf',
                        'name': 'document.pdf',
                        'user': 'U789',
                        'permalink': 'https://files.slack.com/files/T123/F456',
                        'created': '1234567890'
                    }
                }
            ]
        }
        mock_client.stars_list.return_value = mock_response
        mock_client.users_info.return_value = {
            'user': {'real_name': 'File Sharer', 'name': 'filesharer'}
        }
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)
        saved_items = integration.fetch_saved_items()

        self.assertEqual(len(saved_items), 1)
        self.assertEqual(saved_items[0]['type'], 'file')
        self.assertEqual(saved_items[0]['text'], 'Test Document.pdf')
        self.assertEqual(saved_items[0]['user'], 'File Sharer')
        self.assertEqual(saved_items[0]['url'], 'https://files.slack.com/files/T123/F456')

    @patch('slack_to_omnifocus.WebClient')
    def test_slack_api_error_handling(self, mock_webclient):
        """Test handling of Slack API errors."""
        from slack_sdk.errors import SlackApiError

        mock_client = MagicMock()
        mock_error_response = {'error': 'invalid_auth'}
        mock_client.stars_list.side_effect = SlackApiError(
            message='Invalid authentication',
            response=mock_error_response
        )
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)
        saved_items = integration.fetch_saved_items()

        # Should return empty list on error
        self.assertEqual(len(saved_items), 0)

    @patch('slack_to_omnifocus.WebClient')
    def test_user_name_caching(self, mock_webclient):
        """Test that user names are cached to reduce API calls."""
        mock_client = MagicMock()
        mock_response = {
            'items': [
                {
                    'type': 'message',
                    'channel': 'C123',
                    'message': {'text': 'Message 1', 'user': 'U456', 'ts': '123'}
                },
                {
                    'type': 'message',
                    'channel': 'C123',
                    'message': {'text': 'Message 2', 'user': 'U456', 'ts': '124'}
                }
            ]
        }
        mock_client.stars_list.return_value = mock_response
        mock_client.users_info.return_value = {
            'user': {'real_name': 'Cached User', 'name': 'cacheduser'}
        }
        mock_client.conversations_info.return_value = {
            'channel': {'name': 'general'}
        }
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)
        saved_items = integration.fetch_saved_items()

        # users_info should only be called once due to caching
        self.assertEqual(mock_client.users_info.call_count, 1)
        self.assertEqual(len(saved_items), 2)
        self.assertEqual(saved_items[0]['user'], 'Cached User')
        self.assertEqual(saved_items[1]['user'], 'Cached User')


class TestOmniFocusIntegration(unittest.TestCase):
    """Test OmniFocus task creation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'slack_token': 'xoxp-test-token-123',
            'omnifocus': {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            self.config_path = f.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    @patch('slack_to_omnifocus.WebClient')
    @patch('slack_to_omnifocus.subprocess.run')
    def test_add_task_to_omnifocus(self, mock_subprocess, mock_webclient):
        """Test adding a task to OmniFocus."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        integration = SlackToOmniFocus(config_path=self.config_path)
        result = integration.add_to_omnifocus(
            task_name='Test Task',
            note='Test note content'
        )

        self.assertTrue(result)
        mock_subprocess.assert_called_once()

        # Verify AppleScript was called with correct command
        call_args = mock_subprocess.call_args
        self.assertEqual(call_args[0][0][0], 'osascript')
        self.assertEqual(call_args[0][0][1], '-e')
        self.assertIn('Test Task', call_args[0][0][2])
        self.assertIn('Test note content', call_args[0][0][2])

    @patch('slack_to_omnifocus.WebClient')
    @patch('slack_to_omnifocus.subprocess.run')
    def test_add_task_escapes_quotes(self, mock_subprocess, mock_webclient):
        """Test that quotes are properly escaped in task names and notes."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        integration = SlackToOmniFocus(config_path=self.config_path)
        result = integration.add_to_omnifocus(
            task_name='Task with "quotes"',
            note='Note with "quotes" and \\backslash'
        )

        self.assertTrue(result)

        # Verify escaping in AppleScript
        call_args = mock_subprocess.call_args[0][0][2]
        self.assertIn('\\"', call_args)
        self.assertIn('\\\\', call_args)

    @patch('slack_to_omnifocus.WebClient')
    @patch('slack_to_omnifocus.subprocess.run')
    def test_add_task_failure(self, mock_subprocess, mock_webclient):
        """Test handling of OmniFocus task creation failure."""
        from subprocess import CalledProcessError

        mock_subprocess.side_effect = CalledProcessError(
            returncode=1,
            cmd=['osascript'],
            stderr='Error: OmniFocus not running'
        )

        integration = SlackToOmniFocus(config_path=self.config_path)
        result = integration.add_to_omnifocus('Test Task', 'Test note')

        self.assertFalse(result)


class TestTaskFormatting(unittest.TestCase):
    """Test formatting of Slack items as OmniFocus tasks."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'slack_token': 'xoxp-test-token-123',
            'omnifocus': {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            self.config_path = f.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    @patch('slack_to_omnifocus.WebClient')
    def test_format_message_task(self, mock_webclient):
        """Test formatting a message as an OmniFocus task."""
        integration = SlackToOmniFocus(config_path=self.config_path)

        message_item = {
            'type': 'message',
            'text': 'This is a test message\nWith multiple lines',
            'user': 'John Doe',
            'channel': '#general',
            'timestamp': '1234567890.123456',
            'permalink': 'https://slack.com/archives/C123/p1234567890'
        }

        task_name, note = integration.format_task(message_item)

        self.assertEqual(task_name, 'Slack: This is a test message')
        self.assertIn('From: John Doe', note)
        self.assertIn('Channel: #general', note)
        self.assertIn('This is a test message', note)
        self.assertIn('With multiple lines', note)
        self.assertIn('https://slack.com/archives/C123/p1234567890', note)

    @patch('slack_to_omnifocus.WebClient')
    def test_format_long_message_truncates_title(self, mock_webclient):
        """Test that long messages are truncated in task name."""
        integration = SlackToOmniFocus(config_path=self.config_path)

        long_text = 'A' * 150
        message_item = {
            'type': 'message',
            'text': long_text,
            'user': 'Test User',
            'channel': '#test',
            'timestamp': '123',
            'permalink': 'https://slack.com/test'
        }

        task_name, note = integration.format_task(message_item)

        # Task name should be truncated to ~100 chars plus "Slack: " prefix
        self.assertLess(len(task_name), 120)
        self.assertTrue(task_name.startswith('Slack: A'))

        # Full text should be in note
        self.assertIn(long_text, note)

    @patch('slack_to_omnifocus.WebClient')
    def test_format_file_task(self, mock_webclient):
        """Test formatting a file as an OmniFocus task."""
        integration = SlackToOmniFocus(config_path=self.config_path)

        file_item = {
            'type': 'file',
            'text': 'Important Document.pdf',
            'url': 'https://files.slack.com/files/T123/F456/document.pdf',
            'user': 'Jane Smith',
            'timestamp': '1234567890'
        }

        task_name, note = integration.format_task(file_item)

        self.assertEqual(task_name, 'Slack File: Important Document.pdf')
        self.assertIn('Shared by: Jane Smith', note)
        self.assertIn('https://files.slack.com/files/T123/F456/document.pdf', note)

    @patch('slack_to_omnifocus.WebClient')
    def test_format_multiline_message(self, mock_webclient):
        """Test formatting multiline messages."""
        integration = SlackToOmniFocus(config_path=self.config_path)

        message_item = {
            'type': 'message',
            'text': 'Line 1\nLine 2\nLine 3',
            'user': 'Test User',
            'channel': '#test',
            'timestamp': '123',
            'permalink': 'https://slack.com/test'
        }

        task_name, note = integration.format_task(message_item)

        # Task name should only have first line
        self.assertEqual(task_name, 'Slack: Line 1')

        # Note should have all lines
        self.assertIn('Line 1', note)
        self.assertIn('Line 2', note)
        self.assertIn('Line 3', note)


class TestRemoveSavedItems(unittest.TestCase):
    """Test removing items from Slack saved items."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'slack_token': 'xoxp-test-token-123',
            'omnifocus': {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            self.config_path = f.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    @patch('slack_to_omnifocus.WebClient')
    def test_remove_message_from_saved(self, mock_webclient):
        """Test removing a message from saved items."""
        mock_client = MagicMock()
        mock_client.stars_remove.return_value = {'ok': True}
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)

        item = {
            'type': 'message',
            'item': {
                'type': 'message',
                'channel': 'C123',
                'message': {'ts': '1234567890.123456'}
            }
        }

        result = integration.remove_saved_item(item)

        self.assertTrue(result)
        mock_client.stars_remove.assert_called_once_with(
            channel='C123',
            timestamp='1234567890.123456'
        )

    @patch('slack_to_omnifocus.WebClient')
    def test_remove_file_from_saved(self, mock_webclient):
        """Test removing a file from saved items."""
        mock_client = MagicMock()
        mock_client.stars_remove.return_value = {'ok': True}
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)

        item = {
            'type': 'file',
            'item': {
                'type': 'file',
                'file': {'id': 'F123456'}
            }
        }

        result = integration.remove_saved_item(item)

        self.assertTrue(result)
        mock_client.stars_remove.assert_called_once_with(file='F123456')

    @patch('slack_to_omnifocus.WebClient')
    def test_remove_saved_item_api_error(self, mock_webclient):
        """Test handling of API errors when removing saved items."""
        from slack_sdk.errors import SlackApiError

        mock_client = MagicMock()
        mock_error_response = {'error': 'not_starred'}
        mock_client.stars_remove.side_effect = SlackApiError(
            message='Item not starred',
            response=mock_error_response
        )
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)

        item = {
            'type': 'message',
            'item': {
                'type': 'message',
                'channel': 'C123',
                'message': {'ts': '1234567890.123456'}
            }
        }

        result = integration.remove_saved_item(item)

        self.assertFalse(result)


class TestFullSync(unittest.TestCase):
    """Test the full sync workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'slack_token': 'xoxp-test-token-123',
            'omnifocus': {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config, f)
            self.config_path = f.name

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_path):
            os.unlink(self.config_path)

    @patch('slack_to_omnifocus.WebClient')
    @patch('slack_to_omnifocus.subprocess.run')
    def test_sync_without_removal(self, mock_subprocess, mock_webclient):
        """Test syncing items without removing from Slack."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        mock_client = MagicMock()
        mock_response = {
            'items': [
                {
                    'type': 'message',
                    'channel': 'C123',
                    'message': {
                        'text': 'Test message 1',
                        'user': 'U456',
                        'ts': '123',
                        'permalink': 'https://slack.com/1'
                    }
                },
                {
                    'type': 'message',
                    'channel': 'C456',
                    'message': {
                        'text': 'Test message 2',
                        'user': 'U789',
                        'ts': '124',
                        'permalink': 'https://slack.com/2'
                    }
                }
            ]
        }
        mock_client.stars_list.return_value = mock_response
        mock_client.users_info.side_effect = [
            {'user': {'real_name': 'User 1', 'name': 'user1'}},
            {'user': {'real_name': 'User 2', 'name': 'user2'}}
        ]
        mock_client.conversations_info.side_effect = [
            {'channel': {'name': 'channel1'}},
            {'channel': {'name': 'channel2'}}
        ]
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)
        integration.sync(remove_after_import=False)

        # Verify tasks were created
        self.assertEqual(mock_subprocess.call_count, 2)

        # Verify items were NOT removed from Slack
        mock_client.stars_remove.assert_not_called()

    @patch('slack_to_omnifocus.WebClient')
    @patch('slack_to_omnifocus.subprocess.run')
    def test_sync_with_removal(self, mock_subprocess, mock_webclient):
        """Test syncing items with removal from Slack."""
        mock_subprocess.return_value = MagicMock(returncode=0)

        mock_client = MagicMock()
        mock_response = {
            'items': [
                {
                    'type': 'message',
                    'channel': 'C123',
                    'message': {
                        'text': 'Test message',
                        'user': 'U456',
                        'ts': '123',
                        'permalink': 'https://slack.com/1'
                    }
                }
            ]
        }
        mock_client.stars_list.return_value = mock_response
        mock_client.users_info.return_value = {
            'user': {'real_name': 'Test User', 'name': 'testuser'}
        }
        mock_client.conversations_info.return_value = {
            'channel': {'name': 'general'}
        }
        mock_client.stars_remove.return_value = {'ok': True}
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)
        integration.sync(remove_after_import=True)

        # Verify task was created
        self.assertEqual(mock_subprocess.call_count, 1)

        # Verify item was removed from Slack
        mock_client.stars_remove.assert_called_once()

    @patch('slack_to_omnifocus.WebClient')
    def test_sync_with_no_items(self, mock_webclient):
        """Test sync when there are no saved items."""
        mock_client = MagicMock()
        mock_response = {'items': []}
        mock_client.stars_list.return_value = mock_response
        mock_webclient.return_value = mock_client

        integration = SlackToOmniFocus(config_path=self.config_path)

        # Should complete without error
        integration.sync(remove_after_import=False)

        # No API calls should be made for empty list
        mock_client.stars_remove.assert_not_called()


class TestCommandLineInterface(unittest.TestCase):
    """Test command-line argument parsing and execution."""

    @patch('slack_to_omnifocus.SlackToOmniFocus')
    def test_main_with_dry_run(self, mock_integration_class):
        """Test main function with dry-run flag."""
        mock_instance = MagicMock()
        mock_instance.fetch_saved_items.return_value = [
            {
                'type': 'message',
                'text': 'Test message',
                'user': 'Test User',
                'channel': '#test',
                'timestamp': '123',
                'permalink': 'https://slack.com/test'
            }
        ]
        mock_instance.format_task.return_value = ('Task Name', 'Task Note')
        mock_integration_class.return_value = mock_instance

        with patch('sys.argv', ['script.py', '--dry-run']):
            slack_to_omnifocus.main()

        # Verify sync was not called in dry-run mode
        mock_instance.sync.assert_not_called()

        # Verify items were fetched and formatted
        mock_instance.fetch_saved_items.assert_called_once()
        mock_instance.format_task.assert_called_once()


if __name__ == '__main__':
    unittest.main()
