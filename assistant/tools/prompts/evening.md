You are a personal assistant. Read your identity and memory files first:
`assistant/SOUL.md`, `assistant/STYLE.md`, and `assistant/MEMORY.md`.

## Task: Evening Review

This is an automated task — no human is present. Do not use AskUserQuestion or any interactive prompts. Complete all steps autonomously. If a step fails, skip it gracefully and note the failure in the activity log.

### Steps

1. **Read context**
   - `assistant/MEMORY.md` — current state and active context
   - Today's activity log: `assistant/activity-log/YYYY-MM/YYYY-MM-DD.md` (if it exists)

2. **Review today's activity**
   - Search for `.md` files modified today across the knowledge base (use find or similar)
   - Exclude non-content directories: `.obsidian`, `node_modules`, `.git`, `attachments`
   - Summarize what changed: how many files modified, which areas of the knowledge base were touched
   - Note any significant changes (new files, large edits, deleted content)

3. **Scan tasks**
   - List all files in `assistant/tasks/in-progress/`
   - Read each task's frontmatter: `executor`, `last-active`
   - Flag tasks where `last-active` is more than 24 hours ago as stale
   - Check if any tasks in `in-progress/` appear to be completed based on their progress notes — if so, note them as candidates to move to `done/`

4. **Proactive fixes** (conservative — only act on clear-cut cases)
   - If a task in `in-progress/` has a Result section filled out, move it to `done/`
   - If MEMORY.md contains obviously expired #P2 entries (> 30 days), move them to OLD-MEMORY.md
   - Record all fixes in the activity log

5. **Update MEMORY.md**
   - Add new conclusions, decisions, or state changes from today
   - Mark completed items as done or remove them
   - Follow the format: `- Entry text #PN @YYYY-MM-DD`

6. **Send notification** (only if important)
   - If there are reminders for tomorrow (check MEMORY.md for items dated tomorrow or the day after), send via notify.py:
     ```bash
     python3 assistant/tools/notify.py "Evening reminder:
     - [reminder 1]
     - [reminder 2]"
     ```
   - If stale tasks have been stale for more than 48 hours, include them in the notification
   - If nothing requires attention, do not send a notification

7. **Write activity log**
   - Path: `assistant/activity-log/YYYY-MM/YYYY-MM-DD.md`
   - If the file does not exist, create it with the header: `# Activity Log YYYY-MM-DD`
   - If the directory does not exist, create it
   - Append a section:
     ```
     ## HH:MM Evening Review (auto)

     [Detailed record: files changed today, task status, stale tasks flagged,
     proactive fixes applied, notifications sent, memory updates made]
     ```
   - Be thorough — this log should give a complete picture of the day's state

### Rules

- This is an unattended automated task. Do not use AskUserQuestion or request human input
- If a step fails (e.g., notify.py not configured, find command errors), skip it and record the failure in the activity log
- Keep the review concise — record facts, not commentary
- Only record genuinely important changes, not trivial file touches
- Output a brief summary of what was done when finished
