#!/bin/bash
# Randomized delay task runner
# Adds a random delay before executing, creating a "non-fixed schedule" effect.
# e.g. trigger at 10:00 + random 0~90 min = actual execution 10:00~11:30
#
# Usage: ./run-random.sh <task_name>

set -euo pipefail

TASK_NAME="${1:?Usage: ./run-random.sh <task_name>}"
TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"

# Random delay 0~90 minutes (0~1.5 hours)
MAX_DELAY_MINUTES=90
DELAY_MINUTES=$(( RANDOM % MAX_DELAY_MINUTES ))
DELAY_SECONDS=$(( DELAY_MINUTES * 60 ))

echo "$(date '+%Y-%m-%d %H:%M:%S') Delaying ${DELAY_MINUTES} minutes before running ${TASK_NAME}"
sleep "$DELAY_SECONDS"

# After delay, hand off to the standard run.sh
exec "$TOOLS_DIR/run.sh" "$TASK_NAME"
