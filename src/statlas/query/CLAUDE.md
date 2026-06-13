# src/statlas/query — Context

## Section 1: Evergreen

**What this is:** The query layer — the safe, deterministic "text-to-SQL" plus the only place math happens. `planner` turns a structured `Intent` into validated SQL; `executor` runs it on DuckDB and returns the exact number.

**Module map:**
- `__init__.py` — package marker
- `planner.py` — `build_sql(intent) -> (sql, params)`, `assert_safe()`, `ALLOWED_METRICS`, `ALLOWED_AGG`, `PlanError`
- `executor.py` — `run(con, sql, params) -> QueryResult` (`value`, `games`, `sql`, `params`)

**Architecture decisions (append-only, one line each):**
- SQL is assembled from a fixed template; metric/aggregation are allow-listed and inlined, all filters are parameterized — no injection surface
- `assert_safe` rejects anything not explicitly permitted
- The executor is the SOLE computation site; its result is ground truth
- Phase-4 plan: an LLM may draft SQL for queries too complex for the template, but it must pass `assert_safe`-style validation first

**Non-negotiable constraints:**
- Never execute unvalidated SQL
- `metric` and `aggregation` must be in the allow-lists
- Numbers produced here are not altered downstream

**Session log rules:** Canonical rolling session log lives in the root `CLAUDE.md`; this file stays evergreen.

## Section 2: Rolling Session Log (last 2 sessions only)

_Centralised in the root `CLAUDE.md`._
