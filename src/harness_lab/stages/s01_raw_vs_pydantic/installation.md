# Stage 1 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan and the official installation docs, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install command.

---

## What Will Be Installed & Why

1. **`pydantic-ai-slim[openai]` (Track B Framework):** Introduces idiomatic PydanticAI v2 (`Agent`, `OpenAIChatModel`, `ModelRequest`, `ModelResponse`, `ThinkingPart`, and offline `TestModel`/`FunctionModel`) *only* after Track A raw HTTP is demystified. Using the `-slim[openai]` extra avoids installing unused cloud-provider SDKs while supporting local OpenAI-compatible endpoints (Ollama / LM Studio / MLX).
   *(Alternative: full `pydantic-ai` meta-package if decided during Q&A — note the extra dependency footprint.)*

---

## Official Installation Docs

- PydanticAI Installation Guide: [https://ai.pydantic.dev/install/](https://ai.pydantic.dev/install/)
- PydanticAI Models & OpenAI-Compatible Providers: [https://ai.pydantic.dev/models/](https://ai.pydantic.dev/models/)

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below.)*

```zsh
# Install Track B PydanticAI OpenAI-compatible extra
uv add "pydantic-ai-slim[openai]"

# Verify installed pydantic-ai version and offline TestModel import
uv run python -c "import pydantic_ai; print(pydantic_ai.__version__)"
```

---

## Q&A & Discussion Log

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Package Variant (`pydantic-ai-slim[openai]` vs `pydantic-ai`):** *(TBD in Q&A)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append `uv add` output, lockfile summary, and verified `pydantic_ai.__version__` after approved execution.)*
