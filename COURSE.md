# Agentic Glass-Box Lab — Interactive Antigravity Course

> **Course Format:** Agentic development inside this Antigravity workspace (`agentic-playground`).
> Every stage follows a strict **4-Gate Interactive Protocol** so you understand concepts before installing tools, understand tools before installing them, and inspect every coding slice's architecture, code, and tests before advancing.
>
> **Architecture & Curriculum Spec:** [agentic-playground-agy.md](./agentic-playground-agy.md)  
> **Quick Resume Entrypoint:** [resume.md](./resume.md) (or tell a new chat: `read resume.md`)  
> **Session Handoff (New Chat Resume):** [docs/session-handoff.md](./docs/session-handoff.md)  
> **Live Progress Cursor:** [docs/progress.md](./docs/progress.md)  
> **Workspace Rules & Safety:** [AGENTS.md](./AGENTS.md)

---

## How Each Stage Works (The 4-Gate Protocol)

No stage skips ahead. At every stage `s0N_<name>`, the Antigravity agent works with you through four explicit gates:

### Gate 1 — Pre-Reading & Concept Chat (**HARD STOP**)
1. The agent presents that stage's `reading.md` (for example [s00_foundations/reading.md](./src/harness_lab/stages/s00_foundations/reading.md) — curated links, focus questions, and what to look for).
2. You read the materials, ask questions, challenge assumptions, and discuss mental models with the agent.
3. The agent logs key takeaways and open answers in that stage's `reading.md` under `## Q&A & Discussion Notes`.
4. **Hard Stop:** Do **not** propose or run installations or write code until you explicitly mark Gate 1 ready (`Gate 1 Sign-Off`).

### Gate 2 — Installations & Approval (**HARD STOP**)
1. The agent drafts/presents that stage's `installation.md` detailing **what** will be installed, **why**, official documentation links, and the **exact proposed commands**.
2. You read the official installation docs, ask questions (runtime versions, disk/64 GB memory impact, quantization choices, sandbox implications), and align on decisions.
3. The agent records the conversation and agreed conclusions in `installation.md` under `## Q&A & Discussion Log` and `## Decisions & Approval`.
4. **Hard Stop:** Only after your **explicit approval** does the agent execute the installation commands and append the **raw verification output** to `## Verification Output` in `installation.md`.

### Gate 3 — Coding Part-by-Part (**HARD STOP After Every Part**)
Each stage is broken into small, coherent coding parts (`N.1`, `N.2`, ... listed in each stage's `README.md`). Never build multiple parts in one shot.

For **each single part**:
1. **Plan First:** The agent shares a brief architecture/design slice plan (files to touch, responsibilities, Track A raw vs. Track B PydanticAI separation, invariants, and open questions) and waits for your go-ahead.
2. **Implement & Run Offline Verification:** The agent implements *only* that part, keeping Track A framework-free and Track B idiomatic PydanticAI v2, then runs `uv run pytest` and `uv run ruff check`.
3. **Architecture & Code Eyeball Check (Hard Stop):** The agent stops and presents:
   - Clickable `file://` links to every created or modified file;
   - A concise architecture & code walkthrough (control flow, data structures, safety invariants, Track A vs. Track B boundaries);
   - Raw `uv run pytest` and `uv run ruff check` outputs.
4. **Chat & Verify Before Advancing:** You inspect the code, ask questions, request tweaks or live local checks, and explicitly approve moving to the next part (`N.2`, etc.).

### Gate 4 — Break-It Drills, ADR & Progress Update (**HARD STOP**)
1. Run the stage's hands-on / break-it experiments locally and paste raw wire logs, traces, diffs, or timings (evidence over assertions).
2. Draft a 1-page ADR in [docs/decisions/](./docs/decisions/README.md) with `Status: proposed` capturing the stage's key architectural tradeoff (**only you** mark an ADR `accepted`).
3. Update [docs/progress.md](./docs/progress.md) with completed parts, test/eval evidence, and the next stage cursor before opening the next stage's Gate 1.

---

## Stage Index (Stages 0–6)

| Stage | Directory & Guide | Pre-Reading | Installations | Parts | Stage ADR |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 0** | [s00_foundations/README.md](./src/harness_lab/stages/s00_foundations/README.md) | [reading.md](./src/harness_lab/stages/s00_foundations/reading.md) | [installation.md](./src/harness_lab/stages/s00_foundations/installation.md) | `0.1`–`0.4` | `001-runtime-and-wire-tap.md` |
| **Stage 1** | [s01_raw_vs_pydantic/README.md](./src/harness_lab/stages/s01_raw_vs_pydantic/README.md) | [reading.md](./src/harness_lab/stages/s01_raw_vs_pydantic/reading.md) | [installation.md](./src/harness_lab/stages/s01_raw_vs_pydantic/installation.md) | `1.1`–`1.3` | `002-model-config-and-thinking.md` |
| **Stage 2** | [s02_manual_vs_iter/README.md](./src/harness_lab/stages/s02_manual_vs_iter/README.md) | [reading.md](./src/harness_lab/stages/s02_manual_vs_iter/reading.md) | [installation.md](./src/harness_lab/stages/s02_manual_vs_iter/installation.md) | `2.1`–`2.3` | `003-loop-and-structured-output.md` |
| **Stage 3** | [s03_tools_guardrails/README.md](./src/harness_lab/stages/s03_tools_guardrails/README.md) | [reading.md](./src/harness_lab/stages/s03_tools_guardrails/reading.md) | [installation.md](./src/harness_lab/stages/s03_tools_guardrails/installation.md) | `3.1`–`3.4` | `004-tool-safety-and-hitl.md` |
| **Stage 4** | [s04_mcp_glassbox/README.md](./src/harness_lab/stages/s04_mcp_glassbox/README.md) | [reading.md](./src/harness_lab/stages/s04_mcp_glassbox/reading.md) | [installation.md](./src/harness_lab/stages/s04_mcp_glassbox/installation.md) | `4.1`–`4.3` | `005-mcp-architecture-and-transport.md` |
| **Stage 5** | [s05_memory_lab/README.md](./src/harness_lab/stages/s05_memory_lab/README.md) | [reading.md](./src/harness_lab/stages/s05_memory_lab/reading.md) | [installation.md](./src/harness_lab/stages/s05_memory_lab/installation.md) | `5.1`–`5.3` | `006-memory-and-compaction.md` |
| **Stage 6** | [s06_observatory/README.md](./src/harness_lab/stages/s06_observatory/README.md) | [reading.md](./src/harness_lab/stages/s06_observatory/reading.md) | [installation.md](./src/harness_lab/stages/s06_observatory/installation.md) | `6.1`–`6.5` | `007-eval-gatekeeper-and-capstone.md` |

---

## Copy-Paste Antigravity Session Prompts

Use these prompts in Antigravity chat to drive any stage cleanly without skipping gates:

- **Resume in a New Chat:** `read resume.md`
- **Wrap Up Before Switching Chats:** `prepare for a new chat` (flushes stage notes, `docs/progress.md`, and `docs/session-handoff.md` so the next chat picks up seamlessly via `read resume.md`).
- **Start a Stage (Gate 1 — Pre-Reading):**
  > Let's start Stage `<N>`. Use the `stage-runner` skill, check `docs/progress.md` and `src/harness_lab/stages/s0N_<name>/README.md`, and present `reading.md` first. Stop at Gate 1 so I can read and discuss before touching installations or code.

- **Move to Installations (Gate 2 — Installations & Approval):**
  > Gate 1 is done. Let's review `src/harness_lab/stages/s0N_<name>/installation.md`. Explain what we need and why, link the official docs, and wait for my questions and explicit approval before running any install commands.

- **Build One Coding Part (Gate 3 — Plan → Code → Eyeball):**
  > Let's work on Part `<N.M>` from `src/harness_lab/stages/s0N_<name>/README.md`. Share a brief architecture plan first and wait for my go-ahead. After implementing Part `<N.M>`, run `uv run pytest` and `uv run ruff check`, show me clickable file links, an architecture/code walkthrough, and raw test output, and stop so I can eyeball everything before the next part.

- **Close Out a Stage (Gate 4 — Drills, ADR & Progress):**
  > All coding parts for Stage `<N>` are verified. Let's run the hands-on break-it drills with raw wire/trace/timing evidence, draft `docs/decisions/00X-<title>.md` as `Status: proposed`, and update `docs/progress.md`.
