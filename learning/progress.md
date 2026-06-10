# Statlas — Study Progress

Project: AI-powered sports stats answer engine (a better StatMuse).

## Current status

| Track | Phase | Notes |
|-------|-------|-------|
| **Track 1 — Conceptual** | Phase 0 — Orientation | 3Blue1Brown NN series + Illustrated Transformer |
| **Track 2 — Tooling** | Phase A — Orientation | docs.claude.com; define skill/tool/MCP/connector/plugin/agent |

Repo note: a `p0` scaffold already exists (DuckDB, `src/statlas` NLU/query modules, eval set) —
useful raw material for later phases (esp. Track 1 Phase 4 Text-to-SQL).

## Phase checklist

### Track 1 — Conceptual AI/ML
- [ ] **Phase 0 — Orientation:** 3Blue1Brown NN series, Illustrated Transformer
- [ ] **Phase 1 — Transformers:** Attention Is All You Need, Karpathy "Let's build GPT", run nanoGPT
- [ ] **Phase 2 — NLP/NLU:** HF NLP course, CS224N → *project: NBA entity resolver*
- [ ] **Phase 3 — LLM app layer:** prompt engineering + function calling → *project: question→JSON*
- [ ] **Phase 4 — Text-to-SQL:** Spider/BIRD, arXiv 2410.01066 → *project: NBA→DuckDB SQL gen+validate+run*
- [ ] **Phase 5 — RAG:** Lewis et al. 2020 → *project: glossary + example-query retrieval*
- [ ] **Phase 6 — Evaluation:** *project: 30–50 question eval set + accuracy script*
- [ ] **Phase 7 — Visualization:** auto answer cards
- [ ] **Capstone:** end-to-end NBA ask-anything demo

### Track 2 — AI tooling
- [ ] **Phase A — Orientation:** docs.claude.com; define the 6 core terms
- [ ] **Phase B — Claude Code fundamentals:** scaffold the repo
- [ ] **Phase C — Skills:** write a custom `nba-query` skill
- [ ] **Phase D — Tools/function calling:** expose `run_sql` as a tool
- [ ] **Phase E — MCP:** build a `statmuse-clone` MCP server exposing `query_stats`
- [ ] **Phase F — Agent SDK:** routing agent
- [ ] **Phase G — Cowork automation:** scheduled "stat of the day"

## Daily log

- **2026-06-09 (day1)** — First coach run. Fresh start: Track 1 Phase 0 / Track 2 Phase A.
  Suggested — T1: 3Blue1Brown "But what is a neural network?" (ep.1) + ep.2 gradient descent (~45 min).
  T2: skim docs.claude.com overview, write one-line defs of skill/tool/MCP/connector/plugin/agent (~30 min).
  Stretch: read intro of Illustrated Transformer. *Completed: (awaiting Ashish's input.)*
- **2026-06-10 (day2)** — Still Track 1 Phase 0 / Track 2 Phase A (no completion reported yet for day1).
  Suggested — T1: finish 3Blue1Brown ep.3 backprop + ep.4 backprop calculus (~30 min).
  T2: finalize one-line defs of the 6 core terms + map each to Statlas (~30 min).
  Stretch: start Illustrated Transformer through "self-attention at a high level." *Completed: (awaiting Ashish's input.)*
