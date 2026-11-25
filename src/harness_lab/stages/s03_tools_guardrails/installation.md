# Stage 3 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan and the official docs, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install command.

---

## What Will Be Installed & Why

1. **Python Standard Library (`ast`, `sqlite3`, `asyncio.create_subprocess_exec`):** Powers our safe AST `eval_math` evaluator (no `eval()`/`exec()`), sandboxed SQLite query tool, and `shell=False` subprocess runner with zero extra third-party risk.
2. **Optional `aiosqlite`:** Async wrapper around `sqlite3` if we prefer non-blocking SQLite access right from Stage 3 (also required in Stage 5's `memory_lab`). Installing it here avoids duplicating sync vs. async SQLite helpers later if agreed in Q&A.
3. **Seed Untrusted Test Fixtures in `sandbox_data/`:** Non-package text/markdown/SQLite fixtures created purely as read/write targets inside our security boundary tests.

---

## Official Installation Docs

- PydanticAI Toolsets & Deferred Tools: [https://ai.pydantic.dev/toolsets/](https://ai.pydantic.dev/toolsets/) & [https://ai.pydantic.dev/deferred-tools/](https://ai.pydantic.dev/deferred-tools/)
- PydanticAI Offline Testing (`TestModel` / `FunctionModel`): [https://ai.pydantic.dev/testing/](https://ai.pydantic.dev/testing/)

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below.)*

```zsh
# 1. Verify stdlib sqlite3 FTS5 compile support ahead of Stage 3/5
uv run python -c "import sqlite3; c=sqlite3.connect(':memory:'); print([r[0] for r in c.execute('PRAGMA compile_options') if 'FTS' in r[0]])"

# 2. Optional: install aiosqlite early (shared with Stage 5 memory store)
# uv add aiosqlite
```

---

## Q&A & Discussion Log

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Install `aiosqlite` in Stage 3?:** *(TBD in Q&A: yes/no)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append SQLite `PRAGMA compile_options` output and any `uv add aiosqlite` logs after approved execution.)*
