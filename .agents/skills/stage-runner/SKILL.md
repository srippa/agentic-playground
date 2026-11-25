---
name: stage-runner
description: >-
  Use this skill when implementing, debugging, or verifying any stage (Stage 0 through Stage 6)
  of the agentic-playground harness lab.
---

# Stage Runner Procedure

Follow this workflow when building or verifying any stage in `agentic-playground-agy.md`:

## Steps

Follow the **4-Gate Interactive Course Protocol** defined in `COURSE.md` strictly in order:

1. **Check Continuity & Read Stage Module Docs:** Read `docs/progress.md` first, then read `src/harness_lab/stages/s0N_<name>/README.md` (and the matching section in `agentic-playground-agy.md`).
2. **Gate 1 — Pre-Reading & Concept Chat (Do Not Install or Code Yet):**
   - Present `src/harness_lab/stages/s0N_<name>/reading.md` (reading links, focus questions, and what to watch for).
   - Discuss concepts and answer the user's questions; record key takeaways in `reading.md` under `## Q&A & Discussion Notes`.
   - **Stop** until the user gives Gate 1 sign-off.
3. **Gate 2 — Draft, Discuss & Approve `installation.md` (Do Not Install Yet):**
   - Present/update `src/harness_lab/stages/s0N_<name>/installation.md` listing what is needed and why, official installation documentation URLs, and exact proposed commands.
   - Wait for the user to read the installation docs and ask questions; record the Q&A and agreed conclusions in `installation.md`.
   - Only after explicit user approval, run the approved install commands and append raw verification output to `installation.md`.
4. **Gate 3 — Build & Eyeball One Coding Part at a Time (`N.1`, `N.2`, ...):**
   - Work on **one part at a time** from the stage's `README.md`: share a short architecture plan first and wait for user approval.
   - Implement *only* that part inside `src/harness_lab/stages/s0N_<name>/run.py` (plus helper `scripts/` or shared `core/`, `tools/`, `memory/`, `evals/`). Keep Track A raw code framework-free (no `pydantic-ai`) and Track B idiomatic PydanticAI v2; never silently alter model settings, prompts, or limits, and never refactor earlier stages unasked.
   - Enforce safety rules: never use `eval()` or `shell=True`; confine file, SQLite, and allowlisted subprocess tools strictly to `sandbox_data/`; never register experimental Stage 4 MCP servers in `~/.gemini/config/mcp_config.json`; never edit `notes/` unless explicitly asked.
   - Run offline deterministic tests (`uv run pytest`, marking live tests `@pytest.mark.live`) and lint (`uv run ruff check`).
   - **Hard Stop After Each Part:** Present clickable `file://` links, a concise architecture/code walkthrough, and raw `uv run pytest` + `uv run ruff check` output so the user can eyeball the code, chat about it, and approve moving to the next part.
5. **Gate 4 — Run Live Verification, Break-It Drills & Record Continuity:**
   - Run the stage's CLI/live smoke checks and break-it experiments against local Ollama/LM Studio/MLX (`uv run lab doctor` or `uv run lab stage <N> --xray`), pasting raw wire/trace/timing evidence.
   - Draft a `Status: proposed` ADR in `docs/decisions/NNN-title.md` for real architectural choices, update `docs/progress.md` (including Gate/Part checkboxes), and check `git status` to ensure no `traces/`, `.env`, scratch SQLite DBs, or `.tool_outputs/` are left untracked or staged.
