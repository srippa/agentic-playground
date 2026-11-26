# Stage 1 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **LLM Foundations & Chat Templating**
   - Andrej Karpathy — *Deep Dive into LLMs like ChatGPT* (YouTube)
   - Hugging Face Chat Templating Docs: [https://huggingface.co/docs/transformers/chat_templating](https://huggingface.co/docs/transformers/chat_templating)
2. **Wire Protocol & Streaming Mechanics**
   - OpenAI Chat Completions API Reference: [https://platform.openai.com/docs/api-reference/chat](https://platform.openai.com/docs/api-reference/chat)
   - MDN Server-Sent Events (SSE): [https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
3. **PydanticAI Track B Abstractions**
   - PydanticAI Models Overview: [https://ai.pydantic.dev/models/](https://ai.pydantic.dev/models/)
   - PydanticAI Message History: [https://ai.pydantic.dev/message-history/](https://ai.pydantic.dev/message-history/)

---

## Guided Focus Questions

1. **Chat Templates as Hidden Prompts:** Why is an HTTP `messages: [...]` array not what the transformer actually reads, and how can template mismatches silently corrupt tool calls or reasoning?
2. **SSE Streaming Wire Format:** How do `data: {...}\n\n` frames and `data: [DONE]` work over a single HTTP response, and why does `usage` often arrive only in the final chunk (or require `stream_options`)?
3. **Thinking vs. Answer Separation:** How does separating `<think>` / reasoning fields from user-facing `TextPart` content prevent context bloat or accidental reasoning leakage across turns?
4. **Track A vs. Track B Mapping:** Which PydanticAI types (`ModelRequest`, `SystemPromptPart`, `UserPromptPart`, `ModelResponse`, `ThinkingPart`, `TextPart`) map 1-to-1 to raw Chat Completions JSON?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:** None blocking Gate 2.
- **Key Takeaways:**
  1. **3-Layer Boundary (Chat Templating vs. Wire JSON vs. PydanticAI):** Chat templating (Hugging Face `chat_templating` / Ollama `Modelfile` `TEMPLATE`) happens server/tokenizer-side (Layer 3), converting `messages[]` into a flat string with model-specific special tokens. PydanticAI operates client-side above HTTP (Layer 1), mapping vendor-neutral `ModelMessage` objects (`ModelRequest`/`ModelResponse` + parts) to provider JSON and handling model-family quirks via `ModelProfile` (`thinking_tags`, `openai_chat_thinking_field`, structured output modes).
  2. **How PydanticAI Sends a Chat Turn:** `agent.run(...)` builds a `ModelRequest` (`instructions` / `SystemPromptPart`, `UserPromptPart`, plus `message_history`) → `OpenAIChatModel` translates parts to `/v1/chat/completions` JSON → `OpenAIProvider` / `AsyncOpenAI` sends HTTP `POST` via `httpx.AsyncClient` (where Stage 0 `wire_tap` hooks in) → inference server applies chat template and runs the model → `OpenAIChatModel` parses the response back into `ModelResponse` (`ThinkingPart`, `TextPart`, `ToolCallPart`, `RequestUsage`).
  3. **OpenAI Chat Completions vs. SSE Across Both Tracks:** Chat Completions defines the application-level JSON request/response contract; SSE (`Content-Type: text/event-stream`, `data: {...}\n\n`, `data: [DONE]`) is the wire framing used when `stream=true` (over HTTP `POST`, not browser `EventSource` `GET`). Both Track A and Track B send/receive the exact same wire format—Track A constructs and parses it manually, while Track B delegates parsing to the SDK + `OpenAIChatModel`.
  4. **Multi-Provider vs. OpenAI-Compatible Convergence (incl. OpenCode Zen):** Distinct wire protocols (OpenAI Chat Completions, OpenAI Responses, Anthropic Messages, Gemini) require different adapters; PydanticAI separates `Model` (wire protocol) from `Provider` (base URL + auth), which also explains how gateways like OpenCode Zen route different models across `/chat/completions`, `/responses`, `/messages`, and `/models/<id>`. Track A stays concise in our lab by targeting the OpenAI-compatible `/v1/chat/completions` standard used by local runtimes (Ollama, LM Studio, vLLM), while explicitly surfacing dialect quirks (`<think>` vs. `reasoning` fields, `num_ctx`, streaming `usage`).

---

## Gate 1 Sign-Off

- **Status:** `approved`
- **Approved by User:** Confirmed ready to begin Stage 1 / open Gate 2 (2026-11-26)
