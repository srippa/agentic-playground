# Resume `agentic-playground` Course

> **User Trigger:** When the user says `"read resume.md"` in any new Antigravity conversation, follow these instructions immediately so they can interact right away at the active course gate.

---

## Agent Startup Instructions

1. **Load Context First:** Read these files before replying:
   - [docs/session-handoff.md](./docs/session-handoff.md) (full architectural decisions, file inventory, and invariants)
   - [docs/progress.md](./docs/progress.md) (live **Active Cursor** and Stage × Gate × Parts Progress Matrix)
   - [COURSE.md](./COURSE.md) (4-Gate Interactive Course Protocol)
   - [AGENTS.md](./AGENTS.md) (workspace safety, Dual-Track discipline, and hard-stop rules)
   - Activate the `stage-runner` skill ([.agents/skills/stage-runner/SKILL.md](./.agents/skills/stage-runner/SKILL.md)).
2. **Inspect the Active Stage & Gate:**
   - Check the **Active Cursor** in [docs/progress.md](./docs/progress.md) (initially **Stage 0 — Gate 1**: [s00_foundations/README.md](./src/harness_lab/stages/s00_foundations/README.md) and [s00_foundations/reading.md](./src/harness_lab/stages/s00_foundations/reading.md)).
   - Read that stage's `README.md` plus the active gate file (`reading.md`, `installation.md`, or the current part's code/tests).
3. **Obey Hard-Stop Invariants:**
   - Do **not** run any install commands (`uv add`, `uv python install`, `brew install`, `pip install`, `ollama pull`), pull/delete models, or write/edit code on startup.
   - Respect Track A framework-free isolation, `sandbox_data/` containment, `eval()`/`shell=True` bans, and human-only ownership of `notes/` and ADR `accepted` status.
4. **Respond Ready for Interactive Collaboration:**
   - **If at Gate 1 (`reading.md`):** Present the stage objective, clickable links to the curated reading materials, and the guided focus questions, then stop and invite the user's questions and discussion.
   - **If at Gate 2 (`installation.md`):** Present what will be installed and why, the official installation docs, and the exact proposed commands, then stop for Q&A and explicit approval before running anything.
   - **If at Gate 3 (Coding Part `N.M`):** Present a brief architecture/slice plan for **only** the next uncompleted part from `README.md`, then stop for explicit go-ahead before editing code (and stop again after implementation + `uv run pytest`/`uv run ruff check` so the user can eyeball the architecture, code, and raw test output).
   - **If at Gate 4 (Drills, ADR & Progress):** List the remaining break-it drills, `Status: proposed` ADR draft, and `docs/progress.md` updates for that stage and ask to proceed.

---

## Ending a Chat Cleanly

When you are ready to wrap up mid-stage or after a stage and switch to a fresh conversation, tell the agent:

> `prepare for a new chat`

That triggers the Handoff Protocol in [AGENTS.md](./AGENTS.md) so your stage Q&A (`reading.md` / `installation.md`), [docs/progress.md](./docs/progress.md), and [docs/session-handoff.md](./docs/session-handoff.md) are flushed to disk before you start the next chat with `read resume.md`.
