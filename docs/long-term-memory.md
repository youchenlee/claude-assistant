# Long-Term Memory

Optional enhancement to MEMORY.md. Uses a LanceDB vector database with hybrid search (vector + BM25 keyword) to store and recall past conversations.

- **MEMORY.md** = curated working memory, always in context, ~200 lines
- **LanceDB** = unlimited long-term storage, retrieved on demand

The system degrades gracefully -- if LanceDB is not set up, everything else works normally.

## Prerequisites

- Python 3.10+
- OpenAI API key (for `text-embedding-3-small` embeddings and `gpt-4o-mini` keyword extraction)

## Setup

### Via setup.sh (recommended)

```bash
./setup.sh
# Answer "y" when asked about long-term memory
# Provide your OpenAI API key
```

This creates the virtualenv and installs dependencies automatically.

### Manual setup

```bash
cd assistant/tools
python3 -m venv memory-venv
memory-venv/bin/pip install lancedb pyarrow
```

Add your OpenAI API key to `assistant/tools/config.json`:

```json
{
  "openai_api_key": "sk-..."
}
```

Or set the `OPENAI_API_KEY` environment variable.

## How It Works

### Capture

After each Telegram conversation turn:

1. **Filter**: Skip trivial messages ("ok", "thanks", slash commands, very short exchanges)
2. **Score importance**: Lightweight signal detection (decisions, actions, knowledge signals boost score)
3. **Embed**: Generate a vector via OpenAI `text-embedding-3-small` (1536 dimensions)
4. **Extract keywords**: Use `gpt-4o-mini` to pull 5-15 key terms for BM25 indexing
5. **Store**: Write to LanceDB with scope, agent, timestamp, importance score

Steps 3 and 4 run in parallel to minimize latency. Capture runs in a background thread so the user is never blocked.

### Recall

At the start of each Telegram session turn:

1. **Embed the query** and **extract keywords** (parallel)
2. **Vector search**: Find semantically similar memories
3. **BM25 search**: Find keyword-matching memories
4. **RRF fusion**: Combine rankings using Reciprocal Rank Fusion (no score normalization needed)
5. **Boost**: Recent memories (within 7 days) get up to +20%; high-importance memories get up to +10%
6. **Inject**: Format top results and append to the prompt as reference context

### Scope Isolation

Each agent has its own scope. When agent "coach" recalls memories, it only sees memories stored by "coach" (plus the shared "global" scope). This prevents personality bleed between agents.

## Querying from Terminal

```bash
cd assistant/tools
memory-venv/bin/python3 -c "
import sys; sys.path.insert(0, '.')
import memory_store
results = memory_store.recall('search query here', top_k=5)
for r in results:
    print(f\"[{r['date']}] ({r['scope']}) {r['text'][:200]}\")
"
```

To check how many memories are stored:

```bash
memory-venv/bin/python3 -c "
import sys; sys.path.insert(0, '.')
import memory_store
store = memory_store.get_store()
print(f'Total memories: {store.count()}')
"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Long-term memory not available" on bot start | Check that `memory-venv/` exists and has lancedb installed. Check that OpenAI API key is set. |
| Embedding errors | Verify your OpenAI API key is valid and has credits. The model used is `text-embedding-3-small`. |
| Keyword extraction fails | Uses `gpt-4o-mini`. Check API key permissions. Keyword extraction failure is non-fatal -- vector search still works. |
| Memory not found in recall | New entries may not appear in BM25 results until the FTS index is rebuilt (every 10 inserts). Vector search finds them immediately. |
| Disk space | The LanceDB database lives at `assistant/tools/memory-db/`. Delete it to start fresh. |
| Venv issues | Delete `memory-venv/` and recreate: `python3 -m venv memory-venv && memory-venv/bin/pip install lancedb pyarrow` |
