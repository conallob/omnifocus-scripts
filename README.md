# omnifocus-scripts

Various scripts for automating and integrating OmniFocus with external services and workflows.

## Available Integrations

### Slack Integration
Import your Slack saved messages (starred items) directly into OmniFocus inbox for task triage.

- 📁 Location: `slack-integration/`
- 📖 Documentation: [slack-integration/README.md](slack-integration/README.md)
- 🚀 Quick start: Star messages in Slack, run the script, and find them in OmniFocus inbox

**Features:**
- Automatic import of starred Slack messages
- Preserves context (sender, channel, message content)
- Optional auto-removal after import
- Dry-run mode for preview

See the [Slack Integration README](slack-integration/README.md) for full setup instructions.

### Reschedule Selection

Reschedule whatever task(s) are currently selected in OmniFocus to today,
tomorrow, or the next working day — built for one-keystroke triage via a
global hotkey (e.g. a dedicated keyboard layer + skhd).

- 📁 Location: `reschedule-selection/`
- 📖 Documentation: [reschedule-selection/README.md](reschedule-selection/README.md)
- 🚀 Quick start: select a task in OmniFocus, run `osascript reschedule_selection.applescript today`

## Project Structure

```
omnifocus-scripts/
├── slack-integration/         # Slack to OmniFocus sync tool
│   ├── slack_to_omnifocus.py
│   ├── config.example.json
│   ├── requirements.txt
│   └── README.md
├── reschedule-overdue/        # Reschedule overdue tasks (by project, defer date)
│   ├── reschedule_overdue_tasks.applescript
│   ├── examples/
│   └── README.md
├── reschedule-selection/      # Reschedule the current selection (due date)
│   ├── reschedule_selection.applescript
│   └── README.md
├── .github/
│   ├── workflows/             # CI/CD workflows
│   ├── RELEASE.md            # Release process documentation
│   └── homebrew-formula-template.rb
├── CLAUDE.md                  # Project guidelines for Claude Code
├── LICENSE                    # BSD-3-Clause
└── README.md                  # This file
```

## Installation

### Via Homebrew (Recommended for macOS)

```bash
# Add the tap
brew tap conallob/tap

# Install omnifocus-scripts
brew install omnifocus-scripts

# Scripts will be available at:
# /opt/homebrew/share/omnifocus-scripts (Apple Silicon)
# /usr/local/share/omnifocus-scripts (Intel)
```

### Manual Installation

Clone or download this repository and use the scripts directly:

```bash
git clone https://github.com/conallob/omnifocus-scripts.git
cd omnifocus-scripts
```

## General Usage

Each integration includes its own README with detailed setup and usage instructions. Navigate to the specific integration directory for more information.

After Homebrew installation, scripts are located at `$(brew --prefix)/share/omnifocus-scripts/`

## Contributing

Contributions welcome! Each integration should:
- Include a detailed README
- Provide example configuration files
- Follow security best practices (no hardcoded credentials)
- Include error handling and helpful messages

## Resources

- [OmniFocus AppleScript Guide](https://support.omnigroup.com/omnifocus-applescript/)
- [OmniFocus URL Schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
- [Omni Automation Documentation](https://omni-automation.com/omnifocus/)

## License

See [LICENSE](LICENSE) file for details.
