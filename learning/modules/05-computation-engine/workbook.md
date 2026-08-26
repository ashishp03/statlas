# Module 5 — Computation Engine & Reliability

**Track 1 · advanced · ~3 sessions**
Goal: this is the box that must never be wrong. Per the root `CLAUDE.md`: *"the executor is the
ONLY place a statistic is computed; its number is ground truth and nothing downstream may alter
it."* This module is about **DuckDB as the "SQL engine"** (why it's fast, what its execution
model buys you) and about **reliability techniques that catch a bad SQL draft before it becomes a
wrong answer** — execution-guided decoding and self-consistency voting.

## Objectives
1. Explain, at a mechanical level, why a **vectorized / columnar** execution engine (DuckDB) is
   faster than a naive row-at-a-time interpreter for analytical (OLAP) queries like leaderboards.
2. Recite the **logical query processing order** (`FROM → WHERE → GROUP BY → HAVING → SELECT →
   ORDER BY → LIMIT`) and use it to explain a real bug class (qualifiers applied at the wrong stage).
3. Implement **execution-guided decoding**: generate → try-execute → catch the DB's own error →
   feed it back / resample, instead of trusting a single unchecked SQL draft.
4. Implement **self-consistency voting** over multiple SQL candidates' *results* (not their text)
   and know when it helps vs. when it just amplifies a shared blind spot.

## Read (primary sources)
- **Paper (why DuckDB is fast):** Raasveldt & Mühleisen, *DuckDB: an Embeddable Analytical
  Database* (SIGMOD 2019, demo track). https://duckdb.org/pdf/SIGMOD2019-demo-duckdb.pdf
- **Lecture (query execution models):** CMU 15-445 *Intro to Database Systems* — **"Query
  Execution 1"** (Fall 2022, Andy Pavlo). Iterator/Volcano model vs. vectorized execution — the
  mental model behind why DuckDB processes columns in batches, not rows one at a time.
  https://www.youtube.com/watch?v=I0QdCSu06_o
- **Paper (catch errors before they ship):** Wang et al., *Robust Text-to-SQL Generation with
  Execution-Guided Decoding* (2018) — arXiv **1807.03100**. The core idea: partial-execute a SQL
  draft and use the DB's own runtime errors (type mismatch, empty result, etc.) to prune bad
  candidates during generation, not after. https://arxiv.org/abs/1807.03100
- **Paper (vote, don't trust one sample):** Wang et al., *Self-Consistency Improves Chain of
  Thought Reasoning in Language Models* (2022) — arXiv **2203.11171**. Sample multiple reasoning
  paths, marginalize over the *answer*, not the *text*. Same idea as CHASE-SQL's candidate
  selection (M4 stretch reading). https://arxiv.org/abs/2203.11171
- **Docs:** DuckDB window functions — `RANK() OVER`, `AVG() OVER (PARTITION BY ...)`, `QUALIFY`.
  https://duckdb.org/docs/sql/window_functions

## Theory notes (fill in)
- Row-at-a-time (Volcano/iterator model): each operator's `next()` returns *one tuple* and calls
  pull up the tree. Where does the per-tuple virtual-function-call overhead come from, and why
  does it dominate on modern CPUs? ___
- Vectorized execution processes a *batch* of ~1000–2000 values per operator call. What does this
  buy you specifically (cache locality, SIMD, amortized dispatch)? ___
- `HAVING gp >= 58` vs `WHERE gp >= 58` on a query that also has `GROUP BY player`: which one is
  even legal here, and why (tie to logical processing order)? ___
- Execution-guided decoding catches *runtime* errors (wrong types, empty joins). What class of
  bugs does it NOT catch (a query that runs fine but computes the wrong thing, e.g. a 6-game
  playoff "leader")? What technique from M4/roadmap Stage 9 catches *that* class instead? ___

## Exercises → `exercises.ipynb`
Grounded in the repo's real EDA data (same CSVs as M4) via DuckDB — zero new installs.
1. **Vectorized vs. row-at-a-time, felt not just read** — implement a naive Python `for`-loop sum
   over a column and a numpy vectorized sum over the same data; time both at increasing sizes and
   plot the crossover. This is the CMU lecture's idea, in your hands.
2. **Window-function drills** — write, by hand: (a) `RANK() OVER (ORDER BY pts DESC)` scoring
   leaders, (b) `AVG() OVER (PARTITION BY team_abbreviation)` team-relative scoring, (c) a
   leaderboard with a **min-games qualifier** using `QUALIFY` (or `HAVING` if you subquery first)
   — reproduce the repo's actual reliability rule against this real data.
3. **`assert_safe`, defense in depth** — a second, independent pass at the SELECT-only validator
   from M4 (single-statement, allow-listed tables/columns, no comment-hidden injection); this
   module's version should additionally **enforce a `LIMIT` ceiling** so a runaway query can't
   blow up the process — a computation-engine-specific concern M4's version didn't need.
4. **Execution-guided decoding, simulated** — given a list of candidate SQL strings (some with
   intentional bugs: bad column name, mismatched types, unbalanced parens), run a
   generate→try→catch→retry loop against DuckDB; log which errors got caught and measure the
   before/after success rate.
5. **Self-consistency voting** — given *k* candidate SQL queries answering the same question
   (some subtly wrong), execute all of them and take a majority vote over the **numeric result**;
   show a case where majority vote fixes a single bad candidate, and a case (shared blind spot)
   where it doesn't.

## Math problems (work by hand, verify in the last code cell)
1. **Big-O / constant-factor argument.** For summing *n* values, row-at-a-time interpretation
   pays a per-tuple dispatch cost `c` on top of the O(n) work: total ≈ `n·(w + c)` where `w` is
   the actual work per value. Vectorized batches of size `B` pay dispatch once per batch:
   `(n/B)·c + n·w`. For `n = 500,000`, `c = 50` (arbitrary time units), `w = 1`, and `B = 2000`,
   compute both totals and the speedup ratio — then verify your arithmetic with a code cell.
2. **Logical processing order as a proof obligation.** Given the query
   `SELECT team, AVG(pts) FROM t WHERE gp > 0 GROUP BY team HAVING AVG(pts) > 20 ORDER BY 2 DESC`,
   write out the 6 logical stages in order and state, at each stage, what the "current relation"
   looks like (schema + which rows survive). Confirm `HAVING` is evaluated on *grouped* rows and
   `WHERE` on *raw* rows — this is why you cannot write `WHERE AVG(pts) > 20`.
3. **Self-consistency probability (continuation of M4 Math Problem 2).** For *k* = 5 independent
   candidates each correct with probability *p*, derive the majority-vote correctness probability
   as a function of *p* (binomial, need ≥3/5 correct) and tabulate it for *p* ∈ {0.5, 0.6, 0.7,
   0.8}. At what *p* does majority-of-5 start clearly beating a single sample, and at what *p*
   does it stop mattering much? Verify with a code cell (brute-force enumerate the 32 outcomes).

## Definition of done
- Your vectorized-vs-loop benchmark shows a real, measured speedup (not just an assertion).
- The `QUALIFY`/`HAVING` leaderboard reproduces a *real* reliability finding on the actual EDA
  data (a small-sample leader gets correctly excluded by the games-played qualifier).
- The execution-guided retry loop measurably improves success rate over no-retry on your bugged
  candidate set.

## Ship target (repo)
Hardens `src/statlas/query/executor.py`: the `LIMIT`-ceiling + allow-list validator here is the
spec for the real one; the execution-guided retry loop is the shape of Phase-4's "draft → validate
→ execute → self-correct" path once an LLM starts drafting SQL.

## Carry-over
- The vectorized-vs-loop numbers and the qualifier finding are good material for the next
  `learning/days/dayN/summary.md` write-up.
- Self-consistency voting harness here generalizes directly to M4's CHASE-SQL stretch reading.
