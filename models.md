# Live Model Roster & Rationale (`models.md`)

> **Living Companion to [`models.toml`](./models.toml)**  
> **Hardware Target:** Apple Silicon MacBook Pro (**64 GB Unified Memory** | `46.0 GB` safe wired-GPU ceiling | `3` max hot co-resident models)  
> **Default Co-Resident Stack:** `workhorse` (`22.0 GB`) + `fast` (`6.5 GB`) + `embed` (`0.5 GB`) = **`29.0 GB`** (`+17.0 GB` headroom)  
> **Last Updated:** 2026-11-25 *(all local model pulls intentionally deferred until needed)*

This document explains **what each profile in `models.toml` does**, **why the chosen model fits our 64 GB Apple Silicon hardware**, and **which leading alternatives exist**. As models are pulled, tested with `lab doctor`, gated via `lab gate`, and compared in `lab bench`, update this log alongside `models.toml`.

---

## Quick-Reference Roster

| Profile | Current Tag (`models.toml`) | Provider / Port | `num_ctx` | Est. RAM | Primary Stage(s) | Status |
| :--- | :--- | :--- | ---: | ---: | :--- | :--- |
| **`workhorse`** *(default)* | `qwen3.8:27b` | Ollama (`:11434`) | `32,768` | `22.0 GB` | Stages 1–6 (baseline) | Deferred (not pulled) |
| **`bonsai-2.5`** | `prism-ml/Ternary-Bonsai-2.5-27B-mlx-2bit` | LM Studio / MLX (`:1234`) | `32,768` | `6.5 GB` | Stage 5–6 (quant sweep / `fast` candidate) | Deferred (not pulled) |
| **`alt-family`** | `inkling-2-mini` | Ollama (`:11434`) | `32,768` | `19.0 GB` | Stage 1, Stage 6 Arena | Deferred (not pulled) |
| **`fast`** | `qwen3.5:9b` | Ollama (`:11434`) | `16,384` | `6.5 GB` | Stage 5 compaction/extraction, Stage 6 | Deferred (not pulled) |
| **`chaos`** | `qwen3:4b` | Ollama (`:11434`) | `16,384` | `3.5 GB` | Stages 2–4 break-it drills | Deferred (not pulled) |
| **`decision`** | `tinyjev` *(placeholder; see `tev1` below)* | Ollama (`:11434`) | `8,192` | `2.5 GB` | Stage 6 System-1 routing & risk gating | Deferred (not pulled) |
| **`embed`** | `embeddinggemma-2:270m` | Ollama (`:11434` native) | `8,192` | `0.5 GB` | Stage 5 hybrid memory (`FTS5 + RRF`) | Deferred (Stage 5 Gate 2) |
| **`oracle`** | `gpt-5` | Cloud (`openai_compat`) | `32,768` | `0.0 GB` | Stage 6 ceiling check *(opt-in only)* | **Disabled by default** |

---

## Per-Profile Justifications & Alternatives

### 1. `workhorse` — `qwen3.8:27b`
- **What It Will Be Used For:** Primary dense agentic baseline across Stages 1–6—multi-step tool loops, strict JSON structured output, reasoning/thinking-token control (`reasoning_effort` / `Thinking`), MCP tool use, and the Trip-Planner capstone.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - 27B dense hybrid-attention architecture (with native vision/multimodal capability) tuned specifically for long-horizon coding, research, and multi-turn tool calling.
  - At `Q4_K_M` + `32K` KV cache (`~22 GB`), it leaves plenty of headroom inside our `46.0 GB` wired-GPU ceiling to stay co-resident alongside `fast` + `embed` (`29.0 GB` total) *or* side-by-side with `alt-family` (`~41 GB`) for head-to-head comparisons.
  - Same base architecture as `bonsai-2.5` (`Qwen3.8-27B`), giving us an exact apples-to-apples quantization ladder (`1.76 bpw` QAT vs. `Q4_K_M` vs. Dynamic vs. `Q6_K`/`Q8_0`).
- **Leading Alternatives:**
  - **`gemma4:31b` (Dense, Apache 2.0):** Top non-Qwen dense reasoning alternative (~18–22 GB 4-bit); great for testing prompt/tool-schema portability across vendors.
  - **`gemma4:26b-a4b` (MoE, Apache 2.0):** ~26B total / ~4B active parameters; noticeably faster decode tok/s than a 27B dense model while fitting the same memory footprint.
  - **`unsloth/Qwen3.8-27B-GGUF` (Dynamic 2.0 via LM Studio / `hf.co/unsloth/...`):** Preserves higher bit-width on sensitive attention/router/output layers, reducing malformed JSON and tool-argument slips compared to uniform `Q4_K_M`.
- **Watch-Outs:** Native context is 262K, which would blow up KV-cache RAM if left uncapped; pin `32,768` via `OLLAMA_CONTEXT_LENGTH` / derived Modelfile (since Ollama `/v1/chat/completions` ignores request-body `num_ctx`). Needs Ollama `v0.33.0+` (ours is `0.40.18`).

---

### 2. `bonsai-2.5` — `prism-ml/Ternary-Bonsai-2.5-27B-mlx-2bit`
- **What It Will Be Used For:** Same-base ultra-low-bit quantization anchor in Stage 6 (`lab bench`), and primary candidate to promote into the **`fast`** role (Stage 5 compaction / extraction / fast sub-agent) if it passes `lab gate`.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - PrismML compresses `Qwen3.8-27B` via **1.76 bpw ternary quantization-aware training (QAT)**—weights restricted to `{-1, 0, +1}` with blockwise Hadamard FP16 scales—followed by agentic post-training (~75.6% SWE-bench Verified).
  - Weighs only **~5.9 GB** (~6.5 GB with KV cache)—roughly the RAM of an 8B model while retaining 27B-class tool-calling competence, and decodes much faster on Apple Silicon MLX because memory bandwidth is the primary bottleneck.
- **Leading Alternatives:**
  - **PrismML `llama.cpp` GGUF (`Q2_0` / `PTQ1_0` fork):** Lets you run `Bonsai 2.5` in pure GGUF/`llama-server` without MLX.
  - **Unsloth Dynamic 2-bit / 3-bit GGUF (`UD-Q2_K_XL` / `UD-Q3_K_XL`):** Post-training dynamic quants of `Qwen3.8-27B` for comparing QAT ternary vs. PTQ dynamic compression.
  - **`qwen3.5:9b` (`fast` baseline):** Conventional 4-bit 9B dense model if `Bonsai 2.5` shows edge-case JSON schema fragility under `lab gate`.
- **Watch-Outs:** Ultra-low-bit kernels often land in Apple MLX / LM Studio / upstream `llama.cpp` before stock Ollama; hence configured on LM Studio (`:1234`) by default. Must prove strict JSON (`L1`) and injection resistance (`L4`) in `lab gate` before replacing `fast`.

---

### 3. `alt-family` — `inkling-2-mini`
- **What It Will Be Used For:** Cross-architecture shootout in Stage 1 (chat-template & thinking inspection) and Stage 6 Arena (`lab compare` / `lab bench`) to avoid overfitting our harness to Qwen-family quirks.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - **Thinking Machines Lab** Looped Mixture-of-Experts (`26.4B` total parameters, `~3.4B` active per pass, `24` physical layers where the middle 12 layers loop 3× for `48` effective layer passes).
  - Checkpoint size (~16–20 GB, `19.0 GB` budget here) means it can either run standalone at `Q8_0` (~28 GB) or sit **co-resident alongside `workhorse` `Q4`** (`22 + 19 = 41 GB <= 46 GB`) for instant side-by-side comparisons with zero cold reloads.
- **Leading Alternatives:**
  - **`gemma4:26b-a4b`:** Standard non-looped Apache 2.0 MoE (~26B total / ~4B active) with broad Ollama/LM Studio support and linear KV-cache scaling.
  - **`gemma4:31b`:** Strong dense alternative family if we want dense-vs-dense comparison (`Qwen3.8-27B` vs. `Gemma-4-31B`).
  - **`gpt-oss:20b`:** Open-weights Harmony-format reasoning/tool baseline for testing non-Qwen/non-Gemma tool templates.
- **Watch-Outs:** Requires `inkling2_loop` support (Ollama `0.40.18` satisfies the `v0.33.0+` floor). Because each of the 3 middle loop passes maintains its own KV/conv state, KV cache grows faster with `num_ctx` than a standard 24-layer model—keep `num_ctx` at `32K–64K` when co-residing.

---

### 4. `fast` — `qwen3.5:9b`
- **What It Will Be Used For:** High-throughput helper role—Stage 5 short-term compaction summarization, post-turn memory extraction, fast iteration during harness debugging, and low-latency sub-tasks in Stage 6.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - Hybrid linear-attention + full-attention architecture gives fast generation and low KV growth.
  - At `~6.5 GB` (`16K` ctx), it stays permanently hot in Ollama (`OLLAMA_MAX_LOADED_MODELS=3`) alongside `workhorse` (`22 GB`) and `embed` (`0.5 GB`) with zero eviction thrashing.
- **Leading Alternatives:**
  - **`bonsai-2.5` (`Ternary-Bonsai-2.5-27B`):** Same ~6.5 GB RAM slot, potentially stronger reasoning/tool fidelity if promoted by `lab gate`.
  - **`qwen3:8b`:** Mature, rock-solid fallback tag in Ollama if `qwen3.5:9b` has any template quirks.
  - **`gemma4` small / edge variants (e.g., `e4b`):** Compact Apache 2.0 alternative for lightweight summarization/extraction.
- **Watch-Outs:** Smaller 8B–9B models are more prone to subtle fact drift during Stage 5 lossy compaction—keep compaction prompts tightly schema-constrained and verify with Stage 5 recall tests.

---

### 5. `chaos` — `qwen3:4b`
- **What It Will Be Used For:** **Intentional stress-test & break-it baseline** (Stages 2–4)—reliably provoking malformed JSON, invalid tool arguments, `ModelRetry` backoffs, doom-loop detector trips, and HITL/sandbox guardrail blocks.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - Small (~3.5 GB) and fast, so break-it drills fail and recover in seconds instead of waiting minutes for a 27B model to make a mistake.
  - Uses the same tool-calling conventions as `workhorse` so failures reflect capability limits (lost constraints, argument hallucinations) rather than a broken template.
- **Leading Alternatives:**
  - **`qwen3.5:4b`:** Newer 4B generation with faster hybrid attention.
  - **`llama3.2:3b`:** Classic small Llama baseline—even noisier on strict multi-tool schemas.
  - **Aggressive `Q2_K` quant of a larger model:** Useful specifically to demonstrate *quantization-induced* schema collapse.
- **Watch-Outs:** Never evaluate harness capability using `chaos` pass rates; its job is to prove your guardrails catch bad model behavior cleanly.

---

### 6. `decision` — `tinyjev` *(Placeholder; `tev1` Recommended Concrete Tag)*
- **What It Will Be Used For:** **System-1 fast routing, risk/prompt-injection gating, and budget-aware step-down** in Stage 6 (`core/router.py`, `uv run lab bench --budget-test`). Evaluates state + bounded typed choices without burning long reasoning prose.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - **Note on the tag:** `tinyjev` in `models.toml` is a placeholder descriptor for sub-1B/small local decision models.
  - **Recommended concrete local tag when we reach Stage 6:** Together AI's **`tev1`** (`ollama pull tev1` — `Tev1-0.8B` at ~0.8 GB or `Tev1-4B` built on Qwen3.5), which is SFT-tuned specifically for Jev-style bounded decision schemas (`State + Question + 2..24 options -> option/score`) natively in Ollama.
  - Fits inside ~1–3 GB RAM, running fast alongside `workhorse` without blowing our 64 GB budget.
- **Leading Alternatives:**
  - **`tev1:0.8b` / `tev1:4b` (`ollama pull tev1`):** Concrete open-weight local Jev-inspired decision models (drop-in upgrade over the `tinyjev` placeholder when we pull in Stage 6).
  - **Hosted TypeSafe AI `Jev` (`typesafe-sdk`):** Proprietary System-1 API (~70–500 ms latency, 64K ctx, Choice/Score/Noul/Box primitives, ~$0.042/1M input tokens, 0 output tokens)—requires explicit user opt-in (`is_cloud`).
  - **Constrained `fast` (`qwen3.5:9b` with `temperature=0.0` + enum `format` schema):** Zero extra model slot needed if already co-resident.
- **Watch-Outs:** Keep decision prompts strictly bounded (enum choices/scores) and verify `tev1` tag availability on Ollama when opening Stage 6 Gate 2.

---

### 7. `embed` — `embeddinggemma-2:270m`
- **What It Will Be Used For:** Stage 5 dense semantic memory retrieval (`SQLite FTS5 + dense cosine similarity + RRF`), plus Stage 6 Trip-Planner long-term user preferences and past trip notes.
- **Why It's a Good Fit (64 GB Apple Silicon):**
  - Google DeepMind **EmbeddingGemma 2** text/code backbone: only **~300–380 MB** (`0.5 GB` budgeted with overhead)—effectively free in our 3-model co-residency stack (`workhorse + fast + embed`).
  - **8,192-token context window** (4× v1's 2,048), cleanly embedding long compacted summaries or code blocks without chunk truncation.
  - **Matryoshka Representation Learning (MRL):** Outputs unified `768d` vectors that truncate cleanly to `512d`, `256d`, or `128d` without re-training—pairing cleanly with our Stage 5 SQLite `embedding_model` + `embedding_dim` provenance check.
- **Leading Alternatives:**
  - **`embeddinggemma-2:740m`:** Full multimodal sibling (~1.3 GB) projecting text, code, images, and audio into the exact same `768d` space.
  - **`qwen3-embedding`:** Strong multilingual/code embedding model in the Qwen ecosystem.
  - **`nomic-embed-text` / `mxbai-embed-large`:** Proven lightweight Ollama text-embedding baselines.
- **Watch-Outs:** Never mix vectors across models or Matryoshka dimensions (`768d` vs. `256d`) in the same SQLite table—Stage 5's store enforces `embedding_model` + `embedding_dim` matching. Uses native Ollama `/api/embed` (`api_style = "ollama_native"`).

---

### 8. `oracle` — `gpt-5` *(Disabled by Default)*
- **What It Will Be Used For:** Optional frontier cloud ceiling check in Stage 6 (`lab bench` / diagnostics)—answering *"is this failure a harness bug or a local 27B quantization limit?"*
- **Why It's a Good Fit:** Zero local RAM (`0.0 GB`), frontier tool-calling and reasoning accuracy, and **double-gated** (`enabled = false` + `is_cloud = true` + `allow_cloud=True` in code) so the lab never incurs silent cloud spend.
- **Leading Alternatives:**
  - **Anthropic Claude (Sonnet / Opus)** — top-tier coding/agentic tool discipline.
  - **Google Gemini (Pro)** — strong long-context & multimodal ceiling.
  - **OpenAI (`gpt-5` / `o3`)** — strong strict JSON schema adherence.
- **Watch-Outs:** Requires explicit user approval, `enabled = true` in a local override/TOML, `allow_cloud=True`, and a key in `.env` (never committed, always redacted by `wire_tap.py`).

---

## Live Change & Evaluation Log

| Date | Profile | Action / Event | Notes / Evidence |
| :--- | :--- | :--- | :--- |
| 2026-11-25 | All (`models.toml`) | Initial 64 GB baseline roster defined | Part 0.1 offline validation passed (`29.0 GB` default co-resident stack; pulls deferred). `embeddinggemma-2:270m` selected for Stage 5 `embed`; `tev1` noted as concrete Ollama upgrade for `tinyjev` `decision` placeholder. |
