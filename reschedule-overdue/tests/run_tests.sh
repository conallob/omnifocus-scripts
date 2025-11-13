#!/bin/bash

# ==============================================================================
# Test Runner for Reschedule Overdue Tasks Script
# ==============================================================================
#
# This script runs all unit tests for the reschedule_overdue_tasks.applescript
#
# USAGE:
#   ./run_tests.sh
#
# REQUIREMENTS:
#   - macOS with AppleScript support
#   - OmniFocus 3 or later
#   - Bash shell
#
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "================================================================================"
echo "Reschedule Overdue Tasks - Test Suite"
echo "================================================================================"
echo ""
echo -e "${YELLOW}⚠️  WARNING: Tests will modify your ACTUAL OmniFocus database! ⚠️${NC}"
echo ""
echo "While tests create temporary data and clean up automatically:"
echo "  - Test failures may leave data in your OmniFocus database"
echo "  - Tests interact with the live OmniFocus application"
echo ""
echo "STRONGLY RECOMMENDED:"
echo "  - Ensure you have a recent backup of your OmniFocus database"
echo "  - Pause OmniFocus sync to avoid syncing test data"
echo "  - Be prepared to manually remove test data if cleanup fails"
echo ""
read -p "Press ENTER to continue or Ctrl+C to cancel..."
echo ""

# Check if OmniFocus is running
if ! pgrep -x "OmniFocus" > /dev/null; then
    echo -e "${YELLOW}Warning: OmniFocus is not running. Starting OmniFocus...${NC}"
    open -a "OmniFocus"
    sleep 3
fi

# Run the test suite
echo "Running unit tests..."
echo ""

if osascript "$SCRIPT_DIR/test_reschedule.applescript"; then
    echo ""
    echo -e "${GREEN}✓ Test suite completed successfully${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Test suite failed${NC}"
    exit 1
fi
