# Stage 6 — Observatory, Model Gatekeeper, Evals & Trip-Planner Capstone (`s06_observatory`)

> **Track Focus:** Live `--xray` Observatory & `HarnessBudget` + `Jev` Routing + `lab gate` Gatekeeper + `lab eval` + Multi-Agent Trip-Planner Mini-Capstone (`lab bench`)  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 6.1–6.5)` → `Gate 4 (Drills & ADR 007)`

---

## Objective

Close the Hybrid Lab loop by building full harness observability (OpenTelemetry GenAI conventions + interactive REPL), disciplined multi-model routing (`HarnessBudget` + `Jev`), a two-tier model evaluation suite (**fast `lab gate` candidate gatekeeper** + **end-to-end `lab eval` & quant/family `lab bench`**), and a realistic multi-agent **Trip-Planner mini-capstone** combining Stages 0–5.

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/007-eval-gatekeeper-and-capstone.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 6.1** | Interactive REPL & OTel GenAI Observatory | `prompt-toolkit` glass-box REPL, `--xray` live span/wire trace viewer aligned with OpenTelemetry GenAI semantic conventions, and optional local Logfire/Phoenix export | ⬜ Not started |
| **Part 6.2** | `HarnessBudget` & Tiered `Jev` Router | Explicit step/token/latency/64 GB memory accounting across multi-model roles (`decision` router choosing between `fast`, `workhorse`, `bonsai-2.5`, or `alt-family`) | ⬜ Not started |
| **Part 6.3** | Two-Tier Model Gatekeeper (`lab gate`) | Fast diagnostic benchmark suite screening any newly proposed local model or quant (e.g., `Bonsai 2.5` vs `Q4_K_M`) on JSON/tool/injection reliability before full capstone promotion | ⬜ Not started |
| **Part 6.4** | Harness Evaluation Runner (`lab eval`) | `pydantic-evals` & deterministic assertion suite grading tool selection, compaction retention, HITL compliance, and latency across offline `TestModel`/`FunctionModel` and live runs | ⬜ Not started |
| **Part 6.5** | Multi-Agent Trip-Planner Capstone & Arena (`lab bench`) | End-to-end multi-agent Trip-Planner (researcher, budget/math, sandboxed itinerary writer with Stage 4 MCP notes + Stage 5 preferences + Stage 3 HITL confirmation) + quant/family arena | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Run `uv run pytest` and `uv run ruff check` with all deterministic offline `TestModel` / `FunctionModel` eval and gatekeeper suites passing.
2. Run `uv run lab gate` on a candidate local model/quantization (e.g., `bonsai-2.5` vs `qwen3.8:27b` or `inkling-2-mini`) and record raw pass/fail + latency metrics under `benchmarks/results/` (gitignored) with summary findings.
3. Run the **Multi-Agent Trip-Planner Capstone** locally under `uv run lab bench --xray`, inspecting `Jev` routing decisions, `HarnessBudget` enforcement, Stage 4 MCP calls, Stage 5 memory recall, and Stage 3 HITL approval pause.
4. Draft `docs/decisions/007-eval-gatekeeper-and-capstone.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
