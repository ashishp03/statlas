# data-exploration — Branch Context

> Branch overlay for `data-exploration` (created 2026-06-13). The shared, canonical project context lives
> in the root `CLAUDE.md` (and subdirectory `CLAUDE.md` files) on `main`; THIS file adds only what
> is specific to this branch. Protected by `.gitattributes` (`merge=ours`) so it never merges
> across branches.

## Purpose
Explore NBA data api, find its structure, restrcitions, and understand how to use it.

## Scope — what belongs on this branch
- Owns: `notebooks/` (`initial_eda*.ipynb`) — read-only exploration of NBA data sources; and
  `experiments/vN_*/` — self-contained storage/retrieval + text-to-SQL benchmarks (each carries its own
  pipeline, data, an experiment-local eval set, and docs). Findings flow to `main`; experiment code does not.
- Belongs here: probing `nba_api` endpoints (history depth, columns, restrictions), evaluating
  alternative sources (Basketball-Reference, balldontlie, pbpstats, hoopR, shufinskiy, Kaggle), and
  documenting native-vs-derived metric availability.
- Does NOT belong here: the **product** pipeline (`src/statlas/**`), its warehouse builder, or its
  golden eval set — those live on the product branch (experiment-local pipelines/eval under
  `experiments/` are fine and separate). Findings flow into `CLAUDE.md` architecture decisions on `main`
  via a deps/docs PR, never by merging notebooks or experiment code into `main`.

## Branch-specific instructions
- Notebooks use **Polars** (convert nba_api pandas once with `pl.from_pandas`); execute them with
  `uv run --with jupyter jupyter nbconvert --execute ...` (that provisions jupyter). Deps are managed by
  **uv** (`uv add`/`uv sync`); plain `python script.py` is fine for running scripts.
- Wrap every live API call in try/except + `time.sleep` to tolerate nba_api flakiness/rate limits;
  prefer **binary-searching** boundaries over asserting years.
- Use the **V3** box-score/play-by-play endpoints — the V2 variants are deprecated and return empty.
- balldontlie cells must no-op gracefully when `BALLDONTLIE_API_KEY` is unset.

## Subdirectory notes (branch-specific)
- TODO: `<path/>` — note (only if a folder needs branch-specific guidance; otherwise its shared
  `CLAUDE.md` already covers it)

## Rolling log (most recent first)
- 2026-07-18 — Built `experiments/v1_nba_storage_retrieval_benchmark/` — a self-contained storage/retrieval
  + text-to-SQL benchmark on **real** modern-era data (S1 pulled 14.8k player-seasons, 140k game logs, 102k
  shots, BBRef advanced). Materialized **8 store formats** + an nba↔bbref `canonical_id` crosswalk (590
  matched / 2269 refused); **all 8 stores returned 128/128 eval answers exactly**; recommendation = **DuckDB
  over season-partitioned Parquet** (Parquet ~5× smaller than CSV/SQLite; CSV ~100× slower on warm reads).
  SELECT-only SQL guard + text-to-SQL bake-off (MOCK 16/16; real Ollama models pending). Vector experiment:
  **0% exact as a stat store, 94% few-shot** → "vector DB or parquet?" = different jobs. S2–S6 + docs were
  built by a background **multi-agent workflow** (executor→verifier→reviewer; custom `.claude/agents/`,
  15/20 agents clean, report module capped by usage limit but code landed). Added **`ask.py`** — interactive
  NL→guarded-SQL→DuckDB Q&A over the warehouse (prints the SQL, refuses rather than guesses; LeBron 24.43
  pts/70g 2025 verified). Two-tier eval tolerance (D6: 1e-7 gate, 0.1 for `known` anchors). **Relaxed the
  uv-run rule project-wide**: `python` runs files, uv manages deps (hook + all docs). Started NLU learning
  module `03-nlu-intent-parsing` on a `learning-nlu` worktree. `.python-version` now reads **3.13** (earlier
  3.12/3.13 FLAG appears reconciled).
- 2026-06-22 — Inherited the shared Claude Code automation setup from `main` via `git merge main`
  (PreToolUse hooks: uv-only Bash guard + branch-aware edit guard that blocks `src/statlas/**` here;
  `data-source-scout` subagent; `run-notebook` skill; `context7` MCP). `branch.md` preserved via `merge=ours`.
- 2026-06-21 — Re-ran `notebooks/initial_eda.ipynb` and saved it (commit `1f16534`); the only change was a
  kernelspec refresh (`statlas (3.12.13)` → `statlas (3.13.8.final.0)`). FLAG: `.python-version` pins **3.12**
  but the active `.venv`/kernel is **3.13** — reconcile (either repin or rebuild the env on 3.12).
- 2026-06-21 — Built `notebooks/initial_eda_v2.ipynb`: empirically mapped endpoint history boundaries
  (LeagueDash/ShotChart/PBPv3 → 1996-97, tracking → 2013-14, LeagueLeaders → 1951-52), native-vs-derived
  advanced metrics (ratings/USG/TS/PIE native; PER/BPM/VORP/WS not NBA-provided), and alternative sources
  (added `basketball_reference_web_scraper` + `balldontlie` as deps). Found V2 box-score/PBP endpoints
  deprecated → use V3. Filled Scope + Branch-specific-instructions TODOs above.
- 2026-06-13 — branch created from main.
