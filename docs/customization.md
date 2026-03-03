# Customization

Your agent's personality lives in three files inside the agent directory. Edit them to make the agent yours.

## SOUL.md — Who the Agent Is

This file defines identity, values, thinking patterns, and working methods. It rarely changes.

### Sections

| Section | Purpose | Tip |
|---------|---------|-----|
| Identity | One paragraph: who, what, why | Be specific. "A personal assistant" is too vague |
| Values | 2-4 trade-offs (X > Y) with examples | Abstract values get ignored. Show concrete behavior |
| How I Think | Decision checklist the agent runs before acting | These shape reasoning across all tasks |
| Work Methods | Observable collaboration behaviors | Focus on actions, not personality traits |
| Lessons Learned | Verified solutions to past problems | Start empty. Let it grow organically |

### Mini Example

```markdown
## Identity
I am a research assistant for Alex. I help evaluate papers, summarize findings,
and maintain a literature database.

## Values
### Accuracy > Speed
- If a claim seems off, I check the source before repeating it
- I say "I'm not sure" rather than hallucinate a citation

## How I Think
1. What is the core question?
2. What evidence exists in the knowledge base?
3. What's missing?

## Lessons Learned
### PDF parsing drops footnotes
- **Problem**: Footnote content was silently lost during extraction
- **Resolution**: Always check page count against expected sections
- **Applies when**: Processing any academic PDF | @2026-02-10
```

## STYLE.md — How the Agent Communicates

Calibrate tone using wrong/right example pairs. The agent pattern-matches on these, so make them representative of real conversations.

```markdown
## Tone

Wrong:
> Great question! Let me help you analyze this...

Right:
> Checked it. Three issues: [1] [2] [3]. I recommend [2] because [reason].
```

Add format rules (default length, list vs. prose thresholds) and hard don'ts (things the agent must never do).

## MEMORY.md — Working Memory

Dynamic state, updated every session. Hard limit: 200 lines.

### Format

```
- Entry text #P0 @2026-03-02
- Active project description #P1 @2026-02-15
- Temporary note #P2 @2026-03-01
```

### Priority Levels

| Tag | Meaning | Expires | Date = |
|-----|---------|---------|--------|
| `#P0` | Core facts | Never | Date written |
| `#P1` | Active projects | 90 days | Date of event |
| `#P2` | Temporary context | 30 days | Date of event |

### Rules

- Each line must be self-contained (readable without surrounding lines)
- When the file fills up, expired entries move to `OLD-MEMORY.md`
- The `memory-clean` scheduled task automates this; you can also do it manually
- **Update after every completed task.** This is the single most important discipline

## Protected Directories

Mark directories as read-only for the agent in `CLAUDE.md`:

```markdown
## Permissions
- Protected directories: `journal/`, `personal/`
  - The agent may read these files and annotate status fields
  - The agent must not alter the original meaning of content
  - Ask before making substantive changes
```

The agent will still read these files for context but will not modify their content without explicit permission.

## Tips

1. **Start simple.** Write a 3-line Identity, two Values, and a minimal STYLE.md. Refine as you use it.
2. **Iterate on STYLE.md frequently.** When the agent says something you don't like, add a wrong/right pair.
3. **Let Lessons Learned grow organically.** Don't pre-populate it. Real entries from real problems are far more useful.
4. **Keep MEMORY.md ruthless.** If an entry is no longer relevant, archive or delete it. Stale memory degrades behavior.
5. **Use examples over rules.** "Don't be verbose" is weak. A wrong/right pair showing the exact difference is strong.
