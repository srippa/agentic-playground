# Stage 5 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **Context Engineering & Compaction**
   - Anthropic — *Effective Context Engineering for AI Agents*: [https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
   - Manus — *Context Engineering for AI Agents: Lessons from Building Manus*: [https://manus.im/blog/context-engineering-for-ai-agents-lessons-from-building-manus](https://manus.im/blog/context-engineering-for-ai-agents-lessons-from-building-manus)
2. **Hybrid Retrieval (`FTS5` + Vectors + `RRF`)**
   - SQLite FTS5 Documentation: [https://www.sqlite.org/fts5.html](https://www.sqlite.org/fts5.html)
   - Cormack, Clarke & Buettcher — *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*: [https://dl.acm.org/doi/10.1145/1571941.1572114](https://dl.acm.org/doi/10.1145/1571941.1572114)
3. **Long-Term Agent Memory Architectures & Courses**
   - MemGPT — *Towards LLMs as Operating Systems*: [https://arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)
   - *Generative Agents* (Episodic Memory, Reflection, Retrieval): [https://arxiv.org/abs/2309.02427](https://arxiv.org/abs/2309.02427)
   - Letta Memory Architecture Docs: [https://docs.letta.com/configuration/memory](https://docs.letta.com/configuration/memory)
   - LangMem Conceptual Guide: [https://langchain-ai.github.io/langmem/](https://langchain-ai.github.io/langmem/)
   - DeepLearning.AI — *LLMs as Operating Systems: Agent Memory*: [https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory)
   - DeepLearning.AI — *Agent Memory: Building Memory-Aware Agents*: [https://learn.deeplearning.ai/courses/agent-memory-building-memory-aware-agents](https://learn.deeplearning.ai/courses/agent-memory-building-memory-aware-agents)
4. **Optional Stretch Reading (Production & Temporal Graph Memory)**
   - Mem0 Docs: [https://docs.mem0.ai](https://docs.mem0.ai)
   - Mem0 Paper (Production Long-Term Memory): [https://arxiv.org/abs/2504.19413](https://arxiv.org/abs/2504.19413)
   - Zep / Graphiti (Temporal Knowledge Graphs): [https://github.com/getzep/graphiti](https://github.com/getzep/graphiti)
   - `sqlite-vec` (Native SQLite Vector Extension): [https://github.com/asg017/sqlite-vec](https://github.com/asg017/sqlite-vec)

---

## Guided Focus Questions

1. **KV-Cache Prefix Stability (Manus Lesson):** Why does mutating early system prompt timestamps or dynamically shuffling tools destroy prompt-cache hits, and how should episodic memory be injected instead?
2. **Orphaned Tool-Call Corruption:** What happens on `/v1/chat/completions` when naive sliding-window compaction drops an `assistant` `tool_calls` message while leaving its `role="tool"` reply (or vice versa)?
3. **Why Hybrid FTS5 + Vector Beats Either Alone:** Give a concrete example of an exact ID/code query where embeddings fail and a paraphrased semantic query where BM25/FTS5 misses — and why `RRF` avoids fragile raw-score normalization.
4. **Working vs. Episodic vs. Semantic Memory:** In PydanticAI `history_processors`, what belongs in compacted conversation state vs. persisted in SQLite long-term memory?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
