# Slack to OmniFocus Integration

Automatically import your Slack saved messages (starred items) into OmniFocus inbox for task triage and management.

## Overview

This integration helps you capture important Slack messages and files as OmniFocus tasks. When you star a message in Slack, you can run this script to automatically create inbox tasks in OmniFocus, allowing you to process them as part of your regular workflow.

## Features

- ✅ Import starred/saved Slack messages as OmniFocus inbox tasks
- ✅ Import saved Slack files with links
- ✅ Preserve message context (sender, channel, original text)
- ✅ Optional: Automatically remove items from Slack after importing
- ✅ Dry-run mode to preview imports without making changes
- ✅ User and channel name resolution

## Prerequisites

- **macOS** with OmniFocus installed
- **Python 3.7+**
- **Slack workspace** with appropriate permissions
- **Slack API token** (User Token with `stars:read` and optionally `stars:write` scopes)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd omnifocus-scripts/slack-integration
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install slack-sdk
```

### 3. Create Slack App and Get API Token

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Name your app (e.g., "OmniFocus Integration") and select your workspace
4. Navigate to **"OAuth & Permissions"** in the sidebar
5. Under **"Scopes"** → **"User Token Scopes"**, add:
   - `stars:read` (required - to read saved items)
   - `stars:write` (optional - only if using `--remove-after-import`)
   - `channels:read` (recommended - to resolve channel names)
   - `users:read` (recommended - to resolve user names)
6. Scroll up and click **"Install to Workspace"**
7. Authorize the app
8. Copy the **"User OAuth Token"** (starts with `xoxp-`)

### 4. Configure the Script

```bash
# Copy the example configuration
cp config.example.json config.json

# Edit config.json and add your Slack token
nano config.json  # or use your preferred editor
```

Your `config.json` should look like:

```json
{
  "slack_token": "xoxp-your-actual-token-here",
  "omnifocus": {
    "default_project": null,
    "default_tags": []
  },
  "options": {
    "remove_after_import": false,
    "add_slack_link": true
  }
}
```

**⚠️ Important:** Never commit `config.json` to version control! It contains sensitive credentials.

## Usage

### Basic Usage

Import all saved Slack items to OmniFocus:

```bash
python slack_to_omnifocus.py
```

### Preview Mode (Dry Run)

See what would be imported without making changes:

```bash
python slack_to_omnifocus.py --dry-run
```

### Auto-Remove from Slack

Import items and remove them from Slack saved items after successful import:

```bash
python slack_to_omnifocus.py --remove-after-import
```

### Custom Configuration File

Use a different configuration file:

```bash
python slack_to_omnifocus.py --config /path/to/config.json
```

### Make Script Executable

For easier usage:

```bash
chmod +x slack_to_omnifocus.py
./slack_to_omnifocus.py
```

## How It Works

1. **Authentication**: Script uses your Slack API token to authenticate
2. **Fetch Saved Items**: Retrieves all starred/saved items from Slack using `stars.list` API
3. **Format Tasks**: Converts each item into an OmniFocus task:
   - **Task name**: First line of message or file name (prefixed with "Slack:")
   - **Task note**: Full message text, sender, channel, and permalink
4. **Import to OmniFocus**: Uses AppleScript to create inbox tasks
5. **Optional Cleanup**: Removes items from Slack if `--remove-after-import` is used

## Task Format

### For Messages

```
Task Name: Slack: [First line of message]

Task Note:
From: John Doe
Channel: #general

[Full message text]

Link: https://workspace.slack.com/archives/C123/p1234567890
```

### For Files

```
Task Name: Slack File: [Filename]

Task Note:
Shared by: Jane Smith
URL: https://files.slack.com/files-pri/T123/F456/file.pdf
```

## Automation

### Run on Schedule with Cron

Add to your crontab to run every hour:

```bash
crontab -e
```

Add this line:

```cron
0 * * * * cd /path/to/omnifocus-scripts/slack-integration && /usr/bin/python3 slack_to_omnifocus.py --remove-after-import
```

### Run on Schedule with launchd

Create `~/Library/LaunchAgents/com.user.slack-omnifocus.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.slack-omnifocus</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/slack_to_omnifocus.py</string>
        <string>--remove-after-import</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>WorkingDirectory</key>
    <string>/path/to/omnifocus-scripts/slack-integration</string>
</dict>
</plist>
```

Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.user.slack-omnifocus.plist
```

### Keyboard Shortcut with Automator/Shortcuts

1. Open **Shortcuts** app on macOS
2. Create new shortcut
3. Add **"Run Shell Script"** action
4. Enter: `cd /path/to/slack-integration && python3 slack_to_omnifocus.py`
5. Assign a keyboard shortcut

## Troubleshooting

### "slack-sdk not installed"

```bash
pip install slack-sdk
```

### "Configuration file not found"

Ensure `config.json` exists in the same directory as the script:

```bash
cp config.example.json config.json
# Then edit config.json with your token
```

### "Error fetching saved items: invalid_auth"

Your Slack token is invalid or expired. Create a new token following the installation steps.

### "Error adding task to OmniFocus"

- Ensure OmniFocus is installed and accessible
- Check that OmniFocus has permission to be controlled via AppleScript
- Try running this test AppleScript:

```bash
osascript -e 'tell application "OmniFocus" to activate'
```

### Permission Issues

If you get permission errors, go to **System Preferences** → **Security & Privacy** → **Privacy** → **Automation** and ensure Terminal (or your script runner) can control OmniFocus.

## Security Best Practices

- ✅ Keep `config.json` out of version control (use `.gitignore`)
- ✅ Never share your Slack API token
- ✅ Use the minimum required OAuth scopes
- ✅ Regularly rotate your API tokens
- ✅ Consider using environment variables instead of config files for tokens

### Using Environment Variables

You can also set your Slack token via environment variable:

```bash
export SLACK_TOKEN="xoxp-your-token"
```

Then modify `config.json` to use it:

```json
{
  "slack_token": "${SLACK_TOKEN}"
}
```

## Workflow Suggestions

### Daily Triage Workflow

1. Throughout the day, star important Slack messages that need action
2. During your daily review, run: `python slack_to_omnifocus.py --remove-after-import`
3. Process new inbox tasks in OmniFocus as part of your regular triage

### Weekly Review

1. Star messages during the week
2. Run with `--dry-run` first to review what will be imported
3. Import and clear: `python slack_to_omnifocus.py --remove-after-import`

## Testing

### Running Tests

The project includes comprehensive unit tests covering all major functionality.

#### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

Or install manually:

```bash
pip install pytest pytest-cov pytest-mock
```

#### Run All Tests

```bash
# Run all tests with verbose output
pytest test_slack_to_omnifocus.py -v

# Run with coverage report
pytest test_slack_to_omnifocus.py --cov=slack_to_omnifocus --cov-report=html

# Run specific test class
pytest test_slack_to_omnifocus.py::TestSlackAPIInteractions -v

# Run specific test method
pytest test_slack_to_omnifocus.py::TestSlackAPIInteractions::test_fetch_saved_messages -v
```

#### Using unittest (No pytest required)

```bash
python -m unittest test_slack_to_omnifocus.py
```

### Test Coverage

The test suite covers:

- ✅ **Configuration loading** - Valid/invalid configs, missing tokens
- ✅ **Slack API interactions** - Fetching messages, files, error handling
- ✅ **User and channel caching** - Minimize API calls
- ✅ **OmniFocus integration** - Task creation, AppleScript execution
- ✅ **Task formatting** - Messages, files, multiline content
- ✅ **Saved item removal** - Unstarring items after import
- ✅ **Full sync workflow** - With and without removal
- ✅ **Error handling** - API failures, subprocess errors

All tests use mocks to avoid requiring actual Slack/OmniFocus access.

### Test Structure

```
test_slack_to_omnifocus.py
├── TestConfigLoading         # Configuration file tests
├── TestSlackAPIInteractions  # Slack API calls
├── TestOmniFocusIntegration  # OmniFocus task creation
├── TestTaskFormatting        # Format conversion
├── TestRemoveSavedItems      # Slack item removal
├── TestFullSync             # End-to-end workflow
└── TestCommandLineInterface  # CLI argument parsing
```

### Writing New Tests

When adding new features:

1. Add test cases to the appropriate test class
2. Use mocking for external dependencies:
   ```python
   @patch('slack_to_omnifocus.WebClient')
   @patch('slack_to_omnifocus.subprocess.run')
   def test_new_feature(self, mock_subprocess, mock_webclient):
       # Test code here
   ```
3. Ensure tests are independent and can run in any order
4. Verify all tests pass before submitting PRs

## Contributing

Issues and pull requests welcome! Please ensure:
- Code follows PEP 8 style guidelines
- Add tests for new features (see Testing section above)
- All existing tests pass: `pytest test_slack_to_omnifocus.py`
- Update documentation

## License

See LICENSE file in repository root.

## Support

For issues and questions:
- Check [Issues](../../issues) for existing problems
- Create a new issue with detailed information
- Include error messages and your Python version

## Related Resources

- [Slack API Documentation](https://api.slack.com/docs)
- [OmniFocus AppleScript Guide](https://support.omnigroup.com/omnifocus-applescript/)
- [OmniFocus URL Schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
