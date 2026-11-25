# Stage 6 — Installations & Setup (`Gate 2`)

> **Rule (Hard Stop):** Review this plan and the official installation docs, ask questions, record conclusions below, and **wait for explicit user approval** before executing any install or `ollama pull` command.

---

## What Will Be Installed & Why

1. **`prompt-toolkit`:** Builds our interactive Stage 6 glass-box REPL (`lab repl`) with multi-line input, history, and status bars without conflicting with streamed `--xray` output.
2. **Optional `mlx-lm` (Apple Silicon):** Native MLX inference/benchmarking option for comparing MLX vs. GGUF/Ollama quantizations directly on 64 GB Apple Silicon.
3. **Optional `pydantic-ai-slim[logfire]` / `typesafe-sdk`:** Adds OpenTelemetry/Logfire span export (can target a local collector / Phoenix instance instead of cloud) and optional routing helpers if decided during Q&A.
4. **Optional Model Arena & Gatekeeper Candidate Pulls:** e.g., `inkling-2-mini`, `Qwen3.8-27B` quantization sweep tags, or `bonsai-2.5` — pulled only after verifying disk & 64 GB co-residency budgets per `.agents/skills/local-runtime-guard/SKILL.md`.

---

## Official Installation Docs

- `prompt-toolkit`: [https://github.com/prompt-toolkit/python-prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)
- Apple `mlx-lm`: [https://github.com/ml-explore/mlx-lm](https://github.com/ml-explore/mlx-lm)
- PydanticAI Evals & Logfire: [https://ai.pydantic.dev/evals/](https://ai.pydantic.dev/evals/) & [https://ai.pydantic.dev/logfire/](https://ai.pydantic.dev/logfire/)
- Arize Phoenix (Local OTel Tracing UI): [https://docs.arize.com/phoenix](https://docs.arize.com/phoenix)

---

## Proposed Commands (Pending Approval)

*(Do NOT execute until `Status: approved` below.)*

```zsh
# 1. Required for interactive Stage 6 REPL
uv add prompt-toolkit

# 2. Optional observability / MLX / routing extras (decide in Q&A)
# uv add "pydantic-ai-slim[logfire]"
# uv add mlx-lm
# uv add typesafe-sdk

# 3. Optional local arena / quant-sweep model pulls (confirm exact tags & 64 GB budget in Q&A)
# ollama pull <approved-candidate-tag>
```

---

## Q&A & Discussion Log

- **Q1:**
- **A1:**

---

## Decisions & Approval

- **Status:** `pending`
- **Install `mlx-lm` / `logfire` extra / `typesafe-sdk`?:** *(TBD in Q&A)*
- **Candidate Arena / Quant Model Tags Approved:** *(TBD in Q&A)*
- **User Explicit Approval:** *(waiting for user go-ahead)*

---

## Verification Output

*(Append `uv add` outputs, verified imports, and `ollama list` / `mlx-lm` check outputs after approved execution.)*
