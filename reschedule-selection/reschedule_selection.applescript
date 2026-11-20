#!/usr/bin/osascript

(*
================================================================================
Reschedule the Current OmniFocus Selection
================================================================================

PURPOSE:
Sets the due date of whichever task(s) are currently selected in the front
OmniFocus document window. Designed to be bound to a global hotkey (e.g. via
skhd + a dedicated keyboard layer) for one-keystroke rescheduling while
triaging the inbox or a perspective.

USAGE:
	osascript reschedule_selection.applescript today
	osascript reschedule_selection.applescript tomorrow
	osascript reschedule_selection.applescript next-workday

PARAMETERS:
	1. target - One of "today", "tomorrow", "next-workday"
	            ("next-workday" skips Saturday/Sunday, landing on Monday)

BEHAVIOR:
	The existing time-of-day on each task's due date is preserved; tasks
	with no due date yet default to 5:00 PM.

RETURNS:
	A record containing:
		- success (boolean): Whether the operation succeeded
		- count (integer): Number of tasks rescheduled
		- tasks (list): Names of rescheduled tasks
		- errorMsg (text): Error message if failed

REQUIREMENTS:
	- OmniFocus 3 or later, with a document window open and a selection made
	- macOS with AppleScript support

AUTHOR: Claude Code
CREATED: 2026-11-20
================================================================================
*)

on run argv
	if (count of argv) < 1 then
		return {success:false, count:0, tasks:{}, errorMsg:"Usage: reschedule_selection.applescript <today|tomorrow|next-workday>"}
	end if

	set target to item 1 of argv

	try
		set dayOffset to my offsetForTarget(target)
		set targetDate to (current date) + (dayOffset * days)
		set result to my rescheduleSelection(targetDate)
		return result
	on error errMsg number errNum
		return {success:false, count:0, tasks:{}, errorMsg:errMsg & " (" & errNum & ")"}
	end try
end run

(*
================================================================================
HANDLER: offsetForTarget
================================================================================
Translates a target keyword into a day offset from today.

PARAMETERS:
	target (text) - "today", "tomorrow", or "next-workday"

RETURNS:
	integer - Days to add to the current date
*)
on offsetForTarget(target)
	if target is "today" then
		return 0
	else if target is "tomorrow" then
		return 1
	else if target is "next-workday" then
		set wd to weekday of (current date)
		if wd is Friday then
			return 3
		else if wd is Saturday then
			return 2
		else
			return 1
		end if
	else
		error "Invalid target. Use 'today', 'tomorrow', or 'next-workday'"
	end if
end offsetForTarget

(*
================================================================================
HANDLER: rescheduleSelection
================================================================================
Sets the due date of every currently-selected tree item in the front
OmniFocus document window, preserving each task's existing time-of-day.

PARAMETERS:
	targetDate (date) - The date (time-of-day ignored) to reschedule to

RETURNS:
	record - {success, count, tasks, errorMsg}
*)
on rescheduleSelection(targetDate)
	set rescheduledTasks to {}
	set taskCount to 0

	tell application "OmniFocus"
		try
			set selectedItems to value of selected trees of content of front document window

			if (count of selectedItems) is 0 then
				return {success:false, count:0, tasks:{}, errorMsg:"Nothing selected in the front OmniFocus window"}
			end if

			repeat with anItem in selectedItems
				set existingDue to due date of anItem
				if existingDue is not missing value then
					set hh to hours of existingDue
					set mm to minutes of existingDue
				else
					set hh to 17
					set mm to 0
				end if

				set newDue to targetDate
				set time of newDue to (hh * hours) + (mm * minutes)
				set due date of anItem to newDue

				set taskCount to taskCount + 1
				set end of rescheduledTasks to name of anItem
			end repeat

			return {success:true, count:taskCount, tasks:rescheduledTasks, errorMsg:""}
		on error errMsg number errNum
			return {success:false, count:0, tasks:{}, errorMsg:errMsg & " (" & errNum & ")"}
		end try
	end tell
end rescheduleSelection
