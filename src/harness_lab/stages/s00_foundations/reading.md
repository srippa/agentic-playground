# Stage 0 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **Local Model Serving & Native vs. OpenAI-Compatible APIs**
   - Ollama Docs: [https://docs.ollama.com](https://docs.ollama.com)
   - Ollama Native API Spec: [https://github.com/ollama/ollama/blob/main/docs/api.md](https://github.com/ollama/ollama/blob/main/docs/api.md)
   - Ollama OpenAI Compatibility API: [https://github.com/ollama/ollama/blob/main/docs/openai.md](https://github.com/ollama/ollama/blob/main/docs/openai.md)
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

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
