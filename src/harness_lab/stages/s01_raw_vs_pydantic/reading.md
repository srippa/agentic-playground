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

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
