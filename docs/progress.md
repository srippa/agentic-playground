# Lab Progress (`agentic-playground`)

**Current Stage:** Stage 1 — Raw HTTP vs. PydanticAI Model (`Gate 1: Pre-Reading Ready`)
**Active Cursor:** `Stage 1 → Gate 1` ([s01_raw_vs_pydantic/reading.md](../src/harness_lab/stages/s01_raw_vs_pydantic/reading.md))
**Resume in a New Conversation:** [docs/session-handoff.md](./session-handoff.md)
**Hardware Target:** MacBook Pro Apple Silicon (64 GB Unified Memory)
**Last Updated:** 2026-11-25

## Completed
- Architecture & curriculum plan finalized in `agentic-playground-agy.md` (Hybrid Lab: Pure Harness Lab Stages 0–5 + Multi-Agent Trip-Planner Mini-Capstone & Model Arena in Stage 6).
- Interactive Antigravity 4-Gate course scaffolding created:
  - `COURSE.md` (4-Gate course hub & copy-paste starter prompts)
  - `docs/session-handoff.md` (durable conversation handoff & copy-paste new-chat resume prompt)
  - Per-stage directories `src/harness_lab/stages/s00_foundations/` through `s06_observatory/` each containing `README.md`, `reading.md`, and `installation.md`.
- Antigravity workspace safety & customizations configured:
  - `AGENTS.md`, `sandbox_data/AGENTS.md`
  - `.agents/hooks.json`, `.agents/hooks/safety_gate.py`, `.agents/hooks/post_edit_guard.py`
  - `.agents/skills/stage-runner/SKILL.md`, `.agents/skills/local-runtime-guard/SKILL.md`
  - `.gitignore`, `.env.example`
- Governance & journal scaffolding created (`docs/progress.md`, `docs/decisions/README.md`, `notes/README.md`).
- **Stage 0 — Foundations (`s00_foundations`) implemented & verified offline (`31 passed, 1 deselected`, `ruff` clean):**
  - Tooling & env: `uv 0.13.10`, Python `3.13.18`, `Ollama.app 0.40.18` (model pulls deferred), `pyproject.toml`, `models.toml`, and living [models.md](../models.md) roster rationale.
  - Core infrastructure (Track A framework-free): `config.py`, `cli.py` (`lab profiles`, `lab doctor`, `lab version`), `core/tracer.py`, `core/wire_tap.py`, `core/sandbox.py`, and `s00_foundations/run.py`.
  - Gate 4 drills & ADR: `lab profiles` (`OK` vs. `OVER BUDGET` break-it), `lab doctor --xray` (redacted `traces/*.jsonl`), live `Ollama 0.40.18` verified via `uv run lab doctor --xray` (`traces/doctor-20261125T155906Z.jsonl`), and `docs/decisions/001-runtime-and-wire-tap.md` (`Status: accepted`).

## Stage × Gate × Parts Progress Matrix

| Stage | Directory | Gate 1 (`reading.md`) | Gate 2 (`installation.md`) | Gate 3 (Coding Parts) | Gate 4 (Drills, ADR & Progress) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 0** | [s00_foundations](../src/harness_lab/stages/s00_foundations/README.md) | ✅ Done | ✅ Done (models deferred) | `0.1` ✅ `0.2` ✅ `0.3` ✅ `0.4` ✅ | `001-runtime-and-wire-tap.md` ✅ Accepted |
| **Stage 1** | [s01_raw_vs_pydantic](../src/harness_lab/stages/s01_raw_vs_pydantic/README.md) | ⏳ Pending | ⬜ Not started | `1.1` ⬜ `1.2` ⬜ `1.3` ⬜ | `002-model-config-and-thinking.md` ⬜ |
| **Stage 2** | [s02_manual_vs_iter](../src/harness_lab/stages/s02_manual_vs_iter/README.md) | ⬜ Not started | ⬜ Not started | `2.1` ⬜ `2.2` ⬜ `2.3` ⬜ | `003-loop-and-structured-output.md` ⬜ |
| **Stage 3** | [s03_tools_guardrails](../src/harness_lab/stages/s03_tools_guardrails/README.md) | ⬜ Not started | ⬜ Not started | `3.1` ⬜ `3.2` ⬜ `3.3` ⬜ `3.4` ⬜ | `004-tool-safety-and-hitl.md` ⬜ |
| **Stage 4** | [s04_mcp_glassbox](../src/harness_lab/stages/s04_mcp_glassbox/README.md) | ⬜ Not started | ⬜ Not started | `4.1` ⬜ `4.2` ⬜ `4.3` ⬜ | `005-mcp-architecture-and-transport.md` ⬜ |
| **Stage 5** | [s05_memory_lab](../src/harness_lab/stages/s05_memory_lab/README.md) | ⬜ Not started | ⬜ Not started | `5.1` ⬜ `5.2` ⬜ `5.3` ⬜ | `006-memory-and-compaction.md` ⬜ |
| **Stage 6** | [s06_observatory](../src/harness_lab/stages/s06_observatory/README.md) | ⬜ Not started | ⬜ Not started | `6.1` ⬜ `6.2` ⬜ `6.3` ⬜ `6.4` ⬜ `6.5` ⬜ | `007-eval-gatekeeper-and-capstone.md` ⬜ |

## Active Stage & Next Action
- **Next:** Start **Stage 1 — Gate 1** by reviewing [src/harness_lab/stages/s01_raw_vs_pydantic/reading.md](../src/harness_lab/stages/s01_raw_vs_pydantic/reading.md) (concept chat & focus questions). Do **not** run Stage 1 installations (`pydantic-ai`) or write Stage 1 code until Gate 1 sign-off and Gate 2 approval are completed.

## Open Questions
- **Resolved:** Python `3.13` (`3.13.18`) chosen and pinned; `uv 0.13.10`, `Ollama.app 0.40.18`, and Stage 0 Python packages installed.
- **Deferred by User:** Local Ollama model pulls are intentionally deferred until needed (e.g., `lab doctor` in Part 0.3 / Gate 4 or Stage 1).
- Penciled in `embeddinggemma-2:270m` (`https://gemma.ai/models/embeddinggemma/`) as the preferred `embed` candidate to revisit at Stage 5 Gate 2.
- Noted `apple/container` (`https://github.com/apple/container`) in [s03_tools_guardrails/reading.md](../src/harness_lab/stages/s03_tools_guardrails/reading.md) to revisit in Stage 3 ADR `004-tool-safety-and-hitl.md`.
