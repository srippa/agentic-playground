# Stage 5 — Short- & Long-Term Memory Lab (`s05_memory_lab`)

> **Track Focus:** Context Budgeting & Compaction + Hybrid SQLite FTS5 / Cosine Vector Memory (RRF) + Track B `ProcessHistory`  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 5.1–5.3)` → `Gate 4 (Drills & ADR 006)`

---

## Objective

Implement both sides of an agent's memory architecture: (1) **short-term working-context engineering** (exact token budgeting, tool-output hygiene, and loss-bounded compaction) and (2) **long-term episodic/semantic memory** backed by SQLite FTS5 + dense embeddings merged via Reciprocal Rank Fusion (`RRF`), then wire Track B's `ProcessHistory` and retrieval tools cleanly into `--xray`.

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/006-memory-and-compaction.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 5.1** | Track A Context Budgeter & History Compactor | Deterministic token budget tracker, sliding working window, and structured compaction preserving critical constraints/decisions without corrupting tool-call/result pairing | ⬜ Not started |
| **Part 5.2** | Hybrid SQLite FTS5 + Vector Store & RRF Merger | `aiosqlite` FTS5 keyword search + `numpy` cosine similarity over local `embed` vectors (inside `sandbox_data/*.db`), fused cleanly with Reciprocal Rank Fusion (`RRF`) | ⬜ Not started |
| **Part 5.3** | Track B `ProcessHistory` & Memory Retrieval Harness | Idiomatic `pydantic-ai` `history_processors` (`ProcessHistory`) + memory recall/write toolset + `uv run lab stage 5 --xray` showing compacted vs. recalled context | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Run `uv run pytest` and `uv run ruff check` with offline tests verifying FTS5 queries, RRF rank fusion, compaction preservation of anchor facts, and paired `tool_call`/`tool_return` integrity.
2. Run **Long-Horizon Needle-in-a-Haystack & Compaction Drill**: feed multi-turn synthetic preferences + distractions past the compaction threshold, verify compacted summaries preserve key facts, and confirm hybrid FTS5+vector beats pure keyword or pure vector alone.
3. Verify 64 GB co-residency guard (local `embed` + `workhorse` / `fast` memory footprint stays safely within budget).
4. Draft `docs/decisions/006-memory-and-compaction.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
