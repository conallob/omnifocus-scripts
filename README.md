# OmniFocus Scripts

Various scripts for automating and integrating various parts of my OmniFocus workflow.

## Scripts

### 1. Mass Reschedule Overdue Tasks (`reschedule_overdue_tasks.js`)

Finds all overdue tasks under a specified project hierarchy and reschedules them to a specified date.

**Features:**
- Recursively finds all overdue tasks in a project and its subprojects
- Supports multiple date formats (absolute dates, relative dates)
- Shows preview of tasks before rescheduling
- Requires confirmation before making changes

**Requirements:**
- macOS with OmniFocus installed
- JavaScript for Automation (JXA) support

**Usage:**
```bash
# Make the script executable
chmod +x reschedule_overdue_tasks.js

# Reschedule to a specific date (YYYY-MM-DD format)
osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "2025-11-15"

# Reschedule to today
osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "today"

# Reschedule to tomorrow
osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "tomorrow"

# Reschedule to 3 days from now
osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "+3d"
```

**Examples:**
```bash
# Reschedule all overdue tasks in "Work" project to December 1st
osascript -l JavaScript reschedule_overdue_tasks.js "Work" "2025-12-01"

# Reschedule all overdue tasks in "Personal" project to today
osascript -l JavaScript reschedule_overdue_tasks.js "Personal" "today"
```

---

### 2. Slack Saved Messages to OmniFocus (`slack_to_omnifocus.py`)

Imports messages from your Slack "Saved Items" into your OmniFocus Inbox, with optional removal from Slack after import.

**Features:**
- Fetches saved messages, files, and file comments from Slack
- Adds them to OmniFocus Inbox with formatted titles and notes
- Preserves message metadata (timestamp, permalink, etc.)
- Optionally removes items from Slack after successful import
- Dry-run mode to preview before importing

**Requirements:**
- Python 3.6+
- `slack-sdk` library
- macOS with OmniFocus installed
- Slack User OAuth Token

**Setup:**

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a Slack App and get your User OAuth Token:
   - Go to https://api.slack.com/apps
   - Create a new app or select an existing one
   - Navigate to "OAuth & Permissions"
   - Add the following User Token Scopes:
     - `stars:read` (required - to read saved items)
     - `stars:write` (optional - to remove saved items)
   - Install the app to your workspace
   - Copy the "User OAuth Token" (starts with `xoxp-`)

3. Configure your token:
   ```bash
   # Option 1: Copy the example file and edit it
   cp .env.example .env
   # Edit .env and add your token

   # Option 2: Export as environment variable
   export SLACK_USER_TOKEN=xoxp-your-token-here
   ```

**Usage:**
```bash
# Make the script executable
chmod +x slack_to_omnifocus.py

# Preview what would be imported (dry-run)
python3 slack_to_omnifocus.py --dry-run

# Import saved messages to OmniFocus
python3 slack_to_omnifocus.py

# Import and remove from Slack after successful import
python3 slack_to_omnifocus.py --remove

# Limit the number of items to process
python3 slack_to_omnifocus.py --limit 10
```

**Command-line Options:**
- `--dry-run`: Show what would be imported without making changes
- `--remove`: Remove items from Slack after adding to OmniFocus
- `--limit N`: Only process the first N saved items (default: 50)

**Examples:**
```bash
# Preview the first 5 saved messages
python3 slack_to_omnifocus.py --dry-run --limit 5

# Import up to 20 saved messages
python3 slack_to_omnifocus.py --limit 20

# Import all saved messages and remove them from Slack
python3 slack_to_omnifocus.py --remove
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/omnifocus-scripts.git
cd omnifocus-scripts

# Make scripts executable
chmod +x reschedule_overdue_tasks.js
chmod +x slack_to_omnifocus.py

# Install Python dependencies (for Slack script)
pip install -r requirements.txt
```

## Security Notes

- Never commit your `.env` file or expose your Slack token
- The `.gitignore` file is configured to exclude sensitive files
- Keep your Slack token secure and rotate it if compromised

## Troubleshooting

### Reschedule Script
- **"Project not found"**: Ensure the project name matches exactly (case-sensitive)
- **Permission denied**: Run `chmod +x reschedule_overdue_tasks.js`
- **OmniFocus not responding**: Make sure OmniFocus is running

### Slack Import Script
- **"SLACK_USER_TOKEN not found"**: Check your `.env` file or environment variable
- **"missing_scope" error**: Add the required OAuth scopes in your Slack App settings
- **"not_authed" error**: Your token may have expired; generate a new one
- **Import fails silently**: Check that OmniFocus is running and accepting AppleScript commands

## License

See [LICENSE](LICENSE) file for details.
