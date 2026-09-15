# Day 7 — 2026-09-13

**Track 1 phase:** Stage 3 ✅ → Stage 4 (LLMs) / parallel deep-dive: M4 Text-to-SQL
**Track 2 phase:** T-B (one item left: `.claude/commands/eval.md`)

## Coach suggested
- **Track 1:** Read `day7/qualifier_worked_example.md` — a **pre-run** DuckDB `QUALIFY` query
  (already executed for you against the day5 EDA CSV) showing the 3P% leaderboard with and
  without a minimum-attempts qualifier. Covers study-plan item **B5c** by example, ~5 min.
  Optional follow-on: re-run it yourself, or paste it into
  `modules/04-text-to-sql/exercises.ipynb` as a gold NL→SQL pair.
- **Track 2:** Add `.claude/commands/eval.md` — a slash command running the p0 eval set (~20 min).
  Still the only open T-B item.
- **Stretch:** **B2 — DIN-SQL** (arXiv 2304.11015), the highest-value paper in the study plan (~45 min).

## What I actually did
-

## Notes & insights
- (from the worked example) The min-games qualifier is a **no-op for per-game counting stats**
  in this dataset — the top-5 PPG list is identical with and without `GP >= 40`. It only bites on
  **rate stats**: unqualified 3P% leaders are four bigs at 100% on ~1 attempt all season.
- Consequence for Statlas: qualifier thresholds are **per-metric metadata**, not a global constant,
  and they must come from a table the planner owns — not from the LLM.

## Coding / exercises
- `day7/qualifier_worked_example.md` — DuckDB `RANK() OVER` + `QUALIFY`, run against
  `days/day5/eda/data/player_stats_2025-26_regular.csv`. Written and executed by the coach.

## Links & resources
- DuckDB window functions: https://duckdb.org/docs/sql/window_functions
- Study plan: `learning/study-plan-nlu-text-to-sql.md` (item B5c; B2 = DIN-SQL)
- M4 module: `learning/modules/04-text-to-sql/`

## Carry-over for next time
- 4 of the 5 gold NL→SQL TODO pairs in `modules/04-text-to-sql/exercises.ipynb` remain.
- `.claude/commands/eval.md` still doesn't exist on any branch.
- Housekeeping (local, needs Ashish): `git worktree prune` (~15 stale entries); commit the
  untracked `experiments/` + `ask.py` + `RESEARCH.md`/`ONBOARDING.md`/`AGENTS.md` on `data-exploration`.
