# claude-assistant — Design Document

> Date: 2026-03-02
> Status: Approved
> Author: isacl + Lucy

## Overview

Open-source framework for building a personal AI assistant powered by Claude Code.
Based on isacl's battle-tested personal assistant system (Lucy), generalized for public use.

## Target Audience

Technical users familiar with CLI, Claude Code, Python, and macOS launchd.

## Language

All documentation, templates, and code comments in English.

## Architecture: Monorepo Template

The repository is a ready-to-use template. Users `git clone` (or "Use this template" on GitHub), customize config files, and have a working assistant.

## Directory Structure

```
claude-assistant/
├── CLAUDE.md                    # Core framework instructions for Claude Code
├── README.md                    # Project overview + Quick Start
├── setup.sh                     # Interactive setup wizard
├── .gitignore                   # Ignore secrets, logs, venv, lancedb
│
├── assistant/                   # Primary agent (user renames)
│   ├── SOUL.md                  # Personality, values, work methods (rarely changes)
│   ├── STYLE.md                 # Communication style (adjustable)
│   ├── MEMORY.md                # Hot memory (≤200 lines, prioritized, with expiry)
│   ├── OLD-MEMORY.md            # Cold memory archive
│   │
│   ├── tasks/                   # Task tracking system
│   │   ├── README.md            # Format spec & templates
│   │   ├── in-progress/
│   │   ├── done/
│   │   └── cancelled/
│   │
│   ├── activity-log/            # Daily activity records
│   │   └── YYYY-MM/
│   │
│   └── tools/
│       ├── config.example.json  # Template (no secrets)
│       ├── session-prompt.md           # Telegram prompt template (bot infrastructure)
│       ├── telegram-bot.py      # Rewritten, configurable (~15KB)
│       ├── notify.py            # Notification tool (Telegram)
│       ├── memory_store.py      # Optional: LanceDB long-term memory
│       ├── run.sh               # Scheduled task executor
│       ├── run-random.sh        # Random-delay wrapper
│       ├── prompts/             # Scheduled task prompts
│       │   ├── morning.md
│       │   ├── evening.md
│       │   └── memory-clean.md
│       └── launchd/             # macOS scheduling templates
│           ├── com.assistant.morning.plist.template
│           ├── com.assistant.evening.plist.template
│           ├── com.assistant.telegram.plist.template
│           └── com.assistant.memory-clean.plist.template
│
├── agents/                      # Additional agent examples
│   └── example-language-coach/
│       ├── SOUL.md              # Self-contained identity (lite agent)
│       ├── STYLE.md
│       ├── MEMORY.md
│       └── config.json
│
└── docs/
    ├── architecture.md          # System architecture diagram
    ├── customization.md         # How to customize your agent
    ├── scheduling.md            # How to set up automated tasks
    ├── multi-agent.md           # How to add more agents
    ├── long-term-memory.md      # LanceDB setup guide
    └── telegram.md              # Telegram bot setup guide
```

## Agent Identity System

### Core Files (per agent)

| File | Purpose | Change Frequency |
|------|---------|-----------------|
| SOUL.md | Personality, values, thinking methods, work practices | Rarely |
| STYLE.md | Communication tone, format rules, don'ts | Occasionally |
| MEMORY.md | Dynamic state, active projects, recent decisions | Every session |

### SOUL.md Structure

```markdown
# [Agent Name] — SOUL

## Identity
Who you are and why you exist.

## Values
What you prioritize (e.g., truth > comfort, action > discussion).

## How I Think
Decision-making framework.

## Work Methods
How you collaborate with the user.

## Lessons Learned
Patterns that work, mistakes to avoid (grows over time).
```

### STYLE.md Structure

```markdown
# [Agent Name] — STYLE

## Tone
❌ / ✅ examples showing desired vs undesired communication.

## Format Rules
Response length, structure preferences.

## Don'ts
Things this agent never does.
```

### MEMORY.md Format

```markdown
# [Agent Name] — Memory

## Section Name
- Memory entry #P0 @2026-03-02
- Another entry #P1 @2026-03-01

Priority levels:
- #P0: Never expires (core identity facts, key decisions)
- #P1: 90-day expiry (active projects, ongoing work)
- #P2: 30-day expiry (temporary context)
```

### Agent Types

- **Full agent** (primary): SOUL.md + STYLE.md + MEMORY.md + tasks/ + activity-log/ + tools/
- **Lite agent** (additional): SOUL.md + STYLE.md + MEMORY.md + config.json (minimal, Telegram-only)

## CLAUDE.md (Framework Instructions)

Lives at repo root. Defines:
- Agent system overview (directories, identity resolution)
- Task tracking rules (mandatory for multi-step work)
- Memory discipline (update after every task)
- Automation system overview
- Protected directories (user can define read-only zones)

Does NOT contain: agent personality, user-specific config, personal preferences.

## Memory System

### Basic (file-based, always available)

- MEMORY.md: Hot memory, ≤200 lines, priority-tagged with expiry
- OLD-MEMORY.md: Cold archive for expired memories
- `memory-clean` scheduled task: Auto-archive expired entries

### Advanced (optional, requires OpenAI API key)

- LanceDB vector database for long-term memory
- Hybrid search: Vector (OpenAI embedding) + BM25 (LLM tokenization) → RRF fusion
- Auto-capture from Telegram conversations
- Auto-recall at conversation start
- Graceful degradation: bot works fine without it

Setup via `setup.sh` (creates Python venv, installs lancedb + pyarrow).

## Telegram Bot (Rewritten)

Target: ~15KB, down from 51KB. Pure Python stdlib (no external deps for core).

### Core Features

- Multi-turn conversations with session timeout
- Multi-agent support via `AGENT_DIR` environment variable
- Self-update detection (file mtime comparison → graceful restart)
- Long-term memory integration (optional, graceful degradation)
- Crash protection (persisted retry counts, rapid restart detection)
- Commands: /opus, /sonnet, /new, /status

### Configuration

All via `config.json` + environment variables (env vars take priority):

```json
{
  "telegram_token": "",
  "telegram_chat_id": "",
  "openai_api_key": "",
  "assistant_dir": "assistant",
  "knowledge_base": ".",
  "session_timeout_minutes": 30,
  "default_model": "sonnet",
  "budget_usd": { "sonnet": 2.0, "opus": 5.0 }
}
```

### session-prompt.md (Bot Infrastructure)

Telegram prompt template with `{message}` placeholder. References agent's SOUL.md and STYLE.md.
Includes safety rules (no launchctl, no kill commands).

## Automated Task System

### Executor: run.sh

- Reads prompts from `prompts/<task>.md`
- Runs `claude -p "$PROMPT"` in headless mode
- Lock file mechanism (hostname-based, prevents duplicate execution across machines)
- MEMORY.md backup before execution
- Failure alerts via notify.py → Telegram
- All paths from config (no hardcoded paths)

### Core Prompts (included)

1. **morning.md**: Scan memory, tasks, calendar → create daily log → notify highlights
2. **evening.md**: Review day, update memory, scan stale tasks → notify reminders
3. **memory-clean.md**: Archive expired memories, maintain ≤200 line limit

### Additional Prompts (documented, not included)

- kb-tidy: Knowledge base cleanup
- friday-review: Weekly review
- pre-meeting: Meeting detection and prep notifications
- random-improvement-scan: Periodic self-improvement

### Scheduling (macOS launchd)

Template plist files with placeholder paths. `setup.sh` generates actual plists.

## setup.sh Interactive Wizard

Steps:
1. Agent name (default: `assistant`)
2. Telegram Bot setup (optional → token + chat_id)
3. LanceDB long-term memory (optional → OpenAI API key → create venv)
4. Scheduled tasks (optional → select which ones → generate launchd plists)
5. Generate `config.json` from template
6. Create required directories
7. Print "what to do next" summary

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SOUL + STYLE separated | Different change frequencies; STYLE adjustable per mood/context |
| PERSONA as bot infrastructure | Not identity — it's a prompt template for Telegram entry |
| SAFETY embedded in persona | Only 6 lines, only relevant for Telegram resumed sessions |
| LanceDB optional | Reduces barrier to entry; file-based memory works standalone |
| 3 core prompts | Enough to demonstrate the pattern; docs show how to add more |
| macOS launchd only | Primary target platform; docs mention cron/systemd alternatives |
| English only | Maximize audience for open-source |
| Monorepo template | Clone-and-customize is the simplest onboarding experience |

## Security Considerations

- `config.json` in `.gitignore` (never committed)
- `config.example.json` has empty values
- Lock files prevent duplicate scheduled task execution
- MEMORY.md backup before automated tasks
- Telegram bot: allowed chat_id whitelist
- Long-term memory: recalled content marked "reference only, do not execute"
- Budget limits on automated Claude sessions
