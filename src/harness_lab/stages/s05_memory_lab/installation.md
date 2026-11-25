# Stage 5 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan, SQLite FTS5 readiness, and local model memory budgets, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install or `ollama pull` command.

---

## What Will Be Installed & Why

1. **`aiosqlite` (if not already installed in Stage 3):** Async SQLite driver backing our persistent episodic memory store and FTS5 lexical index inside `sandbox_data/*.db`.
2. **`numpy`:** Fast, dependency-minimal cosine similarity math over locally embedded memory chunks before introducing any heavy vector DB.
3. **Verify SQLite `ENABLE_FTS5`:** Confirm our Python/macOS SQLite build includes FTS5 full-text indexing.
4. **Local `embed` + `fast` Role Models (64 GB Co-Residency Verified):**
   - `embed` role (preferred candidate noted during Stage 0: `embeddinggemma-2:270m` — ~350 MB text/code backbone, 8K context, Matryoshka `768d`→`128d`; alternatives: `nomic-embed-text` or `qwen3-embedding`).
   - Optional `fast` summarization/compaction model (e.g., `qwen3.5:9b`, `qwen3:8b`, or ultra-fast `bonsai-2.5` if evaluated for compaction latency/memory trade-offs).

---

## Official Installation Docs

- SQLite FTS5 Documentation: [https://www.sqlite.org/fts5.html](https://www.sqlite.org/fts5.html)
- Ollama Embeddings & Model Docs: [https://docs.ollama.com](https://docs.ollama.com)
- EmbeddingGemma Docs: [https://gemma.ai/models/embeddinggemma/](https://gemma.ai/models/embeddinggemma/)
- Workspace Reference: `.agents/skills/local-runtime-guard/SKILL.md`

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below.)*

```zsh
# 1. Install aiosqlite and numpy
uv add aiosqlite numpy

# 2. Verify SQLite FTS5 compile flag
uv run python -c "import sqlite3; c=sqlite3.connect(':memory:'); opts=[r[0] for r in c.execute('PRAGMA compile_options')]; assert 'ENABLE_FTS5' in opts, opts; print('ENABLE_FTS5 OK')"

# 3. Pull approved local embed and fast compaction tags (confirm exact tags & 64 GB fit in Q&A)
# ollama pull <approved-embed-tag>
# ollama pull <approved-fast-tag>
```

---

## Q&A & Discussion Log

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Approved `embed` Model Tag:** *(TBD in Q&A — preferred candidate from Stage 0: `embeddinggemma-2:270m`)*
- **Approved `fast` Compaction Model Tag:** *(TBD in Q&A)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append `uv add`, `ENABLE_FTS5 OK`, and `ollama list` outputs after approved execution.)*
