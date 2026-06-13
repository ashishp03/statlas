# statlas — Project Context

## Section 1: Evergreen

**What this is:** An AI-powered natural-language sports-stats answer engine — "a better StatMuse." Python. A question flows through a fixed pipeline: `question → NLU (intent) → text-to-SQL → DuckDB execution → generation → answer card`. The core bet: **the LLM handles language only; the database does all arithmetic.** Currently a learning project with a working rule-based p0 scaffold; the LLM-driven pipeline is not built yet.

**Current phase:** Foundations-first learning mode (see `learning/roadmap.md`). Stage 3 (transformers & attention) is **complete**; next is Stage 4 (LLMs) → Stage 5 (prompting & tool calling). Product build is paused; the p0 rule-based scaffold is the baseline and ship target for when building resumes.

**Completed work:**
- p0 scaffold: end-to-end **rule-based** pipeline (`parser → planner → executor → engine`) running on seed data, with a CLI (`--debug`/`--rebuild`) and transparency "answer cards"
- Entity resolver (curated nicknames + rapidfuzz fuzzy match), DuckDB seed ingest, golden eval set + runner
- Learning system scaffolded: `progress.md` tracker, dated day logs, `day-template.md`, two parked advanced homework modules
- Day 5 (2026-06-13): verified **`nba_api`** as the real, free data source; ran a full **EDA** on 2025-26 data (report + 6 figures + cached CSVs in `learning/days/day5/eda/`); authored the foundations-first **roadmap**
- Roadmap **Stage 3 (transformers & attention) completed** (2026-06-13): `softmax`/`scaled_dot_product_attention`/`causal_mask` implemented from scratch in `learning/days/day5/exercises/attention_from_scratch.ipynb`, all self-check tests pass

**Module map:**
- `src/statlas/` — the engine package (the pipeline orchestrator + composer)
- `src/statlas/nlu/` — language → structured `Intent`
- `src/statlas/query/` — `Intent` → validated SQL → exact number
- `src/statlas/data/` — DuckDB warehouse builder (seed CSVs + `nba_api` ingest)
- `src/statlas/entities/` — nickname/team → canonical id resolver
- `tests/` — golden eval set + accuracy runner (the scoreboard)
- `learning/` — study system: roadmap (active), curriculum (parked), progress tracker, day logs

**Architecture decisions (append-only, one line each):**
- The LLM handles language only; **DuckDB performs every arithmetic operation** — the model never computes or recalls a stat
- A clean structured `Intent` dataclass is the contract between NLU and the query layer; any LLM parser must return the SAME `Intent`
- v0 is rule-based (regex + keyword maps) so the whole engine runs with **zero API keys**
- SQL is built from a fixed template with an allow-list of columns/aggregations (`assert_safe`); filters are parameterized — nothing to inject
- Phase-4 plan: an LLM may *draft* SQL for complex queries, but it must pass allow-list validation before execution
- The executor is the ONLY place a statistic is computed; its number is ground truth and nothing downstream may alter it
- Every `Answer` carries a transparency `card` exposing the SQL and the games used
- Entity resolution = curated nickname dict + fuzzy match; **refuses to guess** below `min_score` (returns "I don't know" rather than a wrong player)
- DuckDB is an embedded single-file OLAP DB (the "calculator"); default DB is a temp file, overridable via `STATLAS_DB`
- Seed CSVs are ILLUSTRATIVE invented numbers so the engine has data to query offline
- Real data source is `nba_api` (free, no key); `LeagueDashPlayerStats` covers 1996-97→present, deeper history via `LeagueLeaders` (~1979-80)
- Reliability rule: leaderboards need a **minimum-games qualifier** (tiny samples otherwise win — e.g. a 6-game playoff "leader")
- `game_logs` schema (`player_id, season, game_date, opponent_abbr, is_playoff, min, pts, reb, ast, plus_minus`) stays stable so the pipeline is unchanged when real data swaps in
- The learning effort runs in two modes: advanced build plan (`learning/curriculum.md`, PARKED) and foundations-first (`learning/roadmap.md`, ACTIVE)
- Start the LLM step with a free local model (Ollama); Claude Max ≠ general API access
- Dependency/env management is **uv**: deps live in `pyproject.toml`, locked in `uv.lock`, Python pinned via `.python-version` (3.12); `uv sync` installs, `uv add` adds, `uv run` executes. Runtime deps = duckdb/rapidfuzz/pandas/nba_api; `dev` group = pytest/matplotlib/ipykernel/jupyterlab; `llm` extra = anthropic. `requirements.txt` is deprecated (pointer only)

**Non-negotiable constraints:**
- The LLM never computes or recalls statistics — the database does, always
- Any model-drafted SQL is validated (SELECT-only, allow-listed) before it touches the DB
- The engine refuses to guess: an unresolved player/metric returns "I don't know," never a fabricated number
- The structured `Intent` interface between NLU and query stays stable across upgrades
- Every answer is auditable: expose the SQL and the rows used
- Free/open stack first (`nba_api`, DuckDB, local models) before any paid API
- No stat is ever hardcoded; all numbers come from a query against the data

**Session log rules:**
- Keep only the last 2 session logs below
- When adding a new log, delete the oldest if there are already 2
- Summarize deleted sessions as one-line entries under "Completed work" above
- This is the project's canonical rolling log; per-directory `CLAUDE.md` files stay evergreen and point here

## Section 2: Rolling Session Log (last 2 sessions only)


### 2026-06-13 — uv env on the Mac + Stage 3 (transformers) completed
**Built:** Stood up local dev with **uv** on the owner's Mac: ran `uv sync`, then fixed Jupyter notebooks not seeing project deps — the cause was the only registered kernel pointing at Homebrew's Python 3.13, not the project `.venv`; registered `.venv` as a kernel (`uv run python -m ipykernel install --user --name statlas`). **Bumped pinned Python 3.12 → 3.13** (`uv python pin`): tried 3.14 first but `gensim` has no 3.14 wheels and fails to build against its C API, so 3.13 is the ceiling for the current dep set; rebuilt `.venv`, re-registered the kernel, verified all imports + CLI + eval (5/5). Wrote a full **uv setup guide** into the README (install, `uv sync`, `uv run`, kernels, version-bump caveat) and reconciled the README study-plan section with `learning/roadmap.md` stages. Committed + pushed (`6237f9e`) all of the above plus the repo-wide `CLAUDE.md` context files. Then the owner **completed roadmap Stage 3 — transformers & attention**: implemented `softmax` (stable), `scaled_dot_product_attention`, and `causal_mask` from scratch in `learning/days/day5/exercises/attention_from_scratch.ipynb`; verified the notebook executes top-to-bottom with all three ✅ test cells passing. Ticked off `days/day5/TODAY.md`, updated `progress.md` (Stage 3 done → next Stage 4) and `days/day5/summary.md`.
**Notes:** Notebooks run a *kernel*, not the terminal's active venv — activation doesn't help; pick the `.venv`/`statlas` kernel. The earlier `.git/index.lock` issue did not recur (cleared stale locks pre-emptively). Next learning focus: roadmap Stage 4 (LLMs) → Stage 5 (prompting & tool calling).

### 2026-06-13 — Repo context files + today's learning checklist
**Built:** Generated `CLAUDE.md` context files across the repo (root full format; subdirectories scoped to the same format; pure output/data folders skipped). Created the explicit Stage-3 study checklist `learning/days/day5/TODAY.md` and the self-checking exercise notebook `learning/days/day5/exercises/attention_from_scratch.ipynb` (softmax, scaled dot-product attention, causal mask; verified the built-in tests pass with a correct solution). Set the roadmap entry point to Stage 3 (transformers) since Stages 1–2 are revision given the owner's MS in Data Science. **Migrated dependency management to uv:** declared deps in `pyproject.toml` (runtime + `dev` group + `llm` extra), added a `statlas` CLI entry point, pinned Python via `.python-version` (3.12), generated `uv.lock`, and deprecated `requirements.txt`. Verified in a sandbox copy: `uv lock`/`uv sync` succeed, package builds, CLI runs, and the eval suite passes 5/5 (100%).
**Notes:** No product code changed; config + context files only. uv could not be installed onto the owner's Mac from here (separate sandbox) — owner runs `uv` install + `uv sync` per machine.
