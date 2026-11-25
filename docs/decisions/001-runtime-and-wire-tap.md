# 001: Local 64 GB Runtime Strategy & Wire-Tap Transport
Date: 2026-11-25 · Stage: 0 · Status: accepted

## Context
We are building an inspectable dual-track agentic lab (Track A framework-free Python vs. Track B PydanticAI v2) on an Apple Silicon MacBook Pro with 64 GB unified memory (~48 GB default macOS wired-GPU ceiling). To compare raw HTTP behavior against framework behavior honestly, we need:
1. Reproducible Python packaging and a declarative local-first model roster (`models.toml`) that prevents accidental cloud spend and 64 GB memory thrashing.
2. Accurate HTTP-level observability that works identically across Track A and Track B without buffering SSE streams, leaking credentials, or silently ignoring Ollama's `num_ctx` trap on `/v1/chat/completions`.
3. Safe workspace boundaries before introducing agent tools in later stages.

## Options
1. **Wire Observation Layer:**
   - *Option A:* Log high-level Python SDK request/response objects or `httpx.event_hooks` (`await response.aread()`). Simple, but hides SDK schema rewrites and buffers live SSE streams.
   - *Option B (Chosen):* Wrap `httpx.AsyncBaseTransport` (`WireTapTransport` + `_TeeAsyncByteStream`) to tee raw bytes while streaming and redact sensitive headers at one choke point.
2. **Local Runtime API Plane:**
   - *Option A:* Exclusively `/v1/chat/completions` everywhere. Portable, but Ollama silently ignores request-body `num_ctx` on `/v1` and omits loaded-VRAM / `context_length` introspection.
   - *Option B (Chosen):* Hybrid control/data plane—OpenAI-compatible `/v1` for portable inference alongside native Ollama `/api/version`, `/api/tags`, `/api/ps`, `/api/show`, and `/api/embed` in `lab doctor` and `embed`.
3. **Workspace Containment & Live-Test Isolation:**
   - *Option A:* Rely on prompts or ad-hoc path checks per tool.
   - *Option B (Chosen):* Centralize resolved-path containment (`core/sandbox.py`) blocking traversals, symlinks, and protected files, and deselect `@pytest.mark.live` by default (`pyproject.toml`).

## Decision
- Standardize on `uv` (`0.13.10`) + Python `3.13.18` + `Ollama.app` (`0.40.18`, optional LM Studio `:1234`), with model pulls deferred until needed and documented in `models.toml` + `models.md`.
- Enforce a `46.0 GB` safe wired-GPU ceiling and `3`-slot co-residency check (`workhorse + fast + embed = 29.0 GB`) in `src/harness_lab/config.py`, plus a double-gated `oracle` cloud guard (`enabled=false`, `is_cloud=true`, `allow_cloud=True`).
- Implement `WireTapTransport` (`src/harness_lab/core/wire_tap.py`) and `JsonlTraceWriter` (`core/tracer.py`) with a `512 KB` log-capture cap, zero-buffering SSE teeing, TTFT/total timing, and case-insensitive header redaction (`Authorization`, `X-API-Key`, `API-Key`, `Proxy-Authorization`, `Cookie`, `Set-Cookie`) to gitignored `traces/*.jsonl`.
- Implement `lab doctor` (`src/harness_lab/stages/s00_foundations/run.py`) and resolved-path `sandbox_data/` containment (`src/harness_lab/core/sandbox.py`).

## Why
Offline verification and Gate 4 drills confirm every invariant deterministically:
- `uv run pytest -v` passed `31 passed, 1 deselected in 0.15s` (zero `pydantic_ai` imports, zero `eval()`/`exec()`/`shell=True`, gated SSE chunk arrival before stream end, symlink/traversal blocks, secret-header redaction).
- `uv run ruff check .` reported `All checks passed!`.
- `uv run lab profiles` verified `workhorse + fast + embed = 29.0 GB / 46.0 GB (OK)`, while break-it `uv run lab profiles --coresident workhorse,alt-family,fast` caught `47.5 GB / 46.0 GB (OVER BUDGET)`.
- `uv run lab doctor --xray` wrote `traces/doctor-20261125T154900Z.jsonl` with `"authorization":"[REDACTED]"` and clean error telemetry while `traces/` stayed untracked in git.
- Live terminal `uv run lab doctor --xray` verified `Ollama 0.40.18` (`REACHABLE`, `/v1` `ok`, 0.4–11.3 ms across `/api/version`, `/api/tags`, `/api/ps`, `/v1/models`), writing `traces/doctor-20261125T155906Z.jsonl` with `"authorization":"[REDACTED]"` on the live HTTP 200 `/v1/models` call.

## Consequences
- **Easier later:** Stage 1–6 Track A and Track B calls share one wire-tap client (`create_wire_tap_client`), enabling exact wire diffs and `--xray` panels; `sandbox.py` prevents duplicated path checks across Stage 3–6 tools.
- **Tradeoffs / Watch-outs:** Live Ollama/LM Studio telemetry requires launching `Ollama.app` (and pulling models when ready) and running `uv run lab doctor --xray` or `uv run pytest -m live` outside zero-network sandboxes.
