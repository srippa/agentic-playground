# Agentic Glass-Box Lab (`agentic-playground`)

A hands-on, framework-transparent agent harness engineering course and lab built inside an interactive Antigravity workspace. You start with a single raw HTTP call to a local open model and progressively evolve into structured ReAct/output-validation loops, sandboxed tool guardrails & Human-in-the-Loop approvals, local Model Context Protocol (MCP) servers, hybrid short-/long-term memory, OpenTelemetry observability, two-tier model gatekeeping, and a multi-agent **Trip-Planner mini-capstone**.

> **Status:** Interactive 4-Gate course scaffolding and safety governance ready (`Stage 0 → Gate 1`).  
> **Start / Resume in Antigravity:** Open a conversation in this workspace and send `read resume.md` ([resume.md](./resume.md)).

---

## Core Philosophy

- **Dual-Track "No Magic" Discipline:** Every abstraction is built twice so you see the exact mechanics before adopting framework ergonomics:
  - **Track A (Raw Harness):** Framework-free Python (`stdlib`, `httpx`, `pydantic`, `mcp` SDK — no `pydantic-ai`).
  - **Track B (PydanticAI v2):** Idiomatic `Agent.iter()`, `AbstractCapability`, `Hooks`, `WrapperToolset`, `ProcessHistory`, and `MCPToolset`.
- **Glass-Box `--xray` Observability:** Raw HTTP/SSE wire frames, normalized `ModelMessage` state transitions, MCP JSON-RPC 2.0 handshakes, token budgets, and timings recorded as inspectable JSONL traces and Rich CLI panels.
- **Local-First Hardware Target (64 GB Apple Silicon Unified Memory):** Tuned for local runtimes (Ollama / LM Studio / optional MLX), explicit `num_ctx` verification, 3-model hot co-residency (`workhorse` + `fast` + `embed`), quantization comparisons (`Q4_K_M`, `Q6_K`/`Q8_0`/Dynamic quants, 1-bit `Bonsai 2.5`), and multi-model `HarnessBudget` + `Jev` decision routing.

---

## How the Course Works (4-Gate Interactive Protocol)

Every stage in [COURSE.md](./COURSE.md) advances strictly through four hard-stop gates — no installs or code happen silently ahead of you:

1. **Gate 1 — Pre-Reading (`reading.md`):** Discuss the stage's curated links and focus questions first, logging takeaways before any tooling setup.
2. **Gate 2 — Installations (`installation.md`):** Review what will be installed, why, official installation docs, and exact proposed commands; run installs or model pulls **only** after your explicit approval.
3. **Gate 3 — One Coding Part at a Time (`README.md` Parts `N.1`, `N.2`, …):** Brief architecture plan → implement *only* that part → run offline `uv run pytest` and `uv run ruff check` → stop and inspect clickable files, code walkthrough, and raw test output before proceeding.
4. **Gate 4 — Drills, ADR & Progress:** Run local break-it drills with wire/trace evidence, draft a 1-page `Status: proposed` ADR in [docs/decisions/](./docs/decisions/README.md), and update [docs/progress.md](./docs/progress.md).

Use `prepare for a new chat` whenever switching threads, and `read resume.md` in a fresh conversation to pick up at the active gate cursor.

---

## Curriculum Stages (Stages 0–6)

| Stage | Guide | Pre-Reading (Gate 1) | Installations (Gate 2) | Coding Parts (Gate 3) | Focus |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 0** | [s00_foundations](./src/harness_lab/stages/s00_foundations/README.md) | [reading.md](./src/harness_lab/stages/s00_foundations/reading.md) | [installation.md](./src/harness_lab/stages/s00_foundations/installation.md) | `0.1`–`0.4` | Workspace skeleton, 64 GB model profiles, `httpx` wire-tap transport, `lab doctor` |
| **Stage 1** | [s01_raw_vs_pydantic](./src/harness_lab/stages/s01_raw_vs_pydantic/README.md) | [reading.md](./src/harness_lab/stages/s01_raw_vs_pydantic/reading.md) | [installation.md](./src/harness_lab/stages/s01_raw_vs_pydantic/installation.md) | `1.1`–`1.3` | Raw `/v1/chat/completions` + SSE + `<think>` separation vs. `pydantic-ai` models |
| **Stage 2** | [s02_manual_vs_iter](./src/harness_lab/stages/s02_manual_vs_iter/README.md) | [reading.md](./src/harness_lab/stages/s02_manual_vs_iter/reading.md) | [installation.md](./src/harness_lab/stages/s02_manual_vs_iter/installation.md) | `2.1`–`2.3` | Manual ReAct & schema retry loops vs. `Agent.iter()`, `output_type`, `AbstractCapability` |
| **Stage 3** | [s03_tools_guardrails](./src/harness_lab/stages/s03_tools_guardrails/README.md) | [reading.md](./src/harness_lab/stages/s03_tools_guardrails/reading.md) | [installation.md](./src/harness_lab/stages/s03_tools_guardrails/installation.md) | `3.1`–`3.4` | Sandboxed AST/file/SQLite/subprocess tools, artifact spill, `WrapperToolset`, `DeferredToolRequests` HITL |
| **Stage 4** | [s04_mcp_glassbox](./src/harness_lab/stages/s04_mcp_glassbox/README.md) | [reading.md](./src/harness_lab/stages/s04_mcp_glassbox/reading.md) | [installation.md](./src/harness_lab/stages/s04_mcp_glassbox/installation.md) | `4.1`–`4.3` | Project-scoped `FastMCP` KV/notes server, raw JSON-RPC 2.0 `stdio` client, `MCPToolset` |
| **Stage 5** | [s05_memory_lab](./src/harness_lab/stages/s05_memory_lab/README.md) | [reading.md](./src/harness_lab/stages/s05_memory_lab/reading.md) | [installation.md](./src/harness_lab/stages/s05_memory_lab/installation.md) | `5.1`–`5.3` | Token budgeting, lossless-bounded compaction, SQLite FTS5 + cosine vector `RRF`, `ProcessHistory` |
| **Stage 6** | [s06_observatory](./src/harness_lab/stages/s06_observatory/README.md) | [reading.md](./src/harness_lab/stages/s06_observatory/reading.md) | [installation.md](./src/harness_lab/stages/s06_observatory/installation.md) | `6.1`–`6.5` | REPL + OTel `--xray`, `HarnessBudget` + `Jev` router, `lab gate` gatekeeper, `lab eval`, Trip-Planner capstone (`lab bench`) |

---

## Repository Map

- **Course & Architecture Hub:** [COURSE.md](./COURSE.md) · [agentic-playground-agy.md](./agentic-playground-agy.md)
- **Session Resume & Continuity:** [resume.md](./resume.md) · [docs/progress.md](./docs/progress.md) · [docs/session-handoff.md](./docs/session-handoff.md)
- **Architecture Decision Records (ADRs):** [docs/decisions/README.md](./docs/decisions/README.md)
- **Antigravity Workspace Rules, Hooks & Skills:** [AGENTS.md](./AGENTS.md) · [.agents/hooks.json](./.agents/hooks.json) · [.agents/skills/stage-runner/SKILL.md](./.agents/skills/stage-runner/SKILL.md) · [.agents/skills/local-runtime-guard/SKILL.md](./.agents/skills/local-runtime-guard/SKILL.md)
- **Sandbox Rules & Env Template:** [sandbox_data/AGENTS.md](./sandbox_data/AGENTS.md) · [.env.example](./.env.example)

---

## Safety & Sandbox Invariants

- **Local-First & Zero Silent Spend:** Offline `TestModel` / `FunctionModel` suites (`uv run pytest`) run without network or model spend; live tests are marked `@pytest.mark.live`; installs, model pulls, and paid cloud profiles require explicit user confirmation.
- **Strict Containment:** File, SQLite, and `asyncio.create_subprocess_exec(..., shell=False)` tools stay confined to `sandbox_data/`; `eval()`, `exec()`, and `shell=True` are forbidden; all files under `sandbox_data/` are treated as untrusted test fixtures.
- **Secrets & MCP Isolation:** `.env`, keys, `traces/`, `.tool_outputs/`, SQLite DBs, and benchmark outputs remain gitignored and redacted; experimental Stage 4 MCP servers stay scoped inside the project harness (never registered globally).
