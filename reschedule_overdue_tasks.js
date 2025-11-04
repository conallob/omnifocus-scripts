#!/usr/bin/env osascript -l JavaScript

/**
 * Mass Reschedule Overdue Tasks in OmniFocus
 *
 * This script finds all overdue tasks under a specified project hierarchy
 * and reschedules them to a specified date.
 *
 * Usage:
 *   osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "2025-11-15"
 *   osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "today"
 *   osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "tomorrow"
 *   osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "+3d"
 */

ObjC.import('stdlib');

function run(argv) {
    const app = Application('OmniFocus');
    app.includeStandardAdditions = true;

    // Parse arguments
    if (argv.length < 2) {
        console.log('Usage: osascript -l JavaScript reschedule_overdue_tasks.js "Project Name" "target_date"');
        console.log('');
        console.log('Examples:');
        console.log('  osascript -l JavaScript reschedule_overdue_tasks.js "Work" "2025-11-15"');
        console.log('  osascript -l JavaScript reschedule_overdue_tasks.js "Personal" "today"');
        console.log('  osascript -l JavaScript reschedule_overdue_tasks.js "Project" "tomorrow"');
        console.log('  osascript -l JavaScript reschedule_overdue_tasks.js "Project" "+3d" (3 days from now)');
        $.exit(1);
    }

    const projectName = argv[0];
    const targetDateStr = argv[1];

    // Parse target date
    const targetDate = parseDate(targetDateStr);
    if (!targetDate) {
        console.log('Error: Invalid date format. Use YYYY-MM-DD, "today", "tomorrow", or "+Nd" (N days from now)');
        $.exit(1);
    }

    console.log(`Rescheduling overdue tasks in project "${projectName}" to ${formatDate(targetDate)}`);
    console.log('');

    // Get the default document
    const doc = app.defaultDocument;

    // Find the project
    const project = findProject(doc, projectName);
    if (!project) {
        console.log(`Error: Project "${projectName}" not found`);
        $.exit(1);
    }

    // Get all overdue tasks in the project hierarchy
    const overdueTasks = getOverdueTasks(project);

    if (overdueTasks.length === 0) {
        console.log('No overdue tasks found in this project hierarchy.');
        return;
    }

    console.log(`Found ${overdueTasks.length} overdue task(s):\n`);

    // List all overdue tasks
    overdueTasks.forEach((task, index) => {
        const dueDate = task.dueDate() ? formatDate(task.dueDate()) : 'No due date';
        console.log(`${index + 1}. ${task.name()} (Due: ${dueDate})`);
    });

    // Ask for confirmation
    console.log('');
    const response = app.displayDialog(
        `Reschedule ${overdueTasks.length} overdue task(s) to ${formatDate(targetDate)}?`,
        {
            buttons: ['Cancel', 'Reschedule'],
            defaultButton: 'Reschedule',
            cancelButton: 'Cancel',
            withTitle: 'Confirm Reschedule'
        }
    );

    if (response.buttonReturned === 'Reschedule') {
        // Reschedule all overdue tasks
        let rescheduled = 0;
        overdueTasks.forEach(task => {
            try {
                task.dueDate = targetDate;
                rescheduled++;
            } catch (e) {
                console.log(`Warning: Could not reschedule "${task.name()}": ${e}`);
            }
        });

        console.log(`\nSuccessfully rescheduled ${rescheduled} task(s) to ${formatDate(targetDate)}`);
    } else {
        console.log('\nOperation cancelled by user.');
    }
}

/**
 * Find a project by name (searches recursively)
 */
function findProject(doc, projectName) {
    const allProjects = doc.flattenedProjects();

    for (let i = 0; i < allProjects.length; i++) {
        const project = allProjects[i];
        if (project.name() === projectName) {
            return project;
        }
    }

    return null;
}

/**
 * Get all overdue tasks in a project and its subprojects
 */
function getOverdueTasks(project) {
    const now = new Date();
    const overdueTasks = [];

    function collectOverdueTasks(container) {
        // Get tasks directly in this container
        const tasks = container.tasks();

        for (let i = 0; i < tasks.length; i++) {
            const task = tasks[i];

            // Skip completed tasks
            if (task.completed()) {
                continue;
            }

            // Check if task is overdue
            const dueDate = task.dueDate();
            if (dueDate && dueDate < now) {
                overdueTasks.push(task);
            }

            // Recursively check child tasks
            if (task.tasks) {
                collectOverdueTasks(task);
            }
        }

        // Check subprojects if this is a project
        if (container.projects) {
            const subprojects = container.projects();
            for (let i = 0; i < subprojects.length; i++) {
                collectOverdueTasks(subprojects[i]);
            }
        }
    }

    collectOverdueTasks(project);
    return overdueTasks;
}

/**
 * Parse date string into Date object
 */
function parseDate(dateStr) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Handle relative dates
    if (dateStr.toLowerCase() === 'today') {
        return today;
    }

    if (dateStr.toLowerCase() === 'tomorrow') {
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        return tomorrow;
    }

    // Handle "+Nd" format (e.g., "+3d" for 3 days from now)
    const relativeMatch = dateStr.match(/^\+(\d+)d$/i);
    if (relativeMatch) {
        const days = parseInt(relativeMatch[1]);
        const futureDate = new Date(today);
        futureDate.setDate(futureDate.getDate() + days);
        return futureDate;
    }

    // Handle YYYY-MM-DD format
    const dateMatch = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (dateMatch) {
        const year = parseInt(dateMatch[1]);
        const month = parseInt(dateMatch[2]) - 1; // JavaScript months are 0-indexed
        const day = parseInt(dateMatch[3]);
        return new Date(year, month, day);
    }

    return null;
}

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
