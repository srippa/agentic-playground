# Stage 4 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **MCP Protocol Specification & Official Ecosystem**
   - Model Context Protocol Spec & Architecture: [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
   - Official MCP Reference Servers: [https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
   - Official MCP Inspector: [https://github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector)
2. **Python Server & Client Tooling**
   - FastMCP Documentation: [https://gofastmcp.com/](https://gofastmcp.com/)
   - PydanticAI MCP Client Integration (`MCPToolset`): [https://ai.pydantic.dev/mcp/](https://ai.pydantic.dev/mcp/)
3. **Structured Courses**
   - DeepLearning.AI — *MCP: Build Rich-Context AI Apps with Anthropic*: [https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic](https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic)
   - Hugging Face — *MCP Course*: [https://huggingface.co/learn/mcp-course](https://huggingface.co/learn/mcp-course)

---

## Guided Focus Questions

1. **Tools vs. Direct Functions vs. CLI vs. MCP:** When does paying the MCP process/IPC boundary make architectural sense compared to plain Python tools in `tools/`?
2. **JSON-RPC 2.0 Handshake & Capabilities:** What is negotiated during `initialize` / `notifications/initialized`, and how do `tools`, `resources`, and `prompts` differ cleanly?
3. **Transport Tradeoffs (`stdio` vs. Streamable HTTP):** Why is `stdio` ideal for local sandboxed lab servers while Streamable HTTP replaces legacy HTTP+SSE for remote servers — and what stdout hygiene bug breaks `stdio` servers immediately? *(Hint: `print()` vs. `stderr`!)*
4. **Tool Name Collisions & Untrusted Schemas:** How can a malicious or bloated MCP server poison tool descriptions or bloat context, and how does `MCPToolset` prefixing + filtering defend against it?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
