# Reschedule Overdue Tasks Script

An AppleScript automation tool for mass rescheduling overdue tasks within OmniFocus project hierarchies.

## Overview

This script finds all overdue tasks under a specified project (including subprojects and nested tasks) and reschedules them to a new target date. Perfect for handling backlogs after vacation, illness, or workflow changes.

## Features

- 🔍 **Hierarchical Search**: Searches entire project hierarchies, including subprojects
- 🌲 **Nested Task Support**: Handles nested tasks and subtasks at any depth
- 📅 **Flexible Date Input**: Accepts dates as "today", "tomorrow", or "YYYY-MM-DD" format
- ✅ **Smart Filtering**: Only reschedules incomplete, overdue tasks
- 📊 **Detailed Reporting**: Returns count and names of rescheduled tasks
- 🧪 **Comprehensive Tests**: Full unit test suite included

## Requirements

- macOS 10.10 or later
- OmniFocus 3 or later
- AppleScript/OSA support

## Installation

1. Clone this repository or download the script:
```bash
git clone <repository-url>
cd omnifocus-scripts/reschedule-overdue
```

2. Make the script executable (optional):
```bash
chmod +x reschedule_overdue_tasks.applescript
```

## Usage

### Basic Usage

```bash
osascript reschedule_overdue_tasks.applescript "Project Name" "2025-01-15"
```

### Examples

**Reschedule to a specific date:**
```bash
osascript reschedule_overdue_tasks.applescript "Work Projects" "2025-12-01"
```

**Reschedule to today:**
```bash
osascript reschedule_overdue_tasks.applescript "Personal" "today"
```

**Reschedule to tomorrow:**
```bash
osascript reschedule_overdue_tasks.applescript "Weekly Review" "tomorrow"
```

### From Within AppleScript

You can also load and use the handlers directly in your own scripts:

```applescript
set scriptPath to "/path/to/reschedule_overdue_tasks.applescript"
set rescheduleScript to load script POSIX file scriptPath

tell rescheduleScript
    set targetDate to current date
    set result to rescheduleOverdueTasks("My Project", targetDate)
end tell

-- Check results
if success of result is true then
    log "Rescheduled " & (count of result) & " tasks"
else
    log "Error: " & (errorMsg of result)
end if
```

## How It Works

1. **Parse Input**: Converts date string to date object
2. **Find Project**: Locates the project by name
3. **Collect Tasks**: Recursively gathers all tasks in project hierarchy
4. **Filter Overdue**: Identifies tasks with defer dates before today
5. **Reschedule**: Updates defer date for each overdue task
6. **Report**: Returns count and task names

## Script Behavior

### What Gets Rescheduled

✅ Tasks with defer dates before today
✅ Incomplete tasks only
✅ Tasks in subprojects
✅ Nested subtasks at any depth

### What Doesn't Get Rescheduled

❌ Completed tasks
❌ Tasks without defer dates
❌ Tasks with future defer dates
❌ Tasks with today's date

## Return Value

The script returns a record with the following properties:

```applescript
{
    success: boolean,        -- Whether operation succeeded
    count: integer,          -- Number of tasks rescheduled
    tasks: list of text,     -- Names of rescheduled tasks
    errorMsg: text          -- Error message if failed
}
```

### Example Success Response

```applescript
{
    success: true,
    count: 5,
    tasks: {"Task 1", "Task 2", "Task 3", "Task 4", "Task 5"},
    errorMsg: ""
}
```

### Example Error Response

```applescript
{
    success: false,
    count: 0,
    tasks: {},
    errorMsg: "Project 'XYZ' not found"
}
```

## Testing

The script includes a comprehensive unit test suite that verifies all functionality.

### Running Tests

```bash
cd tests
./run_tests.sh
```

Or run tests directly:

```bash
osascript tests/test_reschedule.applescript
```

### Test Coverage

The test suite includes:

- ✅ Date parsing (today, tomorrow, YYYY-MM-DD)
- ✅ Rescheduling overdue tasks
- ✅ Handling projects with no overdue tasks
- ✅ Error handling for nonexistent projects
- ✅ Empty project handling
- ✅ Nested task support
- ✅ Mixed overdue and current tasks

**Note**: Tests create a temporary test project in your OmniFocus database and clean it up automatically. It's recommended to run tests on a backup or when you can easily review changes.

### Test Output

```
================================================================================
Starting Test Suite: Reschedule Overdue Tasks
================================================================================

TEST: parseDate
  ✓ PASS: parseDate

TEST: rescheduleOverdueTasks with overdue tasks
  ✓ PASS: rescheduleOverdueTasks

...

================================================================================
Test Results Summary
================================================================================
Total Tests: 7
Passed: 7
Failed: 0

All tests passed! ✓
================================================================================
```

## Integration Examples

### Keyboard Maestro

Create a macro that prompts for project name and date, then runs:

```bash
osascript /path/to/reschedule_overdue_tasks.applescript "$KMVAR_ProjectName" "$KMVAR_TargetDate"
```

### Alfred Workflow

Create a workflow with input: `reschedule {query}`

Parse the query and execute the script.

### Cron Job

Schedule regular rescheduling:

```bash
# Every Monday at 9 AM, reschedule overdue tasks to today
0 9 * * 1 osascript /path/to/reschedule_overdue_tasks.applescript "Weekly Projects" "today"
```

### Shortcuts (macOS/iOS)

1. Create new Shortcut
2. Add "Run AppleScript" action
3. Use the handlers from the script
4. Add to menu bar or share sheet

## Troubleshooting

### "Project not found" error

- Verify the project name exactly matches (case-sensitive)
- Check if project is in a folder (use full project name)
- Ensure OmniFocus is running

### Tasks not rescheduling

- Verify tasks actually have defer dates set
- Check that tasks are marked as incomplete
- Ensure defer dates are actually in the past

### Permission errors

- Grant Terminal/Script Editor permission to control OmniFocus
- Check System Preferences → Security & Privacy → Automation

### Script runs slowly

- Normal for large project hierarchies
- OmniFocus database size affects performance
- Consider running during off-hours for very large projects

## Limitations

- Only reschedules tasks using **defer dates** (not due dates)
- Project name must match exactly (case-sensitive)
- Requires OmniFocus to be running
- Limited to projects accessible in default document

## Future Enhancements

Possible improvements:

- Support for due date rescheduling
- Regex pattern matching for project names
- Batch processing of multiple projects
- Interactive mode with task preview
- CSV export of rescheduled tasks
- Undo functionality

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See LICENSE file in repository root.

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review OmniFocus AppleScript documentation
- Open an issue in the repository

## Author

Created with Claude Code

## Version History

- **1.0.0** (2025-11-11): Initial release
  - Basic rescheduling functionality
  - Hierarchical project search
  - Comprehensive test suite
  - Full documentation
