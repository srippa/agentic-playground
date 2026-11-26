# 002: Model Config, Thinking Separation & Wire Comparator
Date: 2026-11-26 · Stage: 1 · Status: accepted

## Context
Stage 1 compares raw OpenAI-compatible HTTP/SSE calls (Track A) against PydanticAI v2's `OpenAIChatModel` + `ModelRequest`/`ModelResponse` abstraction (Track B) on 64 GB Apple Silicon while local Ollama model pulls remain deferred. We needed to capture real wire payloads, SSE framing, prompt-cache/reasoning token accounting, and multi-turn `<think>` history behavior side-by-side without hiding framework mechanics.

## Options
1. **PydanticAI Dependency Footprint:**
   - *Option A:* `pydantic-ai-slim[openai]` only (minimal lockfile).
   - *Option B (Chosen):* Full `pydantic-ai` (`2.75.0`) meta-package so OpenAI, Anthropic, Google, MCP, and Evals SDKs are ready out of the box (including OpenCode Zen cross-protocol testing), while AST tests enforce zero `pydantic_ai` imports in Track A modules.
2. **Thinking / Reasoning Separation Across Turns:**
   - *Option A:* Leave `<think>...</think>` inside assistant message content everywhere.
   - *Option B (Chosen):* Normalize both inline `<think>...</think>` (including truncated `max_tokens` cutoffs) and native `reasoning`/`reasoning_content` fields into typed parts, while keeping Track A's Turn 2 history stripped of prior thinking and exposing Track B's default `openai_chat_send_back_thinking_parts='auto'` behavior in `--xray` wire diffs.
3. **Streaming Deltas & Token Usage Parity:**
   - *Option A:* Minimal 3-field `TokenUsage` and default PydanticAI `stream_text(delta=True)` (`debounce_by=0.1` s).
   - *Option B (Chosen):* Track `cached_tokens` / `cache_write_tokens` / `reasoning_tokens` in Track A `TokenUsage` (matching `RunUsage`) and pass `debounce_by=None` in Track B streaming so token deltas arrive unbuffered.

## Decision
- Implemented Track A raw client (`src/harness_lab/stages/s01_raw_vs_pydantic/track_a_raw.py`) with stdlib + `httpx` + Stage 0 `WireTapTransport`, SSE line accumulator, `extract_thinking()`, and cache/reasoning usage parsing.
- Installed `pydantic-ai==2.75.0` and implemented Track B adapter (`track_b_pydantic.py`) with `OllamaProvider`/`OpenAIProvider`, `debounce_by=None`, and `ModelMessage` anatomy summaries.
- Built `run.py` + lazy `lab stage 1` CLI dispatch (`cli.py`) with `--xray`, `--stream`, `--temperature`, `--reasoning-effort`, and a history-aware `--offline` mock transport for deferred model pulls.

## Why
Gate 4 offline verification and drills confirm the design end-to-end:
- `uv run pytest && uv run ruff check` passed `53 passed, 1 deselected in 0.55s` with zero lint errors, enforcing Track A isolation across `config.py`, `cli.py`, `core/`, `s00_foundations/`, and `track_a_raw.py`.
- `uv run lab stage 1 --offline --stream --xray --profile fast` captured 5 SSE frames, `Turn 1` `40 in / 16 out`, `Turn 2 Stateless` forgetting `4291` (`38 in / 27 out`), and `Turn 2 Stateful` recalling `4291` (`67 in (cached 53) / 20 out` on Track A vs. `92 in` on Track B because PydanticAI re-sent Turn 1's `ThinkingPart` on the wire).
- `uv run lab stage 1 --offline --profile bonsai-2.5 --temperature 0.7 --reasoning-effort high` confirmed `Turn 1` `IDENTICAL messages[]` (`temperature` and `reasoning_effort` matched), `Turn 2` `messages[] DIFFER` on thinking re-serialization, and `traces/s01-20261126T161250Z.jsonl` (`6` events) logged `"authorization": "[REDACTED]"`.

## Consequences
- **Easier later:** Stage 2 (`Agent.iter()` vs. manual ReAct loop) inherits both adapters, `WirePayloadDiff`, and `debounce_by=None` streaming; `cached_tokens` parity prepares Stage 5 KV-cache compaction metrics.
- **Tradeoffs / Watch-outs:** `OllamaProvider`/`OpenAIProvider` emit `PydanticAIDeprecationWarning` for `httpx.AsyncClient` vs. `httpx2.AsyncClient` (targeted for PydanticAI v3); `OllamaProvider` parses `<think>` tags in `stream=False` but expects `delta.reasoning` in `stream=True`; live local-model `--xray` verification runs once models are pulled.
