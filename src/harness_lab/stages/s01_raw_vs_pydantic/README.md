# Stage 1 — Raw HTTP vs. PydanticAI Model (`s01_raw_vs_pydantic`)

> **Track Focus:** Track A (Raw `httpx` SSE + Thinking/Content Separation) vs. Track B (`pydantic-ai` `ModelRequest`/`ModelResponse` Adapter)  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 1.1–1.3)` → `Gate 4 (Drills & ADR 002)`

---

## Objective

Demystify what happens on the wire during a single LLM turn (including chat templating, SSE token streaming, reasoning/`<think>` blocks, and message history) by building Track A from raw HTTP first, then comparing it side-by-side against Track B's `pydantic-ai` abstraction under `--xray`.

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/002-model-config-and-thinking.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 1.1** | Track A Raw HTTP Chat & SSE Parser | Framework-free `httpx` `/v1/chat/completions` client supporting `stream=True` / `stream=False`, SSE chunk parsing, `<think>` extraction, and raw JSON dump | ⬜ Not started |
| **Part 1.2** | Track B PydanticAI Single-Turn Adapter | `pydantic-ai` `Agent` wired to local OpenAI-compatible endpoint (`OpenAIChatModel` / `OpenAIProvider`), exposing `ModelRequest`, `ModelResponse`, `ThinkingPart`, and `TextPart` | ⬜ Not started |
| **Part 1.3** | Side-by-Side `--xray` Comparator | `uv run lab stage 1 --xray` runner diffing raw wire payloads against PydanticAI's normalized `ModelMessage` objects across `workhorse` / `fast` / `bonsai-2.5` | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Confirm Track A modules contain zero `pydantic_ai` imports (`uv run pytest` offline assertions pass).
2. Run `uv run lab stage 1 --xray` locally (or via offline mock/live tests) and inspect raw SSE `data:` frames vs. final `ModelResponse.parts`.
3. Experiment with temperature (`0.0` vs `0.7`) and thinking toggles, inspecting token counts and latency differences.
4. Draft `docs/decisions/002-model-config-and-thinking.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
