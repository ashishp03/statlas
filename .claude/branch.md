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
- 2026-06-22 — Added the shared Claude Code automation setup (commit `5226551`): PreToolUse hooks
  (`guard-bash.sh` forces uv over bare python/pip/jupyter; `guard-edits.sh` protects `uv.lock`/`*.duckdb`
  and branch-aware-blocks `src/statlas/**` edits while on `data-exploration`), wired in `.claude/settings.json`;
  `data-source-scout` subagent; user-only `run-notebook` skill; `context7` MCP (`.mcp.json`). Lives on the
  trunk so feature branches inherit it via `git merge main` and new branches off `main` get it automatically.
- 2026-06-13 — Trunk seeded: brought the uv toolchain and the root context/setup docs
  (`CLAUDE.md`, `README.md`, branch-model infra) over from the `learning` snapshot. Product code
  and study material intentionally stay on their feature branches.
