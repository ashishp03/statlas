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
| **Latest artifacts** | Worked example (2026-09-13) + drafted slash command (2026-09-15) + `/eval` branch-blocker diagnosis (2026-09-16) + **harness verified green 5/5 (2026-09-20)** | `days/day7/qualifier_worked_example.md` — DuckDB `RANK() OVER` + `QUALIFY`; qualifier is a no-op on per-game counting stats, decisive on rate stats. `days/day8/draft-eval-command.md` — the T-B `/eval` slash command, written out; needs only a copy into `.claude/commands/` — but **paste it on `learning`**: `tests/` does not exist on `data-exploration` (found 09-16, see `days/day9/summary.md`). `tests/run_eval.py` was run by the coach 09-20 and is **green, 5/5, self-bootstrapping the DuckDB seed** — nothing is broken behind the `/eval` item; `days/day10/install-eval.sh` now does the install in one command |
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
- **2026-09-01 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Quiet since the 2026-08-25 module-building session (M4 text-to-SQL + M5 computation engine, both
  execution-verified) — one week, flexible timeline, no rush. Nothing new reported completed. Housekeeping
  flags unchanged: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` on `data-exploration` are
  still untracked in git (that branch's working tree also now carries untracked `RESEARCH.md`, `ONBOARDING.md`,
  `AGENTS.md`, new `.claude/agents/*`), and the `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning`
  (module 03 — NLU intent parsing, commit `37222fd`) still shows **prunable** (safe on the branch, just untidy).
  Suggested — T1: open **M4's first paper** — the text-to-SQL survey **arXiv 2410.01066**, intro + taxonomy
  section, with `modules/04-text-to-sql/workbook.md` open beside it (~60–75 min); the module is already built
  and waiting, and it's the most directly load-bearing thing for Statlas. (Karpathy's "Intro to LLMs" remains
  the alternative if classic Stage-4 fundamentals feel better today.) T2: close out **T-B** — add
  `.claude/commands/eval.md` running the p0 eval set (~20–30 min; still the only open T-B item, and
  `.claude/commands/` doesn't exist yet on any branch). Stretch: fill in the 3 remaining gold query pairs
  left as a TODO in `modules/04-text-to-sql/exercises.ipynb`. *Completed: (awaiting Ashish's input.)*
- **2026-09-02 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Quiet since the 2026-08-25 module-building session (M4 text-to-SQL + M5 computation engine, both
  execution-verified) — nothing new reported completed; flexible timeline, no rush. Housekeeping flags
  unchanged from 09-01: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` on `data-exploration`
  are still untracked in git (alongside untracked `RESEARCH.md`, `ONBOARDING.md`, `AGENTS.md`,
  `.claude/agents/*`), and the `learning-nlu` worktree at `~/Desktop/Projects/statlas-learning`
  (module 03 — NLU intent parsing, commit `37222fd`) still shows **prunable** (safe on the branch, just
  untidy). New minor flag: the `learning` branch is held checked-out by several stale/locked worktrees
  from old sessions (`git worktree list` shows ~15) — `git worktree prune` when convenient.
  Suggested — T1: continue in **M4 — Text-to-SQL**: the survey **arXiv 2410.01066**, intro + taxonomy,
  with `modules/04-text-to-sql/workbook.md` open beside it (~60–75 min) — the module is built and waiting,
  and it's the most load-bearing piece for Statlas. (Karpathy's "Intro to LLMs" stays the alternative if
  classic Stage-4 fundamentals feel better today.) T2: close out **T-B** — add `.claude/commands/eval.md`
  running the p0 eval set (~20–30 min; still the only open T-B item, and `.claude/commands/` still doesn't
  exist on any branch — verified today). Stretch: fill in the 3 remaining gold query pairs left as a TODO
  in `modules/04-text-to-sql/exercises.ipynb`. *Completed: (awaiting Ashish's input.)*
- **2026-09-03 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session (M4 text-to-SQL + M5 computation engine, both
  execution-verified); nothing new reported completed, no new commits on any branch since — flexible timeline,
  no rush. Changed the framing today: instead of repeating the ~75-min paper read that hasn't landed for four
  runs, offered a **small hands-on on-ramp** into M4 (write gold NL→SQL pairs), with the survey paper kept as
  the "if you have a long block" option. Housekeeping flags unchanged: `experiments/v1_nba_storage_retrieval_benchmark/`
  + `ask.py` and now also `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/`.claude/agents/*` are untracked on
  `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) is safe on its branch but its worktree path
  `~/Desktop/Projects/statlas-learning` no longer exists on disk. `git worktree prune` was attempted this run
  and failed on permissions (~15 stale/locked entries remain) — needs to be run by Ashish locally.
  Suggested — T1: open `modules/04-text-to-sql/exercises.ipynb` and finish **exercise 1** — add the 5 missing
  gold NL→SQL pairs (assists leader, a team filter, a per-36-style ratio…) against the day5 EDA CSV until the
  assert goes green (~30 min); if the block is bigger, continue into the SELECT-only guard TODOs 1–4 in the
  same notebook, or read the survey **arXiv 2410.01066** intro + taxonomy with `workbook.md` open.
  T2: close out **T-B** — add `.claude/commands/eval.md` running the p0 eval set (~20 min; still the only open
  T-B item, `.claude/commands/` still doesn't exist on any branch — verified today). Stretch: Karpathy
  **"Intro to Large Language Models"** (~1 hr) for the classic Stage-4 fundamentals.
  *Completed: (awaiting Ashish's input.)*
- **2026-09-04 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session (M4 text-to-SQL + M5 computation engine, both
  execution-verified); no new commits and no working-tree file changes on any branch since — flexible timeline,
  no rush. Kept 09-03's "small hands-on on-ramp" framing but **flipped the order of effort**: made the 20-min
  Track-2 win (`.claude/commands/eval.md`) the lead item since it's been the single open T-B item for ~2 months
  and is the cheapest thing on the board, with a **single** gold NL→SQL pair in
  `modules/04-text-to-sql/exercises.ipynb` as the Track-1 micro-step (~15–20 min) rather than the full set of 5.
  Housekeeping flags unchanged: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` +
  `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/`.claude/agents/*` still untracked on `data-exploration`;
  `learning-nlu` (module 03, commit `37222fd`) safe on its branch though its worktree path
  `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked worktrees still need a local
  `git worktree prune` (permission-blocked from this session again).
  Suggested — T1: open `modules/04-text-to-sql/exercises.ipynb`, add **one** gold NL→SQL pair (the assists
  leader) against the day5 EDA CSV and run the cell (~15–20 min); keep going into the other 4 pairs / the
  SELECT-only guard TODOs if it's flowing. T2: add `.claude/commands/eval.md` running the p0 eval set (~20 min)
  — closes T-B. Stretch: survey **arXiv 2410.01066** intro + taxonomy with `modules/04-text-to-sql/workbook.md`
  open, or Karpathy **"Intro to Large Language Models"** (~1 hr). *Completed: (awaiting Ashish's input.)*
- **2026-09-05 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session (M4 text-to-SQL + M5 computation engine, both
  execution-verified); no new commits on any branch and no modified files anywhere in the repo in the last 7 days
  — flexible timeline, no rush, and a quiet stretch is fine. It's a Saturday, so today's framing offers **two
  sizes** of the same next step rather than one fixed block: a ~15-min micro-step and a longer weekend option,
  keeping 09-04's "cheapest thing first" ordering. Housekeeping flags unchanged:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/
  `.claude/agents/*` still untracked on `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe on
  its branch though its worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked
  worktrees still need a local `git worktree prune` (permission-blocked from this session again).
  Suggested — T1: open `modules/04-text-to-sql/exercises.ipynb` and add **one** gold NL→SQL pair (the assists
  leader) against the day5 EDA CSV, run the cell (~15 min); if the Saturday block is bigger, continue through the
  other 4 pairs and the SELECT-only guard TODOs 1–4 in the same notebook (~60–75 min). T2: add
  `.claude/commands/eval.md` running the p0 eval set (~20 min) — still the only open T-B item, and
  `.claude/commands/` still doesn't exist on any branch (verified today). Stretch: 3Blue1Brown **"Large Language
  Models explained briefly"** (~7 min) as a zero-friction toe-dip into Stage 4, with Karpathy's full "Intro to
  LLMs" (~1 hr) as the bigger version. *Completed: (awaiting Ashish's input.)*
- **2026-09-06 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session (M4 text-to-SQL + M5 computation engine, both
  execution-verified); verified again today — no new commits on any branch, and no file in the repo modified in
  the last 7 days. Flexible timeline, no rush. **Changed the approach this run:** the same two items
  (one gold NL→SQL pair + `.claude/commands/eval.md`) have led four runs in a row without landing, so today's
  lead item is a **zero-prep re-entry point instead of a task** — open the repo and run the already-working
  `experiments/v1_nba_storage_retrieval_benchmark/ask.py` on `data-exploration` and ask it a few NBA questions,
  watching the SQL it prints. Rationale: it re-establishes contact with the project in ~10 min with nothing to
  build, and the printed SQL is exactly the M4 gold-pair material, so it feeds the stalled next step naturally.
  Housekeeping flags unchanged: `experiments/…` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/
  `.claude/agents/*` still untracked on `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe on
  its branch though its worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked
  worktrees still need a local `git worktree prune`.
  Suggested — T1: run `ask.py`, ask 3–4 questions, paste the best generated SQL into
  `modules/04-text-to-sql/exercises.ipynb` as a gold NL→SQL pair (~15 min). T2: add `.claude/commands/eval.md`
  running the p0 eval set (~20 min) — still the only open T-B item, `.claude/commands/` still doesn't exist on
  any branch (verified today). Stretch: 3Blue1Brown **"Large Language Models explained briefly"** (~7 min).
  *Completed: (awaiting Ashish's input.)*
- **2026-09-06 (session — NLU + text-to-SQL study plan)** — Ashish asked directly for a consolidated
  **reading/watching** plan for NLU and text-to-SQL (coding deliberately deferred — the graded
  notebooks already exist). Built `learning/study-plan-nlu-text-to-sql.md`: one linear consume-list
  merging the M2 / M4 / M5 workbook "Read" sections with roadmap Stages 2, 5, 6 and 7, so the whole
  NLU→SQL half of the project is a single ordered list instead of four scattered ones. Structure:
  **Part A (NLU)** — vector semantics (skippable revision) → BERT §3 → Sentence-BERT → neural
  entity-linking survey + rapidfuzz docs → Anthropic tool-use/structured-output docs + Toolformer;
  **Part B (Text-to-SQL ⭐)** — survey 2410.01066 (intro + prompting only) → DIN-SQL 2304.11015 →
  Spider → BIRD → execution-guided decoding 1807.03100 → self-consistency 2203.11171 → CHASE-SQL
  (skim) → DuckDB SIGMOD paper + CMU 15-445 "Query Execution 1" + DuckDB window-function docs.
  Every item carries a **size tag (S/M/L)** so a session can be matched to the time actually
  available, and a **one-line takeaway** that serves as its definition-of-done. Recommended order
  puts **Part B before Part A** (B builds the thing that doesn't exist; A upgrades accuracy on
  something that already works), with a ~5-hour load-bearing core (items 1–7) inside a ~14–18-hour
  full list. Also resolved a **citation conflict**: `roadmap.md` cites survey arXiv 2406.08426 while
  the M4 workbook cites 2410.01066 — noted in the plan as "either works, pick one, don't re-read the
  other." Reconfirmed the **module 03 (`03-nlu-intent-parsing`) gap**: only M2 exists on the
  `learning-nlu` branch; the intent-parsing module was never committed and would need rebuilding.
  *Completed: study plan shipped (this session). No coding exercises added — by request.*
- **2026-09-10 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session; verified again today — no commits on any branch
  since, and nothing in the repo modified in the last 5 days. Flexible timeline, no rush. **New angle this run:**
  the 09-06 session produced `learning/study-plan-nlu-text-to-sql.md` — a reading-only consume list, built at
  Ashish's explicit request — and that request is a signal: the coding on-ramps (gold NL→SQL pair, `ask.py`)
  have led five runs without landing, so today's lead item is a **reading item from his own plan**, and the
  smallest one in it: **B5c — DuckDB window-function docs** (~20 min, tagged in the plan as "most immediately
  useful item in Part B"). It's zero-setup, it's a docs page not a paper, and `QUALIFY` is literally how the
  repo's min-games-qualifier rule gets written. Housekeeping flags unchanged:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/
  `.claude/agents/*` still untracked on `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe on
  its branch though its worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked
  worktrees still need a local `git worktree prune` (permission-blocked from this session again).
  Suggested — T1: read **B5c**, DuckDB window functions (https://duckdb.org/docs/sql/window_functions) —
  `RANK() OVER`, `AVG() OVER (PARTITION BY ...)`, `QUALIFY`, and the logical clause order (~20 min).
  T2: add `.claude/commands/eval.md` running the p0 eval set (~20 min) — still the only open T-B item,
  `.claude/commands/` still doesn't exist on any branch (verified today). Stretch: **B2 — DIN-SQL**
  (arXiv 2304.11015), the highest-value paper in the plan (~45 min). *Completed: (awaiting Ashish's input.)*
- **2026-09-11 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session; verified again today — no commits on any branch
  since 09-10's coach commit, and nothing in the repo modified in the last 6 days. Flexible timeline, no rush.
  **Adjustment this run:** kept yesterday's B5c (DuckDB window functions) as the topic — it is genuinely the
  smallest, most load-bearing item on the board — but converted it from *reading* into a **single runnable
  query**. Rationale: a docs-page read has no artifact and nothing to stop on, whereas one `QUALIFY` query
  against the existing `days/day5/eda/data/player_stats_2025-26_regular.csv` produces a real answer (top-5
  scorers with a min-games qualifier), teaches the same three constructs by use, and *is* the repo's
  reliability rule ("leaderboards need a minimum-games qualifier") written in SQL. ~10 minutes, zero setup —
  DuckDB is already a dependency and can read the CSV directly. Housekeeping flags unchanged:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/
  `.claude/agents/*` still untracked on `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe
  on its branch though its worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15
  stale/locked worktrees still need a local `git worktree prune` (permission-blocked from this session again).
  Suggested — T1: one DuckDB `QUALIFY` query over the day5 EDA CSV — top 5 PPG with `GP >= 40`, using
  `RANK() OVER (ORDER BY PTS DESC)` + `QUALIFY` (~10 min); if it flows, paste it into
  `modules/04-text-to-sql/exercises.ipynb` as a gold NL→SQL pair. T2: add `.claude/commands/eval.md` running
  the p0 eval set (~20 min) — still the only open T-B item, `.claude/commands/` still doesn't exist on any
  branch (verified today). Stretch: **B2 — DIN-SQL** (arXiv 2304.11015), the highest-value paper in the
  study plan (~45 min). *Completed: (awaiting Ashish's input.)*
- **2026-09-13 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool calling)**.
  Still quiet since the 2026-08-25 module-building session — verified again today: no commits on any branch
  since 09-11's coach commit, and nothing in the repo modified in the last 8 days. (No 09-12 run landed.)
  Flexible timeline, no rush. **Changed the approach again this run — and this time did the work instead of
  assigning it.** Rationale: the 09-11 run had already shrunk B5c to "one runnable QUALIFY query, ~10 min"
  and it still didn't land, which suggests the blocker isn't task size but *starting* — opening a terminal,
  finding the CSV, remembering the column names. So today's Track-1 item is a **read, not a build**: the coach
  ran the query and shipped `days/day7/qualifier_worked_example.md`, a ~5-minute annotated result.
  Substantive finding worth keeping: the min-games qualifier is a **no-op on per-game counting stats** in the
  day5 dataset (top-5 PPG is identical with and without `GP >= 40` — Dončić 33.5 / SGA 31.1 / Edwards 28.8 /
  Brown 28.7 / Maxey 28.3), but **decisive on rate stats** — unqualified 3P% leaders are four bigs tied at
  100% on ~1 attempt all season, vs. Kennard .478 / Portis .456 / Spencer .449 once `GP >= 40 AND FG3A >= 3.0`
  is applied. Implication recorded for the build: qualifier thresholds are **per-metric metadata owned by the
  planner**, not a global constant and never LLM-generated (allow-list candidate). Housekeeping flags unchanged:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/
  `.claude/agents/*` still untracked on `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe
  on its branch though its worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15
  stale/locked worktrees still need a local `git worktree prune` (permission-blocked from this session again).
  Suggested — T1: read `days/day7/qualifier_worked_example.md` (~5 min), optionally paste its query into
  `modules/04-text-to-sql/exercises.ipynb` as a gold NL→SQL pair. T2: add `.claude/commands/eval.md` running
  the p0 eval set (~20 min) — still the only open T-B item, `.claude/commands/` still doesn't exist on any
  branch (verified today). Stretch: **B2 — DIN-SQL** (arXiv 2304.11015), ~45 min.
  *Completed: worked example written + executed by the coach (this session). Awaiting Ashish's input on the rest.*
- **2026-09-15 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting & tool
  calling)**. Verified today: still no commits on any branch since 09-11's coach commit, and nothing in the repo
  modified in the last 8 days apart from the coach's own day7 files. (No 09-12 or 09-14 run landed; the 09-13
  entry above is being committed today, late, because that run hit the git-lock permission issue — `git worktree
  prune` is still needed locally.) Flexible timeline, no rush. **Two deliberate changes this run.** (1) Track 1
  **finally opens Stage 4 instead of circling M4/text-to-SQL.** Every run since 09-05 has assigned some flavour
  of the same text-to-SQL on-ramp (gold pair -> `ask.py` -> B5c reading -> B5c as one query -> B5c pre-run for
  him to read) and none landed; the roadmap's actual next stage — LLMs — has been "next" since June and has
  never been opened. So today's item is the 3Blue1Brown **"Large Language Models explained briefly"** (~7 min):
  passive, phone-watchable, a different modality from eight consecutive terminal/reading tasks, and it moves the
  stage marker rather than adding depth to a stage already marked next. (2) Track 2: rather than assign
  `.claude/commands/eval.md` a **ninth** time, the coach **wrote it** — `days/day8/draft-eval-command.md` holds
  the complete file (frontmatter, `allowed-tools` scoped to `python tests/run_eval.py`, failure-triage steps
  mapping each `[FAIL]` to parser/planner/executor/data, an explicit "never edit `eval_set.json` to make a case
  pass" rule, and `$ARGUMENTS`). The remaining work is a `mkdir` + paste, ~2 min, and it checks off **T-B** and
  opens **T-C (Skills)**. Also committed day7's files to the `learning` branch this run — they had been sitting
  untracked in the `data-exploration` working tree. Housekeeping flags otherwise unchanged:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/
  `.claude/agents/*` still untracked on `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe on
  its branch though its worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked
  worktrees still need a local `git worktree prune`.
  Suggested — T1: 3B1B **"Large Language Models explained briefly"** (~7 min) — Stage 4, first contact.
  T2: copy `days/day8/draft-eval-command.md` -> `.claude/commands/eval.md`, run `/eval` (~5 min).
  Stretch: **B2 — DIN-SQL** (arXiv 2304.11015), ~45 min.
  *Completed: `/eval` slash command drafted in full by the coach (this session). Awaiting Ashish's input on the rest.*
- **2026-09-16 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting &
  tool calling)**. Verified today: no commits on any branch since 09-15's coach commit (`c3b5a2e`), and
  the only files touched in the repo in the last 4 days are the coach's own day7/day8 files. Nothing new
  reported completed. Flexible timeline, no rush. **The substantive result of this run is a diagnosis
  rather than a new assignment:** the `/eval` slash command has been assigned ~9 times and drafted in
  full, and the reason the "2-minute paste" keeps not landing may simply be that **it cannot work on the
  branch the working tree is checked out on**. `tests/run_eval.py` and `tests/eval_set.json` exist only
  on `learning`; `data-exploration` (currently checked out) has `src/`, `experiments/`, `notebooks/`,
  `scripts/` and **no `tests/` at all**. So pasting the command there and typing `/eval` errors out on a
  missing file. Recorded in `days/day9/summary.md` with the two one-line fixes (`git switch learning`, or
  `git checkout refs/heads/learning -- tests/`). The coach also attempted to pre-run the harness to
  confirm it goes green, but the sandbox lacks `duckdb`/`rapidfuzz` and the install timed out — the first
  real run stays with Ashish. Track 1 is **deliberately unchanged** from 09-15 (3B1B "Large Language
  Models explained briefly", ~7 min): it was offered only once, it is the smallest move available on the
  roadmap's actual next stage, and churning the topic every run has not helped. Housekeeping flags
  unchanged: `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` +
  `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/`.claude/agents/*` still untracked on `data-exploration`;
  `learning-nlu` (module 03, commit `37222fd`) safe on its branch though its worktree path
  `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked worktrees plus ~20 broken
  refs (now warning on every `git branch`) still need a local `git worktree prune`.
  Suggested — T1: 3B1B **"Large Language Models explained briefly"** (~7 min) — Stage 4, first contact.
  T2: install `/eval` **on `learning`** (or `git checkout refs/heads/learning -- tests/` first), then run
  it and report the accuracy line — or the error, which is equally useful (~5 min). Stretch: **B2 —
  DIN-SQL** (arXiv 2304.11015), ~45 min.
  *Completed: branch-mismatch blocker on the `/eval` item diagnosed (this session). Awaiting Ashish's input on the rest.*
- **2026-09-20 (coach run)** — Foundations: Stage 3 ✅; next **Stage 4 (LLMs) → Stage 5 (prompting &
  tool calling)**. Verified today: no commits on any branch since 09-16's coach commit (`ab6c174`),
  and the only files touched in the repo in the last 7 days are the coach's own day7–day9 files.
  Nothing new reported completed. Flexible timeline, no rush — it's a Sunday, and a quiet stretch
  is fine. **This run closed the last open question behind the `/eval` item instead of re-assigning
  it.** 09-16 diagnosed *why* the paste kept failing (no `tests/` on `data-exploration`) but could
  not confirm the harness itself worked — the sandbox lacked `duckdb`/`rapidfuzz` and the install
  timed out. Installed them today, extracted the `learning` tree with `git archive` and ran
  `python tests/run_eval.py`: **5/5 = 100%**, all five golden questions passing (Wemby ±4.40 vs OKC,
  Wemby 28.60 PPG vs OKC, LeBron 27.75 PPG 2013, Jokić 10.00 APG playoffs, Wemby 60 total REB vs
  OKC), and the script **self-bootstraps its DuckDB seed** (5 players, 15 game logs) so there is no
  setup step. Two things follow: the p0 baseline is *verified* working rather than assumed, and the
  eval set is thin — 5 questions against M7's target of 40–50, which makes **growing the eval set**
  the natural follow-on once `/eval` exists (and every M4 gold NL→SQL pair can double as an eval
  case). Also shipped `days/day10/install-eval.sh` — it switches nothing, but creates
  `.claude/commands/` and extracts the command body out of `days/day8/draft-eval-command.md`
  automatically, reducing the Track-2 item from "mkdir + find the fenced block + paste" to one
  `bash` line; the script was executed in this session and verified to produce a correct 20-line
  `eval.md`. Track 1 is **deliberately unchanged for the third run** (3B1B "Large Language Models
  explained briefly", ~7 min): churning the topic every run has not helped, and it remains the
  smallest possible move on the roadmap's actual next stage. Housekeeping flags unchanged:
  `experiments/v1_nba_storage_retrieval_benchmark/` + `ask.py` +
  `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md`/`.claude/agents/*` still untracked on
  `data-exploration`; `learning-nlu` (module 03, commit `37222fd`) safe on its branch though its
  worktree path `~/Desktop/Projects/statlas-learning` is gone from disk; ~15 stale/locked worktrees
  plus ~20 broken refs still need a local `git worktree prune`.
  Suggested — T1: 3B1B **"Large Language Models explained briefly"** (~7 min) — Stage 4, first contact.
  T2: `git switch learning` then `bash learning/days/day10/install-eval.sh`, then type `/eval`
  (~2 min; the harness is confirmed green, so it will print `Accuracy: 5/5 = 100%`). Stretch:
  **B2 — DIN-SQL** (arXiv 2304.11015), ~45 min.
  *Completed: eval harness run and verified green 5/5 by the coach + one-command installer shipped
  (this session). Awaiting Ashish's input on the rest.*
