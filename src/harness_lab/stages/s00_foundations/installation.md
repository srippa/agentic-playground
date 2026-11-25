# Stage 0 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan and the official installation docs, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install or `ollama pull` command.

---

## What Will Be Installed & Why

1. **`uv` (Python Package & Project Manager):** Reproducible dependency lockfiles (`uv.lock`), fast virtual environments, and isolated Python version management without polluting system Python.
2. **Python `3.12` or `3.13` (via `uv`):** Modern typing (`Self`, type aliases), `asyncio` improvements, and full compatibility with `httpx`, `pydantic`, and Stage 1+ `pydantic-ai`.
3. **`ruff` (Linter & Formatter):** Fast static verification (`uv run ruff check`) enforced after every Gate 3 coding part.
4. **Core Python Runtime & Test Libraries:**
   - `httpx`: Raw async HTTP client + custom transport hook for the Stage 0 Wire-Tap.
   - `pydantic`: Configuration validation and typed wire-trace schemas (note: pure Pydantic data validation, *not* `pydantic-ai` yet).
   - `rich`: Console panels/tables for the Glass-Box X-Ray Inspector.
   - `pytest`: Deterministic offline unit test runner (with `@pytest.mark.live` marker deselected by default).
5. **Local Model Runtime(s) & Initial Baseline Model:**
   - **Ollama** (primary local runtime) and/or **LM Studio** (secondary local OpenAI-compatible server / MLX GGUF inspection).
   - Initial local weights within our 64 GB unified memory budget (confirm exact model tag, e.g., `qwen3.8:27b` or `Fast` baseline, during Q&A below).

---

## Official Installation Docs

Read these official guides before approving execution:

- `uv` Installation: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
- Installing Python with `uv`: [https://docs.astral.sh/uv/guides/install-python/](https://docs.astral.sh/uv/guides/install-python/)
- `ruff` Installation: [https://docs.astral.sh/ruff/installation/](https://docs.astral.sh/ruff/installation/)
- Ollama Download & Docs: [https://ollama.com/download](https://ollama.com/download) & [https://docs.ollama.com](https://docs.ollama.com)
- LM Studio Docs: [https://lmstudio.ai/docs](https://lmstudio.ai/docs)

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below. Exact `uv` / `ollama pull` tags may be refined during Q&A.)*

```zsh
# 1. Check already-installed tools first (read-only check)
which uv ollama ruff python3

# 2. Install uv / ruff / ollama ONLY if missing (confirm preferred installer method during Q&A)
# brew install uv ruff ollama

# 3. Pin Python version via uv (confirm 3.12 vs 3.13 during Q&A)
uv python install 3.12
uv init --python 3.12

# 4. Install Stage 0 Track A & dev dependencies (no pydantic-ai yet)
uv add httpx pydantic rich
uv add --dev pytest ruff

# 5. Pull initial local runtime model(s) (confirm exact tag & disk/memory budget during Q&A)
# ollama pull <approved-model-tag>
```

---

## Q&A & Discussion Log

*(Record user questions, doc clarifications, Python version choice `3.12` vs `3.13`, and local runtime/tag choices here.)*

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Python Version Chosen:** *(TBD in Q&A: `3.12` vs `3.13`)*
- **Local Runtime & Model Tags Approved:** *(TBD in Q&A)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append exact command outputs, `uv --version`, `python --version`, `uv run pytest`, `uv run ruff check`, and `ollama list` after approved execution.)*
