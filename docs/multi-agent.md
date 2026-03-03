# Multi-Agent Setup

You can run multiple agents with different personalities, each with its own Telegram bot.

## Agent Types

### Full agent (primary)

The `assistant/` directory (or whatever you renamed it to). Has the complete structure:

```
assistant/
  SOUL.md, STYLE.md, MEMORY.md, OLD-MEMORY.md
  tasks/          -- task tracking
  activity-log/   -- daily records
  tools/          -- scripts, prompts, config, bot
```

There is one full agent. It owns the shared tooling (telegram-bot.py, run.sh, prompts, launchd templates).

### Lite agent (additional)

Lives under `agents/<name>/`. Minimal structure:

```
agents/language-coach/
  SOUL.md          -- personality
  STYLE.md         -- communication style
  MEMORY.md        -- working memory
  config.json      -- telegram token + chat_id
```

No tasks/, activity-log/, or tools/ directories. Lite agents use the primary agent's `telegram-bot.py` and only need a separate Telegram bot token.

## Adding a New Agent

### 1. Create the directory

```bash
mkdir -p agents/my-agent
```

### 2. Write identity files

Create three files:

- **SOUL.md**: Identity, values, thinking methods. See the example in `agents/example-language-coach/SOUL.md`.
- **STYLE.md**: Tone, format rules, don'ts. Use wrong/right pairs to calibrate.
- **MEMORY.md**: Start with user basics and empty sections for projects/pending items.

### 3. Create config.json

```json
{
  "telegram_token": "your-bot-token-from-botfather",
  "telegram_chat_id": "your-chat-id"
}
```

Each agent needs its own Telegram bot (create one via @BotFather). The `telegram_chat_id` can be the same across agents if you want all bots to respond to the same user.

### 4. Create a launchd plist

Copy the Telegram template and set `AGENT_DIR` to point to your new agent:

```bash
cp assistant/tools/launchd/com.assistant.telegram.plist.template \
   ~/Library/LaunchAgents/com.my-agent.telegram.plist
```

Edit the plist:
- Change `Label` to `com.my-agent.telegram`
- `ProgramArguments`: python3 path and `assistant/tools/telegram-bot.py` (same shared script)
- Add `AGENT_DIR` to `EnvironmentVariables` with value `agents/my-agent`
- Update `ASSISTANT_TELEGRAM_TOKEN` and `ASSISTANT_ALLOWED_CHATS` with the new bot's credentials
- Update log paths to avoid overwriting the primary agent's logs

### 5. Load and test

```bash
launchctl load ~/Library/LaunchAgents/com.my-agent.telegram.plist
```

Send a message to the new bot on Telegram. Check logs at `assistant/tools/logs/telegram.log`.

## How AGENT_DIR Works

The `AGENT_DIR` environment variable tells `telegram-bot.py` which agent directory to use. It affects:

- Which SOUL.md, STYLE.md, MEMORY.md are loaded
- Which config.json is read for tokens and settings
- Which session-prompt.md template is used for new sessions
- Which scope is used for long-term memory isolation

If `AGENT_DIR` is not set, the bot falls back to the `assistant_dir` value in config.json (default: `assistant`).

## Shared Bot Script

There is one `telegram-bot.py`. Multiple instances run simultaneously, each with a different `AGENT_DIR`:

```
Instance 1: AGENT_DIR=assistant        → reads assistant/SOUL.md, etc.
Instance 2: AGENT_DIR=agents/coach     → reads agents/coach/SOUL.md, etc.
Instance 3: AGENT_DIR=agents/advisor   → reads agents/advisor/SOUL.md, etc.
```

Each instance:
- Uses its own bot token (from its own config.json)
- Maintains its own session state
- Has its own PID lock (prevents duplicate instances of the same agent)
- Writes to scoped long-term memory (if enabled)

## Example: Language Coach

The `agents/example-language-coach/` directory is a working reference. It demonstrates:

- A focused SOUL.md with domain-specific values (Correction > Encouragement)
- A STYLE.md tuned for mobile chat (short responses, bold corrections)
- A MEMORY.md structured for tracking learner progress (mistake patterns, mastered patterns, vocabulary)
- A minimal config.json with just Telegram credentials

To activate it: fill in the token and chat_id in its config.json, create a launchd plist pointing `AGENT_DIR` to `agents/example-language-coach`, and load it.
