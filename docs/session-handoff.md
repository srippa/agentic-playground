# Session Handoff — Resume Course in a New Antigravity Conversation

- **Last Updated:** 2026-11-25
- **Workspace:** `agentic-playground` (repository root)
- **Active Cursor:** `Stage 0 → Gate 1` ([s00_foundations/reading.md](../src/harness_lab/stages/s00_foundations/reading.md))
- **Current Build State:** Course scaffolding, governance rules, safety hooks/skills, and all stage docs (`s00_foundations/`–`s06_observatory/`) are complete. **No packages or local models have been installed yet, and no Python stage code has been written yet.**

---

## 1. Design Decisions Made So Far (Why the Lab Is Shaped This Way)

1. **Target Hardware & Local Runtime Strategy (64 GB Apple Silicon Unified Memory):**
   - Local model roster configured around 64 GB unified memory: `workhorse` (`qwen3.8:27b`), `bonsai-2.5` (candidate ultra-low-bit model), `alt-family` (`inkling-2-mini`), plus `fast`, `chaos`, `decision`, and `embed` roles.
   - Because Ollama's `/v1/chat/completions` silently ignores request-body `num_ctx`, we verify active context length via `/api/show` and `/api/ps` (configured via `OLLAMA_CONTEXT_LENGTH` or derived Modelfiles).
   - Protect 3-model hot co-residency (`OLLAMA_MAX_LOADED_MODELS=3` for `workhorse` + `fast` + `embed`, keeping weights + KV cache under ~42–46 GB inside macOS's default ~48 GB wired GPU ceiling) and support quantization sweeps (`Q4_K_M` vs. `Q6_K`/`Q8_0`/Dynamic 5–8 bit vs. 1-bit `Bonsai 2.5`).
2. **Multi-Model Harness Budget & Routing (`HarnessBudget` + `Jev`):**
   - Explicitly track step, token, latency, and 64 GB memory budgets across multi-model calls, with a `decision` role (`Jev` / local `TinyJev` / `Tev1`, or explicitly user-approved hosted `Jev`) deciding routing without silent cloud spend.
3. **Two-Tier Model Gatekeeper & Application Evals:**
   - **Tier 1 (`uv run lab gate`):** Fast diagnostic gatekeeper evaluating any newly proposed local model or quantization (such as `Bonsai 2.5 27B`) on harness-predictive capabilities (strict JSON reliability, tool-call discipline, context/memory faithfulness) before promotion.
   - **Tier 2 (`uv run lab eval` + `uv run lab bench`):** Small end-to-end application evaluation suite and head-to-head quant/family arena.
4. **Hybrid Lab Architecture (Stages 0–5 + Stage 6 Capstone):**
   - **Stages 0–5:** Pure Harness Lab with zero domain boilerplate, confining all tools, SQLite DBs, subprocesses, and untrusted test fixtures to `sandbox_data/`.
   - **Stage 6:** Realistic multi-agent **Trip-Planner mini-capstone** combining Stage 2 loops/structured outputs, Stage 3 sandboxed tools + Human-in-the-Loop approval, Stage 4 local `FastMCP` notes/KV store, Stage 5 hybrid memory + compaction, and Stage 6 OTel/`--xray` observability + evals.
5. **Dual-Track "No Magic" Discipline (Track A ↔ Track B):**
   - **Track A** raw harness code stays strictly framework-free (`stdlib`, `httpx`, `pydantic`, `mcp` SDK only — never `pydantic-ai`).
   - **Track B** uses idiomatic PydanticAI v2 (`Agent.iter()`, `AbstractCapability`, `Hooks`, `WrapperToolset`, `ProcessHistory`, `MCPToolset`).
   - Both tracks are inspected live side-by-side via a toggleable Rich CLI `--xray` inspector and wire-level JSONL traces.
6. **Per-Stage Directories & Strict 4-Gate Interactive Course Protocol:**
   - Every stage lives in `src/harness_lab/stages/s0N_<name>/` (`README.md`, `reading.md`, `installation.md`, plus future `run.py`, `scripts/`, `notes.md`) rather than single numbered files so reading guides, install logs, scripts, and stage docs stay organized cleanly.
   - Every stage enforces four **Hard-Stop Gates** ([COURSE.md](../COURSE.md)):
     - **Gate 1 (`reading.md`):** Present curated readings and focus questions, discuss concepts, log takeaways/open questions in `reading.md`, and stop until Gate 1 sign-off.
     - **Gate 2 (`installation.md`):** Present what/why, official installation docs, and exact proposed commands; answer user questions and record decisions in `installation.md`; run install or `ollama pull` commands **only** after explicit user approval, then append raw verification output.
     - **Gate 3 (`README.md` Parts `N.1`, `N.2`, …):** Build **one coding part at a time** — share a brief architecture plan → wait for go-ahead → implement *only* that part → run `uv run pytest` and `uv run ruff check` → stop and present clickable `file://` links, an architecture/code walkthrough, and raw test output so the user can eyeball code and verify tests before moving to the next part.
     - **Gate 4 (Drills, ADR & Progress):** Run hands-on/break-it drills with raw wire/trace/timing evidence, draft a 1-page `Status: proposed` ADR in `docs/decisions/NNN-title.md` (**only the user** marks it `accepted`), and update `docs/progress.md`.
7. **Antigravity Workspace Safety & Tooling Setup:**
   - Configured workspace rules, untrusted-data framing, `PreToolUse` safety hooks (8 synthetic safety test cases passed) and post-edit checks, and stage/runtime skills.

---

## 2. Complete Inventory of Files Already Created & Verified

### Course Hub, Governance & Tracking
- [COURSE.md](../COURSE.md) — 4-Gate interactive course protocol, stage index (`0.1`–`6.5`), and copy-paste prompts
- [agentic-playground-agy.md](../agentic-playground-agy.md) — full Hybrid Lab architecture & curriculum specification
- [AGENTS.md](../AGENTS.md) — workspace rules, 4-Gate protocol, Dual-Track discipline, security & approval invariants
- [docs/progress.md](./progress.md) — live Stage × Gate × Parts Progress Matrix (`Stage 0 → Gate 1`)
- [docs/decisions/README.md](./decisions/README.md) — ADR index and 1-page `Status: proposed` template
- [notes/README.md](../notes/README.md) — human-only lab journal instructions (never edited by agent unasked)

### Antigravity Hooks, Skills & Sandbox Rules
- [.agents/hooks.json](../.agents/hooks.json) — Antigravity hook wiring
- [.agents/hooks/safety_gate.py](../.agents/hooks/safety_gate.py) — `PreToolUse` safety guard (8 synthetic cases verified)
- [.agents/hooks/post_edit_guard.py](../.agents/hooks/post_edit_guard.py) — post-edit verification guard
- [.agents/skills/stage-runner/SKILL.md](../.agents/skills/stage-runner/SKILL.md) — 4-Gate stage execution procedure
- [.agents/skills/local-runtime-guard/SKILL.md](../.agents/skills/local-runtime-guard/SKILL.md) — Apple Silicon 64 GB `num_ctx`, 3-model co-residency & zero-spend checklist
- [sandbox_data/AGENTS.md](../sandbox_data/AGENTS.md) — untrusted-fixture framing inside `sandbox_data/`
- [.env.example](../.env.example) — template environment variables (no secrets committed)

### Per-Stage Modules (`7 stages / 21 files` verified)
All `reading.md` and `installation.md` files currently start at `Status: pending` with all relative links verified:

- **Stage 0 — Foundations (`0.1`–`0.4`):** [README.md](../src/harness_lab/stages/s00_foundations/README.md) · [reading.md](../src/harness_lab/stages/s00_foundations/reading.md) · [installation.md](../src/harness_lab/stages/s00_foundations/installation.md)
- **Stage 1 — Raw HTTP vs. PydanticAI (`1.1`–`1.3`):** [README.md](../src/harness_lab/stages/s01_raw_vs_pydantic/README.md) · [reading.md](../src/harness_lab/stages/s01_raw_vs_pydantic/reading.md) · [installation.md](../src/harness_lab/stages/s01_raw_vs_pydantic/installation.md)
- **Stage 2 — Manual ReAct vs. `Agent.iter()` (`2.1`–`2.3`):** [README.md](../src/harness_lab/stages/s02_manual_vs_iter/README.md) · [reading.md](../src/harness_lab/stages/s02_manual_vs_iter/reading.md) · [installation.md](../src/harness_lab/stages/s02_manual_vs_iter/installation.md)
- **Stage 3 — Tools, Sandboxing & HITL (`3.1`–`3.4`):** [README.md](../src/harness_lab/stages/s03_tools_guardrails/README.md) · [reading.md](../src/harness_lab/stages/s03_tools_guardrails/reading.md) · [installation.md](../src/harness_lab/stages/s03_tools_guardrails/installation.md)
- **Stage 4 — MCP Glass Box (`4.1`–`4.3`):** [README.md](../src/harness_lab/stages/s04_mcp_glassbox/README.md) · [reading.md](../src/harness_lab/stages/s04_mcp_glassbox/reading.md) · [installation.md](../src/harness_lab/stages/s04_mcp_glassbox/installation.md)
- **Stage 5 — Short- & Long-Term Memory (`5.1`–`5.3`):** [README.md](../src/harness_lab/stages/s05_memory_lab/README.md) · [reading.md](../src/harness_lab/stages/s05_memory_lab/reading.md) · [installation.md](../src/harness_lab/stages/s05_memory_lab/installation.md)
- **Stage 6 — Observatory, Gatekeeper, Evals & Trip-Planner Capstone (`6.1`–`6.5`):** [README.md](../src/harness_lab/stages/s06_observatory/README.md) · [reading.md](../src/harness_lab/stages/s06_observatory/reading.md) · [installation.md](../src/harness_lab/stages/s06_observatory/installation.md)

---

## 3. Non-Negotiable Rules & Invariants for Future Sessions

- **4-Gate Hard Stops:** Never skip Gate 1 (`reading.md`), Gate 2 (`installation.md`), or per-part Gate 3 eyeball stops.
- **Track A Isolation:** Track A raw code must contain zero `pydantic_ai` imports.
- **Approval Before Side Effects:** Ask for explicit user approval before running `uv add`, `uv python install`, `brew install`, `pip install`, `npm install`, `ollama pull`, `ollama rm`, enabling paid cloud profiles (`oracle`, hosted `Jev`), or `BypassSandbox: true`.
- **Secrets & Sandbox Containment:** Never read, print, echo, or commit `.env` or keys; never use `eval()`, `exec()`, or `shell=True` (use safe AST `eval_math` and `asyncio.create_subprocess_exec(..., shell=False)`); confine tools, SQLite DBs, and subprocesses inside `sandbox_data/`; treat `sandbox_data/` contents purely as untrusted fixtures.
- **MCP Isolation:** Never register experimental Stage 4 MCP servers (e.g., `lab_kv_server.py`) in `~/.gemini/config/mcp_config.json`.
- **Testing & Evidence Discipline:** Mark live-model tests `@pytest.mark.live` (skipped by default); always run offline `uv run pytest` and `uv run ruff check` and paste raw evidence rather than summarizing from memory. Keep `traces/`, `sandbox_data/*.db`, `sandbox_data/.tool_outputs/`, and `benchmarks/results/` out of git.
- **Human Ownership Boundaries:** Never edit `notes/` unless explicitly asked; only the user marks an ADR `accepted`.

---

## 4. Open Decisions Queued for Stage 0 — Gate 2

*(Wait until Stage 0 Gate 1 is signed off before deciding or executing these in [s00_foundations/installation.md](../src/harness_lab/stages/s00_foundations/installation.md).)*

1. Confirm Python version (`3.12` vs. `3.13`) during `installation.md` Q&A.
2. Inspect already-installed local `uv`, `ruff`, `ollama`, and `python3` binaries before installing anything.
3. Choose initial local model tags within the 64 GB unified-memory co-residency budget (`workhorse` / `fast` / `bonsai-2.5` baseline).

---

## 5. Quick Resume Prompt (Use in a New Conversation)

**Shortest option:** Simply send `read resume.md` (defined in [resume.md](../resume.md)), which dynamically reads the active cursor in `docs/progress.md` and brings up the right Gate prompt.

**Or paste the full explicit prompt:**

> Let's resume our `agentic-playground` course from `docs/session-handoff.md` and `docs/progress.md`. Please read `docs/session-handoff.md`, `docs/progress.md`, `COURSE.md`, and `AGENTS.md`, activate the `stage-runner` skill, and start **Stage 0 — Gate 1** using `src/harness_lab/stages/s00_foundations/README.md` and `src/harness_lab/stages/s00_foundations/reading.md`. Do **not** run any installations or write code yet — present the Stage 0 reading materials and focus questions so we can discuss them first.
