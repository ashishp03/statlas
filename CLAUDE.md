# statlas — Project Context

> **Branch overlay:** @.claude/branch.md — branch-specific instructions & rolling log for whatever
> branch you're checked out on. THIS root file is the shared, canonical context (source of truth on
> `main`); the `@import` above pulls in the current branch's specifics. See "Branch model &
> context-file workflow" below for how this is set up and how to start a new branch.

## Section 1: Evergreen

**What this is:** An AI-powered natural-language sports-stats answer engine — "a better StatMuse." Python. A question flows through a fixed pipeline: `question → NLU (intent) → text-to-SQL → DuckDB execution → generation → answer card`. The core bet: **the LLM handles language only; the database does all arithmetic.** Currently a learning project with a working rule-based p0 scaffold; the LLM-driven pipeline is not built yet.

**Current phase:** Foundations-first learning mode (see `learning/roadmap.md`). Stage 3 (transformers & attention) is **complete**; next is Stage 4 (LLMs) → Stage 5 (prompting & tool calling). Product build is paused; the p0 rule-based scaffold is the baseline and ship target for when building resumes.

**Completed work:**
- p0 scaffold: end-to-end **rule-based** pipeline (`parser → planner → executor → engine`) running on seed data, with a CLI (`--debug`/`--rebuild`) and transparency "answer cards"
- Entity resolver (curated nicknames + rapidfuzz fuzzy match), DuckDB seed ingest, golden eval set + runner
- Learning system scaffolded: `progress.md` tracker, dated day logs, `day-template.md`, two parked advanced homework modules
- Day 5 (2026-06-13): verified **`nba_api`** as the real, free data source; ran a full **EDA** on 2025-26 data (report + 6 figures + cached CSVs in `learning/days/day5/eda/`); authored the foundations-first **roadmap**
- Roadmap **Stage 3 (transformers & attention) completed** (2026-06-13): `softmax`/`scaled_dot_product_attention`/`causal_mask` implemented from scratch in `learning/days/day5/exercises/attention_from_scratch.ipynb`, all self-check tests pass
- Repo-wide `CLAUDE.md` context tree + Stage-3 study checklist/exercise notebook (2026-06-13); migrated dependency management to **uv** (`pyproject.toml` + `uv.lock`, Python pinned 3.12, `requirements.txt` dropped)
- Adopted the Option-A shared-core + per-branch-overlay branch model (2026-06-13): `@.claude/branch.md` import, `.gitattributes` `merge=ours`, `scripts/new-branch.sh`

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
- Dependency/env management is **uv**: deps live in `pyproject.toml`, locked in `uv.lock`, Python pinned via `.python-version` (3.12); `uv sync` installs, `uv add` adds, `uv run` executes. Runtime deps = duckdb/rapidfuzz/pandas/nba_api; `dev` group = pytest/matplotlib/ipykernel/jupyterlab; `llm` extra = anthropic. `requirements.txt` has been removed — `pyproject.toml` + `uv.lock` are the single source of truth

**Non-negotiable constraints:**
- The LLM never computes or recalls statistics — the database does, always
- Any model-drafted SQL is validated (SELECT-only, allow-listed) before it touches the DB
- The engine refuses to guess: an unresolved player/metric returns "I don't know," never a fabricated number
- The structured `Intent` interface between NLU and query stays stable across upgrades
- Every answer is auditable: expose the SQL and the rows used
- Free/open stack first (`nba_api`, DuckDB, local models) before any paid API
- No stat is ever hardcoded; all numbers come from a query against the data

**Branch model & context-file workflow (Option A — shared core + per-branch overlay):**
- `main` is the trunk: the SHARED source of truth for **setup + context only**. It holds this root `CLAUDE.md`, `README.md`, and the toolchain (`pyproject.toml`, `uv.lock`, `.python-version`). Edit these on `main`, then flow them to feature branches with `git merge main`.
- Product code and study/EDA material do **NOT** live on `main` and are **not merged back** into it — they live on their feature branches (`learning`, `data-exploration`, …). `main` stays lightweight: deps + docs + the branch-model infra.
- Feature branches are created FROM `main`, so they inherit the shared setup + context automatically — files are never copied between branches; a branch is a full snapshot of its parent commit. Each branch then grows its own code/material on top.
- Branch-specific instructions + log live in ONE file: `.claude/branch.md`. Same path on every branch, different content per branch (including `main`'s own trunk overlay). This root file `@import`s it, so Claude always loads "shared core + this branch's specifics."
- Subdirectory `CLAUDE.md` files describe the *code* and live on the branch that holds that code (not on `main`); a branch needing a note about one of its folders can also add a section inside its `.claude/branch.md`.
- Conflict protection: `.gitattributes` marks `.claude/branch.md` as `merge=ours`, so merging `main`↔branch always keeps the *current* branch's copy. One-time per clone: `git config merge.ours.driver true`.
- To create a new branch: `git switch -c <name> main`, then `cp .claude/branch.template.md .claude/branch.md` and fill it in — or just run `scripts/new-branch.sh <name> "purpose"`, which does both and commits. Pull later shared updates with `git merge main` (your `branch.md` is preserved).

**Session log rules:**
- Keep only the last 2 session logs below
- When adding a new log, delete the oldest if there are already 2
- Summarize deleted sessions as one-line entries under "Completed work" above
- This is the project's canonical rolling log; per-directory `CLAUDE.md` files stay evergreen and point here

## Section 2: Rolling Session Log (last 2 sessions only)


### 2026-06-22 — Claude Code automation setup + rolling-log maintenance
**Built:** Added a shared Claude Code automation suite on `main` and merged it to every branch: two PreToolUse hooks (`.claude/hooks/guard-bash.sh` forces `uv` over bare `python`/`pip`/`jupyter`; `.claude/hooks/guard-edits.sh` protects `uv.lock`/`*.duckdb` everywhere and branch-aware-blocks `src/statlas/**` edits only on `data-exploration`), wired via `.claude/settings.json`; a read-only `data-source-scout` subagent; a user-only `run-notebook` skill; and a `context7` MCP server (`.mcp.json`). All 13 hook self-tests pass. Updated the per-branch `.claude/branch.md` rolling logs on all three branches and resolved a `CLAUDE.md` conflict on `learning` in favor of `main`'s canonical branch-model wording.
**Notes:** No "Co-Authored-By: Claude" trailer per owner preference (saved to memory). FLAG: `.python-version` pins **3.12** but the active `.venv`/kernel is **3.13** — reconcile. Pruned a stale `learning` worktree at `/tmp/statlas-learning` (cleared by macOS); branch ref intact.

### 2026-06-21 — NBA data-source EDA v2 + source integration
**Built:** On `data-exploration`, built `notebooks/initial_eda_v2.ipynb` (+ `EDA_v2_FINDINGS.md` and three SVG figures): empirically mapped `nba_api` endpoint history boundaries (LeagueDash/ShotChart/PBPv3 → 1996-97, tracking → 2013-14, LeagueLeaders → 1951-52), confirmed native advanced metrics (ratings/USG/TS/PIE) vs derived/absent (PER/BPM/VORP/WS), and found V2 box-score/PBP endpoints deprecated → use V3. Added `basketball_reference_web_scraper` + `balldontlie` as deps; re-ran `initial_eda.ipynb` (kernelspec 3.12→3.13).
**Notes:** Exploration material stays on `data-exploration`; findings flow to `main` as architecture-decision/docs updates, never by merging notebooks into `main`.
