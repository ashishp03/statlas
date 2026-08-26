# learning/modules/05-computation-engine — Context

## Section 1: Evergreen

**What this is:** Computation-engine & reliability module, built 2026-08-25 alongside `04-text-to-sql/` at Ashish's request. Covers why DuckDB's vectorized execution model is fast (DuckDB SIGMOD paper, CMU 15-445 "Query Execution 1"), execution-guided decoding (Wang 2018, arXiv 1807.03100), and self-consistency voting (Wang 2022, arXiv 2203.11171), plus math problems (vectorization cost model, logical query-processing order, self-consistency binomial probability). Ship target: hardens `src/statlas/query/executor.py`.

**Module map:**
- `workbook.md` — papers/theory/math problems + blanks
- `exercises.ipynb` — graded coding exercises (verified to execute cleanly end-to-end 2026-08-25, no TODOs left unfilled — every cell runs and every assert passes as shipped)

**Architecture decisions (append-only, one line each):**
- Same real-data grounding as M4 (`days/day5/eda/data/player_stats_2025-26_regular.csv`); the min-games-qualifier exercise uses STL (Kadary Richmond, 3 GP, tops the unqualified board) for a genuine before/after demonstration
- `assert_safe_bounded` here is deliberately a *second*, independent implementation from M4's `assert_safe` — this module's adds a `LIMIT` ceiling, a computation-engine-specific concern M4's schema-linking-focused version didn't need

**Non-negotiable constraints:**
- Not the roadmap's next default suggestion (Stage 4/LLMs remains next per `progress.md`) — parallel deep-dive

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

- **2026-08-25** — Module built from scratch (workbook + notebook), notebook execution-verified end-to-end (`jupyter nbconvert --execute`, all asserts pass as-shipped).
