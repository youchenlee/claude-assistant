# Task Tracking System

Every meaningful unit of work gets a task file for tracking.

## Directory Structure

```
tasks/
├── in-progress/   <- Currently being worked on
├── done/          <- Completed work
├── cancelled/     <- Cancelled work (with reason)
└── README.md      <- This file
```

## File Naming

```
YYYYMMDD-HHMM-short-summary.md
```

Example: `20260302-1400-setup-task-tracking.md`

- Date-time = when the task was created
- Summary should describe the goal, not the process
- No spaces in filename; use `-` as separator

## Frontmatter Template

```yaml
---
created: YYYY-MM-DD HH:MM
requester: user | assistant-auto | assistant
context: trigger source (e.g. terminal, telegram, auto-morning)
executor: who is currently working on this (see Executor section)
last-active: YYYY-MM-DD HH:MM
---
```

## Body Template

```markdown
# Short summary

## Goal
What needs to be achieved.

## Plan
1. Step one
2. Step two

## Progress Log
- YYYY-MM-DD HH:MM: What was done
- YYYY-MM-DD HH:MM: What was done

## Result
(Fill in when completed or cancelled)
```

## Executor Field

Tracks *who* is currently working on a task, used to determine if work is still active:

| executor value | meaning | liveness check |
|---|---|---|
| `claude-code` | Interactive Claude Code session | User-driven; generally alive while session is open |
| `telegram-<session_id>` | Telegram bot session | Stale if `last-active` > 30 minutes |
| `auto-<task_name>` | Scheduled/automated task | Stale if `last-active` > 30 minutes |
| *(empty)* | Completed or cancelled task | -- |

**Update `last-active` whenever progress is made.**

## Status Transitions

- **Create** -- Place in `in-progress/`, set `executor` and `last-active`
- **Complete** -- Move to `done/`, fill in Result, clear `executor`
- **Cancel** -- Move to `cancelled/`, fill in cancellation reason, clear `executor`
- **Resume** -- New session opens file in `in-progress/`, updates `executor` to itself, continues work
- **Stale detection** -- Periodic scans of `in-progress/`; tasks with `last-active` older than 24 hours are flagged as stale and reported to the user

## When to Create Tasks

### Must create

1. User explicitly assigns a task (regardless of size)
2. Work involves more than 3 steps
3. Work may span sessions (session could timeout or be closed)
4. Automated task discovers something requiring human intervention

### Skip

1. Single-question answers ("What does this function do?")
2. Pure information lookups with no follow-up action
3. Items already tracked by another mechanism (e.g. routine scans logged in activity-log)

### Gray area

**Better to over-track than under-track.** An unnecessary task file can be moved to `done/` with "No action needed." A missing task file means the user cannot track it and a new session cannot resume it.
