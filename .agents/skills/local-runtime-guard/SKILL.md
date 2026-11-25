---
name: local-runtime-guard
description: >-
  Use this skill when configuring, diagnosing, or benchmarking local Ollama or LM Studio models
  on this 64 GB Apple Silicon machine (including num_ctx, co-residency, quantization sweeps, and Jev routing).
---

# Local Runtime Guard (64 GB Apple Silicon)

Use this runbook before live model runs, Stage 5 memory tests, or Stage 6 benchmarks:

## Steps

1. **Verify Ollama Version & Health:**
   - Confirm `ollama --version` is **v0.33.0+** (for `qwen3.8:27b` tool-call parsing and `inkling2_loop` support) or **v0.35+** if running local Jev-style decision models (`TinyJev` / `Tev1`).
   - Run `uv run lab doctor` (or query `/api/tags` and `/api/ps`) to confirm the daemon is reachable.
2. **Check Real `num_ctx`:**
   - Remember Ollama's `/v1/chat/completions` silently ignores request-body `num_ctx`.
   - Verify active `num_ctx` via `/api/show` and `/api/ps`, configured via `OLLAMA_CONTEXT_LENGTH` or derived Modelfiles (`PARAMETER num_ctx ...`).
   - For `Inkling-2-Mini`, keep `num_ctx` at `32K–64K` on 64 GB because its 3× looped layers grow KV-cache memory faster.
3. **Protect 3-Model Co-Residency & Wired GPU Ceiling:**
   - Ensure `OLLAMA_MAX_LOADED_MODELS=3` and explicit `keep_alive` values in `models.toml` so `workhorse` + `fast` + `embed` (~27–38 GB combined) stay simultaneously hot without cold reloads.
   - Keep total active weights + KV caches under ~42–46 GB (within macOS's default ~48 GB wired GPU limit) to avoid swap.
4. **Zero-Spend Guard:**
   - Ask for explicit user confirmation before `ollama pull`, `ollama rm`, or running paid cloud profiles (`oracle`, hosted `Jev`).
