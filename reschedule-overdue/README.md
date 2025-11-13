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

### ⚠️ IMPORTANT WARNING ⚠️

**Tests modify your ACTUAL OmniFocus database!**

While tests create a temporary project and clean it up automatically:
- Test failures may leave test data in your OmniFocus database
- Tests interact with the live OmniFocus application
- **STRONGLY RECOMMENDED**: Run tests only when:
  - You have a recent backup of your OmniFocus database
  - You can easily review and remove any leftover test data
  - OmniFocus sync is paused (to avoid syncing test data)

Consider running tests in a separate OmniFocus database or user account for complete isolation.

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

- ✅ Date parsing (today, tomorrow, YYYY-MM-DD) with validation
- ✅ Rescheduling overdue tasks
- ✅ Handling projects with no overdue tasks
- ✅ Error handling for nonexistent projects
- ✅ Empty project handling
- ✅ Nested task support
- ✅ Mixed overdue and current tasks
- ✅ Invalid date format rejection (e.g., "2025-13-45")

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

## Performance Considerations

### Expected Performance

The script uses a recursive approach to traverse project hierarchies. Performance varies based on project structure:

**Small Projects (< 50 tasks)**
- Execution time: < 1 second
- No noticeable delay

**Medium Projects (50-200 tasks)**
- Execution time: 1-5 seconds
- Acceptable for interactive use

**Large Projects (200-500 tasks)**
- Execution time: 5-15 seconds
- May show brief processing delay

**Very Large Projects (500+ tasks)**
- Execution time: 15+ seconds
- Consider running during off-peak times
- AppleScript performance limitations may become noticeable

### Performance Factors

Performance depends on:
- **Project depth**: Deeply nested subprojects add overhead
- **Task nesting**: Multiple levels of subtasks slow traversal
- **OmniFocus database size**: Larger databases have slower queries
- **System resources**: Available CPU and memory

### Optimization Tips

For better performance:
- Run the script when OmniFocus is not busy syncing
- Close other applications to free system resources
- Process one project at a time rather than entire folder hierarchies
- Consider splitting very large projects into smaller ones

### Technical Note

The recursive algorithm in `getAllTasksInProject` (lines 134-161) examines every task and subtask. While this ensures complete coverage, AppleScript's performance characteristics make it slower than native code for large datasets.

If you regularly work with projects containing 1000+ tasks, expect execution times of 30+ seconds. Consider alternative approaches (batch processing overnight, project restructuring) for such cases.

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
