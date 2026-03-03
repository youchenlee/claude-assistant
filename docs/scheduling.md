# Scheduling

Automated tasks let the agent run unattended on a schedule -- morning planning, evening review, memory cleanup, or anything you define.

## How run.sh Works

`assistant/tools/run.sh` is the task runner. It takes a task name, finds the matching prompt, and executes it via `claude -p`.

```
./run.sh morning
```

### Execution flow

1. **Path derivation**: All paths are computed relative to the script's location. No hardcoded paths.
2. **Lock file check**: Creates `logs/.lock-YYYY-MM-DD-<task>` with hostname. If the file already exists, the task is skipped (already ran today).
3. **Race condition guard**: After writing the lock, sleeps 3 seconds, then re-reads. If another machine claimed the lock during that window, exits.
4. **MEMORY.md backup**: Copies to `MEMORY.md.bak` before execution to guard against concurrent writes.
5. **Claude CLI call**: Runs `claude -p <prompt> --dangerously-skip-permissions --max-budget-usd 2.00 --model sonnet`.
6. **Failure alert**: On non-zero exit, sends a notification via `notify.py`.

### Authentication

`run.sh` unsets `ANTHROPIC_API_KEY` to force OAuth authentication (Claude Max subscription). Make sure `claude login` has been run on the machine.

## Adding a New Scheduled Task

### 1. Write the prompt

Create `assistant/tools/prompts/<task-name>.md`:

```markdown
You are a personal assistant. Read your identity and memory files first:
`assistant/SOUL.md`, `assistant/STYLE.md`, and `assistant/MEMORY.md`.

## Task: <Task Name>

This is an automated task — no human is present. Do not use AskUserQuestion.
Complete all steps autonomously. If a step fails, skip it and log the failure.

### Steps
1. ...
2. ...

### Rules
- This is unattended. No interactive prompts.
- Keep notifications concise.
- Write results to the activity log.
```

### 2. Create a launchd plist (macOS)

Copy from the template directory and fill in the placeholders:

```bash
cp assistant/tools/launchd/com.assistant.morning.plist.template \
   ~/Library/LaunchAgents/com.myagent.newtask.plist
```

Edit the plist: change the label, the task name argument, and the schedule.

Key fields:
- `ProgramArguments`: path to `run.sh` and the task name
- `StartCalendarInterval`: when to run (Hour/Minute/Weekday)

### 3. Load with launchctl

```bash
launchctl load ~/Library/LaunchAgents/com.myagent.newtask.plist
```

To unload: `launchctl unload <path>`. To check status: `launchctl list | grep myagent`.

### Randomized scheduling

Use `run-random.sh` instead of `run.sh` to add a random delay (0-90 minutes) before execution. Useful for tasks that shouldn't run at a fixed time.

## Lock File Mechanism

Lock files prevent duplicate execution when the same schedule exists on multiple machines (e.g., desktop + laptop synced via iCloud/Dropbox).

```
logs/.lock-2026-03-02-morning
```

Contents: `hostname HH:MM:SS`

- **Write-sleep-verify**: After writing the lock, the script sleeps 3 seconds, then re-reads. If the contents changed (another machine won), it exits.
- **Auto-cleanup**: Lock files older than 7 days are automatically deleted.
- **One lock per task per day**: The date is embedded in the filename.

## Prompt Writing Guidelines

- **Autonomous**: Never use `AskUserQuestion` or request human input. The task must complete unattended.
- **Graceful failure**: If a step fails (missing file, API error), skip it and record the failure in the activity log.
- **Concise notifications**: Use `notify.py` only when there is something worth reporting. Never send empty or trivial messages.
- **Activity logging**: Write detailed records to `assistant/activity-log/YYYY-MM/YYYY-MM-DD.md` so failures can be diagnosed later.
- **Identity loading**: Always start the prompt with instructions to read SOUL.md, STYLE.md, and MEMORY.md.

## Linux Alternatives

### cron

`run.sh` works with cron. Add entries to your crontab:

```
0 7 * * * /path/to/assistant/tools/run.sh morning
0 22 * * * /path/to/assistant/tools/run.sh evening
30 22 * * 0 /path/to/assistant/tools/run.sh memory-clean
```

The lock file mechanism still works -- if multiple machines share the same filesystem (e.g., NFS, synced folder), only one will execute.

### systemd timers

Create a service and timer unit pair. The service runs `run.sh`, the timer defines the schedule. Same effect as launchd but with systemd's dependency management.

## Troubleshooting

| Problem | Check |
|---------|-------|
| Task never runs | `launchctl list \| grep <label>` -- is the plist loaded? |
| Task runs but Claude fails | Check `assistant/tools/logs/<date>-<task>.log` for error output |
| Auth errors | Run `claude login` on the machine. Verify with `claude -p "hello" --model sonnet` |
| Budget exceeded | Increase `--max-budget-usd` in run.sh or switch to a cheaper model |
| Lock file prevents execution | A previous run already claimed today's lock. Delete `logs/.lock-*` files manually if needed |
| Duplicate execution | Ensure both machines share the same `logs/` directory (via cloud sync) |
