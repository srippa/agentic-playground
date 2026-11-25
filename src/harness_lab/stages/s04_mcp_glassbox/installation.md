# Stage 4 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan and the official installation docs, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install command.
> **MCP Isolation Rule:** Experimental lab servers (`lab_kv_server.py`) stay strictly inside this project's `MCPToolset` / `stdio` harness and MUST NEVER be added to `~/.gemini/config/mcp_config.json`.

---

## What Will Be Installed & Why

1. **`pydantic-ai-slim[openai,mcp]`:** Adds PydanticAI's `mcp` extra (`MCPToolset`, `MCPServerStdio`, `MCPServerStreamableHTTP`) plus the underlying official `mcp` Python SDK used directly by Track A's framework-free JSON-RPC client.
2. **`fastmcp`:** Clean ergonomic Python server framework for authoring our project-local `lab_kv_server.py` (`tools`, `resources`, `prompts`) without boilerplate protocol parsing.
3. **`uvx` / Optional `npx` Verification:** Check `uvx` (bundled with `uv`) for ephemeral server launches; optionally check whether `npx` is installed if we want to inspect `lab_kv_server.py` with the standalone MCP Inspector locally.

---

## Official Installation Docs

- FastMCP Installation: [https://gofastmcp.com/getting-started/installation](https://gofastmcp.com/getting-started/installation)
- PydanticAI MCP Integration: [https://ai.pydantic.dev/mcp/](https://ai.pydantic.dev/mcp/)
- MCP Inspector: [https://github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector)

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below.)*

```zsh
# 1. Install MCP extra for pydantic-ai-slim + official mcp SDK + fastmcp
uv add "pydantic-ai-slim[openai,mcp]" fastmcp

# 2. Verify installed mcp & fastmcp versions and uvx availability
uv run python -c "import mcp, fastmcp; print('mcp & fastmcp ready')"
which uvx
# Optional check if using MCP Inspector interactively:
# which npx
```

---

## Q&A & Discussion Log

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Use MCP Inspector (`npx`)?:** *(TBD in Q&A: yes/no)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append `uv add` output, verified module imports, and `uvx` path check after approved execution.)*
