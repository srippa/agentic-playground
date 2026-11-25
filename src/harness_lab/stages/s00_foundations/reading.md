# Stage 0 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **Local Model Serving & Native vs. OpenAI-Compatible APIs**
   - Ollama Docs: [https://docs.ollama.com](https://docs.ollama.com)
   - Ollama Native API Spec: [https://docs.ollama.com/api](https://docs.ollama.com/api)
   - Ollama OpenAI Compatibility API: [https://docs.ollama.com/api/openai-compatibility](https://docs.ollama.com/api/openai-compatibility)
   - LM Studio Docs: [https://lmstudio.ai/docs](https://lmstudio.ai/docs)
2. **Quantization & 64 GB Unified Memory Fitting**
   - Unsloth Dynamic 2.0 Quantization Blog: [https://unsloth.ai/blog/dynamic-v2-0](https://unsloth.ai/blog/dynamic-v2-0)
   - Workspace Reference: `.agents/skills/local-runtime-guard/SKILL.md`
3. **Wire-Level HTTP Inspection & Terminal UI**
   - HTTPX Transports & Interception: [https://www.python-httpx.org/advanced/transports/](https://www.python-httpx.org/advanced/transports/)
   - Rich Library Docs: [https://rich.readthedocs.io/](https://rich.readthedocs.io/)

---

## Guided Focus Questions

Use these questions in chat with Antigravity to test your mental model before moving to Gate 2:

1. **Native vs. OpenAI-Compat Endpoints:** What fields exist in Ollama's native `/api/chat` (e.g., `options.num_ctx`, `keep_alive`, eval timings) that disappear or require extensions on `/v1/chat/completions`?
2. **KV-Cache & 64 GB Memory Math:** Why does doubling `num_ctx` (e.g., from `8192` to `32768`) blow up unified memory alongside model weights, and how does running concurrent local roles (`workhorse` + `fast` + `embed`) constrain our budget?
3. **Quantization Tradeoffs:** What parts of a transformer network suffer most from naive uniform quantization vs. dynamic quantization, and why might `1-bit` / ultra-low-bit models like `Bonsai 2.5` behave differently from `Q4_K_M`?
4. **Intercepting Without Magic:** Why build our wire tap at the `httpx.AsyncBaseTransport` layer instead of logging high-level Python SDK objects?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:** None blocking Gate 2; `embeddinggemma-2:270m` (`https://gemma.ai/models/embeddinggemma/`) noted in Stage 5 docs (`src/harness_lab/stages/s05_memory_lab/installation.md` and `docs/progress.md`) to revisit at Stage 5 Gate 2.
- **Key Takeaways:**
  1. **Native `/api/*` vs. OpenAI `/v1`:** Native `/api/chat` honors `options.num_ctx`, `keep_alive`, and returns nanosecond timings (`load_duration`, `prompt_eval_duration`, `eval_duration`), while `/api/ps` and `/api/show` provide runtime introspection. `/v1/chat/completions` gives portability (PydanticAI Track B, LM Studio) but silently ignores request-body `num_ctx`. Both interfaces can coexist in a session as long as `num_ctx` is pinned identically (avoiding runner reloads) and per-conversation history stays on one schema. Local Ollama/LM Studio require no real API key (only a dummy placeholder like `"ollama"` for OpenAI SDKs); `OLLAMA_API_KEY` is only for hosted Ollama Cloud.
  2. **Ollama + LM Studio Coexistence:** Run cleanly on separate ports (`:11434` vs. `:1234`) and complement each other (Ollama for CLI/co-residency/native introspection; LM Studio for MLX and Hugging Face Dynamic quants). They store weights separately and do not share RAM, so never load the same large model in both simultaneously on 64 GB unified memory.
  3. **`num_ctx`, KV-Cache & Context Rot:** `num_ctx` pre-allocates KV-cache memory (scaling with `num_ctx × OLLAMA_NUM_PARALLEL`), so pin `OLLAMA_NUM_PARALLEL=1` and enable Flash Attention + `Q8_0` KV cache. More importantly, giant context windows trigger *context rot* and *lost-in-the-middle* degradation plus Apple Silicon memory-bandwidth slowdowns—treat `num_ctx` (`16K`–`32K`) as a hard safety ceiling while actively managing a smaller working context via tool offloading (Stage 3), MCP state (Stage 4), and compaction + hybrid memory (Stage 5).
  4. **Quantization as an Empirical Dimension:** Uniform 4-bit (`Q4_K_M`) recovers most chat accuracy, but agentic loops compound small logit-margin drops in strict JSON/tool-calling. On 64 GB, we will benchmark `Q4_K_M` vs. Dynamic 2.0 / `Q6_K` / `Q8_0` vs. ultra-low-bit (`Bonsai 2.5`) empirically in Stage 6 (`lab gate` / `lab bench`).
  5. **Wire-Tapping at `httpx.AsyncBaseTransport`:** Captures exact raw HTTP traffic across both Track A and Track B (no SDK magic), centralizes header redaction (`Authorization` / `x-api-key`), enables fast offline `httpx.MockTransport` tests, and requires teeing `AsyncByteStream` so streaming SSE responses stay live.

---

## Gate 1 Sign-Off

- **Status:** `approved`
- **Approved by User:** Confirmed ready to review Gate 2 (2026-11-25)
