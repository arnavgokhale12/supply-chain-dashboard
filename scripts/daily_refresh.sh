#!/bin/bash
# Daily refresh script for Supply Chain Dashboard
# This script activates the virtual environment and runs the Python refresh script.
#
# Usage:
#   ./scripts/daily_refresh.sh
#
# To schedule with cron (runs daily at 6 AM):
#   crontab -e
#   0 6 * * * /Users/arnavgokhale/Desktop/Projects/supply-chain-dashboard/scripts/daily_refresh.sh >> /Users/arnavgokhale/Desktop/Projects/supply-chain-dashboard/logs/refresh.log 2>&1

set -e

# Navigate to project directory
cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Run the refresh script
python "$PROJECT_DIR/scripts/daily_refresh.py"

# Deactivate virtual environment
deactivate
