#!/bin/bash
# Daily sync script for SWTR tasks
# This script is meant to be run by cron once per day

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Run sync with current user
# The script will read the user from the token file
python swtr_sync_cli.py --max-results 1000 --save

# Deactivate virtual environment
deactivate
