# claude-assistant

A personal AI assistant framework powered by Claude Code.

Define your agent's personality in markdown, give it persistent memory, and let it work for you -- in your terminal, over Telegram, or on a schedule.

## Features

- **Persistent identity** -- SOUL.md and STYLE.md define personality and communication style across sessions
- **Priority-based memory** -- hot memory with automatic expiry (#P0/#P1/#P2), cold archive for expired entries
- **Task tracking** -- file-based work tickets with lifecycle management (create, resume, complete, cancel)
- **Telegram bot** -- multi-turn conversations, multi-agent support, self-updating on file changes
- **Scheduled automation** -- morning planning, evening review, memory cleanup, all running headlessly
- **Multi-agent support** -- primary assistant plus additional specialized agents (e.g., language coach)
- **Long-term memory** -- optional LanceDB vector + BM25 hybrid search for conversation history
- **macOS launchd integration** -- automated scheduling with hostname-based lock-file deduplication

## Quick Start

```bash
git clone https://github.com/youchenlee/claude-assistant.git
cd claude-assistant
./setup.sh
```

The setup wizard walks you through:

1. Naming your agent
2. Telegram bot (optional)
3. Long-term memory with LanceDB (optional)
4. Scheduled tasks via launchd (optional)

Then customize your agent:

```bash
# Define your agent's personality
$EDITOR assistant/SOUL.md

# Set communication style
$EDITOR assistant/STYLE.md

# Open Claude Code and start chatting
claude
```

## How It Works

The framework has three entry points, all converging on the same identity system:

**Terminal** -- Claude Code reads `CLAUDE.md` at the project root, which instructs it to load the agent's identity files (`SOUL.md`, `STYLE.md`, `MEMORY.md`). You get an interactive session with a persistent personality.

**Telegram** -- The bot polls for messages and spawns a Claude session for each conversation. The `session-prompt.md` template injects the agent's identity into each session. Multiple agents are supported via the `AGENT_DIR` environment variable.

**Automation** -- macOS launchd (or cron/systemd on Linux) triggers `run.sh`, which feeds a prompt file to `claude -p` in headless mode. The agent executes the task autonomously -- scanning calendars, reviewing the day, cleaning up memory.

## Project Structure

```
claude-assistant/
├── CLAUDE.md                          # Framework instructions (Claude reads this first)
├── README.md                          # This file
├── setup.sh                           # Interactive setup wizard
├── LICENSE                            # MIT
│
├── assistant/                         # Primary agent directory (rename to your agent's name)
│   ├── SOUL.md                        # Personality, values, thinking methods
│   ├── STYLE.md                       # Communication tone and format rules
│   ├── MEMORY.md                      # Hot memory (≤200 lines, priority-tagged)
│   ├── OLD-MEMORY.md                  # Cold archive for expired memories
│   │
│   ├── tasks/                         # File-based task tracking
│   │   ├── in-progress/               # Active work
│   │   ├── done/                      # Completed
│   │   └── cancelled/                 # Cancelled (with reason)
│   │
│   ├── activity-log/                  # Daily activity records
│   │
│   └── tools/
│       ├── config.example.json        # Configuration template (no secrets)
│       ├── session-prompt.md           # Telegram session prompt template
│       ├── notify.py                  # Telegram notification helper
│       ├── memory_store.py            # LanceDB long-term memory (optional)
│       ├── run.sh                     # Scheduled task executor
│       ├── run-random.sh              # Random-delay wrapper for run.sh
│       ├── prompts/                   # Headless task prompts
│       │   ├── morning.md             # Daily planning
│       │   ├── evening.md             # Daily review
│       │   └── memory-clean.md        # Weekly memory archival
│       └── launchd/                   # macOS scheduling templates
│           └── com.assistant.*.plist.template
│
├── agents/                            # Additional agents
│   └── example-language-coach/        # Example lite agent
│       ├── SOUL.md
│       ├── STYLE.md
│       ├── MEMORY.md
│       └── config.json
│
└── docs/                              # Documentation
```

## Agent Identity System

Each agent is defined by three markdown files:

**SOUL.md** -- Who the agent is. Personality, values (expressed as trade-offs like "truth > comfort"), decision-making framework, collaboration style, and lessons learned. This file rarely changes.

**STYLE.md** -- How the agent communicates. Tone calibrated through wrong/right example pairs, format rules, and hard "don't" boundaries. Adjust this whenever you want to change how responses feel.

**MEMORY.md** -- What the agent knows right now. Each entry is a single self-contained line tagged with a priority level and date:

```
- User prefers terminal over GUI #P0 @2026-03-02
- Working on API migration project #P1 @2026-02-15
- Meeting with design team moved to Friday #P2 @2026-03-01
```

| Tag | Meaning | Expiry |
|-----|---------|--------|
| `#P0` | Core facts | Never |
| `#P1` | Active projects | 90 days |
| `#P2` | Temporary context | 30 days |

The agent updates MEMORY.md after every meaningful task. Expired entries are archived to OLD-MEMORY.md automatically by the `memory-clean` scheduled task.

## Documentation

- [docs/customization.md](docs/customization.md) -- Customize your agent's personality and behavior
- [docs/telegram.md](docs/telegram.md) -- Set up the Telegram bot
- [docs/scheduling.md](docs/scheduling.md) -- Configure automated tasks (launchd, cron, systemd)
- [docs/multi-agent.md](docs/multi-agent.md) -- Add specialized agents
- [docs/long-term-memory.md](docs/long-term-memory.md) -- Enable LanceDB vector + keyword memory
- [docs/architecture.md](docs/architecture.md) -- System architecture and design decisions

## Requirements

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (authenticated via `claude login`)
- Python 3.10+ (for Telegram bot, notifications, and long-term memory)
- macOS (for launchd scheduling; see [docs/scheduling.md](docs/scheduling.md) for Linux alternatives with cron or systemd)

## License

[MIT](LICENSE)

## Acknowledgments

Built by [youchenlee](https://github.com/youchenlee). Extracted from a real, battle-tested personal assistant system.

The long-term memory system was inspired by [memory-lancedb-pro](https://github.com/win4r/memory-lancedb-pro). The multi-agent architecture drew ideas from [OpenClaw](https://openclaw.ai/).
