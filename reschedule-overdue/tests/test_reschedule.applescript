#!/usr/bin/osascript

(*
================================================================================
Unit Tests for Reschedule Overdue Tasks Script
================================================================================

PURPOSE:
Comprehensive test suite for the reschedule_overdue_tasks.applescript script.

USAGE:
	osascript test_reschedule.applescript

REQUIREMENTS:
	- OmniFocus 3 or later
	- Test project setup (see setupTestEnvironment handler)
	- macOS with AppleScript support

NOTES:
	This test suite creates temporary test data in OmniFocus and cleans it up
	after testing. It's recommended to run tests on a backup or test database.

AUTHOR: Claude Code
CREATED: 2025-11-11
================================================================================
*)

property testProjectName : "TEST_RescheduleScript_" & ((current date) as string)
property testsPassed : 0
property testsFailed : 0
property testResults : {}

-- Load the main script
property scriptPath : (do shell script "dirname " & quoted form of POSIX path of (path to me)) & "/../reschedule_overdue_tasks.applescript"

on run
	log "================================================================================
	log "Starting Test Suite: Reschedule Overdue Tasks"
	log "================================================================================"
	log ""

	try
		-- Setup test environment
		setupTestEnvironment()

		-- Run all tests
		testParseDate()
		testRescheduleOverdueTasks()
		testNoOverdueTasks()
		testNonexistentProject()
		testEmptyProject()
		testNestedTasks()
		testMixedOverdueAndCurrent()

		-- Cleanup
		cleanupTestEnvironment()

		-- Report results
		reportResults()

	on error errMsg
		log "CRITICAL ERROR: " & errMsg
		cleanupTestEnvironment()
		return {success:false, error:errMsg}
	end try

	-- Return success/failure based on test results
	if testsFailed > 0 then
		return {success:false, passed:testsPassed, failed:testsFailed}
	else
		return {success:true, passed:testsPassed, failed:testsFailed}
	end if
end run

(*
================================================================================
TEST: parseDate
================================================================================
Tests the date parsing functionality.
*)
on testParseDate()
	log "TEST: parseDate"

	try
		-- Test "today"
		set testDate to parseDate("today")
		set todayDate to current date
		set time of todayDate to 0
		assertEqual(testDate, todayDate, "parseDate('today')")

		-- Test "tomorrow"
		set testDate to parseDate("tomorrow")
		set tomorrowDate to (current date) + (1 * days)
		set time of tomorrowDate to 0
		assertEqual(testDate, tomorrowDate, "parseDate('tomorrow')")

		-- Test YYYY-MM-DD format
		set testDate to parseDate("2025-12-25")
		set expectedDate to current date
		set year of expectedDate to 2025
		set month of expectedDate to 12
		set day of expectedDate to 25
		set time of expectedDate to 0
		assertEqual(testDate, expectedDate, "parseDate('2025-12-25')")

		passTest("parseDate")
	on error errMsg
		failTest("parseDate", errMsg)
	end try
end testParseDate

(*
================================================================================
TEST: rescheduleOverdueTasks
================================================================================
Tests the main reschedule functionality with overdue tasks.
*)
on testRescheduleOverdueTasks()
	log "TEST: rescheduleOverdueTasks with overdue tasks"

	try
		-- Create test tasks with overdue dates
		tell application "OmniFocus"
			tell default document
				set testProj to first flattened project whose name is testProjectName

				-- Create overdue task
				set overdueDate to (current date) - (5 * days)
				set time of overdueDate to 0
				make new task at end of tasks of testProj with properties {name:"Overdue Task 1", defer date:overdueDate}

				-- Create another overdue task
				set overdueDate2 to (current date) - (3 * days)
				set time of overdueDate2 to 0
				make new task at end of tasks of testProj with properties {name:"Overdue Task 2", defer date:overdueDate2}
			end tell
		end tell

		-- Wait for OmniFocus to process
		delay 0.5

		-- Run reschedule with tomorrow as target
		set targetDate to (current date) + (1 * days)
		set time of targetDate to 0
		set result to rescheduleOverdueTasks(testProjectName, targetDate)

		-- Verify results
		if success of result is true then
			if (count of result) ≥ 2 then
				passTest("rescheduleOverdueTasks")
			else
				failTest("rescheduleOverdueTasks", "Expected at least 2 tasks rescheduled, got " & (count of result))
			end if
		else
			failTest("rescheduleOverdueTasks", errorMsg of result)
		end if

	on error errMsg
		failTest("rescheduleOverdueTasks", errMsg)
	end try
end testRescheduleOverdueTasks

(*
================================================================================
TEST: testNoOverdueTasks
================================================================================
Tests behavior when no tasks are overdue.
*)
on testNoOverdueTasks()
	log "TEST: No overdue tasks"

	try
		-- Create test project with only future tasks
		tell application "OmniFocus"
			tell default document
				-- Delete existing tasks in test project
				set testProj to first flattened project whose name is testProjectName
				delete every task of testProj

				-- Create future task
				set futureDate to (current date) + (5 * days)
				set time of futureDate to 0
				make new task at end of tasks of testProj with properties {name:"Future Task", defer date:futureDate}
			end tell
		end tell

		delay 0.5

		-- Run reschedule
		set targetDate to (current date) + (1 * days)
		set time of targetDate to 0
		set result to rescheduleOverdueTasks(testProjectName, targetDate)

		-- Verify no tasks were rescheduled
		if success of result is true and count of result is 0 then
			passTest("testNoOverdueTasks")
		else
			failTest("testNoOverdueTasks", "Expected 0 tasks rescheduled, got " & (count of result))
		end if

	on error errMsg
		failTest("testNoOverdueTasks", errMsg)
	end try
end testNoOverdueTasks

(*
================================================================================
TEST: testNonexistentProject
================================================================================
Tests error handling for nonexistent projects.
*)
on testNonexistentProject()
	log "TEST: Nonexistent project"

	try
		set targetDate to current date
		set result to rescheduleOverdueTasks("NONEXISTENT_PROJECT_XYZ123", targetDate)

		-- Should return success=false
		if success of result is false then
			passTest("testNonexistentProject")
		else
			failTest("testNonexistentProject", "Expected failure for nonexistent project")
		end if

	on error errMsg
		failTest("testNonexistentProject", errMsg)
	end try
end testNonexistentProject

(*
================================================================================
TEST: testEmptyProject
================================================================================
Tests behavior with an empty project.
*)
on testEmptyProject()
	log "TEST: Empty project"

	try
		-- Ensure test project is empty
		tell application "OmniFocus"
			tell default document
				set testProj to first flattened project whose name is testProjectName
				delete every task of testProj
			end tell
		end tell

		delay 0.5

		-- Run reschedule
		set targetDate to current date
		set result to rescheduleOverdueTasks(testProjectName, targetDate)

		-- Verify no tasks were rescheduled
		if success of result is true and count of result is 0 then
			passTest("testEmptyProject")
		else
			failTest("testEmptyProject", "Expected 0 tasks in empty project")
		end if

	on error errMsg
		failTest("testEmptyProject", errMsg)
	end try
end testEmptyProject

(*
================================================================================
TEST: testNestedTasks
================================================================================
Tests handling of nested subtasks.
*)
on testNestedTasks()
	log "TEST: Nested tasks"

	try
		tell application "OmniFocus"
			tell default document
				set testProj to first flattened project whose name is testProjectName
				delete every task of testProj

				-- Create parent task with overdue subtask
				set parentTask to make new task at end of tasks of testProj with properties {name:"Parent Task"}

				set overdueDate to (current date) - (2 * days)
				set time of overdueDate to 0
				make new task at end of tasks of parentTask with properties {name:"Overdue Subtask", defer date:overdueDate}
			end tell
		end tell

		delay 0.5

		-- Run reschedule
		set targetDate to current date
		set result to rescheduleOverdueTasks(testProjectName, targetDate)

		-- Verify subtask was found and rescheduled
		if success of result is true and count of result ≥ 1 then
			passTest("testNestedTasks")
		else
			failTest("testNestedTasks", "Nested task not rescheduled")
		end if

	on error errMsg
		failTest("testNestedTasks", errMsg)
	end try
end testNestedTasks

(*
================================================================================
TEST: testMixedOverdueAndCurrent
================================================================================
Tests with a mix of overdue and current tasks.
*)
on testMixedOverdueAndCurrent()
	log "TEST: Mixed overdue and current tasks"

	try
		tell application "OmniFocus"
			tell default document
				set testProj to first flattened project whose name is testProjectName
				delete every task of testProj

				-- Create overdue task
				set overdueDate to (current date) - (1 * days)
				set time of overdueDate to 0
				make new task at end of tasks of testProj with properties {name:"Overdue", defer date:overdueDate}

				-- Create current task
				set todayDate to current date
				set time of todayDate to 0
				make new task at end of tasks of testProj with properties {name:"Today", defer date:todayDate}

				-- Create future task
				set futureDate to (current date) + (2 * days)
				set time of futureDate to 0
				make new task at end of tasks of testProj with properties {name:"Future", defer date:futureDate}

				-- Create task with no date
				make new task at end of tasks of testProj with properties {name:"No Date"}
			end tell
		end tell

		delay 0.5

		-- Run reschedule
		set targetDate to (current date) + (1 * days)
		set time of targetDate to 0
		set result to rescheduleOverdueTasks(testProjectName, targetDate)

		-- Verify only the overdue task was rescheduled
		if success of result is true and count of result is 1 then
			passTest("testMixedOverdueAndCurrent")
		else
			failTest("testMixedOverdueAndCurrent", "Expected 1 task rescheduled, got " & (count of result))
		end if

	on error errMsg
		failTest("testMixedOverdueAndCurrent", errMsg)
	end try
end testMixedOverdueAndCurrent

(*
================================================================================
HELPER: setupTestEnvironment
================================================================================
Creates test project and data in OmniFocus.
*)
on setupTestEnvironment()
	log "Setting up test environment..."

	tell application "OmniFocus"
		tell default document
			-- Create test project
			try
				make new project with properties {name:testProjectName}
				log "Created test project: " & testProjectName
			on error
				log "Test project already exists"
			end try
		end tell
	end tell

	delay 1
end setupTestEnvironment

(*
================================================================================
HELPER: cleanupTestEnvironment
================================================================================
Removes test project and data from OmniFocus.
*)
on cleanupTestEnvironment()
	log ""
	log "Cleaning up test environment..."

	try
		tell application "OmniFocus"
			tell default document
				-- Delete test project
				set testProjects to (every flattened project whose name is testProjectName)
				repeat with proj in testProjects
					delete proj
				end repeat
				log "Deleted test project"
			end tell
		end tell
	on error errMsg
		log "Warning: Cleanup failed - " & errMsg
	end try
end cleanupTestEnvironment

(*
================================================================================
HELPER: assertEqual
================================================================================
Asserts two values are equal.
*)
on assertEqual(actual, expected, testName)
	if actual is not equal to expected then
		error "Assertion failed in " & testName & ": expected " & (expected as text) & ", got " & (actual as text)
	end if
end assertEqual

(*
================================================================================
HELPER: passTest
================================================================================
Records a passed test.
*)
on passTest(testName)
	set testsPassed to testsPassed + 1
	set end of testResults to {name:testName, status:"PASS"}
	log "  ✓ PASS: " & testName
	log ""
end passTest

(*
================================================================================
HELPER: failTest
================================================================================
Records a failed test.
*)
on failTest(testName, errorMsg)
	set testsFailed to testsFailed + 1
	set end of testResults to {name:testName, status:"FAIL", error:errorMsg}
	log "  ✗ FAIL: " & testName
	log "    Error: " & errorMsg
	log ""
end failTest

(*
================================================================================
HELPER: reportResults
================================================================================
Displays final test results.
*)
on reportResults()
	log "================================================================================"
	log "Test Results Summary"
	log "================================================================================"
	log "Total Tests: " & (testsPassed + testsFailed)
	log "Passed: " & testsPassed
	log "Failed: " & testsFailed
	log ""

	if testsFailed > 0 then
		log "Failed Tests:"
		repeat with result in testResults
			if status of result is "FAIL" then
				log "  - " & (name of result) & ": " & (error of result)
			end if
		end repeat
	else
		log "All tests passed! ✓"
	end if

	log "================================================================================"
end reportResults

(*
================================================================================
Include handlers from main script
================================================================================
*)

-- Copy the handlers from the main script here
on parseDate(dateStr)
	set dateStr to dateStr as text

	if dateStr is "today" then
		set targetDate to current date
		set time of targetDate to 0
		return targetDate
	else if dateStr is "tomorrow" then
		set targetDate to (current date) + (1 * days)
		set time of targetDate to 0
		return targetDate
	else
		try
			set AppleScript's text item delimiters to "-"
			set dateParts to text items of dateStr
			set AppleScript's text item delimiters to ""

			if (count of dateParts) is not 3 then
				error "Invalid date format"
			end if

			set yearVal to (item 1 of dateParts) as integer
			set monthVal to (item 2 of dateParts) as integer
			set dayVal to (item 3 of dateParts) as integer

			set targetDate to current date
			set year of targetDate to yearVal
			set month of targetDate to monthVal
			set day of targetDate to dayVal
			set time of targetDate to 0

			return targetDate
		on error
			error "Invalid date format"
		end try
	end if
end parseDate

on rescheduleOverdueTasks(projectName, targetDate)
	set rescheduledTasks to {}
	set taskCount to 0

	tell application "OmniFocus"
		tell default document
			try
				set matchingProjects to (every flattened project whose name is projectName)

				if (count of matchingProjects) is 0 then
					return {success:false, count:0, tasks:{}, errorMsg:"Project not found"}
				end if

				set targetProject to item 1 of matchingProjects
				set currentDate to current date
				set currentDate to currentDate - (time of currentDate)

				set allTasks to my getAllTasksInProject(targetProject)

				repeat with aTask in allTasks
					set taskDueDate to defer date of aTask
					set taskCompleted to completed of aTask

					if taskDueDate is not missing value and taskCompleted is false then
						set normalizedDueDate to taskDueDate - (time of taskDueDate)

						if normalizedDueDate < currentDate then
							set defer date of aTask to targetDate
							set taskCount to taskCount + 1
							set end of rescheduledTasks to name of aTask
						end if
					end if
				end repeat

				return {success:true, count:taskCount, tasks:rescheduledTasks, errorMsg:""}

			on error errMsg number errNum
				return {success:false, count:0, tasks:{}, errorMsg:errMsg}
			end try
		end tell
	end tell
end rescheduleOverdueTasks

on getAllTasksInProject(aProject)
	set allTasks to {}

	tell application "OmniFocus"
		tell default document
			set projectTasks to every task of aProject
			set allTasks to allTasks & projectTasks

			repeat with aTask in projectTasks
				set subtasks to my getAllSubtasks(aTask)
				set allTasks to allTasks & subtasks
			end repeat

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

on getAllSubtasks(aTask)
	set allSubtasks to {}

	tell application "OmniFocus"
		tell default document
			set subtasks to every task of aTask
			set allSubtasks to allSubtasks & subtasks

			repeat with subtask in subtasks
				set nestedSubtasks to my getAllSubtasks(subtask)
				set allSubtasks to allSubtasks & nestedSubtasks
			end repeat
		end tell
	end tell

	return allSubtasks
end getAllSubtasks
