#!/bin/bash
# Automated task runner for the assistant
# Usage: ./run.sh <task_name>
# Example: ./run.sh morning
#          ./run.sh evening
#          ./run.sh memory-clean

set -euo pipefail

# --- Path derivation (all paths relative to script location) ---
TASK_NAME="${1:?Usage: ./run.sh <task_name>}"
TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="$(cd "$TOOLS_DIR/.." && pwd)"
KB_DIR="$(cd "$AGENT_DIR/.." && pwd)"

PROMPT_FILE="$TOOLS_DIR/prompts/${TASK_NAME}.md"
LOG_DIR="$TOOLS_DIR/logs"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/${TODAY}-${TASK_NAME}.log"
LOCK_FILE="$LOG_DIR/.lock-${TODAY}-${TASK_NAME}"
HOSTNAME=$(hostname -s)

# PATH may be incomplete under launchd
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# Force OAuth authentication (Max subscription) instead of API key.
# If ANTHROPIC_API_KEY is set, -p mode charges API credits (separate billing).
# Unsetting it makes claude use the OAuth session (Max subscription quota).
unset ANTHROPIC_API_KEY

CLAUDE_BIN=$(which claude 2>/dev/null || echo "$HOME/.local/bin/claude")

# Check that claude CLI exists
if [ ! -x "$CLAUDE_BIN" ]; then
  echo "Error: claude CLI not found" >&2
  exit 1
fi

# Check that prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
  echo "Error: prompt file not found: $PROMPT_FILE" >&2
  echo "Available tasks: $(ls "$TOOLS_DIR/prompts/" 2>/dev/null | sed 's/.md$//' | tr '\n' ' ')" >&2
  exit 1
fi

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Clean up lock files older than 7 days
find "$LOG_DIR" -name ".lock-*" -mtime +7 -delete 2>/dev/null || true

# === Duplicate execution prevention ===
# Multiple machines (e.g. desktop + laptop) may have the same schedule.
# Lock files prevent the same task from running twice on the same day.
# Lock file contents: hostname + time (for debugging).

if [ -f "$LOCK_FILE" ]; then
  LOCK_HOST=$(head -1 "$LOCK_FILE" 2>/dev/null || echo "unknown")
  echo "Skipped: today's ${TASK_NAME} was already run by ${LOCK_HOST}" >&2
  exit 0
fi

# Claim the lock (write hostname and time)
echo "${HOSTNAME} $(date '+%H:%M:%S')" > "$LOCK_FILE"

# Brief pause to let sync services propagate the lock file
sleep 3

# Re-check that the lock is still ours (simple race condition guard)
CURRENT_LOCK=$(head -1 "$LOCK_FILE" 2>/dev/null || echo "")
if [[ "$CURRENT_LOCK" != "${HOSTNAME}"* ]]; then
  echo "Skipped: another machine claimed the lock ($CURRENT_LOCK)" >&2
  exit 0
fi

# Replace hardcoded "assistant/" in prompts with actual agent directory name
AGENT_BASENAME=$(basename "$AGENT_DIR")
PROMPT=$(sed "s|assistant/|${AGENT_BASENAME}/|g" "$PROMPT_FILE")

echo "=== Automated task: $TASK_NAME ===" | tee "$LOG_FILE"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "Host: $HOSTNAME" | tee -a "$LOG_FILE"
echo "---" | tee -a "$LOG_FILE"

# Back up MEMORY.md before execution (guard against concurrent writes)
cp "$AGENT_DIR/MEMORY.md" "$AGENT_DIR/MEMORY.md.bak" 2>/dev/null || true

# cd to knowledge base root so CLAUDE.md is automatically picked up
cd "$KB_DIR"

# Run Claude Code
"$CLAUDE_BIN" -p "$PROMPT" \
  --dangerously-skip-permissions \
  --max-budget-usd 2.00 \
  --model sonnet \
  --output-format text \
  2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "---" | tee -a "$LOG_FILE"
echo "Done: $(date '+%Y-%m-%d %H:%M:%S') (exit code: $EXIT_CODE)" | tee -a "$LOG_FILE"

# Send alert on failure via notify.py
if [ "$EXIT_CODE" -ne 0 ]; then
  python3 "$TOOLS_DIR/notify.py" "Warning: automated task ${TASK_NAME} failed (exit=$EXIT_CODE). Log: $LOG_FILE" 2>/dev/null || true
fi
