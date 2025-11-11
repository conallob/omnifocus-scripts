# Slack to OmniFocus Integration

Import your Slack starred items as tasks in OmniFocus with a single command.

## Features

- ✅ **Secure**: Prevents AppleScript injection attacks with proper string escaping
- ✅ **Complete**: Handles pagination for users with hundreds of starred items
- ✅ **Reliable**: Automatically handles Slack API rate limiting with retry logic
- ✅ **Smart Caching**: Minimizes API calls by caching user and channel names
- ✅ **Configurable**: Customize projects, tags, and task formatting
- ✅ **Dry Run Mode**: Preview changes before making them
- ✅ **Well Tested**: Comprehensive test suite with 20+ test cases

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Requirements

- macOS 10.10 or later
- Python 3.7 or later
- OmniFocus 3 or later
- Slack workspace access with starred items

## Installation

### 1. Install Python Dependencies

```bash
cd slack-integration
pip3 install -r requirements.txt
```

### 2. Get Your Slack Token

1. Go to https://api.slack.com/apps
2. Create a new app or select an existing one
3. Navigate to "OAuth & Permissions"
4. Add the following **User Token Scopes**:
   - `stars:read` - Read starred items
   - `users:read` - Read user information
   - `channels:read` - Read channel information
   - `groups:read` - Read private channel information
5. Install the app to your workspace
6. Copy the **User OAuth Token** (starts with `xoxp-`)

### 3. Configure the Integration

```bash
cp config.example.json config.json
# Edit config.json and add your Slack token
```

## Configuration

Edit `config.json` with your preferences:

```json
{
  "slack": {
    "token": "xoxp-your-slack-user-token-here"
  },
  "omnifocus": {
    "default_project": "Slack Tasks",
    "default_tags": ["slack", "from-slack"]
  },
  "options": {
    "add_slack_link": true,
    "task_prefix": "Slack:"
  }
}
```

### Configuration Options

#### `slack.token` (required)
Your Slack user token (starts with `xoxp-`).

#### `omnifocus.default_project` (optional)
The OmniFocus project where tasks will be created. If empty or omitted, tasks are created in the Inbox.

#### `omnifocus.default_tags` (optional)
Array of tags to add to each task. Tags must already exist in OmniFocus.

Example: `["slack", "to-review"]`

#### `options.add_slack_link` (optional, default: true)
If `true`, adds a direct link to the Slack message in the task notes.

#### `options.task_prefix` (optional, default: "Slack:")
Prefix added to task names. Set to empty string `""` to disable.

## Usage

### Basic Import

Import all starred items:

```bash
python3 slack_to_omnifocus.py
```

### Dry Run Mode

Preview what would be imported without making changes:

```bash
python3 slack_to_omnifocus.py --dry-run
```

This is useful for:
- Checking your configuration
- Seeing the exact AppleScript that would be executed
- Verifying how tasks will be formatted

### Custom Config File

Use a different configuration file:

```bash
python3 slack_to_omnifocus.py --config my-config.json
```

### Example Session

```bash
$ python3 slack_to_omnifocus.py

============================================================
Slack to OmniFocus Import
============================================================

Fetching starred items from Slack...
  Page 1: 87 items
  Page 2: 45 items
Total starred items fetched: 132

Processing 132 items...

[1/132] Slack: Message from John in #general...
[2/132] Slack: File: Q4-Report.pdf...
[3/132] Slack: Message from Sarah in #marketing...
...

============================================================
Import Statistics
============================================================
Items processed:  132
Tasks created:    132
API calls made:   265
Errors:           0
============================================================
```

## How It Works

### 1. Fetch Starred Items

The script fetches all your starred items from Slack using the `stars.list` API endpoint. It automatically handles pagination, so even if you have hundreds of starred items, they'll all be imported.

### 2. Resolve Names

For each item, the script:
- Looks up user display names (instead of showing user IDs)
- Resolves channel names (instead of showing channel IDs)
- Caches results to minimize API calls

### 3. Format Tasks

Each starred item is converted into an OmniFocus task:

**Message items:**
```
Task Name: Slack: Message from John in #general
Note:
Can you review the Q4 numbers?

Link: https://slack.com/app_redirect?team=...
From: John
Channel: #general
```

**File items:**
```
Task Name: Slack: File: Q4-Report.pdf
Note:
File: Q4-Report.pdf
From: Sarah
Link: https://files.slack.com/...
```

**Channel items:**
```
Task Name: Slack: Channel: #random
Note:
Starred channel: #random
```

### 4. Create OmniFocus Tasks

The script generates and executes AppleScript to create tasks in OmniFocus. All strings are properly escaped to prevent injection attacks.

## Testing

### Run All Tests

```bash
cd tests
python3 -m pytest test_slack_to_omnifocus.py -v
```

### Run Specific Test Categories

```bash
# Security tests
python3 -m pytest test_slack_to_omnifocus.py::TestAppleScriptEscaping -v

# Pagination tests
python3 -m pytest test_slack_to_omnifocus.py::TestPagination -v

# Rate limiting tests
python3 -m pytest test_slack_to_omnifocus.py::TestRateLimiting -v
```

### Test Coverage

```bash
python3 -m pytest --cov=slack_to_omnifocus --cov-report=html
```

### What's Tested

- ✅ AppleScript injection prevention (newlines, quotes, backslashes)
- ✅ Configuration loading and validation
- ✅ User and channel name caching
- ✅ Pagination with multiple pages
- ✅ Rate limiting with automatic retry
- ✅ Error handling for API failures
- ✅ Task formatting for all item types
- ✅ Very long message texts (10,000+ characters)
- ✅ Messages with many newlines
- ✅ OmniFocus task creation
- ✅ Dry run mode
- ✅ End-to-end workflow

## Security

### AppleScript Injection Prevention

This script properly escapes all user-provided strings before inserting them into AppleScript:

- **Backslashes** (`\`) → `\\\\`
- **Double quotes** (`"`) → `\\"`
- **Newlines** (`\n`) → `\\n`
- **Carriage returns** (`\r`) → `\\r`

This prevents malicious Slack messages from breaking out of string context and executing arbitrary code.

**Example of protected code:**

```python
# Malicious input attempting code execution
malicious = 'task"\n  do shell script "rm -rf /"\n  set x to "'

# After escaping, it's just text
safe = escape_applescript_string(malicious)
# Result: 'task\\"\\n  do shell script \\"rm -rf /\\"\\n  set x to \\"'
```

### Token Security

- Never commit `config.json` to version control (it's in `.gitignore`)
- Use user tokens with minimal required scopes
- Rotate tokens if compromised

## Troubleshooting

### "Module not found" error

Install dependencies:
```bash
pip3 install -r requirements.txt
```

### "Invalid auth" error from Slack

- Verify your token starts with `xoxp-`
- Check that you're using a **user token**, not a bot token
- Ensure the token has required scopes: `stars:read`, `users:read`, `channels:read`
- Try regenerating the token in Slack API settings

### Tasks not appearing in OmniFocus

- Ensure OmniFocus is running
- Check if `default_project` exists (if specified)
- Look in the OmniFocus Inbox if no project is specified
- Review error messages in the terminal output

### "Project not found" error

The project name in `omnifocus.default_project` must match exactly (case-sensitive). Either:
- Create the project in OmniFocus first, or
- Leave `default_project` empty to create tasks in the Inbox

### "Tag not found" error

All tags in `omnifocus.default_tags` must exist in OmniFocus before running the script. Create them first in OmniFocus → Tags.

### Rate limiting errors

The script automatically handles rate limiting by:
- Waiting the amount of time specified by Slack's `Retry-After` header
- Retrying the request
- Continuing with the import

If rate limiting persists:
- Run the import during off-peak hours
- Reduce the number of starred items
- Wait a few minutes between runs

### Script is slow

Performance tips:
- The script makes 1-2 API calls per starred item (more if names aren't cached)
- First run will be slower as it builds the cache
- Subsequent runs reuse cached user/channel names
- Large imports (100+ items) may take several minutes

### AppleScript errors

Common AppleScript issues:
- **"OmniFocus got an error: Can't get document 1"** - OmniFocus isn't running
- **"Can't get project..."** - Project doesn't exist or name doesn't match
- **"Can't get tag..."** - Tag doesn't exist in OmniFocus
- **Timeout errors** - OmniFocus is busy; try again

Grant permissions:
1. System Preferences → Security & Privacy → Automation
2. Ensure Terminal/Script Editor can control OmniFocus

## Performance Considerations

### API Calls

The script minimizes API calls through:
- **Pagination**: Fetches 100 items per page
- **Caching**: User and channel names cached in memory
- **Batching**: All items fetched before processing begins

Typical API call count:
- 1 call per page of starred items (~100 items each)
- 1 call per unique user (cached)
- 1 call per unique channel (cached)

Example: 250 starred items from 15 users in 8 channels:
- ~3 pages of results = 3 calls
- 15 unique users = 15 calls
- 8 unique channels = 8 calls
- **Total: ~26 API calls**

### Rate Limits

Slack's rate limits (as of 2024):
- Tier 3 methods: 50+ requests per minute
- The script stays well within limits for normal usage
- Automatic retry on rate limit errors

## Architecture

### Code Structure

```
slack-integration/
├── slack_to_omnifocus.py    # Main script
├── config.example.json        # Example configuration
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes secrets
├── README.md                  # This file
└── tests/
    └── test_slack_to_omnifocus.py  # Comprehensive tests
```

### Key Functions

- `escape_applescript_string()` - Prevents injection attacks
- `fetch_starred_items()` - Handles pagination and rate limiting
- `get_user_name()` / `get_channel_name()` - Cached lookups
- `format_task()` - Converts Slack items to task format
- `create_omnifocus_task()` - Executes AppleScript safely

## Limitations

- Only imports **starred** items (not all messages)
- Requires OmniFocus to be running
- User token scopes required (not suitable for bot-only apps)
- Slack links may expire if message/file is deleted
- Maximum AppleScript string length (~32KB for very long messages)

## Future Enhancements

Possible improvements:
- [ ] Support for Slack threads
- [ ] Incremental sync (only import new items)
- [ ] Two-way sync (complete in OmniFocus → unstar in Slack)
- [ ] Custom task templates
- [ ] Support for saved messages (in addition to stars)
- [ ] Export to CSV/JSON
- [ ] GUI configuration tool
- [ ] Scheduled automatic imports

## Contributing

Contributions welcome! Areas for improvement:
- Additional test coverage
- Support for more item types
- Performance optimizations
- Documentation improvements

Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Changelog

### Version 1.0.0 (2025-11-11)

Initial release with:
- ✅ Secure AppleScript string escaping
- ✅ Full pagination support
- ✅ Rate limiting handling
- ✅ Comprehensive test suite (20+ tests)
- ✅ User/channel name caching
- ✅ Dry run mode
- ✅ Configurable projects, tags, and formatting
- ✅ Support for messages, files, and channels

## Author

Created with Claude Code

---

**Need Help?**

- 📖 Check the [Troubleshooting](#troubleshooting) section
- 🐛 Open an issue for bugs
- 💡 Submit a PR for improvements
- 📚 Review the test suite for usage examples
