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

## Approved Commands

*(User chose the full `pydantic-ai` meta-package over `pydantic-ai-slim[openai]` and approved execution on 2026-11-26.)*

```zsh
# Install full pydantic-ai meta-package (Track B framework + all default providers/extras)
uv add pydantic-ai

# Verify installed pydantic-ai version and offline/OpenAI model imports
uv run python -c "import pydantic_ai; from pydantic_ai.models.test import TestModel; from pydantic_ai.models.openai import OpenAIChatModel; print('pydantic-ai:', pydantic_ai.__version__, '| TestModel:', TestModel.__name__, '| OpenAIChatModel:', OpenAIChatModel.__name__)"
```

---

## Q&A & Discussion Log

- **Q1:** Why not just use the full `pydantic-ai` package instead of `pydantic-ai-slim[openai]`?
- **A1:** Both expose the identical `import pydantic_ai` API (`pydantic-ai` is a meta-package installing `pydantic-ai-slim` with default provider/tool extras including OpenAI, Anthropic, Google, MCP, Evals, Logfire, etc.). `pydantic-ai-slim[openai]` keeps `uv.lock` minimal for staged learning/production containers, while full `pydantic-ai` gives batteries-included multi-provider support (useful for experimenting with OpenCode Zen's OpenAI/Anthropic/Gemini routes, MCP, and evals) with negligible overhead on 64 GB Apple Silicon. Track A isolation remains identical (zero `pydantic_ai` imports in Track A).
- **Q2:** Should we pull local Ollama models now or keep them deferred?
- **A2:** Keep Ollama model pulls deferred until needed for live runs; offline tests use `httpx.MockTransport` and PydanticAI `TestModel`/`FunctionModel`.

---

## Decisions & Approval

- **Status:** `approved`
- **Package Variant (`pydantic-ai-slim[openai]` vs `pydantic-ai`):** `pydantic-ai` (full meta-package)
- **Local Ollama Model Pulls:** Deferred until needed for live runs
- **User Explicit Approval:** User approved installing full `pydantic-ai` and deferring Ollama model pulls (2026-11-26)

---

## Verification Output

```text
$ uv add pydantic-ai
Resolved 102 packages in 1.83s
   Building harness-lab @ file:///Users/shmuelrippa/dvlp/agentic-playground
      Built harness-lab @ file:///Users/shmuelrippa/dvlp/agentic-playground
Prepared 79 packages in 985ms
Uninstalled 1 package in 1ms
Installed 79 packages in 101ms
 + pydantic-ai==2.75.0
 + pydantic-ai-slim==2.75.0
 + pydantic-evals==2.75.0
 + pydantic-graph==2.75.0
 + openai==3.60.0
 + anthropic==2.14.0
 + google-genai==2.34.0
 + mcp==2.3.0
 + fastmcp-slim==4.2.6
 + logfire==6.0.1
 + prompt-toolkit==3.0.53
(79 packages installed; pyproject.toml updated with "pydantic-ai>=2.75.0")

$ uv run python -c "import pydantic_ai; from pydantic_ai.models.test import TestModel; from pydantic_ai.models.openai import OpenAIChatModel; print('pydantic-ai:', pydantic_ai.__version__, '| TestModel:', TestModel.__name__, '| OpenAIChatModel:', OpenAIChatModel.__name__)"
pydantic-ai: 2.75.0 | TestModel: TestModel | OpenAIChatModel: OpenAIChatModel

$ uv run pytest && uv run ruff check
============================= test session starts ==============================
platform darwin -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/shmuelrippa/dvlp/agentic-playground
configfile: pyproject.toml
testpaths: tests
plugins: platformdirs-4.14.8, anyio-4.16.0, logfire-sdk-6.0.1
collecting ... 
collected 32 items / 1 deselected / 31 selected                                

tests/test_config_and_cli.py .........                                   [ 29%]
tests/test_doctor.py .......                                             [ 51%]
tests/test_sandbox_and_hygiene.py .......                                [ 74%]
tests/test_wire_tap.py ........                                          [100%]

======================= 31 passed, 1 deselected in 0.11s =======================
All checks passed!
```
