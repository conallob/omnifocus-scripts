#!/usr/bin/osascript

(*
================================================================================
Reschedule Overdue Tasks in Project Hierarchy
================================================================================

PURPOSE:
This script reschedules all overdue tasks under a specified project hierarchy
to a new target date.

USAGE:
	osascript reschedule_overdue_tasks.applescript "Project Name" "2025-01-15"
	osascript reschedule_overdue_tasks.applescript "Project Name" "today"
	osascript reschedule_overdue_tasks.applescript "Project Name" "tomorrow"

PARAMETERS:
	1. projectName - The name of the project (will search hierarchy)
	2. targetDate - The date to reschedule to (YYYY-MM-DD, "today", or "tomorrow")

RETURNS:
	A record containing:
		- success (boolean): Whether the operation succeeded
		- count (integer): Number of tasks rescheduled
		- tasks (list): Names of rescheduled tasks
		- error (text): Error message if failed

REQUIREMENTS:
	- OmniFocus 3 or later
	- macOS with AppleScript support

AUTHOR: Claude Code
CREATED: 2025-11-11
================================================================================
*)

on run argv
	-- Parse command-line arguments
	if (count of argv) < 2 then
		return {success:false, errorMsg:"Usage: reschedule_overdue_tasks.applescript <project-name> <target-date>"}
	end if

	set projectName to item 1 of argv
	set targetDateStr to item 2 of argv

	-- Main execution
	try
		set targetDate to parseDate(targetDateStr)
		set result to rescheduleOverdueTasks(projectName, targetDate)
		return result
	on error errMsg number errNum
		return {success:false, errorMsg:"Error: " & errMsg & " (" & errNum & ")"}
	end try
end run

(*
================================================================================
HANDLER: rescheduleOverdueTasks
================================================================================
Finds and reschedules all overdue tasks in a project hierarchy.

PARAMETERS:
	projectName (text) - Name of the project to search
	targetDate (date) - The date to reschedule tasks to

RETURNS:
	record - {success, count, tasks, errorMsg}
*)
on rescheduleOverdueTasks(projectName, targetDate)
	set rescheduledTasks to {}
	set taskCount to 0

	tell application "OmniFocus"
		tell default document
			try
				-- Find the project
				set matchingProjects to (every flattened project whose name is projectName)

				if (count of matchingProjects) is 0 then
					return {success:false, count:0, tasks:{}, errorMsg:"Project '" & projectName & "' not found"}
				end if

				set targetProject to item 1 of matchingProjects

				-- Get current date/time for comparison
				set currentDate to current date
				set currentDate to currentDate - (time of currentDate) -- Normalize to midnight

				-- Get all tasks in project hierarchy (including subprojects)
				set allTasks to my getAllTasksInProject(targetProject)

				-- Filter and reschedule overdue tasks
				repeat with aTask in allTasks
					set taskDueDate to defer date of aTask
					set taskCompleted to completed of aTask

					-- Check if task is overdue (has due date, not completed, due date is before today)
					if taskDueDate is not missing value and taskCompleted is false then
						-- Normalize the due date to midnight for comparison
						set normalizedDueDate to taskDueDate - (time of taskDueDate)

						if normalizedDueDate < currentDate then
							-- Task is overdue, reschedule it
							set defer date of aTask to targetDate

							-- Track rescheduled task
							set taskCount to taskCount + 1
							set end of rescheduledTasks to name of aTask
						end if
					end if
				end repeat

				return {success:true, count:taskCount, tasks:rescheduledTasks, errorMsg:""}

			on error errMsg number errNum
				return {success:false, count:0, tasks:{}, errorMsg:errMsg & " (" & errNum & ")"}
			end try
		end tell
	end tell
end rescheduleOverdueTasks

(*
================================================================================
HANDLER: getAllTasksInProject
================================================================================
Recursively gets all tasks from a project and its subprojects.

PARAMETERS:
	aProject (project) - The OmniFocus project to search

RETURNS:
	list - All tasks in the project hierarchy
*)
on getAllTasksInProject(aProject)
	set allTasks to {}

	tell application "OmniFocus"
		tell default document
			-- Get tasks directly in this project
			set projectTasks to every task of aProject
			set allTasks to allTasks & projectTasks

			-- Recursively get tasks from each task (for nested tasks)
			repeat with aTask in projectTasks
				set subtasks to my getAllSubtasks(aTask)
				set allTasks to allTasks & subtasks
			end repeat

			-- Get tasks from subprojects (if any)
			try
				set subprojects to every project of aProject
				repeat with subproject in subprojects
					set subprojectTasks to my getAllTasksInProject(subproject)
					set allTasks to allTasks & subprojectTasks
				end repeat
			end try
		end tell
	end tell

	return allTasks
end getAllTasksInProject

(*
================================================================================
HANDLER: getAllSubtasks
================================================================================
Recursively gets all subtasks of a task.

PARAMETERS:
	aTask (task) - The OmniFocus task to search

RETURNS:
	list - All subtasks
*)
on getAllSubtasks(aTask)
	set allSubtasks to {}

	tell application "OmniFocus"
		tell default document
			set subtasks to every task of aTask
			set allSubtasks to allSubtasks & subtasks

			-- Recursively get nested subtasks
			repeat with subtask in subtasks
				set nestedSubtasks to my getAllSubtasks(subtask)
				set allSubtasks to allSubtasks & nestedSubtasks
			end repeat
		end tell
	end tell

	return allSubtasks
end getAllSubtasks

(*
================================================================================
HANDLER: parseDate
================================================================================
Parses a date string into an AppleScript date object.

PARAMETERS:
	dateStr (text) - Date string ("YYYY-MM-DD", "today", "tomorrow")

RETURNS:
	date - Parsed date object
*)
on parseDate(dateStr)
	set dateStr to dateStr as text

	-- Handle special keywords
	if dateStr is "today" then
		set targetDate to current date
		set time of targetDate to 0 -- Set to midnight
		return targetDate
	else if dateStr is "tomorrow" then
		set targetDate to (current date) + (1 * days)
		set time of targetDate to 0 -- Set to midnight
		return targetDate
	else
		-- Parse YYYY-MM-DD format
		try
			set AppleScript's text item delimiters to "-"
			set dateParts to text items of dateStr
			set AppleScript's text item delimiters to ""

			if (count of dateParts) is not 3 then
				error "Invalid date format. Use YYYY-MM-DD, 'today', or 'tomorrow'"
			end if

			set yearVal to (item 1 of dateParts) as integer
			set monthVal to (item 2 of dateParts) as integer
			set dayVal to (item 3 of dateParts) as integer

			set targetDate to current date
			set year of targetDate to yearVal
			set month of targetDate to monthVal
			set day of targetDate to dayVal
			set time of targetDate to 0 -- Set to midnight

			return targetDate
		on error
			error "Invalid date format. Use YYYY-MM-DD, 'today', or 'tomorrow'"
		end try
	end if
end parseDate
