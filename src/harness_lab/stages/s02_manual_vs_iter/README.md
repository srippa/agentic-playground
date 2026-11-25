# Stage 2 — Manual ReAct Loop vs. `Agent.iter()` & Structured Output (`s02_manual_vs_iter`)

> **Track Focus:** Track A (Manual `while` ReAct Loop & Retry Mechanics) vs. Track B (`Agent.iter()`, `output_type` Validation, and `AbstractCapability` / `Hooks`)  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 2.1–2.3)` → `Gate 4 (Drills & ADR 003)`

---

## Objective

Understand the core mechanics of an agentic loop by writing Track A's manual tool-call & schema-retry `while` loop from scratch, then inspecting how Track B (`pydantic-ai` `Agent.iter()`, typed `output_type`, and `AbstractCapability` / `Hooks`) structures the exact same state machine with explicit stop conditions and budgets.

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/003-loop-and-structured-output.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 2.1** | Track A Manual ReAct Loop & Schema Retries | Framework-free `while` loop dispatching JSON tool schemas, appending `role="tool"` results, validating final JSON via Pydantic, feeding validation errors back into retries, and enforcing `max_steps` | ⬜ Not started |
| **Part 2.2** | Track B `Agent.iter()`, `output_type` & `AbstractCapability` | Step-by-step `async with agent.iter(...)` node inspector (`UserPromptNode` → `ModelRequestNode` → `CallToolsNode` → `End`), `UsageLimits`, typed `output_type`, and custom `AbstractCapability` / `Hooks` | ⬜ Not started |
| **Part 2.3** | Trace Replay & Failure Stress Harness | `uv run lab stage 2 --xray` comparing Track A loop traces against Track B node transitions, plus deterministic/chaos retry-exhaustion drills | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Run `uv run pytest` and `uv run ruff check` with zero offline failures (testing retry exhaustion, malformed JSON self-correction, and step caps).
2. Run `uv run lab stage 2 --xray` comparing Track A manual steps vs. Track B `Agent.iter()` nodes on a local model (`workhorse` / `fast`) and deliberately weak `chaos` / malformed inputs.
3. Inspect how tool-call IDs (`tool_call_id`) bind assistant calls to `role="tool"` responses on the wire.
4. Draft `docs/decisions/003-loop-and-structured-output.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
