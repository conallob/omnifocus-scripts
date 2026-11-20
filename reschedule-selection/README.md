# Reschedule Selection Script

An AppleScript automation tool for rescheduling the due date of whatever
task(s) are currently selected in OmniFocus — built for one-keystroke
triage, typically bound to a global hotkey.

## Overview

Unlike [`reschedule-overdue`](../reschedule-overdue), which sweeps an entire
project hierarchy for overdue tasks, this script acts on the current
*selection* in the front OmniFocus document window. Select one or more
tasks (in the inbox, a perspective, or a project), run the script, and
their due date moves to today, tomorrow, or the next working day.

## Features

- 🎯 **Selection-based**: Acts on whatever is currently selected, no project name required
- 📅 **Three targets**: `today`, `tomorrow`, `next-workday` (skips Sat/Sun)
- 🕐 **Time-of-day preserved**: Keeps each task's existing due time; defaults to 5:00 PM for tasks with no due date yet
- ⌨️ **Hotkey-friendly**: Designed to be driven by a global hotkey daemon (e.g. [skhd](https://github.com/koekeishiya/skhd)) rather than typed interactively

## Requirements

- macOS 10.10 or later
- OmniFocus 3 or later
- AppleScript/OSA support

## Usage

```bash
osascript reschedule_selection.applescript today
osascript reschedule_selection.applescript tomorrow
osascript reschedule_selection.applescript next-workday
```

Select the task(s) in OmniFocus first — the script acts on the front
window's current selection and returns an error if nothing is selected.

## Return Value

```applescript
{
    success: boolean,        -- Whether the operation succeeded
    count: integer,          -- Number of tasks rescheduled
    tasks: list of text,     -- Names of rescheduled tasks
    errorMsg: text           -- Error message if failed
}
```

## Integration: a dedicated keyboard layer + skhd

This script was built to pair with a physical keyboard layer dedicated to
OmniFocus actions (see
[conallob/dotfiles](https://github.com/conallob/dotfiles)'s
`Chrysalis_Keyboardio-Model-100_layout.schema.md` for the Keyboardio Model
100 layout that sends `F13`/`F14`/`F15` from that layer). Bind those keys
with [skhd](https://github.com/koekeishiya/skhd):

```
# ~/.config/skhd/skhdrc
f13 : osascript /path/to/reschedule_selection.applescript today
f14 : osascript /path/to/reschedule_selection.applescript tomorrow
f15 : osascript /path/to/reschedule_selection.applescript next-workday
```

After installing via Homebrew (see the top-level README), the script lives
at `$(brew --prefix)/share/omnifocus-scripts/reschedule-selection/reschedule_selection.applescript`.

### Other integrations

**Keyboard Maestro:**
```bash
osascript /path/to/reschedule_selection.applescript today
```
bound to any hotkey or palette button of your choice.

**Alfred Workflow:** a keyword `reschedule {query}` that maps `today` /
`tomorrow` / `next-workday` straight through to the script.

## Troubleshooting

### "Nothing selected in the front OmniFocus window"

- Make sure an OmniFocus document window is frontmost and at least one
  row is selected before running the script.

### Permission errors

- Grant Terminal/the hotkey daemon permission to control OmniFocus via
  System Settings → Privacy & Security → Automation (and Accessibility,
  for `skhd` itself).

## Limitations

- Only reschedules **due dates** (not defer dates) — the opposite of
  `reschedule-overdue`, which only touches defer dates.
- Operates on the front document window's selection; it does not accept a
  project or task name.

## Author

Created with Claude Code

## Version History

- **1.0.0** (2026-11-20): Initial release
