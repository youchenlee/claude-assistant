# Hot Memory

<!-- This is the agent's working memory — dynamic facts and state, updated frequently.
     Hard limit: 200 lines. When full, move expired entries to OLD-MEMORY.md.

     Priority and expiry system:
       #P0 = Core identity (never expires — date is write date, for traceability only)
       #P1 = Active projects (expires after 90 days — date is event date)
       #P2 = Temporary info (expires after 30 days — date is event date)

     Format: `- content #PN @YYYY-MM-DD`

     Rules:
       - Each line is self-contained (can be understood without surrounding context)
       - Expired or irrelevant memories move to OLD-MEMORY.md
       - Update after every completed task — context can be compressed or reset at any time
-->

---

## User

<!-- Core facts about the user that the agent should always know. -->

- Name: {{USER}} #P0 @2026-01-01
- Location: (your city/timezone) #P0 @2026-01-01

## Active Projects

<!-- What the user is currently working on. Keep entries actionable. -->

- (Example: Building a personal knowledge management system) #P1 @2026-01-01

## Completed

<!-- Recent completions for context continuity. Move to OLD-MEMORY.md after 30 days. -->

- (Example: Set up agent identity files — SOUL.md, STYLE.md, MEMORY.md) #P2 @2026-01-01

## Pending

<!-- Outstanding items the agent should track and surface when relevant. -->

- (Example: Research vector database options for long-term memory) #P2 @2026-01-01
