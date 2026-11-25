# Stage 0 — Foundations (`s00_foundations`)

> **Track Focus:** Shared Infrastructure, Wire-Tap Transport & Local 64 GB Runtime Verification  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 0.1–0.4)` → `Gate 4 (Drills & ADR 001)`

---

## Objective

Establish a deterministic, observable Python workspace powered by `uv`, build a framework-free `httpx` wire-tap transport that captures exact HTTP requests, responses, and timings without leaking secrets, and verify local Apple Silicon 64 GB runtimes (Ollama / LM Studio / optional MLX) before touching any agent framework.

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/001-runtime-and-wire-tap.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 0.1** | Workspace Skeleton & 64 GB Model Profiles | `pyproject.toml`, config module with local 64 GB model profile table (`workhorse`, `bonsai-2.5`, `fast`, `chaos`, `decision`, `embed`), `lab` CLI entrypoint | ⬜ Not started |
| **Part 0.2** | Glass-Box Wire-Tap HTTP Transport | Custom `httpx` transport/hooks capturing exact request JSON, response headers/body, latency, and header redaction to JSONL `traces/` | ⬜ Not started |
| **Part 0.3** | Local Runtime Doctor (`lab doctor`) | Probe Ollama / LM Studio `/v1/models`, report loaded tags, `num_ctx`, Apple Silicon 64 GB memory headroom, and `Bonsai 2.5` readiness | ⬜ Not started |
| **Part 0.4** | Sandbox & Test Hygiene Guardrails | Resolved-path `sandbox_data/` containment helpers, `@pytest.mark.live` default-skip config, offline wire-tap unit tests | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Run `uv run pytest` and `uv run ruff check` with zero offline failures.
2. Run `uv run lab doctor` against your local runtime and inspect raw wire logs in `traces/` (confirming secrets/auth headers are redacted).
3. Verify memory co-residency discipline per `.agents/skills/local-runtime-guard/SKILL.md` (explicit `num_ctx`, unified-memory budget check).
4. Draft `docs/decisions/001-runtime-and-wire-tap.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
