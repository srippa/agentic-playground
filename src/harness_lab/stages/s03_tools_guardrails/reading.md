# Stage 3 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **Tool Design & Ergonomics for Agents**
   - Anthropic — *Writing Effective Tools for Agents — with Agents*: [https://www.anthropic.com/engineering/writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
2. **PydanticAI Toolsets, Approval & Offline Testing**
   - PydanticAI Toolsets (`WrapperToolset`, composition): [https://ai.pydantic.dev/toolsets/](https://ai.pydantic.dev/toolsets/)
   - PydanticAI Deferred Tools (Human-in-the-Loop): [https://ai.pydantic.dev/deferred-tools/](https://ai.pydantic.dev/deferred-tools/)
   - PydanticAI Testing (`TestModel`, `FunctionModel`): [https://ai.pydantic.dev/testing/](https://ai.pydantic.dev/testing/)
3. **Indirect Prompt Injection & Sandbox Threat Models**
   - Simon Willison on Prompt Injection: [https://simonwillison.net/tags/prompt-injection/](https://simonwillison.net/tags/prompt-injection/)
   - Workspace Reference: `sandbox_data/AGENTS.md`

---

## Guided Focus Questions

1. **Schema Ergonomics & Error Messages:** How do clear parameter descriptions and actionable error strings returned to the model (rather than raw Python tracebacks) cut wasted tool retries?
2. **Containment Over Blacklists:** Why do naive string checks (`".." not in path`) fail against symlinks or resolved paths, and why must `Path.resolve().is_relative_to(sandbox_root)` be enforced right inside the tool boundary?
3. **Context Bloat vs. Artifact Spill:** Why is returning a 50 KB tool payload verbatim destructive to both accuracy and 64 GB KV cache — and how should a harness truncate inline output while spilling full bytes to `sandbox_data/.tool_outputs/`?
4. **Why `DeferredToolRequests` Exists:** Why must dangerous/mutating tool calls pause execution and return control to the host caller rather than blocking inside a tool coroutine on `input()`?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
