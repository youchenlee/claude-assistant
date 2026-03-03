# Claude Assistant Framework

## Overview

This is a personal AI assistant framework powered by Claude Code. The primary agent directory is `assistant/` (rename it to match your agent's name). Additional agents live under `agents/<name>/`.

## Agent System

### Identity Resolution

- **Terminal / scheduled tasks**: Claude reads this file, then loads the primary agent's identity files from `assistant/`.
- **Telegram**: The `session-prompt.md` template in `assistant/tools/` defines the session prompt per agent, selected via `AGENT_DIR` environment variable.

### Standard Agent Structure

Each agent directory contains:

| File | Purpose | Change Frequency |
|------|---------|-----------------|
| `SOUL.md` | Personality, values, thinking methods | Rarely |
| `STYLE.md` | Communication tone, format rules | Occasionally |
| `MEMORY.md` | Active state, projects, recent decisions | Every session |
| `OLD-MEMORY.md` | Archive for expired memories | Periodically |

Supporting directories (primary agent only):

- `tasks/` -- Task tracking (in-progress, done, cancelled)
- `activity-log/` -- Daily activity records
- `tools/` -- Automation scripts, prompts, config

### Agent Types

- **Full agent** (primary): All identity files + tasks/ + activity-log/ + tools/
- **Lite agent** (additional): SOUL.md + STYLE.md + MEMORY.md + config.json

---

## Session Start (mandatory)

At the beginning of every session, read these files from the primary agent directory:

1. `assistant/SOUL.md` -- personality and values
2. `assistant/STYLE.md` -- communication style
3. `assistant/MEMORY.md` -- current state and active context

Adopt the identity, tone, and context defined in these files. If MEMORY.md references in-progress tasks, scan `assistant/tasks/in-progress/` and prioritize continuing unfinished work.

---

## Core Rules

- **Action-oriented**: Infer intent and execute. Adjust if wrong.
- **Explore before assuming**: Read relevant files before proposing changes. Never guess about code or content you haven't opened.
- **Memory discipline**: Update MEMORY.md after every meaningful task. Context may be compressed or restarted at any time -- your memory file is the only thing that persists.
- **Protected directories**: If the user defines directories as protected (read-only), you may annotate or update status fields but must not alter the original meaning. Ask before making substantive changes.

---

## Memory System

### MEMORY.md Format

Each entry is a single line tagged with a priority level and date:

```
- Entry text #P0 @2026-03-02
- Another entry #P1 @2026-02-15
- Temporary note #P2 @2026-03-01
```

### Priority Levels

| Tag | Meaning | Expiry | Date convention |
|-----|---------|--------|-----------------|
| `#P0` | Core facts (identity, key decisions) | Never | Date written |
| `#P1` | Active projects, ongoing work | 90 days | Date of event |
| `#P2` | Temporary context | 30 days | Date of event |

### Rules

- Keep MEMORY.md under 200 lines.
- Expired entries move to OLD-MEMORY.md (cold archive).
- The `memory-clean` scheduled task automates archival; you can also do it manually.
- **Update after every completed task.** This is the most important operational discipline.

---

## Task Tracking (mandatory)

Multi-step work **must** have a task ticket. This is not optional.

### Directory Structure

```
assistant/tasks/
  in-progress/   -- Active work
  done/           -- Completed
  cancelled/      -- Cancelled (with reason)
```

### Filename Format

```
YYYYMMDD-HHMM-short-description.md
```

The datetime is when the task was created. Use hyphens, no spaces.

### Frontmatter Template

```yaml
---
created: YYYY-MM-DD HH:MM
requester: user | assistant-auto | assistant
context: trigger source (telegram / auto-<task> / claude-code)
executor: who is currently executing (see below)
last-active: YYYY-MM-DD HH:MM
---
```

### Body Template

```markdown
# Short description

## Goal
What needs to be accomplished.

## Plan
1. Step one
2. Step two

## Progress
- YYYY-MM-DD HH:MM: What was done

## Result
(Fill when completed or cancelled)
```

### Executor Field

Tracks who is currently working on a task:

| Value | Meaning | Considered alive? |
|-------|---------|-------------------|
| `claude-code` | Interactive Claude Code session | Yes (user-driven) |
| `telegram-<id>` | Telegram bot session | last-active > 30 min = stale |
| `auto-<task>` | Scheduled task | last-active > 30 min = stale |
| (empty) | Completed or cancelled | -- |

Update `last-active` with every progress entry.

### Lifecycle

- **Create** in `in-progress/` with executor and last-active set.
- **Complete**: Move to `done/`, fill Result, clear executor.
- **Cancel**: Move to `cancelled/`, fill reason, clear executor.
- **Resume**: New session opens task in `in-progress/`, updates executor to itself.

### When to Create a Task

**Must create:**
- User assigns work (any size)
- Work exceeds 3 steps
- Work may span sessions

**Skip:**
- Single-question answers
- Pure information lookups with no follow-up action

**When in doubt, create one.** A task created but unused costs nothing. A missed task means no continuity across sessions.

---

## Automation

Scheduled tasks use `assistant/tools/run.sh`, which executes prompts from `assistant/tools/prompts/` via `claude -p` in headless mode.

### Key mechanisms

- **Lock files**: Hostname-based, prevents duplicate execution across machines.
- **MEMORY.md backup**: Taken before each run to guard against concurrent writes.
- **Failure alerts**: Sent via `notify.py` to Telegram (if configured).
- **Activity logging**: Each run writes to `assistant/activity-log/YYYY-MM/YYYY-MM-DD.md`.

### Core scheduled tasks

| Task | Schedule | Purpose |
|------|----------|---------|
| `morning` | Daily, morning | Scan memory, tasks, calendar; create daily summary; notify highlights |
| `evening` | Daily, evening | Review day, update memory, flag stale tasks |
| `memory-clean` | Weekly | Archive expired memory entries, enforce 200-line limit |

Automated tasks must complete fully without user interaction.

---

## Permissions

- The agent can read and write all files in the knowledge base unless marked as protected.
- Changes to the knowledge base structure should be justified and recorded in MEMORY.md.
- **Never** run `launchctl` commands (bootout/bootstrap/unload/load) or `kill`/`pkill` targeting the Telegram bot process from within a Telegram session -- these will terminate the bot before the response is delivered.
