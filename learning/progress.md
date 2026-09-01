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
| **Foundations (roadmap.md)** | **Stage 3 — Transformers & attention ✅ DONE** → next **Stage 4 (LLMs)** | Stage 3 complete 2026-06-13: 3B1B + Illustrated Transformer + Attention §3 read; `softmax`/`scaled_dot_product_attention`/`causal_mask` implemented from scratch, all ✅ tests pass. Stages 1–2 were revision (skipped) |
| **Env** | uv on the Mac, Python 3.13 | `uv sync` + `.venv` registered as Jupyter kernel; 3.14 blocked by `gensim` wheels |
| **Reference built** | EDA on real NBA data | `days/day5/eda/` — report + 6 figures + cached CSVs |
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
- **2026-06-13 (day5, Stage 3 worked + env setup)** — Ashish completed roadmap **Stage 3 —
  Transformers & attention** (the `days/day5/TODAY.md` checklist, all 5 steps): watched 3B1B
  "Attention visually explained," read the Illustrated Transformer + *Attention Is All You Need*
  §3.1–3.2, and implemented `softmax` (numerically stable), `scaled_dot_product_attention`
  (scale by √d + additive mask), and `causal_mask` from scratch in numpy in
  `exercises/attention_from_scratch.ipynb` — **all three ✅ test cells pass** (verified end-to-end).
  Also stood up the local env: installed **uv** on the Mac, bumped pinned Python to **3.13**
  (3.14 blocked by `gensim` wheels), `uv sync`, registered `.venv` as a Jupyter kernel, and wrote
  the uv setup guide into the README. **Next: Stage 4 (LLMs) → Stage 5 (prompting & tool calling).**
  *Completed: Stage 3 (watch+read+code, tests green) + uv/3.13 env (this session).*
- **2026-06-21 (day6)** — Foundations track: **Stage 3 (transformers) ✅ done**, next **Stage 4 (LLMs)**.
  No new completion reported since day5 (no rush — flexible timeline). Suggested — T1: Karpathy
  "Intro to Large Language Models" (~1-hr talk) to open Stage 4 (tokenization, context windows,
  sampling/temperature). T2: finish T-B by adding `.claude/commands/eval.md` (the root `CLAUDE.md`
  now exists). Stretch: Hugging Face LLM Course ch.1–2. *Completed: (awaiting Ashish's input.)*
- **2026-06-24 (coach run)** — Foundations: **Stage 3 (transformers) ✅**, next **Stage 4 (LLMs)**.
  No completion reported since day5; day6 targets carry forward unchanged (flexible timeline, no rush).
  Suggested — T1: Karpathy **"Intro to Large Language Models"** (~1-hr talk) to open Stage 4
  (tokenization, pretraining vs fine-tuning, context windows, sampling/temperature). T2: close out
  **T-B** by adding `.claude/commands/eval.md` (slash command running the p0 eval set). Stretch:
  Hugging Face LLM Course ch. 1–2. *Completed: (awaiting Ashish's input.)*
- **2026-06-29 (coach run)** — Foundations: **Stage 3 (transformers) ✅**, next **Stage 4 (LLMs)**.
  Still no completion reported since day5 (flexible timeline — no rush). day6/day7 Stage-4 targets
  carry forward unchanged. Suggested — T1: Karpathy **"Intro to Large Language Models"** (~1-hr talk)
  to anchor Stage 4 (tokenization, pretraining vs. fine-tuning, context windows, sampling/temperature);
  if already watched, jump to **Hugging Face LLM Course ch. 1–2** and actually run a `pipeline()` call.
  T2: close out **T-B** by adding `.claude/commands/eval.md` (slash command running the p0 eval set).
  Stretch: 3Blue1Brown "Large Language Models explained briefly." *Completed: (awaiting Ashish's input.)*
- **2026-07-19 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Big practical session 2026-07-18 (on `data-exploration`): built `experiments/v1_nba_storage_retrieval_benchmark/`
  (8 store formats, 128/128 eval exact; recommendation DuckDB + season-partitioned Parquet), a SELECT-only-guarded
  **text-to-SQL bake-off** (MOCK 16/16; real Ollama models still pending) and interactive `ask.py`; also started NLU
  module `03-nlu-intent-parsing` on a `learning-nlu` worktree — great de-facto Stage 4/5 + text-to-SQL groundwork.
  Suggested — T1: run the **real-model leg of the bake-off** with a local Ollama model (e.g. `qwen2.5-coder:7b`),
  compare vs MOCK 16/16 (~60–75 min). T2: finally close **T-B** — add `.claude/commands/eval.md` running the p0
  eval set (~20–30 min). Stretch: continue module 03 — but first rescue it: the `learning-nlu` worktree at
  `~/Desktop/Projects/statlas-learning` shows **prunable** in `git worktree list`; commit that work before it's lost.
  *Completed: (awaiting Ashish's input.)*
- **2026-07-30 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  No completion reported since the 2026-07-18 practical session (flexible timeline — no rush); 07-19's
  targets carry forward unchanged. Also flagging: the `experiments/v1_nba_storage_retrieval_benchmark/`
  work (and `ask.py`) on `data-exploration` is still **fully untracked in git** (not committed on that
  branch or pushed anywhere) — worth a commit soon so it isn't lost. Suggested — T1: Karpathy's
  **"Intro to Large Language Models"** (~1 hr) if Stage 4 hasn't been opened yet; if it has, run the
  **real-model leg of the text-to-SQL bake-off** with a local Ollama model (e.g. `qwen2.5-coder:7b`)
  against the MOCK 16/16 baseline (~60–75 min). T2: close out **T-B** — add `.claude/commands/eval.md`
  running the p0 eval set (~20–30 min). Stretch: rescue module `03-nlu-intent-parsing` — the
  `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning` still shows **prunable**; commit
  that work before it's lost. *Completed: (awaiting Ashish's input.)*
- **2026-07-31 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still no completion reported since the 2026-07-18 practical session (flexible timeline — no rush); 07-19/07-30's
  targets carry forward unchanged. Housekeeping flags persist: `experiments/v1_nba_storage_retrieval_benchmark/`
  + `ask.py` on `data-exploration` remain fully untracked in git, and the `learning-nlu` worktree at
  `~/Desktop/Projects/statlas-learning` (module 03 — NLU intent parsing, commit `37222fd`) still shows
  **prunable**, unchanged since first flagged 07-19. Suggested — T1: Karpathy's **"Intro to Large Language
  Models"** (~1 hr) to open Stage 4 (tokenization, pretraining vs. fine-tuning, context windows,
  sampling/temperature) — no rush if it's not been the week for it. T2: close out **T-B** — add
  `.claude/commands/eval.md` running the p0 eval set (~20–30 min; still the only open T-B item). Stretch:
  rescue module `03-nlu-intent-parsing` — commit or copy the `learning-nlu` worktree content in before it's
  lost. *Completed: (awaiting Ashish's input.)*
- **2026-08-02 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still no completion reported since the 2026-07-18 practical session (flexible timeline — no rush); 07-19/07-30/07-31's
  targets carry forward unchanged. Housekeeping flags persist: `experiments/v1_nba_storage_retrieval_benchmark/`
  + `ask.py` on `data-exploration` remain fully untracked in git, and the `learning-nlu` worktree at
  `~/Desktop/Projects/statlas-learning` (module 03 — NLU intent parsing, commit `37222fd`) still shows
  **prunable**, unchanged since first flagged 07-19. Suggested — T1: Karpathy's **"Intro to Large Language
  Models"** (~1 hr) to open Stage 4 (tokenization, pretraining vs. fine-tuning, context windows,
  sampling/temperature). T2: close out **T-B** — add `.claude/commands/eval.md` running the p0 eval set
  (~20–30 min; still the only open T-B item). Stretch: rescue module `03-nlu-intent-parsing` — commit or
  copy the `learning-nlu` worktree content in before it's lost. *Completed: (awaiting Ashish's input.)*
- **2026-08-20 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still no completion reported since the 2026-07-18 practical session (flexible timeline — no rush, it's been a
  quiet few weeks and that's fine); 07-19/07-30/07-31/08-02's targets carry forward unchanged. Housekeeping flags
  persist: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` on `data-exploration` remain fully
  untracked in git, and the `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning` (module 03 — NLU
  intent parsing, commit `37222fd`) still shows **prunable** (unchanged since first flagged 07-19 — not urgent,
  the commit itself is safe on the `learning-nlu` branch, just tidy it when convenient). Suggested — T1:
  Karpathy's **"Intro to Large Language Models"** (~1 hr) to open Stage 4 (tokenization, pretraining vs.
  fine-tuning, context windows, sampling/temperature). T2: close out **T-B** — add `.claude/commands/eval.md`
  running the p0 eval set (~20–30 min; still the only open T-B item). Stretch: rescue module
  `03-nlu-intent-parsing` — commit or copy the `learning-nlu` worktree content in before it's lost.
  *Completed: (awaiting Ashish's input.)*
- **2026-08-21 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still no completion reported since the 2026-07-18 practical session (flexible timeline — no rush; over a month
  quiet now, and that's fine); 07-19 through 08-20's targets carry forward unchanged. Housekeeping flags persist:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` on `data-exploration` remain fully untracked in git,
  and the `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning` (module 03 — NLU intent parsing, commit
  `37222fd`) still shows **prunable** (unchanged since first flagged 07-19 — not urgent, the commit is safe on the
  `learning-nlu` branch). Suggested — T1: Karpathy's **"Intro to Large Language Models"** (~1 hr) to open Stage 4
  (tokenization, pretraining vs. fine-tuning, context windows, sampling/temperature). T2: close out **T-B** — add
  `.claude/commands/eval.md` running the p0 eval set (~20–30 min; still the only open T-B item). Stretch: rescue
  module `03-nlu-intent-parsing` — commit or copy the `learning-nlu` worktree content in before it's lost.
  *Completed: (awaiting Ashish's input.)*
- **2026-08-25 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still no completion reported since the 2026-07-18 practical session (flexible timeline — no rush; it's been
  quiet for over a month now, and that's fine); 07-19 through 08-21's targets carry forward unchanged.
  Housekeeping flags persist: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` on `data-exploration`
  remain fully untracked in git, and the `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning`
  (module 03 — NLU intent parsing, commit `37222fd`) still shows **prunable** (unchanged since first flagged
  07-19 — not urgent, the commit is safe on the `learning-nlu` branch). Suggested — T1: Karpathy's **"Intro to
  Large Language Models"** (~1 hr) to open Stage 4 (tokenization, pretraining vs. fine-tuning, context windows,
  sampling/temperature); if already watched, jump into **Hugging Face LLM Course ch. 1–2** and run a `pipeline()`
  call. T2: close out **T-B** — add `.claude/commands/eval.md` running the p0 eval set (~20–30 min; still the
  only open T-B item). Stretch: rescue module `03-nlu-intent-parsing` — commit or copy the `learning-nlu`
  worktree content in before it's lost. *Completed: (awaiting Ashish's input.)*
- **2026-08-25 (session — text-to-SQL/SQL-engine study push)** — Ashish asked directly for a
  focused NLU + text-to-SQL + SQL-engine study package: papers, math problems, coding exercises,
  videos. Built out **M4 — Text-to-SQL** and **M5 — Computation Engine & Reliability** in
  `learning/modules/` (previously stubs in `curriculum.md`'s table), each with a `workbook.md`
  (papers: survey arXiv 2410.01066, DIN-SQL 2304.11015, Spider 1809.08887, BIRD 2305.03111,
  CHASE-SQL 2410.01943 stretch for M4; DuckDB SIGMOD paper, CMU 15-445 "Query Execution 1",
  execution-guided decoding 1807.03100, self-consistency 2203.11171 for M5; math problems in both)
  and a graded `exercises.ipynb`, grounded in the repo's real `days/day5/eda` player-stats CSV via
  DuckDB (not a toy DB). Both notebooks were **execution-verified end-to-end**
  (`jupyter nbconvert --execute`, all asserts pass) before shipping — M4 ships with 3/8 gold pairs
  filled in as an intentional TODO, M5 has none left unfilled. Also appended a **math problems**
  section to the existing M2 (NLU) workbook (cosine similarity by hand, precision/recall
  monotonicity at the `min_score` threshold including the refusal case, bias-variance framing).
  This is a **parallel deep-dive**, not a roadmap-order change — Stage 4 (LLMs) remains the
  foundations-first default next focus per the coach's run earlier today.
  *Completed: M4 + M5 modules shipped and verified, M2 math addendum (this session).*
- **2026-08-31 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Since the last coach note, real forward motion happened on 08-25: **M4 (Text-to-SQL)** and **M5
  (Computation Engine & Reliability)** modules were built and execution-verified (workbooks + graded
  notebooks, grounded in the real day5 EDA data) — a parallel deep-dive, not a formal Stage-4 start,
  but directly useful groundwork for it. Quiet since (6 days — flexible timeline, no rush). Housekeeping
  flags persist: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` on `data-exploration` remain
  untracked in git, and the `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning` (module 03 —
  NLU intent parsing, commit `37222fd`) still shows **prunable** (safe, just untidy — flagged since 07-19).
  Suggested — T1: Karpathy's **"Intro to Large Language Models"** (~1 hr) to formally open Stage 4
  (tokenization, pretraining vs. fine-tuning, context windows, sampling/temperature) — or, since M4's
  workbook is already built and ready, jump straight into its first paper (arXiv 2410.01066 survey intro)
  if text-to-SQL is more exciting right now than the classic LLM-fundamentals detour. T2: close out **T-B**
  — add `.claude/commands/eval.md` running the p0 eval set (~20–30 min; still the only open T-B item).
  Stretch: rescue module `03-nlu-intent-parsing` — commit or copy the `learning-nlu` worktree content in
  before it's lost. *Completed: (awaiting Ashish's input.)*
