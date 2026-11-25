# Stage 2 — Pre-Reading & Concept Discussion (`Gate 1`)

> **Rule (Hard Stop):** Read and discuss these materials **before** approving installations (`Gate 2`) or writing code (`Gate 3`).

---

## Curated Reading Materials

1. **Agent Loops & ReAct Fundamentals**
   - Anthropic — *Building Effective Agents*: [https://www.anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents)
   - Amp Code — *How to Build an Agent*: [https://ampcode.com/how-to-build-an-agent](https://ampcode.com/how-to-build-an-agent)
   - Real Python — *Agentic Loop*: [https://realpython.com/agentic-loop/](https://realpython.com/agentic-loop/)
   - Yao et al. — *ReAct: Synergizing Reasoning and Acting in Language Models*: [https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
2. **PydanticAI Execution Graph, Structured Output & Capabilities**
   - PydanticAI Agents & Execution (`Agent.iter()`): [https://ai.pydantic.dev/agents/](https://ai.pydantic.dev/agents/)
   - PydanticAI Structured Output & Retries: [https://ai.pydantic.dev/output/](https://ai.pydantic.dev/output/)
   - PydanticAI Capabilities (`AbstractCapability`): [https://ai.pydantic.dev/capabilities/](https://ai.pydantic.dev/capabilities/)

---

## Guided Focus Questions

1. **Workflow vs. Agent Loop:** By Anthropic's taxonomy, when should we stay with deterministic code workflows instead of letting a model decide the next action inside a `while` loop?
2. **Self-Correction on Validation Failure:** When a model returns JSON that violates a Pydantic schema, why does feeding back the exact Pydantic validation error string outperform generic "try again" prompts — and where should `output_retries` stop?
3. **Why `Agent.iter()` Beats `agent.run()` in a Glass-Box Lab:** What visibility and control do you gain by manually stepping `UserPromptNode` → `ModelRequestNode` → `CallToolsNode` → `End`?
4. **Cross-Cutting Policies via `AbstractCapability`:** What concerns belong inside an agent's loop vs. cleanly factored into `AbstractCapability` / `Hooks` (e.g., X-Ray tracing, token/step budgets, guardrails)?

---

## Q&A & Discussion Notes

*(Recorded during Gate 1 chat before moving to Gate 2.)*

- **Open Questions:**
- **Key Takeaways:**

---

## Gate 1 Sign-Off

- **Status:** `pending`
- **Approved by User:** *(waiting for user confirmation to open `installation.md`)*
