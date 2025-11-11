#!/usr/bin/osascript

(*
================================================================================
Example Usage: Reschedule Overdue Tasks
================================================================================

This file demonstrates various ways to use the reschedule_overdue_tasks script.

USAGE:
	Run this script directly, or copy examples into your own scripts.

================================================================================
*)

-- Set path to main script
set scriptPath to (do shell script "dirname " & quoted form of POSIX path of (path to me)) & "/../reschedule_overdue_tasks.applescript"

(*
================================================================================
EXAMPLE 1: Reschedule to Tomorrow
================================================================================
Reschedule all overdue tasks in "Work" project to tomorrow.
*)
on example1()
	log "Example 1: Reschedule to Tomorrow"
	log "=================================="

	set projectName to "Work"
	set targetDateStr to "tomorrow"

	-- Execute via command line
	set shellCommand to "osascript " & quoted form of scriptPath & " " & ¬
		quoted form of projectName & " " & ¬
		quoted form of targetDateStr

	set result to do shell script shellCommand

	log "Result: " & result
	log ""
end example1

(*
================================================================================
EXAMPLE 2: Reschedule to Specific Date
================================================================================
Reschedule all overdue tasks to a specific date.
*)
on example2()
	log "Example 2: Reschedule to Specific Date"
	log "======================================"

	set projectName to "Personal"
	set targetDate to "2025-12-01"

	set shellCommand to "osascript " & quoted form of scriptPath & " " & ¬
		quoted form of projectName & " " & ¬
		quoted form of targetDate

	set result to do shell script shellCommand

	log "Result: " & result
	log ""
end example2

(*
================================================================================
EXAMPLE 3: Load and Use Handlers Directly
================================================================================
Load the script and call handlers directly for more control.
*)
on example3()
	log "Example 3: Use Handlers Directly"
	log "================================"

	-- Load the script
	set rescheduleScript to load script POSIX file scriptPath

	-- Call the handler
	tell rescheduleScript
		set targetDate to (current date) + (7 * days) -- One week from now
		set result to rescheduleOverdueTasks("Weekly Review", targetDate)
	end tell

	-- Process results
	if success of result is true then
		log "Successfully rescheduled " & (count of result) & " tasks:"
		repeat with taskName in tasks of result
			log "  - " & taskName
		end repeat
	else
		log "Error: " & (errorMsg of result)
	end if

	log ""
end example3

(*
================================================================================
EXAMPLE 4: Interactive Mode
================================================================================
Prompt user for project and date, then reschedule.
*)
on example4()
	log "Example 4: Interactive Mode"
	log "==========================="

	-- Prompt for project name
	set projectName to text returned of (display dialog "Enter project name:" default answer "")

	-- Prompt for date
	set dateChoices to {"Today", "Tomorrow", "Next Monday", "Custom Date"}
	set dateChoice to choose from list dateChoices with prompt "Reschedule to:"

	if dateChoice is false then
		log "Cancelled"
		return
	end if

	set dateChoice to item 1 of dateChoice

	-- Determine target date
	if dateChoice is "Today" then
		set targetDateStr to "today"
	else if dateChoice is "Tomorrow" then
		set targetDateStr to "tomorrow"
	else if dateChoice is "Next Monday" then
		-- Calculate next Monday
		set today to current date
		set dayOfWeek to weekday of today as integer -- Sunday = 1
		set daysUntilMonday to (9 - dayOfWeek) mod 7
		if daysUntilMonday is 0 then set daysUntilMonday to 7
		set nextMonday to today + (daysUntilMonday * days)

		-- Format as YYYY-MM-DD
		set yyyy to year of nextMonday as string
		set mm to text -2 thru -1 of ("0" & ((month of nextMonday) as integer))
		set dd to text -2 thru -1 of ("0" & (day of nextMonday))
		set targetDateStr to yyyy & "-" & mm & "-" & dd
	else
		-- Custom date
		set targetDateStr to text returned of (display dialog "Enter date (YYYY-MM-DD):" default answer "")
	end if

	-- Execute script
	set shellCommand to "osascript " & quoted form of scriptPath & " " & ¬
		quoted form of projectName & " " & ¬
		quoted form of targetDateStr

	try
		set result to do shell script shellCommand
		display dialog "Success! Rescheduled tasks." & return & return & result buttons {"OK"} default button 1
	on error errMsg
		display dialog "Error: " & errMsg buttons {"OK"} default button 1 with icon stop
	end try

	log ""
end example4

(*
================================================================================
EXAMPLE 5: Batch Processing Multiple Projects
================================================================================
Reschedule overdue tasks in multiple projects at once.
*)
on example5()
	log "Example 5: Batch Processing"
	log "==========================="

	-- Define projects to process
	set projectList to {"Work", "Personal", "Errands", "Home"}
	set targetDateStr to "today"

	log "Rescheduling overdue tasks in " & (count of projectList) & " projects to " & targetDateStr & "..."
	log ""

	-- Process each project
	repeat with aProject in projectList
		log "Processing: " & aProject

		set shellCommand to "osascript " & quoted form of scriptPath & " " & ¬
			quoted form of aProject & " " & ¬
			quoted form of targetDateStr

		try
			set result to do shell script shellCommand
			log "  Result: " & result
		on error errMsg
			log "  Error: " & errMsg
		end try
	end repeat

	log ""
	log "Batch processing complete!"
	log ""
end example5

(*
================================================================================
EXAMPLE 6: Conditional Rescheduling
================================================================================
Only reschedule if overdue count exceeds a threshold.
*)
on example6()
	log "Example 6: Conditional Rescheduling"
	log "==================================="

	set projectName to "Work"
	set threshold to 5
	set targetDateStr to "tomorrow"

	-- Load script to access handlers
	set rescheduleScript to load script POSIX file scriptPath

	tell rescheduleScript
		-- First, get a count of overdue tasks
		set targetDate to parseDate(targetDateStr)
		set result to rescheduleOverdueTasks(projectName, targetDate)

		if success of result is true then
			set overdueCount to count of result

			if overdueCount ≥ threshold then
				log "Found " & overdueCount & " overdue tasks (threshold: " & threshold & ")"
				log "Rescheduling..."
				-- Already rescheduled by previous call
				log "Rescheduled " & overdueCount & " tasks"
			else
				log "Only " & overdueCount & " overdue tasks (threshold: " & threshold & ")"
				log "No action taken"
			end if
		else
			log "Error: " & (errorMsg of result)
		end if
	end tell

	log ""
end example6

(*
================================================================================
MAIN: Run Examples
================================================================================
Uncomment the examples you want to run.
*)
on run
	log ""
	log "================================================================================"
	log "Reschedule Overdue Tasks - Usage Examples"
	log "================================================================================"
	log ""

	-- Run examples (uncomment to enable)
	-- example1()
	-- example2()
	-- example3()
	-- example4()  -- Interactive mode
	-- example5()  -- Batch processing
	-- example6()  -- Conditional

	log "Note: Uncomment example calls in the script to run them"
	log ""
	log "================================================================================"
end run
