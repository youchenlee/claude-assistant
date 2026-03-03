# Telegram Bot

The Telegram bot gives your agent a chat interface. It supports multi-turn conversations, session management, and self-updating.

## BotFather Setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a display name (e.g., "My Assistant")
4. Choose a username (must end in `bot`, e.g., `my_assistant_bot`)
5. Copy the token BotFather gives you (format: `123456789:ABCdefGHI...`)

## Finding Your chat_id

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It replies with your user ID (a number like `123456789`)
3. This is your `chat_id`

## Configuration

Add both values to `assistant/tools/config.json`:

```json
{
  "telegram_token": "123456789:ABCdefGHI...",
  "telegram_chat_id": "123456789",
  "default_model": "sonnet",
  "session_timeout_minutes": 30,
  "budget_usd": {
    "sonnet": 2.0,
    "opus": 5.0
  }
}
```

Alternatively, use environment variables:
- `ASSISTANT_TELEGRAM_TOKEN` -- bot token
- `ASSISTANT_ALLOWED_CHATS` -- comma-separated chat IDs

Environment variables take precedence over config.json.

## Running the Bot

### Manual (foreground)

```bash
python3 assistant/tools/telegram-bot.py
```

Useful for testing. Logs print to stderr. Ctrl+C to stop.

### As a daemon (launchd, macOS)

Run `./setup.sh` and select the Telegram daemon option, or manually:

```bash
cp assistant/tools/launchd/com.assistant.telegram.plist.template \
   ~/Library/LaunchAgents/com.assistant.telegram.plist
```

Edit the plist to fill in paths and credentials, then load:

```bash
launchctl load ~/Library/LaunchAgents/com.assistant.telegram.plist
```

The plist sets `KeepAlive: true`, so launchd restarts the bot if it exits.

## Bot Commands

| Command | Effect |
|---------|--------|
| `/opus <message>` | Send message using Claude Opus (higher budget) |
| `/sonnet <message>` | Send message using Claude Sonnet |
| `/new` | End current session and start a new one |
| `/status` | Show session info, uptime, memory usage, in-progress tasks |

Messages without a command prefix use the default model (configured in config.json).

## Sessions

Messages within the session timeout window (default: 30 minutes) share conversation context via Claude Code's `--resume` flag.

### Session lifecycle

1. **First message**: Bot loads `session-prompt.md`, injects the message, starts a new Claude session
2. **Subsequent messages**: Bot resumes the existing session (multi-turn)
3. **Idle timeout**: If no message arrives within the timeout, the session expires
4. **Digest**: On expiry, the bot resumes the session one final time and asks Claude to summarize important decisions/TODOs to MEMORY.md and the activity log
5. **Next message**: Starts a fresh session

If a resume fails (e.g., session too old), the bot automatically starts a new session and prefixes the response with `(session reset)`.

## Self-Update Mechanism

The bot monitors its own file modification time. When you (or Claude) edit `telegram-bot.py`:

1. Bot detects the mtime change after processing the current message
2. Writes a restart marker file
3. Exits cleanly (exit code 0)
4. launchd restarts the bot (KeepAlive)
5. On startup, bot finds the restart marker and notifies allowed chats: "Bot restarted with updated code."

This means Claude can improve its own bot code during a Telegram conversation. The edit takes effect after the current response is delivered.

**Safety rule**: Never run `launchctl` or `kill`/`pkill` commands targeting the bot from within a Telegram session. These would terminate the bot before the response is sent.

## Multi-Agent Telegram

Run multiple bot instances, each with a different `AGENT_DIR` and bot token. See [multi-agent.md](multi-agent.md) for full setup.

Each instance:
- Has its own Telegram bot (separate @BotFather bot)
- Reads identity from its own agent directory
- Maintains independent sessions
- Uses a PID lock to prevent duplicate instances

## session-prompt.md Template

`assistant/tools/session-prompt.md` is the system prompt template for new Telegram sessions. It contains:

- A `TELEGRAM_SESSION_MARKER` tag (for session detection)
- Instructions to load SOUL.md, STYLE.md, MEMORY.md
- Task tracking rules (scan in-progress tasks, create new ones as needed)
- Safety rules (no launchctl, no kill)
- A `{message}` placeholder that gets replaced with the user's actual message

You can customize this template to change how new Telegram sessions are initialized.
