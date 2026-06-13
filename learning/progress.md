# Statlas — Study Progress

Project: AI-powered sports stats answer engine (a better StatMuse).

> **Mode change 2026-06-13 — FOUNDATIONS FIRST (learn-before-build).** Ashish wants to slow down
> and build core conceptual understanding from the ground up *before* building the product: intro
> videos, lectures, papers for every concept Statlas needs (text-to-SQL, NLP, transformers, LLMs,
> RAG, eval…), plus small **example-coding** exercises (not the product). Master guide is now
> **`learning/roadmap.md`**. The advanced build plan **`learning/curriculum.md`** is PARKED and
> will be revived once foundations feel solid.
>
> *(Earlier 2026-06-10 plan — advanced module-based build — superseded by the above.)*

## Current status

| Track | Stage | Notes |
|-------|-------|-------|
| **Foundations (roadmap.md)** | **Stage 3 — Transformers & attention** (entry point) | MS-DS background → Stage 1 (NN) & Stage 2 (embeddings) are revision; skip/skim. Start: Illustrated Transformer + Attention paper §3 |
| **Reference built today** | EDA on real NBA data | `days/day5/eda/` — report + 6 figures + cached CSVs |
| **Parked** | Build plan (`curriculum.md`) | revive after foundations |

Repo note: the `p0` scaffold (`parser.py`, template `planner.py`, `executor.py`, answer cards)
is the **baseline + ship target** for when we return to building.

## Module checklist (full detail in `curriculum.md`)

### Track 1 — Conceptual AI/ML
- [ ] **M1 — Transformer internals:** Attention paper + Annotated Transformer, Karpathy build-GPT, nanoGPT → *ship: from-scratch attention + notes*  ·  _modules/01 built_
- [ ] **M2 — NLU & entity resolution:** BERT, Sentence-BERT → *ship: embedding `resolver.py` + eval set*  ·  _modules/02 built_
- [ ] **M3 — LLM app layer:** function calling, Toolformer, Pydantic → *ship: LLM `parser.py` returning same Intent*  ⭐weak spot
- [ ] **M4 — Text-to-SQL:** Spider/BIRD, DIN-SQL, arXiv 2410.01066 → *ship: LLM SQL-draft path in `planner.py`*  ⭐weak spot
- [ ] **M5 — Computation engine & reliability:** exec-guided decoding, self-consistency → *ship: hardened `executor.py`*  ⭐weak spot
- [ ] **M6 — RAG:** Lewis et al. 2020, ColBERT → *ship: glossary + example-query retriever*
- [ ] **M7 — Evaluation:** *ship: 40–50 Q eval set + accuracy harness in `tests/`*
- [ ] **M8 — Visualization:** auto answer cards
- [ ] **Capstone:** end-to-end NBA ask-anything demo

### Track 2 — AI tooling
- [ ] **T-B — Claude Code fundamentals:** (orientation folded in) → *ship: `CLAUDE.md` + slash command*
- [ ] **T-C — Skills:** *ship: `nba-query` skill wrapping `engine.ask`*
- [ ] **T-D — Tools/function calling:** *ship: expose `run_sql` as a typed tool*
- [ ] **T-E — MCP:** *ship: `statmuse-clone` MCP server exposing `query_stats`*
- [ ] **T-F — Agent SDK (resident agent):** *ship: routing agent in `src/statlas/agent/`*  ⭐weak spot
- [ ] **T-G — Cowork automation:** *ship: scheduled "stat of the day"*

## Daily log

- **2026-06-09 (day1)** — First coach run. Fresh start: Track 1 Phase 0 / Track 2 Phase A.
  Suggested — T1: 3Blue1Brown "But what is a neural network?" (ep.1) + ep.2 gradient descent (~45 min).
  T2: skim docs.claude.com overview, write one-line defs of skill/tool/MCP/connector/plugin/agent (~30 min).
  Stretch: read intro of Illustrated Transformer. *Completed: (awaiting Ashish's input.)*
- **2026-06-10 (day2)** — Still Track 1 Phase 0 / Track 2 Phase A (no completion reported yet for day1).
  Suggested — T1: finish 3Blue1Brown ep.3 backprop + ep.4 backprop calculus (~30 min).
  T2: finalize one-line defs of the 6 core terms + map each to Statlas (~30 min).
  Stretch: start Illustrated Transformer through "self-attention at a high level." *Completed: (awaiting Ashish's input.)*
- **2026-06-10 (day2, plan overhaul)** — Ashish flagged MS-DS background; wants advanced,
  practice/paper/video-based learning with homework-style notebooks. Restructured the plan:
  added `curriculum.md` (advanced module map, both tracks), and built **M1 — Transformer
  internals** and **M2 — NLU & entity resolution** (each `workbook.md` + graded `exercises.ipynb`).
  New entry point for him: `learning/curriculum.md`, then `learning/modules/01-*`.
- **2026-06-11 (day3)** — First day on the upgraded plan. Track 1: M1 / Track 2: T-B.
  Suggested — T1: M1 session 1 — read *Attention Is All You Need* §3 with the Annotated
  Transformer open beside it, fill the Q/K/V + causal-mask theory blanks, then do
  exercises 1–2 (softmax, scaled dot-product attention) in `modules/01/exercises.ipynb` (~75 min).
  T2: T-B — write a first `CLAUDE.md` for the repo (project layout, how to run tests, p0 entry
  points) (~30 min). Stretch: first ~30 min of Karpathy's "Let's build GPT."
  *Completed: (awaiting Ashish's input.)*
- **2026-06-12 (day4)** — Track 1: M1 / Track 2: T-B (no completion reported for day 3; same targets carry forward, no rush).
  Suggested — T1: M1 session 1 (Attention §3 + Annotated Transformer, workbook blanks, exercises 1–2);
  if already done, exercises 3–4 (multi-head + causal mask) (~75 min).
  T2: T-B — draft `CLAUDE.md`; if done, add a `.claude/commands/eval.md` slash command (~30 min).
  Stretch: first ~30 min of Karpathy "Let's build GPT." *Completed: (awaiting Ashish's input.)*
- **2026-06-13 (day5)** — Track 1: M1 / Track 2: T-B (no completion reported for days 3–4; same targets carry forward, no rush).
  Suggested — T1: M1 session 1 (Attention §3 + Annotated Transformer, workbook blanks, exercises 1–2);
  if already done, exercises 3–4 (multi-head + causal mask) (~75 min).
  T2: T-B — draft `CLAUDE.md`; if done, add a `.claude/commands/eval.md` slash command running the p0 eval set (~30 min).
  Stretch: first ~30 min of Karpathy "Let's build GPT." *Completed: (awaiting Ashish's input.)*
- **2026-06-13 (day5, ACTIVE — pivot day)** — Ashish showed up with time and worked. Sequence:
  (1) verified the real data source (`nba_api`, free, no key); confirmed all three v1 questions
  answerable. (2) Ran a full **EDA** → `days/day5/eda/` (report + 6 figures + cached CSVs).
  (3) Then chose to **slow down to foundations-first**: built `learning/roadmap.md`, a ground-up
  curriculum (StatMuse framing, concept stack NN→NLP→transformers→LLMs→prompting→text-to-SQL→
  SQL→RAG→eval, with example-coding exercises). Parked `curriculum.md`.
  Next focus: roadmap Stage 1 (3B1B + Karpathy micrograd) → Stage 2 (CS224N L1–3).
  *Completed: EDA + roadmap (this session).*
