# Stage 3 — Tools, Sandboxing & Human-in-the-Loop Guardrails (`s03_tools_guardrails`)

> **Track Focus:** Safe Local Tool Suite + Track A Raw Guardrails vs. Track B `WrapperToolset` & `DeferredToolRequests`  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 3.1–3.4)` → `Gate 4 (Drills & ADR 004)`

---

## Objective

Build real local tools that an agent can call safely without escaping the sandbox (`sandbox_data/`), demystify pre-/post-tool validation, output truncation, and prompt-injection boundaries in Track A raw Python, then implement Track B's composable `WrapperToolset` and Human-in-the-Loop (`DeferredToolRequests`) approval flow.

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/004-tool-safety-and-hitl.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 3.1** | Sandboxed Safe Local Tool Suite | Safe AST `eval_math` (no `eval()`/`exec()`), `sandbox_data/` resolved-path file tools, sandboxed `sqlite3` query helper, and `asyncio.create_subprocess_exec(..., shell=False)` allowlisted runner | ⬜ Not started |
| **Part 3.2** | Track A Tool Guardrails & Artifact Spill | Manual pre-execution permission gate, `sandbox_data/` untrusted-fixture framing, and large-output truncation spilling full output to `sandbox_data/.tool_outputs/` | ⬜ Not started |
| **Part 3.3** | Track B `WrapperToolset` & `DeferredToolRequests` | Idiomatic PydanticAI `WrapperToolset` (logging, truncation, path enforcement) + `DeferredToolRequests` pausing mutating tools for explicit human confirmation | ⬜ Not started |
| **Part 3.4** | Offline Security & Injection Test Suite | Deterministic `TestModel` / `FunctionModel` pytest cases asserting path traversal (`../`) blocks, shell/eval rejections, output truncation, and deferred HITL approval | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Run `uv run pytest` and `uv run ruff check` — verify every security, traversal, and HITL test passes offline.
2. Run **Prompt-Injection Break-It Drill**: plant an untrusted fixture instruction inside `sandbox_data/` attempting exfiltration or out-of-sandbox writes; confirm `sandbox_data/AGENTS.md` + path containment + HITL gate block it with raw trace evidence.
3. Verify huge tool outputs truncate cleanly in model context while preserving full content under `sandbox_data/.tool_outputs/`.
4. Draft `docs/decisions/004-tool-safety-and-hitl.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
