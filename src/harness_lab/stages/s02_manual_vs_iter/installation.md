# Stage 2 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan and the official setup notes, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install or model pull command.

---

## What Will Be Installed & Why

1. **No Mandatory Core Framework Installs:** Stage 2 builds on Stage 1's `pydantic-ai-slim[openai]` and Track A's `httpx` + `pydantic`.
2. **Optional `tzdata` Package:** Ensures cross-platform IANA timezone support (`zoneinfo`) if timezone-aware scheduling/clock tools are tested cleanly inside sandbox drills.
3. **Verify `pydantic-ai` v2 Loop & Capability Symbols:** Confirm `Agent.iter`, `AbstractCapability`, `Hooks`, and `UsageLimits` exist in the installed `pydantic-ai` version before authoring Track B.
4. **Optional Local `chaos` Model Tag (Ollama / LM Studio):** A intentionally tiny/weaker local model used *only* for testing JSON schema retry exhaustion and malformed tool-call stress drills (never loaded concurrently with large models without checking our 64 GB memory budget).

---

## Official Installation Docs

- PydanticAI Agents & `Agent.iter()`: [https://ai.pydantic.dev/agents/](https://ai.pydantic.dev/agents/)
- PydanticAI Capabilities: [https://ai.pydantic.dev/capabilities/](https://ai.pydantic.dev/capabilities/)
- Ollama Library / Model Tags: [https://docs.ollama.com](https://docs.ollama.com)

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below.)*

```zsh
# 1. Verify pydantic-ai v2 symbols already installed from Stage 1
uv run python -c "import pydantic_ai; from pydantic_ai.usage import UsageLimits; print(pydantic_ai.__version__, UsageLimits)"

# 2. Optional: add tzdata if needed for timezone-aware tools
# uv add tzdata

# 3. Optional: pull weak local model tag for chaos/retry drills (confirm exact tag & size in Q&A)
# ollama pull <approved-chaos-model-tag>
```

---

## Q&A & Discussion Log

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Install `tzdata`?:** *(TBD in Q&A: yes/no)*
- **Chaos Model Tag Approved (if any):** *(TBD in Q&A)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append verified import check output, any `uv add` output, and `ollama list` after approved execution.)*
