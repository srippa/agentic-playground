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

# 2. Install uv and Ollama Desktop app via Homebrew (keep ruff project-only via uv)
brew install uv
brew install --cask ollama

# 3. Pin Python 3.13 via uv and initialize bare workspace project
uv python install 3.13
uv init --bare --name harness-lab --python 3.13

# 4. Install Stage 0 Track A & dev dependencies (no pydantic-ai yet)
uv add httpx pydantic rich
uv add --dev pytest ruff

# 5. Pull initial local runtime model(s) (deferred until ollama --version is verified)
# ollama pull <approved-model-tag>
```

---

## Q&A & Discussion Log

*(Record user questions, doc clarifications, Python version choice `3.12` vs `3.13`, and local runtime/tag choices here.)*

- **Q1:** Is there any downside to using Homebrew (`brew`) for installing `uv`, `ruff`, and `ollama`?
- **A1:** For `uv`, `brew install uv` is very clean (only minimal release lag vs. standalone). For `ruff`, installing globally via Homebrew risks version drift vs. `uv.lock`, so it is better kept project-only (`uv add --dev ruff`, run via `uv run ruff check`). For `ollama`, `brew install ollama` (CLI formula) makes daemon env vars easy in terminal but lacks the menu-bar app/auto-updater and can lag upstream; `brew install --cask ollama` installs the official signed `/Applications/Ollama.app` (both formulas shouldn't be mixed).
- **Q2:** Will Ollama appear in the Applications menu if installed with `--cask`?
- **A2:** Yes—`brew install --cask ollama` installs `/Applications/Ollama.app`, appearing in `/Applications`, Spotlight, and the menu bar while also exposing the `ollama` CLI.
- **Q3:** Python `3.12` vs `3.13` (and compatibility with the Stage 6 travel assistant / capstone stack)?
- **A3:** Chose Python `3.13`; all planned Stages 0–6 dependencies (`httpx`, `pydantic`, `rich`, `pytest`, `ruff`, `pydantic-ai`, `aiosqlite`, `mcp`, `numpy`, `opentelemetry-*`, `pydantic-evals`) support Python `3.13`. Model pulls deferred until `ollama --version` is verified.
- **Q4:** Why `uv` instead of `pixi`?
- **A4:** `pixi` excels for mixed Conda + C++/CUDA + non-Python toolchains, whereas this lab is 100% PyPI-first (`pydantic-ai` v2, `mcp`/`FastMCP`, `opentelemetry-*`) where `uv` avoids Conda-forge lag, matches upstream MCP (`uv run`/`uvx`) and PydanticAI conventions, and uses standard PEP `pyproject.toml` + `.venv`.

---

## Decisions & Approval

- **Status:** `approved` (Gate 2 complete; model pulls intentionally deferred until needed)
- **Python Version Chosen:** `3.13`
- **Local Runtime & Model Tags Approved:** `Ollama Desktop via brew install --cask ollama; initial model pull deferred until needed`
- **User Explicit Approval:** Approved in chat (2026-11-25) — tools, Python 3.13, and unsandboxed execution approved; confirmed `"defer loading models until we need them"`.

---

## Verification Output

```text
$ uv --version && uv run python --version && uv run ruff --version && uv run pytest --version
uv 0.13.10 (Homebrew 2026-11-24 aarch64-apple-darwin)
Python 3.13.18
ruff 0.17.6
pytest 9.2.0

$ which ollama && ollama --version
/opt/homebrew/bin/ollama
Warning: could not connect to a running Ollama instance
Warning: client version is 0.40.18

$ git status --short
 M docs/progress.md
 M src/harness_lab/stages/s00_foundations/installation.md
 M src/harness_lab/stages/s00_foundations/reading.md
 M src/harness_lab/stages/s05_memory_lab/installation.md
?? .python-version
?? pyproject.toml
?? uv.lock
```

*(Ollama Desktop `0.40.18` installed at `/Applications/Ollama.app`; daemon not yet started, and model pulls deferred pending user confirmation.)*
