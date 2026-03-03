You are a personal assistant. Read your identity and memory files first:
`assistant/SOUL.md`, `assistant/STYLE.md`, and `assistant/MEMORY.md`.

## Task: Morning Planning

This is an automated task — no human is present. Do not use AskUserQuestion or any interactive prompts. Complete all steps autonomously. If a step fails, skip it gracefully and note the failure in the activity log.

### Steps

1. **Read context**
   - `assistant/MEMORY.md` — current state and active context
   - `assistant/SOUL.md` — identity and values (skim for any lessons-learned relevant to today)

2. **Scan tasks**
   - List all files in `assistant/tasks/in-progress/`
   - Read each task's frontmatter: `executor`, `last-active`
   - Classify each task:
     - **Stale**: `last-active` more than 24 hours ago — flag for attention
     - **Active**: updated within 24 hours — note current status
   - If there are no tasks, note that and move on

3. **Scan upcoming memory items**
   - Check `assistant/MEMORY.md` for #P1 and #P2 entries with dates in the next 3 days
   - These are potential reminders or deadlines worth surfacing

4. **Send notification** (if anything noteworthy)
   - If there are stale tasks, upcoming deadlines, or important items, send a summary via notify.py:
     ```bash
     python3 assistant/tools/notify.py "Morning summary:
     - [highlight 1]
     - [highlight 2]"
     ```
   - If nothing noteworthy, skip the notification entirely — do not send empty or trivial messages

5. **Update MEMORY.md**
   - If any new information was discovered (e.g., a task appears abandoned, a deadline is imminent), add or update the relevant entry
   - Follow the format: `- Entry text #PN @YYYY-MM-DD`

6. **Write activity log**
   - Path: `assistant/activity-log/YYYY-MM/YYYY-MM-DD.md`
   - If the file does not exist, create it with the header: `# Activity Log YYYY-MM-DD`
   - If the directory does not exist, create it
   - Append a section:
     ```
     ## HH:MM Morning Planning (auto)

     [Detailed record: what was scanned, how many tasks found, stale task details,
     notifications sent, steps skipped and why, any issues encountered]
     ```
   - Be specific enough that someone reading the log later can fully understand what happened

### Rules

- This is an unattended automated task. Do not use AskUserQuestion or request human input
- If a step fails (e.g., notify.py not configured, no tasks directory), skip it and record the failure in the activity log
- Keep notifications concise — bullet points, no filler
- Output a brief summary of what was done when finished
