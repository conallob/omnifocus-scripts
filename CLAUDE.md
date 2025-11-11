# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains automation scripts for OmniFocus, Apple's task management application. Scripts integrate OmniFocus with various external services and automate workflow tasks.

## Technology Context

### OmniFocus Automation Approaches

OmniFocus supports several automation methods:

1. **AppleScript** - The primary scripting language for OmniFocus automation on macOS
   - Use JXA (JavaScript for Automation) or traditional AppleScript
   - Access OmniFocus objects: projects, tasks, contexts, folders
   - Scripts typically saved as `.applescript` or `.scpt` files

2. **URL Schemes** - For cross-platform and web integrations
   - Format: `omnifocus:///add?name=Task&note=Details`
   - Useful for integrating with web services and shortcuts

3. **Omni Automation** - JavaScript-based automation framework
   - Cross-platform (macOS, iOS, iPadOS)
   - Modern alternative to AppleScript
   - Uses `.omnijs` extension

### OmniFocus Object Model

Key objects in OmniFocus scripting:
- `document` - The main OmniFocus database
- `project` - Container for related tasks
- `task` - Individual action items
- `folder` - Container for projects
- `tag` (formerly context) - Categorical labels for tasks
- `perspective` - Saved views of tasks

## Development Guidelines

### Script Organization

- Group related scripts by function or integration (e.g., `email/`, `calendar/`, `github/`)
- Include documentation at the top of each script explaining purpose and usage
- For AppleScript, include handler functions for reusability

### Testing OmniFocus Scripts

**Manual Testing:**
```bash
# Run AppleScript from command line
osascript path/to/script.applescript

# Compile AppleScript to check syntax
osacompile -o output.scpt input.applescript
```

**Important:** Always test scripts on non-critical OmniFocus data first, as they can modify your task database.

### Common Script Patterns

**Creating a new task:**
```applescript
tell application "OmniFocus"
    tell default document
        make new inbox task with properties {name: "Task Name", note: "Details"}
    end tell
end tell
```

**Querying tasks:**
```applescript
tell application "OmniFocus"
    tell default document
        set taskList to every task of every project whose completed is false
    end tell
end tell
```

## GitHub Integration

This repository uses Claude Code Actions for automated PR reviews and interactive assistance:
- Mention `@claude` in issues or PR comments for help
- Automatic PR reviews run on all pull requests
- See `.github/workflows/README.md` for configuration details

## Running Scripts

### AppleScript Execution
```bash
# Execute directly
osascript script.applescript

# With arguments
osascript script.applescript "arg1" "arg2"
```

### Setting Up Automation
- Scripts can be triggered via macOS shortcuts, cron jobs, or automation tools like Keyboard Maestro
- For scheduled automation, use `launchd` or cron with osascript

## OmniFocus API Resources

- OmniFocus AppleScript documentation: Help → Automation in the OmniFocus menu
- Omni Automation documentation: https://omni-automation.com/omnifocus/
- OmniFocus URL scheme reference: https://support.omnigroup.com/omnifocus-url-schemes/
