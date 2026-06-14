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
- `main` is the trunk. It holds the canonical context: this root `CLAUDE.md`, every subdirectory `CLAUDE.md`, `README.md`, and the toolchain (`pyproject.toml`, `uv.lock`, `.python-version`). These are SHARED — edit them on `main`, then flow changes to feature branches with `git merge main`.
- Feature branches (`learning`, `data-exploration`, …) are created FROM `main`, so they inherit all of the above automatically — files are never copied between branches; a branch is a full snapshot of its parent commit.
- Branch-specific instructions + log live in ONE file: `.claude/branch.md`. Same path on every branch, different content per branch. This root file `@import`s it, so Claude always loads "shared core + this branch's specifics."
- Subdirectory `CLAUDE.md` files are NOT per-branch: they describe the *code* in each folder, which doesn't change between branches. Keep them shared on `main`; if a branch needs a note about a subdirectory, add it as a section inside that branch's `.claude/branch.md` instead of forking the subdir file.
- Conflict protection: `.gitattributes` marks `.claude/branch.md` as `merge=ours`, so merging `main`↔branch always keeps the *current* branch's copy. One-time per clone: `git config merge.ours.driver true`.
- To create a new branch: `git switch -c <name> main`, then `cp .claude/branch.template.md .claude/branch.md` and fill it in — or just run `scripts/new-branch.sh <name> "purpose"`, which does both and commits. Pull later shared updates with `git merge main` (your `branch.md` is preserved).

**Session log rules:**
- Keep only the last 2 session logs below
- When adding a new log, delete the oldest if there are already 2
- Summarize deleted sessions as one-line entries under "Completed work" above
- This is the project's canonical rolling log; per-directory `CLAUDE.md` files stay evergreen and point here

## Section 2: Rolling Session Log (last 2 sessions only)


### 2026-06-13 — Repo context files + today's learning checklist
**Built:** Generated `CLAUDE.md` context files across the repo (root full format; subdirectories scoped to the same format; pure output/data folders skipped). Created the explicit Stage-3 study checklist `learning/days/day5/TODAY.md` and the self-checking exercise notebook `learning/days/day5/exercises/attention_from_scratch.ipynb` (softmax, scaled dot-product attention, causal mask; verified the built-in tests pass with a correct solution). Set the roadmap entry point to Stage 3 (transformers) since Stages 1–2 are revision given the owner's MS in Data Science. **Migrated dependency management to uv:** declared deps in `pyproject.toml` (runtime + `dev` group + `llm` extra), added a `statlas` CLI entry point, pinned Python via `.python-version` (3.12), generated `uv.lock`, and deprecated `requirements.txt`. Verified in a sandbox copy: `uv lock`/`uv sync` succeed, package builds, CLI runs, and the eval suite passes 5/5 (100%).
**Notes:** No product code changed; config + context files only. uv could not be installed onto the owner's Mac from here (separate sandbox) — owner runs `uv` install + `uv sync` per machine.

### 2026-06-13 — Option-A branch model + context-file workflow
**Built:** Adopted the shared-core + per-branch-overlay model. Added a `@.claude/branch.md` import and a "Branch model & context-file workflow" section to this root file; created `.claude/branch.md` (learning overlay), `.claude/branch.template.md`, `.gitattributes` (`.claude/branch.md merge=ours`), and `scripts/new-branch.sh` (branch off main + scaffold overlay + commit). Decision: keep ONE comprehensive root `README.md` on `main`; make `learning/README.md` the learning-branch readme (avoids a divergent same-path README). Subdirectory `CLAUDE.md` files stay shared; branch-specific subdir notes go inside `.claude/branch.md`.
**Notes:** File content written from the assistant sandbox; ALL git steps (clear `.git/*.lock`, deps-only commit/PR of the uv toolchain to `main`, branch creation, `git config merge.ours.driver true`) are run by the owner in Claude Code — git can't execute in the sandbox.
