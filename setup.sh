#!/bin/bash
# claude-assistant setup wizard
# Interactive setup for your personal AI assistant.
# Run: ./setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_DIR="assistant"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[info]${NC} $1"; }
ok()    { echo -e "${GREEN}[ok]${NC} $1"; }
warn()  { echo -e "${YELLOW}[warn]${NC} $1"; }
error() { echo -e "${RED}[error]${NC} $1"; }

echo ""
echo "======================================="
echo "  claude-assistant setup wizard"
echo "======================================="
echo ""

# --- Step 1: Agent name ---
read -rp "Agent name (directory name) [assistant]: " agent_name
AGENT_DIR="${agent_name:-assistant}"

if [ "$AGENT_DIR" != "assistant" ] && [ -d "$SCRIPT_DIR/assistant" ] && [ ! -d "$SCRIPT_DIR/$AGENT_DIR" ]; then
    mv "$SCRIPT_DIR/assistant" "$SCRIPT_DIR/$AGENT_DIR"
    ok "Renamed assistant/ → $AGENT_DIR/"
elif [ "$AGENT_DIR" != "assistant" ] && [ ! -d "$SCRIPT_DIR/$AGENT_DIR" ]; then
    cp -r "$SCRIPT_DIR/assistant" "$SCRIPT_DIR/$AGENT_DIR"
    ok "Created $AGENT_DIR/ from template"
fi

AGENT_PATH="$SCRIPT_DIR/$AGENT_DIR"
TOOLS_PATH="$AGENT_PATH/tools"

# --- Step 1b: User name (for identity templates) ---
echo ""
read -rp "Your name (used in SOUL.md and MEMORY.md) []: " user_name
if [ -n "$user_name" ]; then
    # Escape sed metacharacters in user name
    escaped_name=$(printf '%s\n' "$user_name" | sed 's/[&/\]/\\&/g')
    # Replace {{USER}} placeholder in identity files
    for f in "$AGENT_PATH/SOUL.md" "$AGENT_PATH/MEMORY.md"; do
        if [ -f "$f" ]; then
            sed -i '' "s/{{USER}}/${escaped_name}/g" "$f" 2>/dev/null || \
            sed -i "s/{{USER}}/${escaped_name}/g" "$f" 2>/dev/null
        fi
    done
    ok "Personalized identity files for $user_name"
fi

# --- Step 2: Telegram Bot ---
TELEGRAM_TOKEN=""
TELEGRAM_CHAT_ID=""

echo ""
read -rp "Set up Telegram bot? (y/n) [n]: " setup_telegram
if [[ "${setup_telegram:-n}" =~ ^[Yy] ]]; then
    echo ""
    info "Create a bot via @BotFather on Telegram to get your token."
    info "To find your chat_id, message @userinfobot on Telegram."
    echo ""
    read -rp "  Telegram bot token: " TELEGRAM_TOKEN
    read -rp "  Your Telegram chat_id: " TELEGRAM_CHAT_ID

    if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        ok "Telegram configured"
    else
        warn "Telegram token or chat_id empty — skipping Telegram setup"
        setup_telegram="n"
    fi
fi

# --- Step 3: Long-term memory (LanceDB) ---
OPENAI_API_KEY=""

echo ""
read -rp "Set up long-term memory (requires OpenAI API key)? (y/n) [n]: " setup_memory
if [[ "${setup_memory:-n}" =~ ^[Yy] ]]; then
    echo ""
    info "Long-term memory uses LanceDB with OpenAI embeddings."
    info "You need an OpenAI API key (text-embedding-3-small model)."
    echo ""
    read -rp "  OpenAI API key: " OPENAI_API_KEY

    if [ -n "$OPENAI_API_KEY" ]; then
        info "Creating Python virtual environment..."
        python3 -m venv "$TOOLS_PATH/memory-venv" 2>/dev/null || {
            error "Failed to create venv. Make sure python3 is installed."
            setup_memory="n"
        }

        if [[ "${setup_memory:-n}" =~ ^[Yy] ]]; then
            info "Installing LanceDB and dependencies (this may take a minute)..."
            "$TOOLS_PATH/memory-venv/bin/pip" install --quiet lancedb pyarrow 2>&1 | tail -1 || {
                error "Failed to install dependencies."
                setup_memory="n"
            }

            if [[ "${setup_memory:-n}" =~ ^[Yy] ]]; then
                ok "Long-term memory configured"
            fi
        fi
    else
        warn "No API key provided — skipping long-term memory"
        setup_memory="n"
    fi
fi

# --- Step 4: Scheduled tasks (macOS launchd) ---
SETUP_SCHEDULE="n"

echo ""
if [[ "$(uname)" == "Darwin" ]]; then
    read -rp "Set up scheduled tasks (macOS launchd)? (y/n) [n]: " SETUP_SCHEDULE
    if [[ "${SETUP_SCHEDULE:-n}" =~ ^[Yy] ]]; then
        PLIST_DIR="$HOME/Library/LaunchAgents"
        mkdir -p "$PLIST_DIR"

        TOOLS_ABS="$(cd "$TOOLS_PATH" && pwd)"
        KB_ABS="$(cd "$SCRIPT_DIR" && pwd)"
        PYTHON_ABS="$(which python3 2>/dev/null || echo "/usr/bin/python3")"

        echo ""
        info "Available scheduled tasks:"
        echo "  1. Morning planning  (daily at 07:00)"
        echo "  2. Evening review    (daily at 22:00)"
        echo "  3. Memory cleanup    (weekly, Sunday 22:30)"
        echo "  4. Telegram bot      (always-on daemon)"
        echo ""
        read -rp "Which tasks to enable? (e.g., 1,2,3 or 'all') [none]: " task_selection

        enable_task() {
            local template="$1"
            local name="$2"

            if [ ! -f "$template" ]; then
                warn "Template not found: $template"
                return
            fi

            local plist_name
            plist_name="com.${AGENT_DIR}.${name}.plist"
            local plist_path="$PLIST_DIR/$plist_name"

            sed -e "s|{{AGENT_NAME}}|${AGENT_DIR}|g" \
                -e "s|{{TOOLS_DIR}}|${TOOLS_ABS}|g" \
                -e "s|{{KB_DIR}}|${KB_ABS}|g" \
                -e "s|{{PYTHON_PATH}}|${PYTHON_ABS}|g" \
                -e "s|{{TELEGRAM_TOKEN}}|${TELEGRAM_TOKEN}|g" \
                -e "s|{{CHAT_ID}}|${TELEGRAM_CHAT_ID}|g" \
                -e "s|{{OPENAI_API_KEY}}|${OPENAI_API_KEY}|g" \
                -e "s|{{HOME}}|${HOME}|g" \
                "$template" > "$plist_path"

            ok "Created $plist_name"
            info "  Load with: launchctl load $plist_path"
        }

        LAUNCHD_DIR="$TOOLS_PATH/launchd"

        if [[ "$task_selection" == "all" ]] || [[ "$task_selection" == *"1"* ]]; then
            enable_task "$LAUNCHD_DIR/com.assistant.morning.plist.template" "morning"
        fi
        if [[ "$task_selection" == "all" ]] || [[ "$task_selection" == *"2"* ]]; then
            enable_task "$LAUNCHD_DIR/com.assistant.evening.plist.template" "evening"
        fi
        if [[ "$task_selection" == "all" ]] || [[ "$task_selection" == *"3"* ]]; then
            enable_task "$LAUNCHD_DIR/com.assistant.memory-clean.plist.template" "memory-clean"
        fi
        if [[ "$task_selection" == "all" ]] || [[ "$task_selection" == *"4"* ]]; then
            if [ -n "$TELEGRAM_TOKEN" ]; then
                enable_task "$LAUNCHD_DIR/com.assistant.telegram.plist.template" "telegram"
            else
                warn "Skipping Telegram daemon — no token configured"
            fi
        fi

        echo ""
        info "To activate scheduled tasks, run:"
        info "  launchctl load ~/Library/LaunchAgents/com.${AGENT_DIR}.*.plist"
    fi
else
    warn "Scheduled tasks use macOS launchd. On Linux, see docs/scheduling.md for cron/systemd alternatives."
fi

# --- Step 5: Generate config.json ---
CONFIG_PATH="$TOOLS_PATH/config.json"

cat > "$CONFIG_PATH" <<EOF
{
  "telegram_token": "${TELEGRAM_TOKEN}",
  "telegram_chat_id": "${TELEGRAM_CHAT_ID}",
  "openai_api_key": "${OPENAI_API_KEY}",
  "assistant_dir": "${AGENT_DIR}",
  "session_timeout_minutes": 30,
  "default_model": "sonnet",
  "budget_usd": {
    "sonnet": 2.0,
    "opus": 5.0
  }
}
EOF
ok "Generated config.json"

# --- Step 6: Ensure directories exist ---
mkdir -p "$AGENT_PATH/tasks/in-progress"
mkdir -p "$AGENT_PATH/tasks/done"
mkdir -p "$AGENT_PATH/tasks/cancelled"
mkdir -p "$AGENT_PATH/activity-log"
mkdir -p "$TOOLS_PATH/logs"

# --- Step 7: Summary ---
echo ""
echo "======================================="
echo "  Setup complete!"
echo "======================================="
echo ""
echo "  Agent directory: $AGENT_DIR/"
echo "  Config file:     $AGENT_DIR/tools/config.json"
echo ""

if [[ "${setup_telegram:-n}" =~ ^[Yy] ]]; then
    echo "  Telegram:        configured"
else
    echo "  Telegram:        not configured (run setup again to add)"
fi

if [[ "${setup_memory:-n}" =~ ^[Yy] ]]; then
    echo "  Long-term memory: configured (LanceDB + OpenAI)"
else
    echo "  Long-term memory: not configured (optional)"
fi

if [[ "${SETUP_SCHEDULE:-n}" =~ ^[Yy] ]]; then
    echo "  Scheduling:      plists generated in ~/Library/LaunchAgents/"
else
    echo "  Scheduling:      not configured"
fi

echo ""
echo "Next steps:"
echo "  1. Edit $AGENT_DIR/SOUL.md    — define your agent's personality"
echo "  2. Edit $AGENT_DIR/STYLE.md   — set communication style"
echo "  3. Open Claude Code in this directory and start chatting!"
echo ""
echo "Docs: docs/customization.md (personality), docs/telegram.md (bot setup)"
echo ""
