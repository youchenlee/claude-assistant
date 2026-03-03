# Architecture

## System Overview

claude-assistant is a personal AI assistant framework built on Claude Code. It provides three interaction modes, a persistent memory system, and structured task tracking.

```
        +-----------+       +-------------+      +-------------+
        | Terminal   |       | Telegram    |      | Automation  |
        | (claude)   |       | (bot.py)    |      | (run.sh)    |
        +-----------+       +-------------+      +-------------+
               |                    |                    |
               v                    v                    v
        +---------------------------------------------------+
        |              Claude Code (CLI)                     |
        |   Always reads CLAUDE.md from project root         |
        +---------------------------------------------------+
               |
               v
        +---------------------------------------------------+
        |              Agent Identity Layer                  |
        |   SOUL.md  |  STYLE.md  |  MEMORY.md              |
        +---------------------------------------------------+
               |
               v
        +---------------------------------------------------+
        |              Shared Infrastructure                 |
        |   tasks/   |  activity-log/  |  LanceDB (opt.)    |
        +---------------------------------------------------+
```

`CLAUDE.md` is not an entry point — it is the foundation layer. Claude Code **always** reads it automatically when launched from the project directory, regardless of which entry point triggered the session.

## Entry Points

### Terminal (interactive)

User runs `claude` in the project directory. Claude Code automatically reads `CLAUDE.md`, then loads agent identity files as instructed, and starts an interactive session. Full tool access.

### Telegram (chat)

`telegram-bot.py` polls for messages. On each message:
1. Check chat ID whitelist
2. Load or resume a session (via `session-prompt.md` template)
3. Call `claude -p` with the message
4. Return response to Telegram
5. After idle timeout, digest session to MEMORY.md

### Automation (scheduled)

`run.sh` executes a prompt file via `claude -p` in headless mode:
1. Derive paths from script location
2. Acquire hostname-based lock file
3. Back up MEMORY.md
4. Run Claude with budget cap
5. Send failure alerts via `notify.py`

## Memory System

```
+-------------------+    expired    +-------------------+
|   MEMORY.md       | -----------> |  OLD-MEMORY.md    |
|   (hot, ~200 ln)  |   archive    |  (cold, unlimited)|
+-------------------+              +-------------------+
        ^
        | update after every task
        |
+-------------------+
|   LanceDB         |  (optional)
|   Vector + BM25   |
|   hybrid search   |
+-------------------+
```

- **MEMORY.md**: Curated working memory. Always loaded. Entries tagged `#P0` (permanent), `#P1` (90d), `#P2` (30d).
- **OLD-MEMORY.md**: Archive for expired entries. Kept for reference.
- **LanceDB**: Optional long-term memory. Stores Telegram conversations as embeddings. Queried at session start for relevant context.

## Task Lifecycle

```
  Create             Complete           (or)  Cancel
    |                   |                       |
    v                   v                       v
in-progress/ -----> done/               cancelled/
    ^
    |  Resume (new session picks up stale task)
```

Each task file tracks `executor` (who is working on it) and `last-active` (when they last touched it). Sessions scan `in-progress/` on start and resume stale tasks.

## Security Considerations

| Concern | Mechanism |
|---------|-----------|
| Secrets exposure | `config.json` is gitignored; template `config.example.json` committed instead |
| Unauthorized Telegram access | Chat ID whitelist in config; unrecognized IDs are rejected |
| Runaway costs | Per-model budget caps (`--max-budget-usd`) in both bot and run.sh |
| Duplicate automation | Hostname-based lock files with race condition guard (write, sleep, re-read) |
| Concurrent memory writes | MEMORY.md backed up before each automated run |
| Bot process safety | Bot self-detects code changes and restarts gracefully; `launchctl`/`kill` commands are forbidden from within Telegram sessions |
