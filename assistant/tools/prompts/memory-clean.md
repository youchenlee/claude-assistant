You are a personal assistant. Read your identity and memory files first:
`assistant/SOUL.md`, `assistant/STYLE.md`, and `assistant/MEMORY.md`.

## Task: Memory Cleanup

This is an automated task — no human is present. Do not use AskUserQuestion or any interactive prompts. Complete all steps autonomously. Today's date is noted in CLAUDE.md.

### Steps

1. **Read MEMORY.md**
   - Read `assistant/MEMORY.md` in full
   - Count total lines (excluding blank lines and comments)

2. **Identify expired entries**
   - Check every tagged line for expiry:
     - `#P0` entries: **never expire** — skip these entirely
     - `#P1` entries: expire after **90 days** from the `@YYYY-MM-DD` date
     - `#P2` entries: expire after **30 days** from the `@YYYY-MM-DD` date
   - Build a list of entries to archive

3. **Archive expired entries to OLD-MEMORY.md**
   - Read `assistant/OLD-MEMORY.md`
   - For each expired entry, append it to OLD-MEMORY.md with the archive date prepended:
     ```
     - [archived YYYY-MM-DD] Original entry text #PN @YYYY-MM-DD
     ```
   - Preserve the original text and tags exactly — do not edit or summarize
   - Remove the archived entries from MEMORY.md

4. **Check for compressible entries**
   - Look for entries that are duplicates or can be merged without losing information
   - If two entries say essentially the same thing, combine them into one
   - Be conservative: when in doubt, keep both entries separate

5. **Enforce 200-line limit**
   - After archival and compression, count remaining lines in MEMORY.md
   - If still over 200 lines:
     - Move the lowest-priority entries to OLD-MEMORY.md (#P2 first, then #P1)
     - Among entries of equal priority, move the oldest first
     - Continue until under 200 lines
   - **Never move #P0 entries** to meet the line limit

6. **Write updated MEMORY.md**
   - Write the cleaned MEMORY.md back
   - Ensure the header comments and section structure are preserved

7. **Write activity log**
   - Path: `assistant/activity-log/YYYY-MM/YYYY-MM-DD.md`
   - If the file does not exist, create it with the header: `# Activity Log YYYY-MM-DD`
   - If the directory does not exist, create it
   - Append a section:
     ```
     ## HH:MM Memory Cleanup (auto)

     - Entries archived: N
     - Entries compressed: N
     - Lines before: N
     - Lines after: N
     - Details: [list what was archived and why]
     ```

### Rules

- This is an unattended automated task. Do not use AskUserQuestion or request human input
- **Conservative by default**: If you are unsure whether an entry should be archived, keep it
- Never delete entries — always move them to OLD-MEMORY.md with the archive date
- Preserve original text exactly when archiving (do not rewrite or summarize archived content)
- Do not touch #P0 entries under any circumstances
- Output a brief summary of what was done when finished
