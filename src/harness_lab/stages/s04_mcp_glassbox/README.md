# Stage 4 — Model Context Protocol (MCP) Glass Box (`s04_mcp_glassbox`)

> **Track Focus:** Local `FastMCP` Server + Track A Raw JSON-RPC 2.0 `stdio` Client vs. Track B `MCPToolset`  
> **Stage Gate Sequence:** `Gate 1 (reading.md)` → `Gate 2 (installation.md)` → `Gate 3 (Parts 4.1–4.3)` → `Gate 4 (Drills & ADR 005)`

---

## Objective

Demystify the Model Context Protocol (`MCP`) at the raw JSON-RPC 2.0 wire level before wrapping it in PydanticAI's `MCPToolset`. You will build a local `FastMCP` KV/notes server, drive it with a raw `stdio` client (`initialize` → `tools/list` → `tools/call`), and compose it cleanly into Stage 3's approval and sandbox guardrails — strictly isolated inside this project (never registered globally in Antigravity's `~/.gemini/config/mcp_config.json`).

---

## Stage Files & Navigation

- **Course Hub:** [COURSE.md](../../../../COURSE.md)
- **Progress Cursor:** [docs/progress.md](../../../../docs/progress.md)
- **Gate 1 — Pre-Reading:** [reading.md](./reading.md)
- **Gate 2 — Installations:** [installation.md](./installation.md)
- **Gate 4 — Stage ADR (draft at end):** `docs/decisions/005-mcp-architecture-and-transport.md` (`Status: proposed`)

---

## Gate 3 Coding Parts (One Part at a Time)

Do **not** implement ahead. Each part follows **Plan First → Implement & Run Offline Tests (`uv run pytest` + `uv run ruff check`) → Architecture/Code Eyeball Stop → Explicit Proceed**.

| Part | Scope | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Part 4.1** | Local `FastMCP` KV & Notes Server (`lab_kv_server.py`) | Scoped project-local MCP server exposing deterministic KV/notes tools & resources over `stdio` backed by `sandbox_data/` | ⬜ Not started |
| **Part 4.2** | Track A Raw JSON-RPC 2.0 `stdio` Client | Framework-free `mcp` SDK client performing `initialize`, `tools/list`, and `tools/call` over `stdio` with exact JSON-RPC request/response framing logged for `--xray` | ⬜ Not started |
| **Part 4.3** | Track B `MCPToolset` & Cross-Track Harness | Idiomatic `pydantic-ai` `MCPToolset` with tool prefixing, error handling, optional read-only Streamable HTTP probe, and `uv run lab stage 4 --xray` | ⬜ Not started |

---

## Gate 4 — Hands-On Drills & Definition of Done

1. Run `uv run pytest` and `uv run ruff check` with offline tests verifying JSON-RPC `initialize` → `tools/list` → `tools/call` roundtrips and clean subprocess shutdown.
2. Run `uv run lab stage 4 --xray` inspecting raw JSON-RPC 2.0 handshake & schema payloads vs. PydanticAI `MCPToolset` tool bindings.
3. Verify isolation: confirm `~/.gemini/config/mcp_config.json` is untouched and `lab_kv_server.py` stays strictly scoped to this repo.
4. Draft `docs/decisions/005-mcp-architecture-and-transport.md` (`Status: proposed`) and update [docs/progress.md](../../../../docs/progress.md).
