# Module 4 — Text-to-SQL ⭐

**Track 1 · advanced · ~3–4 sessions**
Goal: this *is* Statlas's central skill. Take a natural-language question over a known schema
and produce SQL that is both **syntactically valid** and **semantically correct** — then prove
correctness with an *execution-accuracy* harness instead of eyeballing it. This module builds the
theory + toy exercises that the repo's `query/planner.py` LLM-SQL-draft path (Phase 4 in the root
`CLAUDE.md`) will eventually use.

## Objectives
1. Explain the text-to-SQL pipeline as **schema linking → difficulty routing → SQL generation →
   execution-guided self-correction** (the DIN-SQL pattern) rather than "ask the model and hope."
2. Distinguish *exact-match* accuracy from *execution accuracy* and know why the field moved to
   the latter (SQL has many syntactically different, semantically equal forms).
3. Build a SELECT-only SQL safety validator by hand — the allow-list gate every drafted query
   must clear before touching DuckDB (this repo's `assert_safe`, non-negotiable per root `CLAUDE.md`).
4. Understand why the field benchmarks on Spider (clean, cross-domain) *and* BIRD (dirty,
   real-world values, efficiency-aware) — they stress different failure modes.

## Read (primary sources)
- **Survey (orientation, read first):** Mohammadjafari et al., *From Natural Language to SQL:
  Review of LLM-based Text-to-SQL Systems* (2024) — arXiv **2410.01066**. Read the intro + the
  prompting / in-context-learning section; skim the taxonomy figure. https://arxiv.org/abs/2410.01066
- **Method (the pattern to copy):** Pourreza & Rafiei, *DIN-SQL: Decomposed In-Context Learning
  of Text-to-SQL with Self-Correction* (2023) — arXiv **2304.11015**. The four-stage pipeline:
  schema linking → difficulty classification → SQL generation (prompt varies by difficulty) →
  self-correction. https://arxiv.org/abs/2304.11015
- **Benchmark:** Yu et al., *Spider: A Large-Scale Human-Labeled Dataset for Complex and
  Cross-Domain Semantic Parsing and Text-to-SQL Task* (2018) — arXiv **1809.08887**. Skim the
  task setup and the **execution accuracy** metric definition. https://arxiv.org/abs/1809.08887
- **Benchmark (harder, dirtier):** Li et al., *Can LLM Already Serve as a Database Interface? A
  Big Bench for Large-Scale Database Grounded Text-to-SQLs* (BIRD, 2023) — arXiv **2305.03111**.
  Note *why* it's harder than Spider: noisy values, external knowledge, execution efficiency
  scoring. https://arxiv.org/abs/2305.03111
- **Stretch (current SOTA pattern):** Pourreza et al., *CHASE-SQL: Multi-Path Reasoning and
  Preference-Optimized Candidate Selection in Text-to-SQL* (2024) — arXiv **2410.01943**. Skim
  only: multiple candidate generation paths + a learned selector, i.e. self-consistency (M5) taken
  further. https://arxiv.org/abs/2410.01943

## Theory notes (fill in)
- Why is **execution accuracy** the standard metric instead of string/AST match? Give an example
  of two SQL queries that are string-different but execution-equal: ___
- DIN-SQL routes "easy" questions straight to generation but "hard" ones through extra
  decomposition steps. What makes a question *hard* for text-to-SQL (not for a human)? ___
- Schema linking = deciding which tables/columns a question refers to *before* generating SQL.
  Why does this step reduce hallucinated column names? ___
- BIRD's authors specifically penalize *inefficient* correct SQL (e.g. a full scan where an
  index/qualifier would do). Why does that matter for a stats engine like Statlas, which needs a
  `HAVING gp >= N` qualifier on every leaderboard? ___

## Exercises → `exercises.ipynb`
Grounded in this repo's real Stage-3/5 data (`learning/days/day5/eda/data/player_stats_2025-26_regular.csv`)
— DuckDB in-memory, zero new installs.
1. **Load the schema** — DuckDB over the EDA CSV; print the column list you'd hand an LLM as
   schema context.
2. **Hand-write the gold set** — 8 NL question → SQL pairs against this schema, spanning simple
   lookup, aggregation, `ORDER BY ... LIMIT` leaderboard, and a leaderboard **with a qualifier**
   (`HAVING GP >= 58`, echoing the repo's reliability rule).
3. **`assert_safe` — the allow-list gate** — implement a SELECT-only validator: single statement,
   no `;` stacking, no DDL/DML keywords, table/column allow-list. Test it against 6 attack
   strings (`DROP TABLE`, stacked `SELECT ...; DELETE ...`, comment-hidden injection, etc.) and 4
   legitimate queries — it must reject all attacks and accept all legit queries.
4. **Execution-accuracy scorer** — `exec_match(pred_sql, gold_sql, conn) -> bool` that runs both,
   compares result sets as **multisets** (order-insensitive) with a float tolerance. Prove two
   differently-*written*-but-equal queries score a match.
5. **Schema-linking heuristic** — a cheap string/fuzzy function `link(question, columns) -> set`
   that guesses which columns a question touches (precursor to what a model + this context would
   do). Score it against your 8 gold questions.
6. **(OPTIONAL) prompt construction** — build the actual prompt string (schema + 2 few-shot
   examples + question) you'd send an LLM, DIN-SQL style; no API call needed, just inspect it.

## Math problems (work by hand, verify in the last code cell)
1. **Set/bag equivalence.** `SELECT team, COUNT(*) FROM t GROUP BY team` and the same query with
   columns reordered in `SELECT` are execution-equal but string-different. Formally: define
   execution accuracy as equality of result *multisets* up to column permutation + float
   tolerance ε. Write the equivalence relation and show it is reflexive/symmetric/transitive
   (i.e. actually an equivalence relation) — this is why exec-accuracy is a sound metric to grade
   on.
2. **Self-consistency arithmetic.** If you sample *k* independent SQL candidates from a model,
   each individually correct with probability *p*, and you take a majority vote over their
   *execution results* (not their text), derive the probability the majority vote is correct as a
   function of *k* and *p* for the 3-candidate case (binomial: need ≥2/3 correct). Compute it for
   *p* = 0.6 and *p* = 0.8 and compare to single-shot accuracy — this is *why* CHASE-SQL/self-
   consistency helps more when the base model is already decent.
3. **Relational algebra by hand.** Translate one of your gold-set leaderboard queries (with the
   `HAVING` qualifier) into relational algebra (σ, π, γ/aggregate). Confirm the **logical
   processing order** `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT` is why
   `HAVING` can reference an aggregate but `WHERE` cannot.

## Definition of done
- `assert_safe` rejects all 6 attack strings and accepts all legit queries (0 false positives/negatives on your test set).
- `exec_match` correctly identifies at least one pair of string-different, execution-equal queries as a match.
- You can state, without looking it up, why BIRD is harder than Spider and why exec-accuracy beats string-match.

## Ship target (repo)
Feeds `src/statlas/query/planner.py`'s Phase-4 "LLM may draft SQL" path per the root `CLAUDE.md`:
the allow-list validator here **is** `assert_safe`'s spec; the gold-set pattern **is** the shape of
the eval set text-to-SQL upgrades get measured against later (Module 7 / roadmap Stage 9).

## Carry-over
- Keep your 8 gold (question, SQL) pairs — they seed the M7/roadmap-Stage-9 evaluation harness.
- `assert_safe` here is the reference implementation; the real `query/planner.py` version must be
  at least as strict.
