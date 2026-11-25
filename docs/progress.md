# Lab Progress (`agentic-playground`)

**Current Stage:** Stage 0 — Foundations (`Gate 1: Pre-Reading Ready`)
**Active Cursor:** `Stage 0 → Gate 1` ([s00_foundations/reading.md](../src/harness_lab/stages/s00_foundations/reading.md))
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

## Stage × Gate × Parts Progress Matrix

| Stage | Directory | Gate 1 (`reading.md`) | Gate 2 (`installation.md`) | Gate 3 (Coding Parts) | Gate 4 (Drills, ADR & Progress) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 0** | [s00_foundations](../src/harness_lab/stages/s00_foundations/README.md) | ⏳ Pending | ⬜ Not started | `0.1` ⬜ `0.2` ⬜ `0.3` ⬜ `0.4` ⬜ | `001-runtime-and-wire-tap.md` ⬜ |
| **Stage 1** | [s01_raw_vs_pydantic](../src/harness_lab/stages/s01_raw_vs_pydantic/README.md) | ⬜ Not started | ⬜ Not started | `1.1` ⬜ `1.2` ⬜ `1.3` ⬜ | `002-model-config-and-thinking.md` ⬜ |
| **Stage 2** | [s02_manual_vs_iter](../src/harness_lab/stages/s02_manual_vs_iter/README.md) | ⬜ Not started | ⬜ Not started | `2.1` ⬜ `2.2` ⬜ `2.3` ⬜ | `003-loop-and-structured-output.md` ⬜ |
| **Stage 3** | [s03_tools_guardrails](../src/harness_lab/stages/s03_tools_guardrails/README.md) | ⬜ Not started | ⬜ Not started | `3.1` ⬜ `3.2` ⬜ `3.3` ⬜ `3.4` ⬜ | `004-tool-safety-and-hitl.md` ⬜ |
| **Stage 4** | [s04_mcp_glassbox](../src/harness_lab/stages/s04_mcp_glassbox/README.md) | ⬜ Not started | ⬜ Not started | `4.1` ⬜ `4.2` ⬜ `4.3` ⬜ | `005-mcp-architecture-and-transport.md` ⬜ |
| **Stage 5** | [s05_memory_lab](../src/harness_lab/stages/s05_memory_lab/README.md) | ⬜ Not started | ⬜ Not started | `5.1` ⬜ `5.2` ⬜ `5.3` ⬜ | `006-memory-and-compaction.md` ⬜ |
| **Stage 6** | [s06_observatory](../src/harness_lab/stages/s06_observatory/README.md) | ⬜ Not started | ⬜ Not started | `6.1` ⬜ `6.2` ⬜ `6.3` ⬜ `6.4` ⬜ `6.5` ⬜ | `007-eval-gatekeeper-and-capstone.md` ⬜ |

## Active Stage & Next Action
- **Next:** Begin **Stage 0 — Gate 1** by reviewing [src/harness_lab/stages/s00_foundations/reading.md](../src/harness_lab/stages/s00_foundations/reading.md) with the user (concept chat & focus questions). Do **not** run installations until Gate 2 (`s00_foundations/installation.md`) Q&A and explicit approval are completed.

## Open Questions
- Confirm preferred Python version (`3.12` vs. `3.13`) and initial Ollama / LM Studio / MLX runtime tags during Stage 0 `installation.md` Q&A.
