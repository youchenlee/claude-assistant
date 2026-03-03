# claude-assistant Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create an open-source, ready-to-clone personal AI assistant framework powered by Claude Code, generalized from isacl's Lucy system.

**Architecture:** Monorepo template repo. Users clone, run `setup.sh`, customize SOUL.md/STYLE.md, and have a working assistant with optional Telegram bot, scheduled tasks, and long-term memory.

**Tech Stack:** Claude Code CLI, Python 3 (stdlib), Bash, macOS launchd, LanceDB (optional), OpenAI API (optional for embeddings)

**Reference:** Design doc at `open-assistant/docs/plans/2026-03-02-claude-assistant-design.md`

**Source material:** isacl's live system at `00-lucy/` (read-only reference, do not modify)

---

## Phase 1: Scaffold & Static Content

### Task 1: Create directory structure and .gitignore

**Files:**
- Create: `open-assistant/.gitignore`
- Create: `open-assistant/assistant/tasks/in-progress/.gitkeep`
- Create: `open-assistant/assistant/tasks/done/.gitkeep`
- Create: `open-assistant/assistant/tasks/cancelled/.gitkeep`
- Create: `open-assistant/assistant/activity-log/.gitkeep`
- Create: `open-assistant/assistant/tools/prompts/.gitkeep`
- Create: `open-assistant/assistant/tools/launchd/.gitkeep`
- Create: `open-assistant/assistant/tools/logs/.gitkeep`
- Create: `open-assistant/agents/example-language-coach/.gitkeep`
- Create: `open-assistant/docs/.gitkeep`

**Step 1: Create all directories and .gitignore**

```bash
cd open-assistant

# Agent directories
mkdir -p assistant/tasks/{in-progress,done,cancelled}
mkdir -p assistant/activity-log
mkdir -p assistant/tools/{prompts,launchd,logs}

# Additional agents
mkdir -p agents/example-language-coach

# Docs (plans/ already exists)
mkdir -p docs
```

`.gitignore`:
```
# Secrets
config.json
*.plist
!*.plist.template

# Runtime
assistant/tools/logs/
assistant/tools/memory-db/
assistant/tools/memory-venv/
assistant/tools/__pycache__/
*.pyc

# macOS
.DS_Store

# Editor
.vscode/
.idea/
```

**Step 2: Add .gitkeep files to empty directories**

Add `.gitkeep` to: `assistant/tasks/in-progress/`, `assistant/tasks/done/`, `assistant/tasks/cancelled/`, `assistant/activity-log/`, `assistant/tools/logs/`

**Step 3: Commit**

```bash
git add -A
git commit -m "scaffold: create directory structure and .gitignore"
```

---

### Task 2: Write CLAUDE.md (framework core instructions)

**Files:**
- Create: `open-assistant/CLAUDE.md`

**Reference:** Read `CLAUDE.md` (root) for structure. Generalize by:
- Removing all Lucy-specific sections
- Removing isacl's personal knowledge base structure references
- Keeping: agent system overview, task tracking rules, memory discipline, automation overview
- Adding: instructions for users to customize

**Content outline:**

```markdown
# Claude Assistant Framework

## Overview
This is a personal AI assistant framework powered by Claude Code.

## Agent System
- Primary agent lives in `assistant/` (rename to your agent's name)
- Additional agents in `agents/<name>/`

### Identity Resolution
- Terminal / auto tasks: reads CLAUDE.md → defaults to primary agent
- Telegram: PERSONA template defines identity per agent

### Standard Agent Structure
- SOUL.md, STYLE.md, MEMORY.md (see docs/customization.md)

## Rules
- Read SOUL.md + STYLE.md + MEMORY.md at conversation start
- Action-oriented: infer intent and execute
- Memory discipline: update MEMORY.md after every meaningful task
- Explore before assuming: read relevant files before proposing changes

## Memory System
### Format
- Each line tagged with #PN @YYYY-MM-DD
- #P0: never expires | #P1: 90 days | #P2: 30 days
- Keep MEMORY.md under 200 lines

## Task Tracking (mandatory)
- Multi-step work MUST have a task ticket in tasks/in-progress/
- See assistant/tasks/README.md for format

## Primary Agent Configuration
### Your Role
Read the following at session start:
- assistant/SOUL.md (personality & values)
- assistant/STYLE.md (communication style)
- assistant/MEMORY.md (current state)

### Memory Maintenance
- Update MEMORY.md after completing work
- Context may be compressed or restarted at any time

## Automation
- Scheduled tasks use `assistant/tools/run.sh`
- Auto tasks must complete autonomously (no interactive questions)
```

**Step 1: Write CLAUDE.md** — generalized from Lucy's version, English, no personal content.

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: add CLAUDE.md framework instructions"
```

---

### Task 3: Write agent identity templates (SOUL.md, STYLE.md, MEMORY.md)

**Files:**
- Create: `open-assistant/assistant/SOUL.md`
- Create: `open-assistant/assistant/STYLE.md`
- Create: `open-assistant/assistant/MEMORY.md`
- Create: `open-assistant/assistant/OLD-MEMORY.md`

**Reference:** Read `00-lucy/SOUL.md`, `00-lucy/STYLE.md`, `00-lucy/PLAYBOOK.md` for structure. Create generic templates with:
- Same section structure
- Example content showing the pattern (not Lucy's personal content)
- Inline comments explaining what each section does and how to customize

**SOUL.md template** should have these sections:
- Identity (who you are)
- Values (what you prioritize — with 2-3 example values)
- How I Think (decision framework — with example questions)
- Work Methods (collaboration style)
- Lessons Learned (empty, grows over time)

**STYLE.md template** should have:
- Tone (with ❌/✅ example pairs)
- Format Rules
- Don'ts

**MEMORY.md template** should have:
- Example entries showing #P0/#P1/#P2 format
- Section structure (Identity, Active Projects, etc.)

**OLD-MEMORY.md**: Empty with header only.

**Step 1: Write all four files**

**Step 2: Commit**

```bash
git add assistant/SOUL.md assistant/STYLE.md assistant/MEMORY.md assistant/OLD-MEMORY.md
git commit -m "feat: add agent identity templates (SOUL, STYLE, MEMORY)"
```

---

### Task 4: Write task tracking system

**Files:**
- Create: `open-assistant/assistant/tasks/README.md`

**Reference:** Read `00-lucy/tasks/README.md`. Generalize by:
- Translating to English
- Removing Lucy-specific executor types (keep the pattern)
- Keeping: file format, frontmatter template, status lifecycle, creation guidelines

**Step 1: Write tasks/README.md**

**Step 2: Commit**

```bash
git add assistant/tasks/
git commit -m "feat: add task tracking system with README and directory structure"
```

---

## Phase 2: Tools & Infrastructure

### Task 5: Write config.example.json

**Files:**
- Create: `open-assistant/assistant/tools/config.example.json`

**Content:**
```json
{
  "telegram_token": "",
  "telegram_chat_id": "",
  "openai_api_key": "",
  "assistant_dir": "assistant",
  "knowledge_base": ".",
  "session_timeout_minutes": 30,
  "default_model": "sonnet",
  "budget_usd": {
    "sonnet": 2.0,
    "opus": 5.0
  }
}
```

**Step 1: Write file**

**Step 2: Commit**

```bash
git add assistant/tools/config.example.json
git commit -m "feat: add config.example.json template"
```

---

### Task 6: Write session-prompt.md (Telegram prompt template)

**Files:**
- Create: `open-assistant/assistant/tools/session-prompt.md`

**Reference:** Read `00-lucy/PERSONA.md` and `00-lucy/SAFETY.md`. Merge safety rules into persona template. Generalize by:
- Using `{AGENT_DIR}` placeholder for agent directory
- Referencing SOUL.md + STYLE.md (not PLAYBOOK)
- Embedding safety rules (no launchctl, no kill)
- Keeping `{message}` placeholder

**Step 1: Write session-prompt.md**

**Step 2: Commit**

```bash
git add assistant/tools/session-prompt.md
git commit -m "feat: add Telegram persona template with embedded safety rules"
```

---

### Task 7: Write notify.py (generalized)

**Files:**
- Create: `open-assistant/assistant/tools/notify.py`

**Reference:** Read `00-lucy/tools/notify.py`. Generalize by:
- Changing env var names from `LUCY_*` to `ASSISTANT_*`
- Config loading uses `AGENT_DIR` or falls back to relative path
- Keep: dedup mechanism, stdin/file/arg input, auto-chunking

**Step 1: Write notify.py** — generalized from Lucy's version

**Step 2: Verify it runs without errors**

```bash
python3 assistant/tools/notify.py --help 2>&1 || python3 assistant/tools/notify.py 2>&1
# Expected: usage message (no crash)
```

**Step 3: Commit**

```bash
git add assistant/tools/notify.py
git commit -m "feat: add notify.py Telegram notification tool"
```

---

### Task 8: Write run.sh (generalized task executor)

**Files:**
- Create: `open-assistant/assistant/tools/run.sh`

**Reference:** Read `00-lucy/tools/run.sh`. Generalize by:
- Deriving paths from script location (no hardcoded `/Users/isacl/`)
- Reading `AGENT_DIR` from config or defaulting to parent directory
- Keeping: lock file mechanism, MEMORY.md backup, OAuth handling, failure alerts
- Using config.json for notification settings

**Step 1: Write run.sh** — make executable

**Step 2: Verify syntax**

```bash
bash -n assistant/tools/run.sh
# Expected: no output (syntax OK)
```

**Step 3: Commit**

```bash
git add assistant/tools/run.sh
git commit -m "feat: add run.sh scheduled task executor"
```

---

### Task 9: Write run-random.sh

**Files:**
- Create: `open-assistant/assistant/tools/run-random.sh`

**Reference:** Read `00-lucy/tools/run-random.sh`. Generalize path handling.

**Step 1: Write run-random.sh** — make executable

**Step 2: Commit**

```bash
git add assistant/tools/run-random.sh
git commit -m "feat: add run-random.sh random-delay wrapper"
```

---

### Task 10: Write scheduled task prompts

**Files:**
- Create: `open-assistant/assistant/tools/prompts/morning.md`
- Create: `open-assistant/assistant/tools/prompts/evening.md`
- Create: `open-assistant/assistant/tools/prompts/memory-clean.md`

**Reference:** Read `00-lucy/tools/prompts/morning.md`, `00-lucy/tools/prompts/evening.md`, `00-lucy/tools/prompts/memory-clean.md`. Generalize by:
- Using `{AGENT_DIR}` references instead of `00-lucy/`
- Removing isacl-specific steps (GitHub repos, specific calendar references)
- Keeping the core pattern: read context → scan → produce output → update memory → log
- Using `assistant/` as default agent directory

**morning.md** core steps:
1. Read SOUL.md + STYLE.md + MEMORY.md
2. Scan tasks/in-progress/ for stale tasks
3. Create/update daily journal (if journal directory configured)
4. Notify highlights via notify.py
5. Update MEMORY.md
6. Write activity-log

**evening.md** core steps:
1. Read identity + memory
2. Review day's changes
3. Scan stale tasks
4. Update MEMORY.md
5. Write activity-log

**memory-clean.md** core steps:
1. Read MEMORY.md
2. Find expired entries (#P1 > 90 days, #P2 > 30 days)
3. Move to OLD-MEMORY.md
4. Ensure MEMORY.md stays ≤ 200 lines

**Step 1: Write all three prompt files**

**Step 2: Commit**

```bash
git add assistant/tools/prompts/
git commit -m "feat: add core scheduled task prompts (morning, evening, memory-clean)"
```

---

### Task 11: Write launchd plist templates

**Files:**
- Create: `open-assistant/assistant/tools/launchd/com.assistant.morning.plist.template`
- Create: `open-assistant/assistant/tools/launchd/com.assistant.evening.plist.template`
- Create: `open-assistant/assistant/tools/launchd/com.assistant.telegram.plist.template`
- Create: `open-assistant/assistant/tools/launchd/com.assistant.memory-clean.plist.template`

**Reference:** Read `00-lucy/tools/launchd/com.lucy.morning.plist` and `com.lucy.telegram.plist` for structure.

Use placeholders: `{{AGENT_NAME}}`, `{{TOOLS_DIR}}`, `{{KB_DIR}}`, `{{PYTHON_PATH}}`, `{{TELEGRAM_TOKEN}}`, `{{CHAT_ID}}`

**Step 1: Write all four template files**

**Step 2: Commit**

```bash
git add assistant/tools/launchd/
git commit -m "feat: add launchd plist templates with placeholders"
```

---

### Task 12: Write Telegram bot (rewrite)

This is the largest task. Rewrite `telegram-bot.py` from scratch, keeping core architecture but removing hardcoded references and simplifying.

**Files:**
- Create: `open-assistant/assistant/tools/telegram-bot.py`

**Reference:** Read `00-lucy/tools/telegram-bot.py` (full file) for the complete feature set.

**Target: ~15KB (down from 51KB)**

**Core architecture to preserve:**
1. Long polling loop with offset persistence
2. Session management (timeout → new session, active → resume)
3. Multi-agent via `AGENT_DIR` env var
4. Self-update detection (mtime comparison → graceful restart)
5. Crash protection (persisted retry counts, rapid restart detection, cooldown)
6. Commands: /opus, /sonnet, /new, /status
7. Long-term memory integration (optional, graceful degradation)
8. Persona.md loading with `{message}` substitution

**Simplifications:**
- All config from config.json + env vars (no hardcoded paths)
- Simpler session digest (summarize → memory update, no complex LLM call)
- Remove session-specific logging complexity
- Cleaner error handling

**Step 1: Study the full original bot**

Read `00-lucy/tools/telegram-bot.py` completely to understand all features.

**Step 2: Write the rewritten bot**

Structure:
```python
# --- Config ---
# Load from config.json + env vars

# --- Logging ---
# Simple file logger

# --- Long-term Memory (optional) ---
# Graceful degradation wrapper

# --- Telegram API ---
# send_message(), get_updates()

# --- Session Management ---
# SessionManager class: create, resume, expire, digest

# --- Command Handling ---
# /opus, /sonnet, /new, /status

# --- Self-Update ---
# mtime detection + graceful restart

# --- Main Loop ---
# Long polling with crash protection
```

**Step 3: Verify syntax**

```bash
python3 -c "import py_compile; py_compile.compile('assistant/tools/telegram-bot.py', doraise=True)"
# Expected: no errors
```

**Step 4: Commit**

```bash
git add assistant/tools/telegram-bot.py
git commit -m "feat: add Telegram bot (rewritten, configurable)"
```

---

### Task 13: Write memory_store.py (generalized)

**Files:**
- Create: `open-assistant/assistant/tools/memory_store.py`

**Reference:** Read `00-lucy/tools/memory_store.py`. Generalize by:
- Config from config.json (no hardcoded paths)
- Derive db path from agent directory
- Keep: hybrid search (vector + BM25 → RRF), scope filtering, importance scoring, recency weighting
- Keep: graceful degradation (works without dependencies)
- Keep: thread safety (double-checked locking)

**Step 1: Write memory_store.py**

**Step 2: Verify syntax**

```bash
python3 -c "import py_compile; py_compile.compile('assistant/tools/memory_store.py', doraise=True)"
# Expected: no errors
```

**Step 3: Commit**

```bash
git add assistant/tools/memory_store.py
git commit -m "feat: add memory_store.py (optional LanceDB long-term memory)"
```

---

## Phase 3: Example Agent & Setup

### Task 14: Write example lite agent (language coach)

**Files:**
- Create: `open-assistant/agents/example-language-coach/SOUL.md`
- Create: `open-assistant/agents/example-language-coach/STYLE.md`
- Create: `open-assistant/agents/example-language-coach/MEMORY.md`
- Create: `open-assistant/agents/example-language-coach/config.json`

**Reference:** Read `00-john/PERSONA.md` and `00-john/MEMORY.md` for inspiration. Create English version showing:
- How a lite agent's SOUL.md is self-contained
- How STYLE.md defines coaching style
- Minimal config.json (just telegram token + chat_id)

**Step 1: Write all four files**

**Step 2: Commit**

```bash
git add agents/example-language-coach/
git commit -m "feat: add example lite agent (language coach)"
```

---

### Task 15: Write setup.sh interactive wizard

**Files:**
- Create: `open-assistant/setup.sh`

**Features:**
1. Detect OS (macOS required for launchd, warn on Linux about cron alternative)
2. Ask agent name → rename `assistant/` directory
3. Ask Telegram setup (y/n) → collect token + chat_id
4. Ask LanceDB setup (y/n) → collect OpenAI key → create venv → install deps
5. Ask scheduling setup (y/n) → select tasks → generate plists from templates
6. Generate `config.json` from `config.example.json` + collected values
7. Create any missing directories
8. Print summary of what was configured and next steps

**Step 1: Write setup.sh** — make executable, include input validation

**Step 2: Verify syntax**

```bash
bash -n setup.sh
# Expected: no output (syntax OK)
```

**Step 3: Commit**

```bash
git add setup.sh
git commit -m "feat: add setup.sh interactive wizard"
```

---

## Phase 4: Documentation

### Task 16: Write README.md

**Files:**
- Create: `open-assistant/README.md`

**Sections:**
- One-line description
- Features list (bullet points)
- Quick Start (5 steps: clone → setup → customize SOUL → start using → optional: Telegram/scheduling)
- Architecture overview (simplified diagram from design doc)
- Project structure (tree view with descriptions)
- Configuration reference
- Links to detailed docs
- License (MIT)
- Credits / Acknowledgments

**Step 1: Write README.md**

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with Quick Start and architecture overview"
```

---

### Task 17: Write documentation files

**Files:**
- Create: `open-assistant/docs/architecture.md`
- Create: `open-assistant/docs/customization.md`
- Create: `open-assistant/docs/scheduling.md`
- Create: `open-assistant/docs/multi-agent.md`
- Create: `open-assistant/docs/long-term-memory.md`
- Create: `open-assistant/docs/telegram.md`

**Content outline per doc:**

**architecture.md**: System diagram (ASCII), data flow for each entry point (terminal, Telegram, auto tasks), memory system diagram, security considerations.

**customization.md**: How to write SOUL.md (with examples), STYLE.md calibration, MEMORY.md format guide, protected directories concept.

**scheduling.md**: How run.sh works, adding new prompts, launchd setup (manual + via setup.sh), cron/systemd alternatives for Linux, lock file mechanism explanation.

**multi-agent.md**: Full vs lite agent, adding a new agent step-by-step, AGENT_DIR mechanism, shared telegram-bot.py, config per agent.

**long-term-memory.md**: Prerequisites (OpenAI API key, Python), setup steps, how hybrid search works, how to query from terminal, troubleshooting.

**telegram.md**: BotFather setup, getting chat_id, config, running the bot, commands, multi-agent Telegram, session management, self-update mechanism.

**Step 1: Write all six docs**

**Step 2: Commit**

```bash
git add docs/
git commit -m "docs: add architecture, customization, scheduling, multi-agent, memory, telegram guides"
```

---

## Phase 5: Final Polish

### Task 18: Add LICENSE file

**Files:**
- Create: `open-assistant/LICENSE`

**Step 1: Write MIT license**

**Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT license"
```

---

### Task 19: End-to-end verification

**Step 1: Verify directory structure matches design**

```bash
find open-assistant -type f | sort
# Compare against design doc structure
```

**Step 2: Verify all Python files have valid syntax**

```bash
python3 -c "
import py_compile
import glob
for f in glob.glob('open-assistant/**/*.py', recursive=True):
    py_compile.compile(f, doraise=True)
    print(f'OK: {f}')
"
```

**Step 3: Verify all shell scripts have valid syntax**

```bash
for f in open-assistant/**/*.sh; do
    bash -n "$f" && echo "OK: $f"
done
```

**Step 4: Verify .gitignore works (no secrets would be committed)**

```bash
cd open-assistant
# Create a fake config.json to verify it's ignored
echo '{"test": true}' > assistant/tools/config.json
git status --porcelain | grep config.json
# Expected: no output (ignored)
rm assistant/tools/config.json
```

**Step 5: Read through README.md and verify Quick Start makes sense**

**Step 6: Final commit if any fixes needed**

---

## Task Dependency Graph

```
Phase 1 (Scaffold & Static Content)
  Task 1 (scaffold) → Task 2 (CLAUDE.md) → Task 3 (identity) → Task 4 (tasks)

Phase 2 (Tools) — can parallelize some
  Task 5 (config)
  Task 6 (persona)
  Task 7 (notify)
  Task 8 (run.sh) → Task 9 (run-random.sh)
  Task 10 (prompts) — depends on Task 8
  Task 11 (launchd templates)
  Task 12 (telegram bot) — depends on Task 5, 6, 7
  Task 13 (memory_store) — depends on Task 5

Phase 3 (Example & Setup)
  Task 14 (example agent) — depends on Task 3
  Task 15 (setup.sh) — depends on Task 5, 11

Phase 4 (Docs)
  Task 16 (README) — depends on all Phase 1-3
  Task 17 (docs) — depends on all Phase 1-3

Phase 5 (Polish)
  Task 18 (LICENSE)
  Task 19 (verification) — depends on everything
```

## Parallelization Opportunities

Within each phase, many tasks are independent:
- **Phase 2**: Tasks 5-7 and 11 can run in parallel. Task 12 and 13 can run in parallel.
- **Phase 4**: Task 16 and 17 can run in parallel.

## Estimated Task Count: 19 tasks
