"""
Comprehensive unit tests for Slack to OmniFocus integration.

Tests cover:
- AppleScript injection prevention
- Pagination handling
- Rate limiting
- Long message texts
- Error handling
- All core functionality
"""

import json
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch, call
import pytest
from slack_sdk.errors import SlackApiError

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from slack_to_omnifocus import (
    SlackToOmniFocus,
    escape_applescript_string
)


class TestAppleScriptEscaping:
    """Test AppleScript string escaping for security."""

    def test_escape_basic_string(self):
        """Test escaping of basic strings."""
        assert escape_applescript_string("hello") == "hello"

    def test_escape_backslashes(self):
        """Test escaping of backslashes."""
        result = escape_applescript_string("path\\to\\file")
        assert "\\\\\\\\" in result

    def test_escape_quotes(self):
        """Test escaping of double quotes."""
        result = escape_applescript_string('He said "hello"')
        assert '\\\\"' in result

    def test_escape_newlines(self):
        """Test escaping of newlines (SECURITY FIX)."""
        result = escape_applescript_string("line1\nline2")
        assert "\\\\n" in result
        assert "\n" not in result

    def test_escape_carriage_returns(self):
        """Test escaping of carriage returns (SECURITY FIX)."""
        result = escape_applescript_string("line1\rline2")
        assert "\\\\r" in result
        assert "\r" not in result

    def test_escape_combined_special_chars(self):
        """Test escaping of multiple special characters."""
        input_str = 'Path: "C:\\Users\\test"\nNew line\rCarriage return'
        result = escape_applescript_string(input_str)

        # Verify all special chars are escaped
        assert "\n" not in result
        assert "\r" not in result
        assert "\\\\n" in result
        assert "\\\\r" in result
        assert '\\\\"' in result

    def test_escape_injection_attempt(self):
        """Test prevention of AppleScript injection attacks."""
        # Attempt to break out of string and run malicious code
        malicious = 'task"\n  do shell script "rm -rf /"\n  set x to "'
        result = escape_applescript_string(malicious)

        # Verify the newlines are escaped, preventing code execution
        assert "\n" not in result
        assert "\\\\n" in result

    def test_escape_none(self):
        """Test handling of None values."""
        assert escape_applescript_string(None) == ""

    def test_escape_empty_string(self):
        """Test handling of empty strings."""
        assert escape_applescript_string("") == ""

    def test_escape_unicode(self):
        """Test handling of unicode characters."""
        result = escape_applescript_string("Hello 世界 🌍")
        assert "Hello" in result
        # Unicode should pass through
        assert "世界" in result
        assert "🌍" in result


class TestConfiguration:
    """Test configuration loading and validation."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {"default_project": "Test"},
            "options": {"add_slack_link": True}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            integration = SlackToOmniFocus(config_path)
            assert integration.config['slack']['token'] == "xoxp-test-token"
        finally:
            os.unlink(config_path)

    def test_missing_config_file(self):
        """Test error handling for missing config file."""
        with pytest.raises(FileNotFoundError):
            SlackToOmniFocus("/nonexistent/config.json")

    def test_invalid_config_missing_token(self):
        """Test error handling for config missing required fields."""
        config_data = {"omnifocus": {}}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required config field"):
                SlackToOmniFocus(config_path)
        finally:
            os.unlink(config_path)


class TestSlackAPIIntegration:
    """Test Slack API integration with mocking."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {},
            "options": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def integration(self, mock_config):
        """Create a SlackToOmniFocus instance for testing."""
        with patch('slack_to_omnifocus.WebClient'):
            return SlackToOmniFocus(mock_config)

    def test_get_user_name_success(self, integration):
        """Test successful user name lookup."""
        integration.client.users_info = Mock(return_value={
            'ok': True,
            'user': {
                'profile': {'display_name': 'Test User'},
                'real_name': 'Test Real',
                'name': 'testuser'
            }
        })

        name = integration.get_user_name('U123')
        assert name == 'Test User'
        assert 'U123' in integration.user_cache

    def test_get_user_name_cached(self, integration):
        """Test that user names are cached."""
        integration.user_cache['U123'] = 'Cached User'
        integration.client.users_info = Mock()

        name = integration.get_user_name('U123')
        assert name == 'Cached User'
        integration.client.users_info.assert_not_called()

    def test_get_user_name_api_error(self, integration):
        """Test error handling in user name lookup."""
        integration.client.users_info = Mock(
            side_effect=SlackApiError("Error", response={'error': 'user_not_found'})
        )

        name = integration.get_user_name('U999')
        assert name == 'U999'  # Falls back to user ID

    def test_get_channel_name_success(self, integration):
        """Test successful channel name lookup."""
        integration.client.conversations_info = Mock(return_value={
            'ok': True,
            'channel': {'name': 'general'}
        })

        name = integration.get_channel_name('C123')
        assert name == 'general'
        assert 'C123' in integration.channel_cache

    def test_get_channel_name_cached(self, integration):
        """Test that channel names are cached."""
        integration.channel_cache['C123'] = 'cached-channel'
        integration.client.conversations_info = Mock()

        name = integration.get_channel_name('C123')
        assert name == 'cached-channel'
        integration.client.conversations_info.assert_not_called()


class TestPagination:
    """Test pagination handling for large datasets."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {},
            "options": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def integration(self, mock_config):
        """Create a SlackToOmniFocus instance for testing."""
        with patch('slack_to_omnifocus.WebClient'):
            return SlackToOmniFocus(mock_config)

    def test_fetch_starred_items_single_page(self, integration):
        """Test fetching starred items with single page."""
        integration.client.stars_list = Mock(return_value={
            'ok': True,
            'items': [{'type': 'message', 'message': {'text': 'test'}}],
            'response_metadata': {}
        })

        items = integration.fetch_starred_items()
        assert len(items) == 1
        integration.client.stars_list.assert_called_once()

    def test_fetch_starred_items_multiple_pages(self, integration):
        """Test fetching starred items with pagination (PAGINATION FIX)."""
        # Simulate 3 pages of results
        page1 = {
            'ok': True,
            'items': [{'type': 'message', 'message': {'text': f'msg{i}'}} for i in range(100)],
            'response_metadata': {'next_cursor': 'cursor1'}
        }
        page2 = {
            'ok': True,
            'items': [{'type': 'message', 'message': {'text': f'msg{i}'}} for i in range(100, 200)],
            'response_metadata': {'next_cursor': 'cursor2'}
        }
        page3 = {
            'ok': True,
            'items': [{'type': 'message', 'message': {'text': f'msg{i}'}} for i in range(200, 250)],
            'response_metadata': {}
        }

        integration.client.stars_list = Mock(side_effect=[page1, page2, page3])

        items = integration.fetch_starred_items()

        # Should have fetched all 250 items across 3 pages
        assert len(items) == 250
        assert integration.client.stars_list.call_count == 3

        # Verify cursor was passed correctly
        calls = integration.client.stars_list.call_args_list
        assert calls[0] == call(limit=100)
        assert calls[1] == call(cursor='cursor1', limit=100)
        assert calls[2] == call(cursor='cursor2', limit=100)

    def test_fetch_starred_items_empty(self, integration):
        """Test fetching when no starred items exist."""
        integration.client.stars_list = Mock(return_value={
            'ok': True,
            'items': [],
            'response_metadata': {}
        })

        items = integration.fetch_starred_items()
        assert len(items) == 0


class TestRateLimiting:
    """Test rate limiting handling."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {},
            "options": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def integration(self, mock_config):
        """Create a SlackToOmniFocus instance for testing."""
        with patch('slack_to_omnifocus.WebClient'):
            return SlackToOmniFocus(mock_config)

    @patch('slack_to_omnifocus.time.sleep')
    def test_rate_limit_handling(self, mock_sleep, integration):
        """Test that rate limiting is handled with retry (RATE LIMITING FIX)."""
        # First call: rate limited
        rate_limit_error = SlackApiError(
            "Rate limited",
            response={
                'error': 'ratelimited',
                'headers': {'Retry-After': '5'}
            }
        )

        # Second call: success
        success_response = {
            'ok': True,
            'items': [{'type': 'message', 'message': {'text': 'test'}}],
            'response_metadata': {}
        }

        integration.client.stars_list = Mock(
            side_effect=[rate_limit_error, success_response]
        )

        items = integration.fetch_starred_items()

        # Should have retried and succeeded
        assert len(items) == 1
        assert integration.client.stars_list.call_count == 2
        mock_sleep.assert_called_once_with(5)

    def test_non_rate_limit_error(self, integration):
        """Test that non-rate-limit errors don't retry infinitely."""
        integration.client.stars_list = Mock(
            side_effect=SlackApiError("Other error", response={'error': 'other'})
        )

        items = integration.fetch_starred_items()

        # Should fail and return empty list
        assert len(items) == 0
        assert integration.client.stars_list.call_count == 1


class TestTaskFormatting:
    """Test task formatting for different item types."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {},
            "options": {"add_slack_link": True, "task_prefix": "Slack:"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def integration(self, mock_config):
        """Create a SlackToOmniFocus instance for testing."""
        with patch('slack_to_omnifocus.WebClient'):
            instance = SlackToOmniFocus(mock_config)
            # Mock the name lookup methods
            instance.get_user_name = Mock(return_value='Test User')
            instance.get_channel_name = Mock(return_value='general')
            return instance

    def test_format_message_task(self, integration):
        """Test formatting of message items."""
        item = {
            'type': 'message',
            'message': {
                'text': 'Hello world',
                'user': 'U123',
                'team': 'T123',
                'ts': '1234567890.123456'
            },
            'channel': 'C123'
        }

        task_name, note = integration.format_task(item)

        assert 'Slack:' in task_name
        assert 'Test User' in task_name
        assert 'general' in task_name
        assert 'Hello world' in note

    def test_format_file_task(self, integration):
        """Test formatting of file items."""
        item = {
            'type': 'file',
            'file': {
                'name': 'document.pdf',
                'user': 'U123',
                'permalink': 'https://files.slack.com/...'
            }
        }

        task_name, note = integration.format_task(item)

        assert 'Slack:' in task_name
        assert 'document.pdf' in task_name
        assert 'document.pdf' in note
        assert 'https://files.slack.com/' in note

    def test_format_channel_task(self, integration):
        """Test formatting of channel items."""
        item = {
            'type': 'channel',
            'channel': {'name': 'random'}
        }

        task_name, note = integration.format_task(item)

        assert 'Slack:' in task_name
        assert 'random' in task_name

    def test_format_unknown_task(self, integration):
        """Test formatting of unknown item types."""
        item = {'type': 'unknown_type'}

        task_name, note = integration.format_task(item)

        assert 'Slack:' in task_name
        assert 'unknown_type' in task_name


class TestLongMessages:
    """Test handling of very long message texts (EDGE CASE)."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {},
            "options": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def integration(self, mock_config):
        """Create a SlackToOmniFocus instance for testing."""
        with patch('slack_to_omnifocus.WebClient'):
            instance = SlackToOmniFocus(mock_config)
            instance.get_user_name = Mock(return_value='Test User')
            instance.get_channel_name = Mock(return_value='general')
            return instance

    def test_very_long_message(self, integration):
        """Test handling of very long message texts."""
        # Create a message with 10,000 characters
        long_text = "A" * 10000

        item = {
            'type': 'message',
            'message': {
                'text': long_text,
                'user': 'U123'
            },
            'channel': 'C123'
        }

        task_name, note = integration.format_task(item)

        # Should handle long text without errors
        assert len(note) >= 10000
        assert "A" * 100 in note  # Verify content is there

    def test_message_with_many_newlines(self, integration):
        """Test handling of messages with many newlines."""
        text_with_newlines = "Line 1\nLine 2\nLine 3\n" * 100

        item = {
            'type': 'message',
            'message': {
                'text': text_with_newlines,
                'user': 'U123'
            },
            'channel': 'C123'
        }

        task_name, note = integration.format_task(item)

        # Should handle many newlines
        assert 'Line 1' in note
        assert note.count('Line') >= 100


class TestOmniFocusIntegration:
    """Test OmniFocus task creation."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {
                "default_project": "Slack Tasks",
                "default_tags": ["slack", "todo"]
            },
            "options": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @pytest.fixture
    def integration(self, mock_config):
        """Create a SlackToOmniFocus instance for testing."""
        with patch('slack_to_omnifocus.WebClient'):
            return SlackToOmniFocus(mock_config)

    @patch('slack_to_omnifocus.subprocess.run')
    def test_create_task_success(self, mock_run, integration):
        """Test successful task creation."""
        mock_run.return_value = Mock(returncode=0, stderr='')

        result = integration.create_omnifocus_task("Test Task", "Test Note")

        assert result is True
        mock_run.assert_called_once()

        # Verify AppleScript was called with osascript
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'osascript'
        assert call_args[1] == '-e'

    @patch('slack_to_omnifocus.subprocess.run')
    def test_create_task_with_special_characters(self, mock_run, integration):
        """Test task creation with special characters."""
        mock_run.return_value = Mock(returncode=0, stderr='')

        task_name = 'Task with "quotes" and \n newlines'
        note = 'Note with \\ backslashes and \r carriage returns'

        result = integration.create_omnifocus_task(task_name, note)

        assert result is True

        # Get the AppleScript that was executed
        applescript = mock_run.call_args[0][0][2]

        # Verify special characters are escaped
        assert "\n" not in applescript or "\\\\n" in applescript
        assert '\\\\"' in applescript

    @patch('slack_to_omnifocus.subprocess.run')
    def test_create_task_dry_run(self, mock_run, integration):
        """Test dry run mode doesn't execute AppleScript."""
        result = integration.create_omnifocus_task(
            "Test Task", "Test Note", dry_run=True
        )

        assert result is True
        mock_run.assert_not_called()

    @patch('slack_to_omnifocus.subprocess.run')
    def test_create_task_failure(self, mock_run, integration):
        """Test handling of task creation failure."""
        mock_run.return_value = Mock(returncode=1, stderr='Error message')

        result = integration.create_omnifocus_task("Test Task", "Test Note")

        assert result is False

    @patch('slack_to_omnifocus.subprocess.run')
    def test_create_task_timeout(self, mock_run, integration):
        """Test handling of AppleScript timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('osascript', 30)

        result = integration.create_omnifocus_task("Test Task", "Test Note")

        assert result is False


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file for testing."""
        config_data = {
            "slack": {"token": "xoxp-test-token"},
            "omnifocus": {},
            "options": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            config_path = f.name

        yield config_path
        os.unlink(config_path)

    @patch('slack_to_omnifocus.subprocess.run')
    @patch('slack_to_omnifocus.WebClient')
    def test_full_import_workflow(self, mock_client_class, mock_run, mock_config):
        """Test complete import workflow."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock starred items
        mock_client.stars_list.return_value = {
            'ok': True,
            'items': [
                {
                    'type': 'message',
                    'message': {'text': 'Test message', 'user': 'U123'},
                    'channel': 'C123'
                }
            ],
            'response_metadata': {}
        }

        # Mock user/channel lookups
        mock_client.users_info.return_value = {
            'ok': True,
            'user': {'profile': {'display_name': 'Test User'}}
        }
        mock_client.conversations_info.return_value = {
            'ok': True,
            'channel': {'name': 'general'}
        }

        # Mock successful task creation
        mock_run.return_value = Mock(returncode=0, stderr='')

        # Run import
        integration = SlackToOmniFocus(mock_config)
        integration.import_starred_items(dry_run=False)

        # Verify workflow executed
        assert integration.stats['items_processed'] == 1
        assert integration.stats['tasks_created'] == 1
        mock_run.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
