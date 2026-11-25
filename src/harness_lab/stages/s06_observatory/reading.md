# Stage 6 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **Agent Evaluation & Error Analysis**
   - Anthropic — *Demystifying Evals for AI Agents*: [https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
   - Hamel Husain — *Your AI Product Needs Evals*: [https://hamel.dev/blog/posts/evals/](https://hamel.dev/blog/posts/evals/)
   - DeepLearning.AI — *Evaluating AI Agents*: [https://learn.deeplearning.ai/courses/evaluating-ai-agents](https://learn.deeplearning.ai/courses/evaluating-ai-agents)
   - PydanticAI Evals: [https://ai.pydantic.dev/evals/](https://ai.pydantic.dev/evals/)
2. **Observability & OpenTelemetry Standards**
   - OpenTelemetry GenAI Semantic Conventions: [https://github.com/open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai)
   - PydanticAI + Logfire Integration: [https://ai.pydantic.dev/logfire/](https://ai.pydantic.dev/logfire/)
   - Arize Phoenix Docs: [https://docs.arize.com/phoenix](https://docs.arize.com/phoenix)
3. **Model Selection, Benchmarks & Local Open Weights**
   - Qwen3.8 Repository: [https://github.com/QwenLM/Qwen3.8](https://github.com/QwenLM/Qwen3.8)
   - Inkling 2 Mini Release Blog: [https://huggingface.co/blog/inkling2mini](https://huggingface.co/blog/inkling2mini)
   - Artificial Analysis Benchmarks: [https://artificialanalysis.ai](https://artificialanalysis.ai)
   - Chatbot Arena / LMArena: [https://lmarena.ai](https://lmarena.ai)

---

## Guided Focus Questions

1. **Outcome vs. Trajectory Grading:** Why do pure final-answer string matches fail for agentic harnesses, and how do trajectory checks (right tool sequence, HITL respected, no leaked secrets) catch regressions hidden by lucky final answers?
2. **Public Leaderboards vs. Application Gatekeepers (`lab gate`):** Why can a model score high on public leaderboards yet fail our local harness (e.g., broken strict JSON schemas, runaway tool loops, or `<think>` budget exhaustion) — and what small, targeted slice predicts real capstone usefulness?
3. **`HarnessBudget` & Multi-Model Routing (`Jev`):** When multiple local models share 64 GB unified memory, how do swap latency, context window pressure, and router accuracy trade off against single-model execution?
4. **Traceability Under Multi-Agent Handoffs:** In the Trip-Planner capstone, what OpenTelemetry attributes (`gen_ai.*`, agent role, parent trace ID) are needed so one `--xray` trace tells the full multi-agent story?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
